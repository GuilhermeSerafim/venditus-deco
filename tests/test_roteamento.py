"""Testes das duas funcoes de roteamento do grafo.

Elas sao o invariante que o produto vende: quando o guarda bloqueia, o caminho
ate a escrita deixa de existir. Ate agora so eram exercitadas indiretamente
pelo test_graph.py, que nunca cobriu o branch fail-closed (decisao ausente).
"""

import pytest
from pydantic import ValidationError

from venditus.graph import rotear_apos_aprovacao, rotear_apos_guarda
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.state import estado_inicial


def _estado_com_decisao(permitir: bool) -> dict:
    s = estado_inicial("tênis impermeável", 340)
    s["decisao_guarda"] = DecisaoGuarda(
        permitir=permitir, justificativa="teste", devolucoes_contraditorias=0 if permitir else 8
    )
    return s


def test_guarda_permite_roteia_para_aprovacao():
    assert rotear_apos_guarda(_estado_com_decisao(True)) == "aprovacao"


def test_guarda_bloqueia_roteia_para_quarentena():
    assert rotear_apos_guarda(_estado_com_decisao(False)) == "quarentena"


def test_decisao_ausente_falha_fechado():
    # Se o guarda nao produziu decisao por qualquer motivo, o roteamento nao
    # pode cair no caminho que escreve.
    s = estado_inicial("tênis impermeável", 340)
    assert s.get("decisao_guarda") is None
    assert rotear_apos_guarda(s) == "quarentena"


def test_aprovado_roteia_para_executor():
    s = estado_inicial("tênis impermeável", 340)
    s["status"] = "aprovado"
    assert rotear_apos_aprovacao(s) == "executor"


def test_rejeitado_nao_roteia_para_executor():
    s = estado_inicial("tênis impermeável", 340)
    s["status"] = "rejeitado"
    assert rotear_apos_aprovacao(s) == "fim"


def test_status_inesperado_falha_fechado():
    s = estado_inicial("tênis impermeável", 340)
    assert s["status"] == "novo"
    assert rotear_apos_aprovacao(s) == "fim"


def test_causa_sem_escrita_com_correcao_e_rejeitada():
    # A regra vivia so no texto do prompt. Agora e invariante de schema.
    for causa in (Causa.SEM_ESTOQUE, Causa.SEM_SORTIMENTO):
        with pytest.raises(ValidationError):
            Diagnostico(
                causa=causa,
                confianca="alta",
                evidencia="x",
                correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
            )


def test_causa_sem_escrita_sem_correcao_continua_valida():
    d = Diagnostico(
        causa=Causa.SEM_SORTIMENTO, confianca="alta", evidencia="não há item de 80L", correcao=None
    )
    assert d.correcao is None
