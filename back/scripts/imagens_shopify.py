"""Anexa imagens aos produtos do demo na Shopify.

Fotos do Wikimedia Commons — licenca livre e URL direta estavel. Cada URL e
verificada antes de ser enviada; a Shopify busca a imagem por conta propria.

Idempotente: pula produto que ja tem midia.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

DOMINIO = (os.environ.get("SHOPIFY_STORE_DOMAIN") or "").strip()
TOKEN = (os.environ.get("SHOPIFY_ADMIN_TOKEN") or "").strip()
VERSAO = (os.environ.get("SHOPIFY_API_VERSION") or "2026-07").strip()
URL = f"https://{DOMINIO}/admin/api/{VERSAO}/graphql.json"

UA = {"User-Agent": "venditus-hackathon/0.1 (contato@osnotaveis.com.br)"}

# Arquivo no Commons + texto alternativo, por SKU.
IMAGENS = {
    "SKU-4471": ("Hiking boots and foot prints.jpeg", "Bota de trilha em terreno molhado"),
    "SKU-8802": ("Hard-shell-jacket.jpg", "Capa de chuva leve"),
    "SKU-1100": ("Hand-knitted Himachali socks,1.jpg", "Meia de la merino"),
    "SKU-1201": ("A backpack with trekking poles and shoes.jpg", "Mochila cargueira de trilha"),
    "SKU-1305": ("LED headlamp (2).jpg", "Lanterna de cabeca LED"),
}

PRODUTOS_POR_SKU = """
query { productVariants(first: 250) { nodes {
    sku
    product { id title media(first: 1) { nodes { id } } }
} } }
"""

CRIAR_MIDIA = """
mutation criarMidia($productId: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $productId, media: $media) {
    media { ... on MediaImage { id status } }
    mediaUserErrors { field message }
  }
}
"""


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


def url_do_commons(arquivo: str) -> str:
    """Resolve o nome do arquivo para a URL direta da imagem redimensionada."""
    resposta = httpx.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "format": "json",
            "titles": f"File:{arquivo}",
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": 1400,
        },
        headers=UA,
        timeout=30,
        follow_redirects=True,
    ).json()
    paginas = (resposta.get("query") or {}).get("pages") or {}
    for pagina in paginas.values():
        info = (pagina.get("imageinfo") or [{}])[0]
        if info.get("thumburl"):
            return info["thumburl"]
    raise RuntimeError(f"nao consegui resolver a URL de {arquivo}")


def main() -> None:
    if not DOMINIO or not TOKEN:
        raise SystemExit("SHOPIFY_STORE_DOMAIN e SHOPIFY_ADMIN_TOKEN sao obrigatorios.")

    dados = chamar(PRODUTOS_POR_SKU)
    por_sku = {
        v["sku"]: v["product"]
        for v in dados["productVariants"]["nodes"]
        if v.get("sku") in IMAGENS
    }

    for sku, (arquivo, alt) in IMAGENS.items():
        produto = por_sku.get(sku)
        if produto is None:
            print(f"  {sku}: produto nao encontrado — rode semear_shopify.py antes")
            continue
        if produto["media"]["nodes"]:
            print(f"  {sku}: ja tem imagem, pulando")
            continue

        url = url_do_commons(arquivo)
        cabecalho = httpx.head(url, headers=UA, timeout=20, follow_redirects=True)
        if cabecalho.status_code != 200 or "image" not in cabecalho.headers.get("content-type", ""):
            print(f"  {sku}: URL nao responde imagem ({cabecalho.status_code}), pulando")
            continue

        resultado = chamar(
            CRIAR_MIDIA,
            {
                "productId": produto["id"],
                "media": [{"originalSource": url, "alt": alt, "mediaContentType": "IMAGE"}],
            },
        )
        erros = resultado["productCreateMedia"]["mediaUserErrors"]
        if erros:
            print(f"  {sku}: ERRO {erros}")
        else:
            estado = resultado["productCreateMedia"]["media"][0]["status"]
            print(f"  {sku}: enviada ({estado}) | {arquivo}")

    print("\nA Shopify baixa a imagem de forma assincrona — leva alguns segundos para aparecer.")


if __name__ == "__main__":
    main()
