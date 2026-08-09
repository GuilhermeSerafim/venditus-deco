"""Dados sintéticos do demo.

Assumido abertamente como sintético. Os dois SKUs abaixo entram no sistema
com diagnóstico idêntico e saem com decisões opostas — é o que o demo prova.
"""

from venditus.models import BuscaFalha, Devolucao, Produto

CATALOGO: list[Produto] = [
    Produto(
        sku="SKU-4471",
        titulo="Tênis Trilha Alpha",
        descricao="Membrana impermeável que mantém os pés secos na trilha. "
                  "Solado com aderência em rocha molhada.",
        atributos={"impermeavel": "", "categoria": "calcado", "genero": "unissex"},
        estoque=12,
    ),
    Produto(
        sku="SKU-8802",
        titulo="Capa de Chuva Leve Nimbus",
        descricao="Tecido leve com repelência à água para o dia a dia. "
                  "Dobra no bolso.",
        atributos={"impermeavel": "", "categoria": "vestuario"},
        estoque=30,
    ),
    Produto(sku="SKU-1100", titulo="Meia Térmica Merino",
            descricao="Lã merino para frio intenso.",
            atributos={"categoria": "meia"}, estoque=44),
    Produto(sku="SKU-1201", titulo="Mochila Cargueira 60L",
            descricao="Estrutura interna ajustável.",
            atributos={"categoria": "mochila", "litragem": "60"}, estoque=8),
    Produto(sku="SKU-1305", titulo="Lanterna de Cabeça Lumen",
            descricao="300 lumens, resistente a respingos.",
            atributos={"categoria": "iluminacao"}, estoque=0),
]

BUSCAS: list[BuscaFalha] = [
    BuscaFalha(termo="tênis impermeável", volume=340),
    BuscaFalha(termo="capa de chuva impermeável", volume=128),
    BuscaFalha(termo="mochila cargueira 80 litros", volume=64),
]

DEVOLUCOES: list[Devolucao] = [
    # SKU-4471 — nada sobre água. Este caso DEVE ser escrito.
    Devolucao(sku="SKU-4471", motivo="Tamanho menor do que o esperado", dias_atras=12),
    Devolucao(sku="SKU-4471", motivo="Tamanho apertado no calcanhar", dias_atras=40),
    Devolucao(sku="SKU-4471", motivo="Cor diferente da foto", dias_atras=66),
    # SKU-8802 — 8 de 11 falam de água. Este caso DEVE ser bloqueado.
    Devolucao(sku="SKU-8802", motivo="Chovi 10 minutos e fiquei todo molhado", dias_atras=5),
    Devolucao(sku="SKU-8802", motivo="Não é impermeável, é só repelente", dias_atras=9),
    Devolucao(sku="SKU-8802", motivo="Molhou tudo dentro da bolsa", dias_atras=14),
    Devolucao(sku="SKU-8802", motivo="A água molhou a mochila por dentro na costura", dias_atras=21),
    Devolucao(sku="SKU-8802", motivo="Molhei inteiro numa chuva forte", dias_atras=28),
    Devolucao(sku="SKU-8802", motivo="Anunciado como impermeável mas molha", dias_atras=44),
    Devolucao(sku="SKU-8802", motivo="Molhou em 5 minutos de chuva", dias_atras=51),
    Devolucao(sku="SKU-8802", motivo="A água atravessa o tecido, não é impermeável", dias_atras=73),
    Devolucao(sku="SKU-8802", motivo="Tamanho grande demais", dias_atras=30),
    Devolucao(sku="SKU-8802", motivo="Zíper veio com defeito", dias_atras=55),
    Devolucao(sku="SKU-8802", motivo="Desisti da compra", dias_atras=80),
]


def devolucoes_do_sku(sku: str, janela_dias: int = 90) -> list[Devolucao]:
    """Devoluções do SKU dentro da janela."""
    return [d for d in DEVOLUCOES if d.sku == sku and d.dias_atras <= janela_dias]
