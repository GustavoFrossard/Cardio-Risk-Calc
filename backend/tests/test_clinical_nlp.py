"""Testes do módulo de texto clínico livre (core/clinical_nlp.py).

Os seis casos clínicos vêm dos testes manuais de validação do auto-preenchimento;
cada um fixa os campos que a extração deixou de identificar naquela rodada.
Execute com: python -m pytest tests -v   (a partir de backend/)
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import clinical_nlp  # noqa: E402
from core.calculator import calcular_risco  # noqa: E402
from core.clinical_nlp import analisar_texto_clinico  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_ner(monkeypatch):
    # O modelo NER é opcional e baixado da internet; as regras não dependem dele.
    monkeypatch.setattr(clinical_nlp, "ENABLE_NER", False)


CASO_1 = ("Paciente de 67 anos, com infarto há 8 meses, em uso de AAS e clopidogrel, função renal "
          "preservada, em programação de herniorrafia umbilical.")
CASO_2 = ("Paciente de 54 anos, portador de fibrilação atrial e diabetes, em uso de insulina e rivaroxabana "
          "(cha2ds2-va 4). 6 METS, creatinina 0,9. Está em programação de cirurgia ortopédica maior.")
CASO_3 = ("Paciente de 64 anos, portador de hipertensão arterial, fibrilação atrial e estenose aórtica, em uso "
          "de varfarina (chads 2). 6 METS, creatinina 0,9. Está em programação de RTU de próstata.")
CASO_4 = ("Paciente de 64 anos, portador de hipertensão arterial e prótese valvar aórtica mecânica, em uso de "
          "varfarina. 8 METS, creatinina 0,9. Está em programação de colecistectomia (intraperitoneal).")
CASO_5 = ("Paciente de 78 anos, portador de hipertensão arterial, diabetes, fibrilação atrial e AVC há 2 meses, "
          "em uso de varfarina (chads2 4). 4 METS, creatinina 1,4. Está em programação de cirurgia ortopédica major.")
CASO_6 = ("Paciente de 67 anos, portadora de HAS e estenose aórtica sintomática, apresentando dispneia aos "
          "moderados esforços. 3,5 METS. Creatinina 2,2. Está em programação de nefrectomia devido lesão de "
          "suspeita neoplásica.")


# ---------- Casos de validação ----------
@pytest.mark.parametrize("texto,esperado", [
    (CASO_1, {"tipo_cirurgia": "intraperitoneal", "rcri_cirurgia_alto_risco": True,
              "usa_aas": True, "prevencao_aas": "secondary", "usa_clopidogrel": True}),
    (CASO_2, {"tipo_cirurgia": "orthopedic_major", "usa_doac": True,
              "tipo_doac": "rivaroxabana_apixabana_edoxabana", "rcri_diabetes_insulina": True}),
    (CASO_3, {"tipo_cirurgia": "urologic_minor", "doenca_valvar_conhecida": True,
              "usa_varfarina": True, "indicacao_varfarina": "af", "chadsvasc_varfarina": 2}),
    (CASO_4, {"tipo_cirurgia": "intraperitoneal", "rcri_cirurgia_alto_risco": True,
              "doenca_valvar_conhecida": True, "indicacao_varfarina": "mechanical_valve"}),
    (CASO_5, {"tipo_cirurgia": "orthopedic_major", "indicacao_varfarina": "af",
              "chadsvasc_varfarina": 4, "avc_3m_varfarina": True}),
    (CASO_6, {"tipo_cirurgia": "urologic_major", "doenca_valvar_conhecida": True,
              "rcri_creatinina_acima_2": True}),
], ids=["caso1", "caso2", "caso3", "caso4", "caso5", "caso6"])
def test_casos_de_validacao(texto, esperado):
    autofill = analisar_texto_clinico(texto)["autofill"]
    assert {k: autofill.get(k) for k in esperado} == esperado


def test_funcao_renal_preservada_nao_e_informacao_ausente():
    faltando = [m["campo"] for m in analisar_texto_clinico(CASO_1)["missing_critical"]]
    assert "funcao_renal" not in faltando


def test_cha2ds2_va_nao_preenche_campo_do_chads2():
    assert "chadsvasc_varfarina" not in analisar_texto_clinico(CASO_2)["autofill"]


def test_estenose_sem_gravidade_nao_vira_condicao_ativa():
    assert "cv_valvopatia_grave" not in analisar_texto_clinico(CASO_6)["autofill"]


@pytest.mark.parametrize("texto,acao", [
    (CASO_3, "Suspender sem ponte"),
    (CASO_4, "Suspender + Ponte com heparina"),
    (CASO_5, "Suspender + Ponte com heparina"),
], ids=["caso3-chads2", "caso4-protese", "caso5-avc-recente"])
def test_texto_ate_conduta_da_varfarina(texto, acao):
    dados = analisar_texto_clinico(texto)["autofill"]
    varfarina = [m for m in calcular_risco(dados)["orientacoes_medicacao"] if m["medicamento"] == "Varfarina"]
    assert varfarina[0]["acao"] == acao


# ---------- CHADS2 ----------
@pytest.mark.parametrize("texto,valor", [
    ("chads 2", 2), ("chads2 4", 4), ("CHADS₂ 5", 5), ("chads2: 3", 3),
    ("escore chads2 de 6", 6), ("chads2 (4)", 4), ("chads 2 varfarina", 2),
    ("cha2ds2-vasc 4", None), ("chads2-vasc 3", None), ("chads-vasc 3", None),
    ("chads2vasc de 5", None), ("cha2ds2-va 4", None), ("chads2-va 4", None), ("chads2 9", None),
])
def test_extracao_do_chads2(texto, valor):
    assert clinical_nlp._extrair_chads2(clinical_nlp._normalizar(texto)) == valor


# ---------- AVC/AIT < 3 meses ----------
@pytest.mark.parametrize("texto,recente", [
    ("AVC há 2 meses", True), ("AIT há 3 semanas", True), ("AVC isquêmico há 45 dias", True),
    ("AVC há 3 meses", False), ("AVC há 6 meses", False), ("AVC há 1 ano", False),
])
def test_avc_ait_recente(texto, recente):
    assert clinical_nlp._avc_ait_recente(clinical_nlp._normalizar(texto)) is recente


# ---------- Valvopatias ----------
@pytest.mark.parametrize("texto", [
    "estenose aórtica", "estenose mitral", "insuficiência aórtica", "insuficiência mitral", "prótese valvar",
    "prótese aórtica", "prótese mitral biológica",
])
def test_valvopatias_reconhecidas(texto):
    assert analisar_texto_clinico(f"Paciente com {texto}.")["autofill"].get("doenca_valvar_conhecida") is True


def test_valvopatia_negada():
    assert "doenca_valvar_conhecida" not in analisar_texto_clinico("Paciente sem valvopatia.")["autofill"]


@pytest.mark.parametrize("texto,ativa", [
    ("estenose aórtica importante sintomática", True),
    ("estenose aórtica grave e sintomática", True),
    ("estenose aórtica sintomática", False),
    ("estenose aórtica importante, assintomática", False),
])
def test_estenose_importante_sintomatica(texto, ativa):
    assert analisar_texto_clinico(texto)["autofill"].get("cv_valvopatia_grave", False) is ativa


@pytest.mark.parametrize("texto,indicacao", [
    ("FA valvar, em uso de varfarina", "rheumatic"),
    ("fibrilação atrial e estenose mitral reumática, varfarina", "rheumatic"),
    ("fibrilação atrial e prótese mecânica mitral, varfarina", "mechanical_valve"),
    ("prótese biológica aórtica, FA, varfarina", "af"),
])
def test_prioridade_da_indicacao_da_varfarina(texto, indicacao):
    assert analisar_texto_clinico(texto)["autofill"]["indicacao_varfarina"] == indicacao


# ---------- AAS ----------
def test_aas_mencao_explicita_vence_inferencia():
    autofill = analisar_texto_clinico("Infarto prévio, AAS para prevenção primária.")["autofill"]
    assert autofill["prevencao_aas"] == "primary"


def test_aas_nao_sobrescreve_escolha_do_usuario():
    r = analisar_texto_clinico("Infarto prévio, em uso de AAS.", {"prevencao_aas": "primary"})
    assert "prevencao_aas" not in r["autofill"]


def test_aas_sem_doenca_aterosclerotica_nao_marca_prevencao():
    assert "prevencao_aas" not in analisar_texto_clinico("Hipertenso, em uso de AAS.")["autofill"]


# ---------- Cirurgia ----------
def test_herniorrafia_inguinal_nao_e_intraperitoneal():
    assert "tipo_cirurgia" not in analisar_texto_clinico("Herniorrafia inguinal programada.")["autofill"]


def test_cirurgia_fora_da_cavidade_nao_marca_criterio_do_rcri():
    autofill = analisar_texto_clinico("Programada artroplastia de quadril.")["autofill"]
    assert autofill["rcri_cirurgia_alto_risco"] is False
