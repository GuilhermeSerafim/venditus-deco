"""Cria na loja Shopify os produtos do demo, iguais aos de venditus.seed.

Idempotente: pula SKU que ja existe. Pode rodar de novo sem duplicar.

O estoque e criado como NAO RASTREADO. A dev store nao concedeu o escopo
read_locations, entao nao da para definir quantidade por localizacao — e
produto sem rastreio e vendavel, que e o que o demo precisa. O adapter trata
nao-rastreado como disponivel.

O metafield venditus.impermeavel e criado VAZIO de proposito: e exatamente a
premissa do produto — o texto existe na descricao e o atributo nao.
"""

import os

import httpx
from dotenv import load_dotenv

from venditus.seed import CATALOGO

load_dotenv()

DOMINIO = (os.environ.get("SHOPIFY_STORE_DOMAIN") or "").strip()
TOKEN = (os.environ.get("SHOPIFY_ADMIN_TOKEN") or "").strip()
VERSAO = (os.environ.get("SHOPIFY_API_VERSION") or "2026-07").strip()
URL = f"https://{DOMINIO}/admin/api/{VERSAO}/graphql.json"

NAMESPACE = "venditus"


def chamar(query: str, variaveis: dict | None = None) -> dict:
    resposta = httpx.post(
        URL,
        json={"query": query, "variables": variaveis or {}},
        headers={"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"},
        timeout=40.0,
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    if "errors" in corpo:
        raise RuntimeError(f"GraphQL: {corpo['errors']}")
    return corpo["data"]


SKUS_EXISTENTES = """
query { productVariants(first: 250) { nodes { sku product { id title } } } }
"""

CRIAR_PRODUTO = """
mutation criar($input: ProductSetInput!) {
  productSet(synchronous: true, input: $input) {
    product { id title variants(first: 1) { nodes { sku } } }
    userErrors { field message }
  }
}
"""

DEFINIR_METAFIELD = """
mutation definir($definition: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $definition) {
    createdDefinition { id name }
    userErrors { field message code }
  }
}
"""


def skus_existentes() -> dict[str, str]:
    dados = chamar(SKUS_EXISTENTES)
    return {
        v["sku"]: v["product"]["id"]
        for v in dados["productVariants"]["nodes"]
        if v.get("sku")
    }


def criar_definicao_de_metafield() -> None:
    """Sem definicao o valor grava mas nao aparece bonito no admin.

    O diff visivel no admin e um dos beats do video.
    """
    entrada = {
        "name": "Impermeavel",
        "namespace": NAMESPACE,
        "key": "impermeavel",
        "description": "Atributo estruturado de impermeabilidade, gerenciado pelo Venditus.",
        "type": "single_line_text_field",
        "ownerType": "PRODUCT",
    }
    dados = chamar(DEFINIR_METAFIELD, {"definition": entrada})
    erros = dados["metafieldDefinitionCreate"]["userErrors"]
    if erros:
        codigos = {e.get("code") for e in erros}
        if "TAKEN" in codigos:
            print(f"  definicao {NAMESPACE}.impermeavel ja existe")
            return
        print(f"  AVISO ao definir metafield: {erros}")
        return
    print(f"  definicao {NAMESPACE}.impermeavel criada")


def criar_produto(produto) -> None:
    entrada = {
        "title": produto.titulo,
        "descriptionHtml": f"<p>{produto.descricao}</p>",
        "status": "ACTIVE",
        "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
        "variants": [
            {
                "optionValues": [{"optionName": "Title", "name": "Default Title"}],
                "sku": produto.sku,
                "price": "199.90",
                "inventoryItem": {"tracked": False},
            }
        ],
        # Sem metafield nenhum, de proposito. A Shopify rejeita valor vazio, e
        # "atributo ausente" e a representacao mais fiel da premissa do produto:
        # o texto existe na descricao e o atributo estruturado nao existe ainda.
        # Quem cria o metafield e o Venditus, quando voce aprova a correcao.
    }
    dados = chamar(CRIAR_PRODUTO, {"input": entrada})
    erros = dados["productSet"]["userErrors"]
    if erros:
        raise RuntimeError(f"{produto.sku}: {erros}")
    print(f"  criado {produto.sku:10} | {produto.titulo}")


def main() -> None:
    if not DOMINIO or not TOKEN:
        raise SystemExit("SHOPIFY_STORE_DOMAIN e SHOPIFY_ADMIN_TOKEN sao obrigatorios.")

    print(f"loja: {DOMINIO} (API {VERSAO})\n")

    print("definicao de metafield:")
    criar_definicao_de_metafield()

    existentes = skus_existentes()
    print(f"\nprodutos ({len(existentes)} SKUs ja na loja):")
    for produto in CATALOGO:
        if produto.sku in existentes:
            print(f"  pula   {produto.sku:10} | ja existe")
            continue
        criar_produto(produto)

    print("\nconferindo:")
    agora = skus_existentes()
    for produto in CATALOGO:
        marca = "OK " if produto.sku in agora else "FALTA"
        print(f"  {marca} {produto.sku}")


if __name__ == "__main__":
    main()
