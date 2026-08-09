"""Executa o demo completo com tudo real: GPT-5.6 e a loja Shopify.

Ate aqui, tudo foi provado com dubles ou com o adapter isolado. Este script
roda o caminho inteiro pela primeira vez — investigador de verdade lendo o
catalogo de verdade, guarda de verdade lendo as devolucoes.

Sao os dois casos do pitch:
  1. tenis  -> devolucoes nao contradizem -> aprova -> escreve  -> busca 0 -> 1
  2. capa   -> devolucoes contradizem     -> bloqueia -> nao escreve

  python scripts/rodar_demo.py
"""

from dotenv import load_dotenv
from langgraph.types import Command

from venditus.app import checkpointer_sqlite, montar
from venditus.seed import BUSCAS
from venditus.state import estado_inicial

load_dotenv()


def separador(titulo: str) -> None:
    print(f"\n{'=' * 66}\n{titulo}\n{'=' * 66}")


def volume_de(termo: str) -> int:
    return next((b.volume for b in BUSCAS if b.termo == termo), 100)


def mostrar_diagnostico(estado: dict) -> None:
    d = estado.get("diagnostico")
    if d is None:
        print("  (sem diagnostico)")
        return
    print(f"  causa:     {d.causa.value}  (confianca: {d.confianca})")
    print(f"  evidencia: {d.evidencia[:96]}")
    if d.correcao:
        c = d.correcao
        print(f"  propoe:    {c.campo} = {c.valor!r} em {c.sku}")
    else:
        print("  propoe:    nenhuma correcao")


def mostrar_guarda(estado: dict) -> None:
    g = estado.get("decisao_guarda")
    if g is None:
        print("  (sem decisao)")
        return
    print(f"  decisao:       {'PERMITIR' if g.permitir else 'BLOQUEAR'}")
    print(f"  justificativa: {g.justificativa[:110]}")
    print(f"  devolucoes contraditorias: {g.devolucoes_contraditorias}")


def rodar(grafo, termo: str, aprovar: bool, thread: str) -> dict:
    separador(f"CASO: {termo!r}")
    cfg = {"configurable": {"thread_id": thread}}

    estado = grafo.invoke(estado_inicial(termo, volume_de(termo)), cfg)

    print(f"\nresultados antes: {estado.get('resultados_antes')}")
    print(f"perda estimada:   R$ {estado.get('perda_estimada'):,.2f}")

    print("\n-- investigador --")
    mostrar_diagnostico(estado)

    print("\n-- guarda --")
    mostrar_guarda(estado)

    pendente = grafo.get_state(cfg).next
    if not pendente:
        print(f"\nstatus final: {estado.get('status')}  |  escreveu: {estado.get('escreveu')}")
        devolucoes = estado.get("devolucoes_consultadas") or []
        if devolucoes:
            print(f"\ndevolucoes que o guarda leu ({len(devolucoes)}):")
            for d in devolucoes[:5]:
                print(f'  "{d.motivo}"  ({d.dias_atras}d)')
        return estado

    print(f"\n>> PAUSADO para aprovacao humana (proximo no: {pendente[0]})")
    print(f">> respondendo: {'APROVAR' if aprovar else 'REJEITAR'}")
    final = grafo.invoke(Command(resume={"aprovado": aprovar}), cfg)

    print(f"\nstatus final:      {final.get('status')}")
    print(f"escreveu:          {final.get('escreveu')}")
    print(f"resultados depois: {final.get('resultados_depois')}")
    return final


def main() -> None:
    grafo = montar(checkpointer=checkpointer_sqlite(":memory:"))

    tenis = rodar(grafo, "tênis impermeável", aprovar=True, thread="demo-tenis")
    capa = rodar(grafo, "capa de chuva impermeável", aprovar=True, thread="demo-capa")

    separador("VEREDITO")
    ok_tenis = tenis.get("escreveu") and tenis.get("resultados_depois", 0) > tenis.get("resultados_antes", 0)
    ok_capa = capa.get("status") == "quarentena" and not capa.get("escreveu")

    print(f"  tenis escreveu e a busca passou a achar:  {'SIM' if ok_tenis else 'NAO'}")
    print(f"  capa foi bloqueada sem escrever:          {'SIM' if ok_capa else 'NAO'}")
    print()
    if ok_tenis and ok_capa:
        print("  Os dois casos entraram com o mesmo diagnostico e sairam diferentes.")
        print("  E a tese, com modelo real e loja real.")
    else:
        print("  ATENCAO: o comportamento esperado nao se confirmou. Veja acima.")


if __name__ == "__main__":
    main()
