from venditus.adapters.fake import FakeCatalogAdapter
from venditus.models import Produto


def _catalogo() -> list[Produto]:
    return [
        Produto(sku="SKU-4471", titulo="Tênis Trilha Alpha",
                descricao="membrana impermeável que mantém os pés secos na trilha",
                atributos={"impermeavel": ""}, estoque=12),
        Produto(sku="SKU-8802", titulo="Capa de Chuva Leve Nimbus",
                descricao="tecido leve com repelência à água para o dia a dia",
                atributos={"impermeavel": ""}, estoque=30),
        Produto(sku="SKU-1100", titulo="Meia Térmica Basic",
                descricao="lã merino", atributos={}, estoque=0),
    ]


def test_descricao_nao_torna_o_produto_encontravel():
    # A premissa do produto: o texto livre existe, mas a busca não o alcança.
    a = FakeCatalogAdapter(_catalogo())
    assert a.buscar("tênis impermeável") == []


def test_atributo_preenchido_torna_encontravel():
    a = FakeCatalogAdapter(_catalogo())
    a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123")
    achados = a.buscar("tênis impermeável")
    assert [p.sku for p in achados] == ["SKU-4471"]


def test_busca_ignora_palavras_curtas():
    a = FakeCatalogAdapter(_catalogo())
    a.aplicar_correcao("SKU-8802", "impermeavel", "true", "def456")
    assert [p.sku for p in a.buscar("capa de chuva impermeável")] == ["SKU-8802"]


def test_produto_sem_estoque_nao_aparece():
    a = FakeCatalogAdapter(_catalogo())
    assert a.buscar("meia térmica") == []


def test_aplicar_correcao_e_idempotente():
    a = FakeCatalogAdapter(_catalogo())
    assert a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123") is True
    assert a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123") is False
    assert a.escritas == 1


def test_correcao_ja_aplicada():
    a = FakeCatalogAdapter(_catalogo())
    assert a.correcao_ja_aplicada("abc123") is False
    a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123")
    assert a.correcao_ja_aplicada("abc123") is True


def test_obter_produto():
    a = FakeCatalogAdapter(_catalogo())
    assert a.obter_produto("SKU-4471").titulo == "Tênis Trilha Alpha"
    assert a.obter_produto("SKU-XXXX") is None
