from venditus.adapters.fake import FakeCatalogAdapter
from venditus.fixid import fix_id
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.nodes import criar_executor, criar_ingest, criar_verificador, quarentena
from venditus.seed import CATALOGO
from venditus.state import estado_inicial


def _diag() -> Diagnostico:
    return Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE, confianca="alta",
        evidencia="Membrana impermeável",
        correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
    )


def test_ingest_registra_resultados_antes():
    a = FakeCatalogAdapter(CATALOGO)
    saida = criar_ingest(a)(estado_inicial("tênis impermeável", 340))
    assert saida["resultados_antes"] == 0
    assert saida["status"] == "diagnosticando"


def test_quarentena_marca_e_nao_escreve():
    s = estado_inicial("capa de chuva impermeável", 128)
    s["decisao_guarda"] = DecisaoGuarda(permitir=False, justificativa="8 devoluções", devolucoes_contraditorias=8)
    saida = quarentena(s)
    assert saida["status"] == "quarentena"
    assert saida["escreveu"] is False


def test_executor_escreve_e_marca():
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    saida = criar_executor(a)(s)
    assert saida["escreveu"] is True
    assert saida["fix_id"] == fix_id("SKU-4471", "impermeavel", "true")
    assert a.escritas == 1


def test_executor_e_idempotente():
    # Retomar de um interrupt re-executa o no inteiro. Nao pode escrever de novo.
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    executor = criar_executor(a)
    executor(s)
    executor(s)
    executor(s)
    assert a.escritas == 1


def test_executor_sem_correcao_nao_escreve():
    # Causas SEM_ESTOQUE e SEM_SORTIMENTO nao geram correcao. O guarda aprova
    # esses casos sem chamar o LLM, entao o executor recebe correcao=None no
    # fluxo real — este branch e alcancavel, nao defensivo.
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("mochila cargueira 80 litros", 64)
    s["diagnostico"] = Diagnostico(
        causa=Causa.SEM_SORTIMENTO,
        confianca="alta",
        evidencia="não há item de 80L no catálogo",
        correcao=None,
    )
    saida = criar_executor(a)(s)
    assert saida["status"] == "sem_correcao"
    assert saida["escreveu"] is False
    assert a.escritas == 0


def test_verificador_mede_antes_e_depois():
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    s["resultados_antes"] = 0
    criar_executor(a)(s)
    saida = criar_verificador(a)(s)
    assert saida["resultados_depois"] == 1
    assert saida["status"] == "aplicado"
