"""Confirma que a loja Shopify responde antes de escrever o adapter.

Somente leitura — nao grava nada. Mesma disciplina da Task 0: descobrir
problema de credencial ou escopo agora custa minutos.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

QUERY = """
query sondar($n: Int!) {
  shop { name myshopifyDomain }
  products(first: $n) {
    nodes {
      id
      title
      totalInventory
      variants(first: 1) { nodes { sku } }
      metafields(first: 20, namespace: "venditus") { nodes { key value } }
    }
  }
}
"""


def main() -> None:
    dominio = (os.environ.get("SHOPIFY_STORE_DOMAIN") or "").strip()
    token = (os.environ.get("SHOPIFY_ADMIN_TOKEN") or "").strip()
    versao = (os.environ.get("SHOPIFY_API_VERSION") or "2026-07").strip()

    print("=== configuracao ===")
    print(f"  dominio: {dominio or '<vazio>'}")
    print(f"  versao:  {versao}")
    print(f"  token:   {'presente (' + str(len(token)) + ' chars)' if token else '<vazio>'}")

    if not dominio or not token:
        raise SystemExit("\nERRO: SHOPIFY_STORE_DOMAIN e SHOPIFY_ADMIN_TOKEN sao obrigatorios.")

    url = f"https://{dominio}/admin/api/{versao}/graphql.json"
    print(f"\n=== chamando {url} ===")

    resposta = httpx.post(
        url,
        json={"query": QUERY, "variables": {"n": 30}},
        headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
        timeout=30.0,
    )
    print(f"  HTTP {resposta.status_code}")

    if resposta.status_code == 401:
        raise SystemExit("  401 — token invalido ou expirado.")
    if resposta.status_code == 404:
        raise SystemExit(f"  404 — dominio ou versao de API errados (versao={versao}).")
    resposta.raise_for_status()

    corpo = resposta.json()
    if "errors" in corpo:
        print("\n  GraphQL retornou erros:")
        for e in corpo["errors"]:
            print(f"    - {e.get('message')}")
        raise SystemExit("  Provavel falta de escopo: precisa de read_products e write_products.")

    dados = corpo["data"]
    loja = dados["shop"]
    print(f"\n  loja: {loja['name']} ({loja['myshopifyDomain']})")

    produtos = dados["products"]["nodes"]
    print(f"\n=== {len(produtos)} produtos ===")
    for p in produtos:
        variantes = p["variants"]["nodes"]
        sku = variantes[0]["sku"] if variantes and variantes[0]["sku"] else "<sem sku>"
        mfs = {m["key"]: m["value"] for m in p["metafields"]["nodes"]}
        print(f"  {sku:12} | {p['title'][:38]:38} | estoque={p['totalInventory']} | venditus={mfs or '{}'}")

    esperados = {"SKU-4471", "SKU-8802"}
    encontrados = {
        v["sku"]
        for p in produtos
        for v in p["variants"]["nodes"]
        if v["sku"]
    }
    faltando = esperados - encontrados

    print("\n=== SKUs do demo ===")
    if faltando:
        print(f"  FALTANDO: {sorted(faltando)}")
        print("  O demo precisa dos dois. Cadastre-os com o metafield venditus.impermeavel VAZIO.")
    else:
        print("  SKU-4471 e SKU-8802 presentes — pronto para a Task 12.")


if __name__ == "__main__":
    main()
