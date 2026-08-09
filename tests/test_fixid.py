from venditus.fixid import fix_id


def test_deterministico():
    assert fix_id("SKU-4471", "impermeavel", "true") == fix_id("SKU-4471", "impermeavel", "true")


def test_muda_com_o_sku():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-8802", "impermeavel", "true")


def test_muda_com_o_campo():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-4471", "cor", "true")


def test_muda_com_o_valor():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-4471", "impermeavel", "false")


def test_formato():
    v = fix_id("SKU-4471", "impermeavel", "true")
    assert len(v) == 16
    assert all(c in "0123456789abcdef" for c in v)
