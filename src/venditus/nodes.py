"""Nós determinísticos do grafo Venditus: ingest, quarentena, executor, verificador.

Os nós de LLM (investigador, guarda) vêm nas Tasks 8 e 9.
"""

from collections.abc import Callable

from venditus.adapters.base import CatalogAdapter
from venditus.fixid import fix_id as calcular_fix_id
from venditus.state import VenditusState

Node = Callable[[VenditusState], VenditusState]


def criar_ingest(catalogo: CatalogAdapter) -> Node:
    """Registra quantos resultados a busca do lojista retorna antes de qualquer ação."""

    def ingest(state: VenditusState) -> VenditusState:
        return {
            **state,
            "resultados_antes": len(catalogo.buscar(state["termo"])),
            "status": "diagnosticando",
        }

    return ingest


def quarentena(state: VenditusState) -> VenditusState:
    """Encerra o fluxo sem escrever. O caso vira hipótese para qualidade."""
    return {**state, "status": "quarentena", "escreveu": False}


def criar_executor(catalogo: CatalogAdapter) -> Node:
    """Escreve no catálogo.

    IDEMPOTENTE POR CONTRATO. Este nó roda depois do interrupt(), e retomar de
    um interrupt re-executa o nó inteiro desde o início. Sem a checagem de
    fix_id, cada retomada duplicaria a escrita.
    """

    def executor(state: VenditusState) -> VenditusState:
        diagnostico = state.get("diagnostico")
        if diagnostico is None or diagnostico.correcao is None:
            return {**state, "status": "sem_correcao", "escreveu": False}

        c = diagnostico.correcao
        fid = calcular_fix_id(c.sku, c.campo, c.valor)

        if catalogo.correcao_ja_aplicada(fid):
            return {**state, "fix_id": fid, "escreveu": True, "status": "aplicado"}

        catalogo.aplicar_correcao(c.sku, c.campo, c.valor, fid)
        return {**state, "fix_id": fid, "escreveu": True, "status": "aplicado"}

    return executor


def criar_verificador(catalogo: CatalogAdapter) -> Node:
    """Mede o resultado da busca depois da correção aplicada."""

    def verificador(state: VenditusState) -> VenditusState:
        return {
            **state,
            "resultados_depois": len(catalogo.buscar(state["termo"])),
            "status": "aplicado",
        }

    return verificador
