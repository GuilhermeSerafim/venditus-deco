"""Ponto de entrada: monta o grafo com as dependencias reais.

REGRA: nunca passar temperature ou top_p. Nos modelos GPT-5.x de raciocinio
esses parametros so sao aceitos com reasoning_effort="none". O controle correto
e reasoning_effort.

O objeto `grafo` no final do modulo e o que `langgraph.json` expoe para o
servidor. Ele e compilado SEM checkpointer de proposito — sob `langgraph dev`
a persistencia e do servidor. Para uso programatico use `montar(...)` passando
um checkpointer.
"""

import os
import sqlite3

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from venditus.adapters.base import CatalogAdapter
from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.seed import CATALOGO

load_dotenv()

MODELO = "gpt-5.6-terra"
"""Um modelo so nos dois nos. A demo custa centavos — dividir entre modelos
economizaria troco e arriscaria a qualidade justamente no guarda."""


def _configurado(nome: str) -> bool:
    """Variavel presente e com valor real.

    Os placeholders do .env.example ('shpat_...', 'sua-loja.myshopify.com') sao
    strings nao-vazias e passariam num bool() ingenuo — quem copia o exemplo
    para .env acabaria tentando falar com uma loja que nao existe.
    """
    valor = (os.environ.get(nome) or "").strip()
    return bool(valor) and "..." not in valor and not valor.startswith("sua-loja")


def criar_catalogo(usar_shopify: bool | None = None) -> CatalogAdapter:
    """Shopify quando ha credencial real; catalogo em memoria caso contrario."""
    if usar_shopify is None:
        usar_shopify = _configurado("SHOPIFY_ADMIN_TOKEN") and _configurado("SHOPIFY_STORE_DOMAIN")

    if usar_shopify:
        try:
            from venditus.adapters.shopify import ShopifyCatalogAdapter
        except ImportError:
            print("[venditus] adapter Shopify ainda nao existe — usando catalogo em memoria")
        else:
            return ShopifyCatalogAdapter()

    return FakeCatalogAdapter(CATALOGO)


def checkpointer_sqlite(caminho: str = "checkpoints.db"):
    """Checkpointer para uso programatico.

    SqliteSaver.from_conn_string() devolve um gerenciador de contexto, nao um
    SqliteSaver — por isso a conexao e aberta explicitamente aqui.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    conexao = sqlite3.connect(caminho, check_same_thread=False)
    return SqliteSaver(conexao)


def montar(usar_shopify: bool | None = None, checkpointer=None):
    return construir_grafo(
        catalogo=criar_catalogo(usar_shopify),
        llm_investigador=ChatOpenAI(model=MODELO, reasoning_effort="medium"),
        llm_guarda=ChatOpenAI(model=MODELO, reasoning_effort="high"),
        checkpointer=checkpointer,
    )


grafo = montar()
