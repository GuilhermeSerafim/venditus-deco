"""Confirma a superficie de API do LangGraph instalada antes de construir em cima.

Esta e a Task 0 do plano. Se algum import falhar aqui, o plano inteiro precisa
ser ajustado antes de qualquer implementacao.
"""

from importlib.metadata import version


def v(pkg: str) -> str:
    try:
        return version(pkg)
    except Exception as exc:  # noqa: BLE001
        return f"<indisponivel: {exc}>"


print("=== versoes ===")
for pkg in ("langgraph", "langgraph-checkpoint", "langgraph-checkpoint-sqlite",
            "langchain-openai", "langchain-core", "pydantic", "openai"):
    print(f"  {pkg}: {v(pkg)}")

print("\n=== grafo ===")
from langgraph.graph import END, START, StateGraph

print("  StateGraph:", StateGraph.__module__)
print("  START/END:", repr(START), repr(END))

print("\n=== interrupt / Command ===")
try:
    from langgraph.types import Command, interrupt

    print("  origem: langgraph.types")
except ImportError as exc:
    print("  langgraph.types falhou:", exc)
    from langgraph.constants import Command, interrupt

    print("  origem: langgraph.constants")
print("  interrupt:", interrupt)
print("  Command:", Command)

print("\n=== checkpointers ===")
from langgraph.checkpoint.memory import MemorySaver

print("  MemorySaver:", MemorySaver.__module__)

try:
    from langgraph.checkpoint.sqlite import SqliteSaver

    print("  SqliteSaver:", SqliteSaver.__module__)
    print("  tem from_conn_string:", hasattr(SqliteSaver, "from_conn_string"))
except ImportError as exc:
    print("  SqliteSaver INDISPONIVEL:", exc)

print("\n=== langchain-openai ===")
from langchain_openai import ChatOpenAI

campos = ChatOpenAI.model_fields
assert "reasoning_effort" in campos, "reasoning_effort ausente — langchain-openai < 1.4.1"
print("  reasoning_effort: OK")
print("  tem temperature:", "temperature" in campos)
print("  tem with_structured_output:", hasattr(ChatOpenAI, "with_structured_output"))

print("\n=== smoke funcional do grafo ===")
from typing import TypedDict


class S(TypedDict, total=False):
    n: int
    marca: str


def no_a(state: S) -> S:
    return {**state, "n": state.get("n", 0) + 1}


def no_pausa(state: S) -> S:
    resposta = interrupt({"pergunta": "continuar?"})
    return {**state, "marca": str(resposta)}


g = StateGraph(S)
g.add_node("a", no_a)
g.add_node("pausa", no_pausa)
g.add_edge(START, "a")
g.add_edge("a", "pausa")
g.add_edge("pausa", END)
app = g.compile(checkpointer=MemorySaver())

cfg = {"configurable": {"thread_id": "smoke-1"}}
r1 = app.invoke({"n": 0}, cfg)
print("  1a invocacao:", r1)
snap = app.get_state(cfg)
print("  pausou? next =", snap.next)
r2 = app.invoke(Command(resume={"aprovado": True}), cfg)
print("  apos resume:", r2)

print("\n=== Task 0 concluida ===")
