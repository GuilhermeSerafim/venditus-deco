from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.nodes import criar_guarda
from venditus.state import estado_inicial
from tests.fakes import FakeLLM


def _diag(sku: str) -> Diagnostico:
    return Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE, confianca="alta", evidencia="menção a impermeabilidade",
        correcao=CorrecaoProposta(sku=sku, campo="impermeavel", valor="true"),
    )


def test_permite_quando_devolucoes_nao_contradizem():
    llm = FakeLLM(DecisaoGuarda(permitir=True, justificativa="nenhuma menção a água", devolucoes_contraditorias=0))
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag("SKU-4471")
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is True
    assert saida["status"] == "aprovado_pelo_guarda"


def test_bloqueia_quando_devolucoes_contradizem():
    llm = FakeLLM(DecisaoGuarda(permitir=False, justificativa="8 de 11 falam de água", devolucoes_contraditorias=8))
    s = estado_inicial("capa de chuva impermeável", 128)
    s["diagnostico"] = _diag("SKU-8802")
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is False
    assert saida["status"] == "bloqueado_pelo_guarda"


def test_prompt_do_guarda_inclui_as_devolucoes_do_sku_certo():
    llm = FakeLLM(DecisaoGuarda(permitir=False, justificativa="x", devolucoes_contraditorias=8))
    s = estado_inicial("capa de chuva impermeável", 128)
    s["diagnostico"] = _diag("SKU-8802")
    criar_guarda(llm)(s)
    assert "Molhou tudo dentro da bolsa" in llm.prompt_recebido
    # Não deve vazar devolução de outro SKU.
    assert "Cor diferente da foto" not in llm.prompt_recebido


def test_sem_correcao_permite_sem_chamar_o_llm():
    llm = FakeLLM(None)
    s = estado_inicial("mochila cargueira 80 litros", 64)
    s["diagnostico"] = Diagnostico(causa=Causa.SEM_SORTIMENTO, confianca="alta",
                                   evidencia="não há item de 80L", correcao=None)
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is True
    assert llm.prompt_recebido is None
