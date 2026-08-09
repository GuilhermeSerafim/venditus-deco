"""Monta o grafo Venditus.

START → ingest → investigador(LLM) → guarda(LLM) → [contradição?]
                                                      ├─ sim → quarentena → END
                                                      └─ não → aprovacao → [aprovado?]
                                                                  ├─ sim → executor → verificador → END
                                                                  └─ não → END

A aresta guarda → quarentena é o produto: quando o pós-venda contradiz a
correção proposta, o caminho até a escrita simplesmente não existe.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from venditus.adapters.base import CatalogAdapter
from venditus.nodes import (
    criar_executor,
    criar_guarda,
    criar_ingest,
    criar_investigador,
    criar_verificador,
    quarentena,
)
from venditus.state import VenditusState


def aprovacao(state: VenditusState) -> VenditusState:
    """Ponto de parada para decisão humana.

    Este nó NÃO escreve nada. Retomar de um interrupt() re-executa o nó
    inteiro desde o início, então qualquer escrita colocada aqui aconteceria
    duas vezes. A escrita mora no nó `executor`, posterior a este.
    """
    diagnostico = state.get("diagnostico")
    decisao = state.get("decisao_guarda")
    resposta = interrupt(
        {
            "termo": state["termo"],
            "perda_estimada": state["perda_estimada"],
            "diagnostico": diagnostico.model_dump() if diagnostico else None,
            "decisao_guarda": decisao.model_dump() if decisao else None,
        }
    )
    aprovado = bool(resposta.get("aprovado")) if isinstance(resposta, dict) else bool(resposta)
    return {**state, "status": "aprovado" if aprovado else "rejeitado"}


def rotear_apos_guarda(state: VenditusState) -> str:
    decisao = state.get("decisao_guarda")
    return "aprovacao" if decisao is not None and decisao.permitir else "quarentena"


def rotear_apos_aprovacao(state: VenditusState) -> str:
    return "executor" if state.get("status") == "aprovado" else "fim"


def construir_grafo(
    catalogo: CatalogAdapter,
    llm_investigador,
    llm_guarda,
    checkpointer,
):
    """Monta e compila o grafo Venditus com os adaptadores e LLMs fornecidos."""
    g = StateGraph(VenditusState)

    g.add_node("ingest", criar_ingest(catalogo))
    g.add_node("investigador", criar_investigador(llm_investigador, catalogo))
    g.add_node("guarda", criar_guarda(llm_guarda))
    g.add_node("quarentena", quarentena)
    g.add_node("aprovacao", aprovacao)
    g.add_node("executor", criar_executor(catalogo))
    g.add_node("verificador", criar_verificador(catalogo))

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "investigador")
    g.add_edge("investigador", "guarda")

    # A ARESTA QUE DEFINE O PRODUTO: contradição no pós-venda desvia para
    # quarentena, e o caminho até a escrita deixa de existir.
    g.add_conditional_edges(
        "guarda", rotear_apos_guarda, {"aprovacao": "aprovacao", "quarentena": "quarentena"}
    )
    g.add_edge("quarentena", END)

    g.add_conditional_edges(
        "aprovacao", rotear_apos_aprovacao, {"executor": "executor", "fim": END}
    )
    g.add_edge("executor", "verificador")
    g.add_edge("verificador", END)

    return g.compile(checkpointer=checkpointer)
