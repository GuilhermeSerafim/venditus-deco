import unicodedata

from venditus.models import Produto

VALORES_VERDADEIROS = {"true", "sim", "1", "verdadeiro"}
TAMANHO_MINIMO_TOKEN = 3


def normalizar(texto: str) -> str:
    """Minúsculas sem acento, para comparar termo de busca com catálogo."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return decomposto.encode("ascii", "ignore").decode("ascii")


def tokenizar(termo: str) -> list[str]:
    """Palavras significativas do termo. Descarta conectivos curtos como 'de'."""
    return [t for t in normalizar(termo).split() if len(t) >= TAMANHO_MINIMO_TOKEN]


class FakeCatalogAdapter:
    """Catálogo em memória.

    A busca casa o token contra o TÍTULO e contra ATRIBUTOS ESTRUTURADOS
    preenchidos — nunca contra a descrição. Isso é deliberado: é exatamente a
    premissa do produto, que texto livre não torna o item encontrável.
    """

    def __init__(self, produtos: list[Produto]) -> None:
        self._produtos = {p.sku: p.model_copy(deep=True) for p in produtos}
        self._aplicadas: set[str] = set()
        self.escritas = 0

    def _casa_token(self, produto: Produto, token: str) -> bool:
        if token in normalizar(produto.titulo):
            return True
        for nome, valor in produto.atributos.items():
            if normalizar(nome) == token and str(valor).lower() in VALORES_VERDADEIROS:
                return True
        return False

    def buscar(self, termo: str) -> list[Produto]:
        tokens = tokenizar(termo)
        if not tokens:
            return []
        return [
            p for p in self._produtos.values()
            if p.estoque > 0 and all(self._casa_token(p, t) for t in tokens)
        ]

    def obter_produto(self, sku: str) -> Produto | None:
        return self._produtos.get(sku)

    def listar_produtos(self) -> list[Produto]:
        return list(self._produtos.values())

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        if fix_id in self._aplicadas:
            return False
        produto = self._produtos.get(sku)
        if produto is None:
            raise KeyError(f"SKU desconhecido: {sku}")
        produto.atributos[campo] = valor
        self._aplicadas.add(fix_id)
        self.escritas += 1
        return True

    def correcao_ja_aplicada(self, fix_id: str) -> bool:
        return fix_id in self._aplicadas
