from typing import TypedDict

from venditus.estimate import perda_estimada
from venditus.models import DecisaoGuarda, Devolucao, Diagnostico


class VenditusState(TypedDict, total=False):
    """Estado que percorre o grafo.

    total=False porque os campos vão sendo preenchidos nó a nó.
    """

    termo: str
    volume: int
    perda_estimada: float
    diagnostico: Diagnostico | None
    decisao_guarda: DecisaoGuarda | None
    devolucoes_consultadas: list[Devolucao]
    """As devoluções que o guarda leu para decidir.

    O guarda usa os textos dentro do prompt e a decisão sai resumida em um
    contador. Sem guardá-los aqui, a tela de bloqueio mostraria "8 devoluções
    contradizem" — uma afirmação — em vez das frases do cliente, que é a prova.
    """
    fix_id: str | None
    resultados_antes: int
    resultados_depois: int
    status: str
    escreveu: bool


def estado_inicial(termo: str, volume: int) -> VenditusState:
    return VenditusState(
        termo=termo,
        volume=volume,
        perda_estimada=perda_estimada(volume),
        diagnostico=None,
        decisao_guarda=None,
        devolucoes_consultadas=[],
        fix_id=None,
        resultados_antes=0,
        resultados_depois=0,
        status="novo",
        escreveu=False,
    )
