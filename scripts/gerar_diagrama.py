"""Gera o diagrama do grafo para o pitch.

Entregavel comprometido do video: sai do grafo compilado de verdade, nao de um
desenho a mao. Nao precisa de servidor, de chave nem de internet.
"""

from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.seed import CATALOGO


class _Stub:
    """LLM de mentira. So existe para o grafo compilar — nada e invocado."""

    def with_structured_output(self, _schema):
        return self

    def invoke(self, _prompt):
        raise NotImplementedError("stub apenas para desenhar o grafo")


def main() -> None:
    grafo = construir_grafo(
        catalogo=FakeCatalogAdapter(CATALOGO),
        llm_investigador=_Stub(),
        llm_guarda=_Stub(),
        checkpointer=MemorySaver(),
    )

    saida = Path("docs/arquitetura")
    saida.mkdir(parents=True, exist_ok=True)

    mermaid = grafo.get_graph().draw_mermaid()
    (saida / "grafo.mmd").write_text(mermaid, encoding="utf-8")
    print(f"mermaid: {saida / 'grafo.mmd'}")

    try:
        (saida / "grafo.png").write_bytes(grafo.get_graph().draw_mermaid_png())
        print(f"png:     {saida / 'grafo.png'}")
    except Exception as exc:  # noqa: BLE001 — renderizacao de PNG exige rede
        print(f"png:     nao gerado ({type(exc).__name__}). O .mmd serve — cole em mermaid.live")

    # A aresta que e o produto precisa estar no desenho.
    arestas_guarda = [e for e in grafo.get_graph().edges if e.source == "guarda"]
    print()
    print("arestas saindo de guarda:")
    for e in arestas_guarda:
        tipo = "condicional" if e.conditional else "direta"
        print(f"  guarda --[{tipo}]--> {e.target}")

    alvos = {e.target for e in arestas_guarda}
    if {"aprovacao", "quarentena"} <= alvos:
        print("\nOK: a bifurcacao do guarda esta no diagrama.")
    else:
        raise SystemExit(f"ERRO: esperava aprovacao e quarentena, encontrei {alvos}")


if __name__ == "__main__":
    main()
