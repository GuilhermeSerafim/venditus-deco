from venditus.state import VenditusState, estado_inicial


def test_estado_inicial():
    s = estado_inicial("tênis impermeável", 340)
    assert s["termo"] == "tênis impermeável"
    assert s["volume"] == 340
    assert s["perda_estimada"] == 3841.73
    assert s["status"] == "novo"
    assert s["escreveu"] is False


def test_typeddict_tem_as_chaves_do_fluxo():
    chaves = set(VenditusState.__annotations__)
    for k in ("termo", "volume", "perda_estimada", "diagnostico", "decisao_guarda",
              "fix_id", "resultados_antes", "resultados_depois", "status", "escreveu"):
        assert k in chaves
