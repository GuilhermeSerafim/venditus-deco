from venditus.estimate import CONVERSAO_ASSUMIDA, TICKET_MEDIO_BRL, perda_estimada


def test_parametros_default_documentados():
    assert CONVERSAO_ASSUMIDA == 0.02
    assert TICKET_MEDIO_BRL == 564.96


def test_caso_do_tenis():
    # 340 buscas x 2% x R$ 564,96
    assert perda_estimada(340) == 3841.73


def test_caso_da_capa():
    assert perda_estimada(128) == 1446.30


def test_volume_zero():
    assert perda_estimada(0) == 0.0


def test_parametros_sobrescritiveis():
    assert perda_estimada(100, conversao=0.05, ticket=100.0) == 500.0
