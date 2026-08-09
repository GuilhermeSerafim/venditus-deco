"""Testes do adapter Shopify com transporte HTTP simulado.

Sem rede e sem credencial: a suite inteira continua rodando em qualquer maquina.
As respostas simuladas abaixo reproduzem o formato real que a loja devolveu.
"""

import httpx
import pytest

from venditus.adapters.shopify import ESTOQUE_NAO_RASTREADO, ShopifyCatalogAdapter


def _produto(sku, titulo, descricao="", metafields=None, tracks=False, total=0):
    return {
        "id": f"gid://shopify/Product/{abs(hash(sku)) % 10**10}",
        "title": titulo,
        "description": descricao,
        "totalInventory": total,
        "tracksInventory": tracks,
        "variants": {"nodes": [{"sku": sku}]},
        "metafields": {"nodes": metafields or []},
    }


CATALOGO_FALSO = [
    # Como a loja real ficou: sem metafield, sem rastreio de estoque.
    _produto("SKU-4471", "Tênis Trilha Alpha", "Membrana impermeável que mantém os pés secos."),
    _produto("SKU-8802", "Capa de Chuva Leve Nimbus", "Tecido leve com repelência à água."),
    # Um produto com rastreio e estoque zerado, para o contraste.
    _produto("SKU-0000", "Lanterna Esgotada", "Sem estoque.", tracks=True, total=0),
]


def _adapter(catalogo=None, ao_gravar=None):
    catalogo = CATALOGO_FALSO if catalogo is None else catalogo
    estado = {"metafields": {}}

    def responder(request: httpx.Request) -> httpx.Response:
        corpo = request.read().decode()
        if "metafieldsSet" in corpo:
            if ao_gravar is not None:
                return ao_gravar(request)
            estado["metafields"]["ultimo"] = corpo
            return httpx.Response(
                200,
                json={
                    "data": {
                        "metafieldsSet": {
                            "metafields": [{"key": "impermeavel", "value": "true"}],
                            "userErrors": [],
                        }
                    }
                },
            )
        return httpx.Response(200, json={"data": {"products": {"nodes": catalogo}}})

    cliente = httpx.Client(transport=httpx.MockTransport(responder))
    adapter = ShopifyCatalogAdapter(
        dominio="loja-teste.myshopify.com", token="shpat_teste", versao="2026-07", cliente=cliente
    )
    return adapter, estado


def test_url_montada_com_a_versao():
    adapter, _ = _adapter()
    assert adapter.url == "https://loja-teste.myshopify.com/admin/api/2026-07/graphql.json"


def test_metafield_ausente_nao_vira_chave():
    # A Shopify rejeita valor vazio; ausencia e a representacao real.
    adapter, _ = _adapter()
    produto = adapter.obter_produto("SKU-4471")
    assert produto is not None
    assert "impermeavel" not in produto.atributos


def test_metafield_presente_vira_atributo():
    catalogo = [
        _produto(
            "SKU-4471",
            "Tênis Trilha Alpha",
            metafields=[{"key": "impermeavel", "value": "true"}],
        )
    ]
    adapter, _ = _adapter(catalogo)
    assert adapter.obter_produto("SKU-4471").atributos["impermeavel"] == "true"


def test_estoque_nao_rastreado_conta_como_disponivel():
    # totalInventory=0 com tracksInventory=False significa vendavel na Shopify.
    # Tratar como zero esconderia o produto e quebraria o demo.
    adapter, _ = _adapter()
    assert adapter.obter_produto("SKU-4471").estoque == ESTOQUE_NAO_RASTREADO


def test_estoque_rastreado_e_zerado_conta_como_zero():
    adapter, _ = _adapter()
    assert adapter.obter_produto("SKU-0000").estoque == 0


def test_busca_nao_encontra_pela_descricao():
    # Mesma premissa do fake: texto livre nao torna o item encontravel.
    adapter, _ = _adapter()
    assert adapter.buscar("tênis impermeável") == []


def test_busca_encontra_com_o_atributo_preenchido():
    catalogo = [
        _produto(
            "SKU-4471",
            "Tênis Trilha Alpha",
            "Membrana impermeável.",
            metafields=[{"key": "impermeavel", "value": "true"}],
        )
    ]
    adapter, _ = _adapter(catalogo)
    assert [p.sku for p in adapter.buscar("tênis impermeável")] == ["SKU-4471"]


def test_produto_sem_estoque_nao_aparece_na_busca():
    adapter, _ = _adapter()
    assert adapter.buscar("lanterna esgotada") == []


def test_aplicar_correcao_grava_e_conta():
    adapter, estado = _adapter()
    assert adapter.aplicar_correcao("SKU-4471", "impermeavel", "true", "fix-1") is True
    assert adapter.escritas == 1
    enviado = estado["metafields"]["ultimo"]
    assert "venditus" in enviado
    assert "impermeavel" in enviado


def test_aplicar_correcao_e_idempotente():
    # Retomar de um interrupt re-executa o no; nao pode gravar de novo.
    adapter, _ = _adapter()
    adapter.aplicar_correcao("SKU-4471", "impermeavel", "true", "fix-1")
    assert adapter.aplicar_correcao("SKU-4471", "impermeavel", "true", "fix-1") is False
    assert adapter.escritas == 1


def test_correcao_ja_aplicada():
    adapter, _ = _adapter()
    assert adapter.correcao_ja_aplicada("fix-1") is False
    adapter.aplicar_correcao("SKU-4471", "impermeavel", "true", "fix-1")
    assert adapter.correcao_ja_aplicada("fix-1") is True


def test_sku_desconhecido_levanta():
    adapter, _ = _adapter()
    with pytest.raises(KeyError):
        adapter.aplicar_correcao("SKU-XXXX", "impermeavel", "true", "fix-1")


def test_user_errors_viram_excecao_e_nao_contam_escrita():
    def falhar(_request):
        return httpx.Response(
            200,
            json={
                "data": {
                    "metafieldsSet": {
                        "metafields": [],
                        "userErrors": [{"field": ["value"], "message": "Value can't be blank."}],
                    }
                }
            },
        )

    adapter, _ = _adapter(ao_gravar=falhar)
    with pytest.raises(RuntimeError, match="metafieldsSet"):
        adapter.aplicar_correcao("SKU-4471", "impermeavel", "", "fix-1")
    assert adapter.escritas == 0
    assert adapter.correcao_ja_aplicada("fix-1") is False


def test_erro_de_graphql_vira_excecao():
    def falhar(_request):
        return httpx.Response(200, json={"errors": [{"message": "Access denied"}]})

    cliente = httpx.Client(transport=httpx.MockTransport(falhar))
    adapter = ShopifyCatalogAdapter(
        dominio="x.myshopify.com", token="t", versao="2026-07", cliente=cliente
    )
    with pytest.raises(RuntimeError, match="Shopify GraphQL"):
        adapter.listar_produtos()
