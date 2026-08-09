"""KPIs agregados do dashboard.

Operam sobre uma lista de estados finais de execucao, mantida pela camada que
roda o grafo. Nenhum acoplamento com o checkpointer.
"""

from venditus.adapters.fake import VALORES_VERDADEIROS
from venditus.models import Produto
from venditus.state import VenditusState

STATUS_BLOQUEADO = "quarentena"


def cobertura_de_atributo(produtos: list[Produto], campo: str) -> float:
    """Fracao de produtos com o atributo estruturado preenchido."""
    if not produtos:
        return 0.0
    preenchidos = sum(
        1 for p in produtos if str(p.atributos.get(campo, "")).lower() in VALORES_VERDADEIROS
    )
    return preenchidos / len(produtos)


def taxa_de_bloqueio(estados: list[VenditusState]) -> float:
    """Fracao de execucoes que o guarda recusou.

    E a metrica do diferencial: nenhum concorrente consegue calcula-la, porque
    nenhum tem o sinal de pre-venda e o de pos-venda no mesmo motor.
    """
    if not estados:
        return 0.0
    bloqueados = sum(1 for e in estados if e.get("status") == STATUS_BLOQUEADO)
    return bloqueados / len(estados)


def receita_recuperada(estados: list[VenditusState]) -> float:
    """Soma da perda estimada apenas das execucoes que resultaram em escrita."""
    return round(sum(e.get("perda_estimada", 0.0) for e in estados if e.get("escreveu")), 2)


def resumo_kpis(produtos: list[Produto], estados: list[VenditusState], campo: str) -> dict:
    """Os quatro numeros do dashboard, mais o denominador de cada um."""
    return {
        "cobertura_de_atributo": cobertura_de_atributo(produtos, campo),
        "receita_recuperada": receita_recuperada(estados),
        "bloqueados": sum(1 for e in estados if e.get("status") == STATUS_BLOQUEADO),
        "execucoes": len(estados),
        "taxa_de_bloqueio": taxa_de_bloqueio(estados),
    }
