"""Buscas rotuladas a mao para medir a acuracia do investigador.

Mora no pacote, nao em tests/, porque nao e fixture de teste — e dado de
avaliacao do produto, e precisa ser importavel fora do pytest.

Toda query aqui DEVE retornar zero resultados no catalogo semeado — o agente
so ve buscas que falharam. O script de avaliacao verifica isso antes de medir
e recusa rodar se algum item retornar resultado, porque um rotulo sobre uma
busca que funciona nao testa nada.

CATEGORIZACAO_ERRADA nao aparece: o catalogo semeado nao tem nenhum produto
mal categorizado, entao nao ha caso honesto para rotular. A avaliacao cobre
cinco das seis causas — isso e uma limitacao declarada, nao um esquecimento.
"""

from venditus.models import Causa

ROTULADOS: list[tuple[str, Causa]] = [
    # --- atributo ausente: produto existe, descricao sustenta, atributo vazio
    ("tênis impermeável", Causa.ATRIBUTO_AUSENTE),
    ("capa de chuva impermeável", Causa.ATRIBUTO_AUSENTE),
    ("tenis impermeavel", Causa.ATRIBUTO_AUSENTE),
    ("capa impermeável leve", Causa.ATRIBUTO_AUSENTE),
    # --- typo: o termo certo existe, escrito errado
    ("tênis impermiavel", Causa.TYPO),
    ("mochila cargeira", Causa.TYPO),
    ("meia termica merinno", Causa.TYPO),
    ("tenis trilha alfa", Causa.TYPO),
    ("lanterna de cabesa", Causa.TYPO),
    # --- sinonimo: o cliente usa palavra que o catalogo nao usa
    ("calçado de trilha", Causa.SINONIMO),
    ("sapato de trilha", Causa.SINONIMO),
    ("mochila 60 litros", Causa.SINONIMO),
    ("meia de lã de ovelha", Causa.SINONIMO),
    # --- sem estoque: produto existe no catalogo mas esta zerado
    ("lanterna de cabeça", Causa.SEM_ESTOQUE),
    ("lanterna lumen", Causa.SEM_ESTOQUE),
    ("lanterna de cabeça 300 lumens", Causa.SEM_ESTOQUE),
    # --- sem sortimento: a loja simplesmente nao vende isso
    ("barraca para duas pessoas", Causa.SEM_SORTIMENTO),
    ("cadeira de camping dobrável", Causa.SEM_SORTIMENTO),
    ("luva térmica de montanha", Causa.SEM_SORTIMENTO),
    ("óculos de sol polarizado", Causa.SEM_SORTIMENTO),
]
