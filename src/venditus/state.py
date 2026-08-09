from typing import TypedDict

from venditus.estimate import perda_estimada
from venditus.models import DecisaoGuarda, Diagnostico


class VenditusState(TypedDict, total=False):
    """Estado que percorre o grafo.

    total=False porque os campos vão sendo preenchidos nó a nó.
    """

    termo: str
    volume: int
    perda_estimada: float
    diagnostico: Diagnostico | None
    decisao_guarda: DecisaoGuarda | None
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
        fix_id=None,
        resultados_antes=0,
        resultados_depois=0,
        status="novo",
        escreveu=False,
    )
