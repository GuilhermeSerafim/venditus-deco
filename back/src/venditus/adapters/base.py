from typing import Protocol

from venditus.models import Produto


class CatalogAdapter(Protocol):
    """Interface do catálogo. Mantém a lógica de domínio ignorante de HTTP.

    Trocar Shopify por VTEX é implementar este protocolo — nenhum nó muda.
    """

    def buscar(self, termo: str) -> list[Produto]:
        """Produtos que a busca da loja retornaria para o termo, com estoque."""
        ...

    def obter_produto(self, sku: str) -> Produto | None: ...

    def listar_produtos(self) -> list[Produto]: ...

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        """Grava o atributo. Retorna False se o fix_id já foi aplicado."""
        ...

    def correcao_ja_aplicada(self, fix_id: str) -> bool: ...
