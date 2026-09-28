"""Testes unitários do motor de cálculo (core/calculator.py).

Os valores esperados vêm da Diretriz SBC 2024 (Gualandro et al., 2024):
Tabela 5 (classes do RCRI), Tabela 6 (pontos do VSG-CRI) e Tabela 7 (classes do VSG-CRI).
Execute com: python -m pytest tests -v   (a partir de backend/)
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calculator import (  # noqa: E402
    calcular_risco,
    pontuar_rcri,
    pontuar_vsg,
    montar_orientacoes_medicacao,
)

RCRI_CRITERIOS = [
    "rcri_cirurgia_alto_risco", "rcri_doenca_coronaria", "rcri_ic",
    "rcri_cerebrovascular", "rcri_diabetes_insulina", "rcri_creatinina_acima_2",
]


def _rcri(n: int) -> dict:
    d = {"risco_cirurgia": "intermediario"}
    d.update({c: True for c in RCRI_CRITERIOS[:n]})
    return d


# ---------- RCRI (Tabela 5) ----------
@pytest.mark.parametrize("n,classe", [
    (0, "baixo"), (1, "baixo"), (2, "intermediario"),
    (3, "alto"), (4, "alto"), (5, "alto"), (6, "alto"),
])
def test_rcri_pontuacao_e_classe(n, classe):
    pts, _ = pontuar_rcri(_rcri(n))
    assert pts == n
    r = calcular_risco(_rcri(n))
    assert r["indice_risco"] == "rcri"
    assert r["pontuacao"] == n
    assert r["classe_risco"] == classe


# ---------- VSG-CRI (Tabelas 6 e 7) ----------
@pytest.mark.parametrize("campo,valor,pontos", [
    ("vsg_faixa_etaria", "lt60", 0),
    ("vsg_faixa_etaria", "60_69", 2),
    ("vsg_faixa_etaria", "70_79", 3),
    ("vsg_faixa_etaria", "gte80", 4),
    ("vsg_dac", True, 2),
    ("vsg_ic", True, 2),
    ("vsg_dpoc", True, 2),
    ("vsg_creatinina_acima_1_8", True, 2),
    ("vsg_tabagismo", True, 1),
    ("vsg_diabetes_insulina", True, 1),
    ("vsg_betabloqueador_cronico", True, 1),
])
def test_vsg_pontos_por_fator(campo, valor, pontos):
    pts, _ = pontuar_vsg({campo: valor})
    assert pts == pontos


def test_vsg_revascularizacao_previa_subtrai_um():
    pts, _ = pontuar_vsg({"vsg_faixa_etaria": "60_69", "vsg_revasc_previa": True})
    assert pts == 1


def test_vsg_pontuacao_nao_fica_negativa():
    pts, _ = pontuar_vsg({"vsg_revasc_previa": True})
    assert pts == 0


def _vsg(pontos_alvo: int) -> dict:
    """Monta um caso vascular com exatamente `pontos_alvo` pontos."""
    d = {"eh_vascular": True, "risco_cirurgia": "intermediario"}
    restante = pontos_alvo
    if restante >= 4:
        d["vsg_faixa_etaria"] = "gte80"; restante -= 4
    elif restante >= 3:
        d["vsg_faixa_etaria"] = "70_79"; restante -= 3
    for campo in ["vsg_dac", "vsg_ic", "vsg_dpoc", "vsg_creatinina_acima_1_8"]:
        if restante >= 2:
            d[campo] = True; restante -= 2
    for campo in ["vsg_tabagismo", "vsg_diabetes_insulina", "vsg_betabloqueador_cronico"]:
        if restante >= 1:
            d[campo] = True; restante -= 1
    assert restante == 0
    return d


@pytest.mark.parametrize("pts,classe", [
    (0, "baixo"), (3, "baixo"), (4, "baixo"),
    (5, "intermediario"), (6, "intermediario"),
    (7, "alto"), (8, "alto"), (12, "alto"),
])
def test_vsg_classe_nos_limiares(pts, classe):
    r = calcular_risco(_vsg(pts))
    assert r["indice_risco"] == "vsg"
    assert r["pontuacao"] == pts
    assert r["classe_risco"] == classe


# ---------- Seleção do índice ----------
@pytest.mark.parametrize("extra,indice", [
    ({}, "rcri"),
    ({"eh_vascular": True}, "vsg"),
    ({"surgery_is_vascular": True}, "vsg"),
    ({"tipo_cirurgia": "vascular_arterial"}, "vsg"),
    ({"tipo_cirurgia": "breast"}, "rcri"),
])
def test_selecao_do_indice(extra, indice):
    d = {"risco_cirurgia": "intermediario"}
    d.update(extra)
    assert calcular_risco(d)["indice_risco"] == indice


# ---------- Regras adicionais ----------
def test_cirurgia_baixo_risco_sem_condicao_ativa_resulta_baixo():
    d = _rcri(2)
    d["risco_cirurgia"] = "baixo"
    assert calcular_risco(d)["classe_risco"] == "baixo"


def test_cirurgia_baixo_risco_nao_rebaixa_classe_alta():
    d = _rcri(3)
    d["risco_cirurgia"] = "baixo"
    assert calcular_risco(d)["classe_risco"] == "alto"


def test_condicao_ativa_forca_risco_alto():
    d = {"risco_cirurgia": "baixo", "cv_coronaria_aguda": True}
    r = calcular_risco(d)
    assert r["classe_risco"] == "alto"
    assert r["tem_condicoes_ativas"] is True


# ---------- Limiar da otimização farmacológica ----------
def _tem_otimizacao(r):
    return any(x["titulo"] == "Otimização farmacológica" for x in r["recomendacoes"])


@pytest.mark.parametrize("caso,esperado", [
    (_rcri(2), False), (_rcri(3), True),
    (_vsg(3), False), (_vsg(6), False), (_vsg(7), True),
])
def test_limiar_otimizacao_por_indice(caso, esperado):
    assert _tem_otimizacao(calcular_risco(caso)) is esperado


# ---------- Medicações ----------
def test_aas_prevencao_primaria_suspende_7_dias():
    o = montar_orientacoes_medicacao({"usa_aas": True, "prevencao_aas": "primary"})
    assert o[0]["dias_antes"] == 7


def test_aas_secundaria_mantem_exceto_neurocirurgia():
    mantem = montar_orientacoes_medicacao(
        {"usa_aas": True, "prevencao_aas": "secondary", "tipo_cirurgia": "general"})
    susp = montar_orientacoes_medicacao(
        {"usa_aas": True, "prevencao_aas": "secondary", "tipo_cirurgia": "neurologic"})
    assert mantem[0]["acao"] == "Manter"
    assert susp[0]["dias_antes"] == 7


@pytest.mark.parametrize("clcr,alto,horas", [
    (80, False, 24), (80, True, 48), (40, False, 48), (40, True, 96),
])
def test_dabigatrana_janela_de_suspensao(clcr, alto, horas):
    o = montar_orientacoes_medicacao({
        "usa_doac": True, "tipo_doac": "dabigatrana", "clcr_doac": clcr,
        "risco_sangramento_doac": "alto" if alto else "baixo"})
    assert o[0]["dias_antes"] * 24 == horas


@pytest.mark.parametrize("chads,avc,acao", [
    (2, False, "Suspender sem ponte"),
    (3, False, "Considerar ponte com heparina"),
    (5, False, "Suspender + Ponte com heparina"),
    (1, True, "Suspender + Ponte com heparina"),
])
def test_varfarina_fa_ponte_com_heparina(chads, avc, acao):
    o = montar_orientacoes_medicacao({
        "usa_varfarina": True, "indicacao_varfarina": "af",
        "chadsvasc_varfarina": chads, "avc_3m_varfarina": avc})
    assert o[0]["acao"] == acao
