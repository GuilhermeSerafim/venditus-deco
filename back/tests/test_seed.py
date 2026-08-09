from venditus.adapters.fake import FakeCatalogAdapter
from venditus.seed import BUSCAS, CATALOGO, DEVOLUCOES, devolucoes_do_sku


def test_os_dois_skus_do_demo_existem():
    skus = {p.sku for p in CATALOGO}
    assert "SKU-4471" in skus
    assert "SKU-8802" in skus


def test_ambos_com_atributo_vazio():
    # O diagnóstico do investigador precisa sair IDÊNTICO nos dois casos.
    por_sku = {p.sku: p for p in CATALOGO}
    assert por_sku["SKU-4471"].atributos["impermeavel"] == ""
    assert por_sku["SKU-8802"].atributos["impermeavel"] == ""


def test_as_duas_buscas_dao_zero():
    a = FakeCatalogAdapter(CATALOGO)
    assert a.buscar("tênis impermeável") == []
    assert a.buscar("capa de chuva impermeável") == []


def test_volumes_do_demo():
    por_termo = {b.termo: b.volume for b in BUSCAS}
    assert por_termo["tênis impermeável"] == 340
    assert por_termo["capa de chuva impermeável"] == 128


def test_devolucoes_separam_os_casos():
    tenis = devolucoes_do_sku("SKU-4471")
    capa = devolucoes_do_sku("SKU-8802")
    assert len(tenis) == 3
    assert not any("molh" in d.motivo.lower() or "impermeáv" in d.motivo.lower() for d in tenis)
    assert len(capa) == 11
    agua = [d for d in capa if "molh" in d.motivo.lower() or "impermeáv" in d.motivo.lower()]
    assert len(agua) == 8


def test_devolucoes_do_sku_desconhecido():
    assert devolucoes_do_sku("SKU-XXXX") == []
