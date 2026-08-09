"""Estimativa de receita perdida por busca sem resultado.

Os dois parâmetros são PREMISSAS declaradas, não medições. Devem aparecer na
tela junto do número sempre que ele for exibido.
"""

CONVERSAO_ASSUMIDA = 0.02
"""Taxa de conversão assumida para tráfego de busca. Conservadora."""

TICKET_MEDIO_BRL = 564.96
"""Ticket médio do e-commerce brasileiro, ABComm 2026."""


def perda_estimada(
    volume: int,
    conversao: float = CONVERSAO_ASSUMIDA,
    ticket: float = TICKET_MEDIO_BRL,
) -> float:
    """Receita mensal estimada perdida por um termo de busca sem resultado."""
    return round(volume * conversao * ticket, 2)
