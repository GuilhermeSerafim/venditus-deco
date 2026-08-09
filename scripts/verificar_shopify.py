"""Prova o ciclo completo contra a loja Shopify real.

Faz o que o demo faz: busca sem resultado -> grava o atributo -> busca de novo.
E confirma que gravar duas vezes com o mesmo fix_id nao duplica escrita.

  python scripts/verificar_shopify.py            # roda o ciclo
  python scripts/verificar_shopify.py --resetar  # apaga o atributo, volta ao "antes"

Use --resetar antes de gravar o video, para o SKU-4471 comecar sem o atributo.
"""

import sys

from dotenv import load_dotenv

from venditus.adapters.shopify import NAMESPACE, ShopifyCatalogAdapter
from venditus.fixid import fix_id

load_dotenv()

SKU = "SKU-4471"
CAMPO = "impermeavel"
TERMO = "tênis impermeável"

APAGAR_METAFIELD = """
mutation apagar($input: MetafieldsDeleteInput!) {
  metafieldsDelete(metafields: [$input]) {
    deletedMetafields { key }
    userErrors { message }
  }
}
"""


def resetar(adapter: ShopifyCatalogAdapter) -> None:
    adapter.listar_produtos()  # popula o mapa de SKU -> id
    gid = adapter._id_por_sku.get(SKU)
    if gid is None:
        raise SystemExit(f"{SKU} nao encontrado na loja.")
    dados = adapter._chamar(
        APAGAR_METAFIELD,
        {"input": {"ownerId": gid, "namespace": NAMESPACE, "key": CAMPO}},
    )
    erros = dados["metafieldsDelete"]["userErrors"]
    print(f"reset: {'erros=' + str(erros) if erros else 'atributo removido de ' + SKU}")
    print(f"busca por {TERMO!r} agora: {len(adapter.buscar(TERMO))} resultado(s)")


def ciclo(adapter: ShopifyCatalogAdapter) -> None:
    produtos = adapter.listar_produtos()
    print(f"catalogo: {len(produtos)} produtos\n")

    alvo = next((p for p in produtos if p.sku == SKU), None)
    if alvo is None:
        raise SystemExit(f"{SKU} nao encontrado. Rode semear_shopify.py antes.")
    print(f"alvo: {alvo.titulo}")
    print(f"  descricao menciona impermeabilidade: {'impermeáv' in alvo.descricao.lower()}")
    print(f"  atributo {CAMPO!r} presente: {CAMPO in alvo.atributos}")
    print(f"  estoque: {alvo.estoque}\n")

    antes = adapter.buscar(TERMO)
    print(f"ANTES  — busca {TERMO!r}: {len(antes)} resultado(s)")

    fid = fix_id(SKU, CAMPO, "true")
    gravou = adapter.aplicar_correcao(SKU, CAMPO, "true", fid)
    print(f"\nescrita: {'aplicada' if gravou else 'ja estava aplicada'} (fix_id={fid})")

    repetiu = adapter.aplicar_correcao(SKU, CAMPO, "true", fid)
    print(f"repetindo com o mesmo fix_id: {'GRAVOU DE NOVO (BUG)' if repetiu else 'ignorada, correto'}")
    print(f"total de escritas: {adapter.escritas}")

    depois = adapter.buscar(TERMO)
    print(f"\nDEPOIS — busca {TERMO!r}: {len(depois)} resultado(s)")
    for p in depois:
        print(f"  {p.sku} | {p.titulo} | {CAMPO}={p.atributos.get(CAMPO)!r}")

    print()
    if len(antes) == 0 and len(depois) >= 1 and adapter.escritas == 1:
        print("OK: 0 -> 1 com uma unica escrita. E o ciclo do demo, na loja real.")
    else:
        raise SystemExit(f"INESPERADO: antes={len(antes)} depois={len(depois)} escritas={adapter.escritas}")


def main() -> None:
    adapter = ShopifyCatalogAdapter()
    print(f"loja: {adapter.dominio} (API {adapter.versao})\n")
    if "--resetar" in sys.argv:
        resetar(adapter)
    else:
        ciclo(adapter)


if __name__ == "__main__":
    main()
