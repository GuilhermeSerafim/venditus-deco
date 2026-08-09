import pytest
from pydantic import ValidationError
from venditus.models import Causa, CorrecaoProposta, Diagnostico, DecisaoGuarda, Produto, Devolucao


def test_causa_tem_as_seis_categorias():
    assert {c.value for c in Causa} == {
        "typo", "sinonimo", "atributo_ausente",
        "categorizacao_errada", "sem_estoque", "sem_sortimento",
    }


def test_diagnostico_aceita_correcao():
    d = Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE,
        confianca="alta",
        evidencia="membrana impermeável que mantém os pés secos",
        correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
    )
    assert d.correcao.sku == "SKU-4471"


def test_diagnostico_sem_correcao_e_valido():
    d = Diagnostico(causa=Causa.SEM_SORTIMENTO, confianca="alta", evidencia="nada no catálogo", correcao=None)
    assert d.correcao is None


def test_confianca_invalida_rejeitada():
    with pytest.raises(ValidationError):
        Diagnostico(causa=Causa.TYPO, confianca="altissima", evidencia="x", correcao=None)


def test_decisao_guarda():
    g = DecisaoGuarda(permitir=False, justificativa="8 devoluções contradizem", devolucoes_contraditorias=8)
    assert g.permitir is False
    assert g.devolucoes_contraditorias == 8


def test_produto_e_devolucao():
    p = Produto(sku="SKU-4471", titulo="Tênis Trilha Alpha", descricao="membrana impermeável",
                atributos={"impermeavel": ""}, estoque=12)
    assert p.estoque == 12
    d = Devolucao(sku="SKU-4471", motivo="tamanho pequeno", dias_atras=30)
    assert d.dias_atras == 30
