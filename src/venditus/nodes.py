"""Nós determinísticos do grafo Venditus: ingest, quarentena, executor, verificador.

Os nós de LLM (investigador, guarda) vêm nas Tasks 8 e 9.
"""

from collections.abc import Callable

from venditus.adapters.base import CatalogAdapter
from venditus.fixid import fix_id as calcular_fix_id
from venditus.models import DecisaoGuarda, Diagnostico
from venditus.seed import devolucoes_do_sku
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


PROMPT_INVESTIGADOR = """Você analisa por que uma busca no e-commerce não retornou resultados.

Termo buscado: "{termo}"
Resultados retornados: {resultados}

Catálogo disponível:
{catalogo}

Classifique a causa em uma das seis categorias e, quando couber, proponha UMA
correção de atributo estruturado.

Regras:
- "atributo_ausente": o produto existe e a descrição sustenta o termo, mas o
  atributo estruturado correspondente está vazio. Proponha preenchê-lo.
- "sinonimo": o cliente usa uma palavra que o catálogo não usa.
- "typo": erro de digitação no termo.
- "categorizacao_errada": o produto está na categoria errada.
- "sem_estoque": o produto existe mas está zerado. NÃO proponha correção.
- "sem_sortimento": a loja não vende esse produto. NÃO proponha correção.

Quando a causa for "atributo_ausente", a correção precisa seguir duas regras
estritas, porque a busca da loja só encontra o produto se elas forem cumpridas:

- O NOME do campo é a própria palavra que o cliente buscou e não encontrou, em
  minúsculas e sem acento. Se ele buscou "impermeável", o campo é "impermeavel".
  Nunca invente um nome diferente nem descreva a categoria do produto.
- O VALOR é exatamente "true". Uma frase descritiva no lugar do valor deixa o
  produto invisível na busca.

Cite na evidência o trecho literal do catálogo que sustenta seu diagnóstico."""


def _formatar_catalogo(catalogo: CatalogAdapter) -> str:
    linhas = []
    for p in catalogo.listar_produtos():
        atributos = ", ".join(f"{k}={v!r}" for k, v in p.atributos.items()) or "nenhum"
        linhas.append(
            f"- {p.sku} | {p.titulo} | estoque={p.estoque}\n"
            f"  descrição: {p.descricao}\n"
            f"  atributos: {atributos}"
        )
    return "\n".join(linhas)


def criar_investigador(llm, catalogo: CatalogAdapter) -> Node:
    modelo = llm.with_structured_output(Diagnostico)

    def investigador(state: VenditusState) -> VenditusState:
        prompt = PROMPT_INVESTIGADOR.format(
            termo=state["termo"],
            resultados=state.get("resultados_antes", 0),
            catalogo=_formatar_catalogo(catalogo),
        )
        return {**state, "diagnostico": modelo.invoke(prompt), "status": "diagnosticado"}

    return investigador


PROMPT_GUARDA = """Você audita uma correção de catálogo antes de ela ser aplicada.

Correção proposta: gravar {campo} = {valor} no produto {sku}
Evidência usada pelo investigador: {evidencia}

Devoluções deste produto nos últimos 90 dias:
{devolucoes}

Pergunta: as devoluções CONTRADIZEM o atributo que se quer gravar?

Contradiz quando os clientes relatam justamente a ausência da característica
que o atributo afirma. Nesse caso, gravar o atributo aumentaria devolução —
o problema não é o catálogo, é a descrição do produto ou o próprio produto.

Não contradiz quando as devoluções tratam de outros assuntos (tamanho, cor,
prazo, arrependimento).

Responda permitir=false apenas se houver contradição direta, e informe quantas
devoluções sustentam isso."""


def criar_guarda(llm) -> Node:
    modelo = llm.with_structured_output(DecisaoGuarda)

    def guarda(state: VenditusState) -> VenditusState:
        diagnostico = state.get("diagnostico")
        if diagnostico is None or diagnostico.correcao is None:
            decisao = DecisaoGuarda(
                permitir=True, justificativa="Nenhuma escrita proposta.", devolucoes_contraditorias=0
            )
            return {
                **state,
                "decisao_guarda": decisao,
                "devolucoes_consultadas": [],
                "status": "aprovado_pelo_guarda",
            }

        c = diagnostico.correcao
        devolucoes = devolucoes_do_sku(c.sku)
        texto = "\n".join(f"- ({d.dias_atras}d) {d.motivo}" for d in devolucoes) or "nenhuma"

        decisao = modelo.invoke(
            PROMPT_GUARDA.format(
                campo=c.campo, valor=c.valor, sku=c.sku,
                evidencia=diagnostico.evidencia, devolucoes=texto,
            )
        )
        status = "aprovado_pelo_guarda" if decisao.permitir else "bloqueado_pelo_guarda"
        # As devolucoes vao para o estado, nao para o DecisaoGuarda: aquele e o
        # schema de saida do LLM, e faze-lo reescrever os textos seria gastar
        # token para reproduzir dado que o no ja tem — e abrir espaco para o
        # modelo parafrasear a frase do cliente.
        return {
            **state,
            "decisao_guarda": decisao,
            "devolucoes_consultadas": devolucoes,
            "status": status,
        }

    return guarda
