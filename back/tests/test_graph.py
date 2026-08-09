from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.seed import CATALOGO
from venditus.state import estado_inicial
from tests.fakes import FakeLLM


def _diag(sku):
    return Diagnostico(causa=Causa.ATRIBUTO_AUSENTE, confianca="alta",
                       evidencia="menção a impermeabilidade",
                       correcao=CorrecaoProposta(sku=sku, campo="impermeavel", valor="true"))


def _montar(sku, permitir, contraditorias):
    catalogo = FakeCatalogAdapter(CATALOGO)
    grafo = construir_grafo(
        catalogo=catalogo,
        llm_investigador=FakeLLM(_diag(sku)),
        llm_guarda=FakeLLM(DecisaoGuarda(permitir=permitir, justificativa="teste",
                                         devolucoes_contraditorias=contraditorias)),
        checkpointer=MemorySaver(),
    )
    return grafo, catalogo


def test_caminho_bloqueado_nao_escreve():
    grafo, catalogo = _montar("SKU-8802", permitir=False, contraditorias=8)
    cfg = {"configurable": {"thread_id": "t-bloqueio"}}
    final = grafo.invoke(estado_inicial("capa de chuva impermeável", 128), cfg)
    assert final["status"] == "quarentena"
    assert final["escreveu"] is False
    assert catalogo.escritas == 0


def test_caminho_feliz_pausa_no_interrupt():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-pausa"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    # Pausado: nada escrito ainda.
    assert catalogo.escritas == 0
    assert grafo.get_state(cfg).next  # há nó pendente


def test_caminho_feliz_escreve_apos_aprovacao():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-aprova"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    final = grafo.invoke(Command(resume={"aprovado": True}), cfg)
    assert final["escreveu"] is True
    assert final["resultados_antes"] == 0
    assert final["resultados_depois"] == 1
    assert catalogo.escritas == 1


def test_rejeicao_humana_nao_escreve():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-rejeita"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    final = grafo.invoke(Command(resume={"aprovado": False}), cfg)
    assert final["escreveu"] is False
    assert catalogo.escritas == 0
