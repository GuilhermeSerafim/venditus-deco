"""Mede a acuracia do investigador contra o conjunto rotulado a mao.

Faz chamadas reais ao modelo. Exige OPENAI_API_KEY.

E o unico numero que responde "o agente funciona?" em vez de "o agente roda?".
Os testes automatizados usam duble de LLM: provam o encanamento, nao o
julgamento.

  python scripts/avaliar_classificador.py
"""

from collections import defaultdict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.app import MODELO
from venditus.nodes import criar_investigador
from venditus.seed import CATALOGO
from venditus.state import estado_inicial
from venditus.avaliacao import ROTULADOS

load_dotenv()


def main() -> None:
    catalogo = FakeCatalogAdapter(CATALOGO)

    # Um rotulo sobre uma busca que funciona nao testa nada — o agente so ve
    # buscas que falharam.
    invalidos = [t for t, _ in ROTULADOS if catalogo.buscar(t)]
    if invalidos:
        raise SystemExit(f"Itens que retornam resultado e nao deveriam: {invalidos}")

    investigador = criar_investigador(
        ChatOpenAI(model=MODELO, reasoning_effort="medium"), catalogo
    )

    acertos = 0
    por_causa: dict[str, list[bool]] = defaultdict(list)
    confusoes: list[tuple[str, str, str]] = []

    print(f"modelo: {MODELO}  |  {len(ROTULADOS)} buscas\n")

    for termo, esperado in ROTULADOS:
        estado = estado_inicial(termo, 100)
        estado["resultados_antes"] = 0
        obtido = investigador(estado)["diagnostico"].causa

        ok = obtido == esperado
        acertos += ok
        por_causa[esperado.value].append(ok)
        if not ok:
            confusoes.append((termo, esperado.value, obtido.value))

        marca = "ok  " if ok else "ERRO"
        print(f"  {marca}  {termo:34} esperado={esperado.value:18} obtido={obtido.value}")

    total = len(ROTULADOS)
    print(f"\n{'=' * 62}")
    print(f"ACURACIA: {acertos}/{total} = {acertos / total:.0%}")
    print("=" * 62)

    print("\npor causa:")
    for causa, resultados in sorted(por_causa.items()):
        certos = sum(resultados)
        print(f"  {causa:20} {certos}/{len(resultados)}")

    if confusoes:
        print("\nonde errou:")
        for termo, esperado, obtido in confusoes:
            print(f"  {termo!r}: esperava {esperado}, respondeu {obtido}")

    print(
        "\nSe a acuracia ficar abaixo de ~70%, o problema costuma ser o prompt,"
        "\nnao o modelo: ajuste as descricoes das causas em PROMPT_INVESTIGADOR"
        "\nantes de subir para gpt-5.6-sol."
    )


if __name__ == "__main__":
    main()
