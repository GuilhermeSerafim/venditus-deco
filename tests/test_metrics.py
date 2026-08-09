from venditus.metrics import (
    cobertura_de_atributo,
    receita_recuperada,
    resumo_kpis,
    taxa_de_bloqueio,
)
from venditus.models import Produto
from venditus.state import estado_inicial


def _produtos():
    return [
        Produto(sku="A", titulo="A", atributos={"impermeavel": "true"}, estoque=1),
        Produto(sku="B", titulo="B", atributos={"impermeavel": ""}, estoque=1),
        Produto(sku="C", titulo="C", atributos={}, estoque=1),
        Produto(sku="D", titulo="D", atributos={"impermeavel": "true"}, estoque=1),
    ]


def _estados():
    aplicado = estado_inicial("tênis impermeável", 340)
    aplicado["status"] = "aplicado"
    aplicado["escreveu"] = True
    bloqueado = estado_inicial("capa de chuva impermeável", 128)
    bloqueado["status"] = "quarentena"
    rejeitado = estado_inicial("mochila cargueira 80 litros", 64)
    rejeitado["status"] = "rejeitado"
    return [aplicado, bloqueado, rejeitado]


def test_cobertura_de_atributo():
    # 2 de 4 produtos com o atributo preenchido
    assert cobertura_de_atributo(_produtos(), "impermeavel") == 0.5


def test_cobertura_com_catalogo_vazio():
    assert cobertura_de_atributo([], "impermeavel") == 0.0


def test_taxa_de_bloqueio():
    # 1 quarentena em 3 execuções
    assert round(taxa_de_bloqueio(_estados()), 4) == 0.3333


def test_taxa_de_bloqueio_sem_execucoes():
    assert taxa_de_bloqueio([]) == 0.0


def test_receita_recuperada_soma_so_o_que_foi_escrito():
    # O bloqueado e o rejeitado nao entram, mesmo tendo perda estimada.
    assert receita_recuperada(_estados()) == 3841.73


def test_receita_recuperada_sem_execucoes():
    assert receita_recuperada([]) == 0.0


def test_resumo_reune_os_quatro_kpis():
    r = resumo_kpis(_produtos(), _estados(), "impermeavel")
    assert r["cobertura_de_atributo"] == 0.5
    assert r["receita_recuperada"] == 3841.73
    assert r["bloqueados"] == 1
    assert r["execucoes"] == 3
