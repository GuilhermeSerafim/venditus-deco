"""Catalogo real via Shopify Admin GraphQL.

Implementa o mesmo protocolo do FakeCatalogAdapter — nenhum no muda ao trocar
um pelo outro. E o que sustenta a promessa de que trocar Shopify por VTEX e
implementar um adapter, nao refatorar o agente.

Tres decisoes que vieram de bater na loja de verdade, nao do desenho no papel:

1. METAFIELD AUSENTE, NAO VAZIO. A Shopify rejeita metafield com valor vazio.
   Um produto sem o atributo simplesmente nao traz a chave em `atributos` — o
   efeito na busca e identico ao do valor vazio, e e mais fiel ao mundo real.

2. ESTOQUE NAO RASTREADO CONTA COMO DISPONIVEL. A dev store nao concedeu
   read_locations, entao os produtos do demo foram criados sem rastreio de
   estoque. Produto sem rastreio e vendavel na Shopify — `totalInventory`
   devolve 0 e mesmo assim ele aparece na loja. Tratar esse 0 como "sem
   estoque" esconderia o produto e quebraria o demo.

3. A BUSCA REUSA A DO FAKE. Nao e preguica: a regra precisa ser identica nos
   dois adapters, senao o comportamento demonstrado no teste diverge do
   comportamento em producao. Duplicar a regra e deixa-la divergir seria pior.
"""

import os

import httpx

from venditus.models import Produto

NAMESPACE = "venditus"
ESTOQUE_NAO_RASTREADO = 999
"""Sentinela para produto vendavel sem rastreio de estoque. Ver decisao 2."""

QUERY_PRODUTOS = """
query listarProdutos($n: Int!) {
  products(first: $n) {
    nodes {
      id
      title
      description
      totalInventory
      tracksInventory
      variants(first: 1) { nodes { sku } }
      metafields(first: 25, namespace: "%s") { nodes { key value } }
    }
  }
}
""" % NAMESPACE

MUTATION_METAFIELD = """
mutation gravar($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key value }
    userErrors { field message }
  }
}
"""


class ShopifyCatalogAdapter:
    """Le e escreve o catalogo de uma loja Shopify.

    `cliente` existe para injecao em teste — sem ele, cria um httpx.Client.
    """

    def __init__(
        self,
        dominio: str | None = None,
        token: str | None = None,
        versao: str | None = None,
        limite: int = 100,
        cliente: httpx.Client | None = None,
    ) -> None:
        self.dominio = dominio or os.environ["SHOPIFY_STORE_DOMAIN"].strip()
        self.token = token or os.environ["SHOPIFY_ADMIN_TOKEN"].strip()
        self.versao = versao or os.environ.get("SHOPIFY_API_VERSION", "2026-07").strip()
        self.limite = limite
        self._cliente = cliente or httpx.Client(timeout=40.0)
        self._aplicadas: set[str] = set()
        self._id_por_sku: dict[str, str] = {}
        self.escritas = 0

    @property
    def url(self) -> str:
        return f"https://{self.dominio}/admin/api/{self.versao}/graphql.json"

    def _chamar(self, query: str, variaveis: dict) -> dict:
        resposta = self._cliente.post(
            self.url,
            json={"query": query, "variables": variaveis},
            headers={"X-Shopify-Access-Token": self.token, "Content-Type": "application/json"},
        )
        resposta.raise_for_status()
        corpo = resposta.json()
        if "errors" in corpo:
            raise RuntimeError(f"Shopify GraphQL: {corpo['errors']}")
        return corpo["data"]

    def listar_produtos(self) -> list[Produto]:
        dados = self._chamar(QUERY_PRODUTOS, {"n": self.limite})
        produtos: list[Produto] = []

        for no in dados["products"]["nodes"]:
            variantes = no["variants"]["nodes"]
            sku = variantes[0]["sku"] if variantes and variantes[0].get("sku") else no["id"]
            self._id_por_sku[sku] = no["id"]

            if no.get("tracksInventory"):
                estoque = no.get("totalInventory") or 0
            else:
                estoque = ESTOQUE_NAO_RASTREADO

            produtos.append(
                Produto(
                    sku=sku,
                    titulo=no["title"],
                    descricao=no.get("description") or "",
                    atributos={m["key"]: m["value"] for m in no["metafields"]["nodes"]},
                    estoque=estoque,
                )
            )
        return produtos

    def obter_produto(self, sku: str) -> Produto | None:
        return next((p for p in self.listar_produtos() if p.sku == sku), None)

    def buscar(self, termo: str) -> list[Produto]:
        # Ver decisao 3 no docstring do modulo: a regra de casamento tem que ser
        # a mesma dos testes, senao producao diverge do que foi demonstrado.
        from venditus.adapters.fake import FakeCatalogAdapter

        return FakeCatalogAdapter(self.listar_produtos()).buscar(termo)

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        if fix_id in self._aplicadas:
            return False

        if sku not in self._id_por_sku:
            self.listar_produtos()
        gid = self._id_por_sku.get(sku)
        if gid is None:
            raise KeyError(f"SKU nao encontrado na Shopify: {sku}")

        dados = self._chamar(
            MUTATION_METAFIELD,
            {
                "metafields": [
                    {
                        "ownerId": gid,
                        "namespace": NAMESPACE,
                        "key": campo,
                        "value": valor,
                        "type": "single_line_text_field",
                    }
                ]
            },
        )
        erros = dados["metafieldsSet"]["userErrors"]
        if erros:
            raise RuntimeError(f"metafieldsSet: {erros}")

        self._aplicadas.add(fix_id)
        self.escritas += 1
        return True

    def correcao_ja_aplicada(self, fix_id: str) -> bool:
        return fix_id in self._aplicadas
