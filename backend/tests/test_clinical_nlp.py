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


# ---------- Conferência das regras com o NER (ner_review) ----------
def _pipeline_falso(achados):
    """Pipeline de NER de mentira: devolve as entidades de `achados` que aparecem no texto.

    `achados` é uma lista de (trecho, rótulo, score). Evita baixar o modelo nos testes.
    """
    def ner(texto):
        saida = []
        for trecho, rotulo, score in achados:
            inicio = texto.find(trecho)
            while inicio != -1:
                saida.append({"entity_group": rotulo, "score": score, "word": trecho.lower(),
                              "start": inicio, "end": inicio + len(trecho)})
                inicio = texto.find(trecho, inicio + 1)
        return saida
    return ner


@pytest.fixture
def ner_falso(monkeypatch):
    def instalar(achados, modelos=("modelo-falso",)):
        monkeypatch.setattr(clinical_nlp, "ENABLE_NER", True)
        monkeypatch.setattr(clinical_nlp, "MODEL_NAMES", list(modelos))
        monkeypatch.setattr(clinical_nlp, "_obter_pipeline_ner",
                            lambda nome_modelo=None: (_pipeline_falso(achados), None))
    return instalar


def _textos(itens):
    return [item["text"] for item in itens]


def test_ner_termo_que_nenhuma_regra_reconhece_vira_aviso(ner_falso):
    ner_falso([("coronariopata", "Disorder", 0.99), ("ICFEr", "Disorder", 0.98)])
    r = analisar_texto_clinico("Paciente de 61 anos, coronariopata, ICFEr. Colecistectomia.")
    assert _textos(r["ner_review"]["nao_reconhecidos"]) == ["coronariopata", "ICFEr"]
    assert r["ner_review"]["nao_reconhecidos"][0] == {
        "text": "coronariopata", "label": "Disorder", "score": 0.99, "negado": False}
    # O modelo só avisa: o campo continua sem preencher.
    assert "rcri_doenca_coronaria" not in r["autofill"]


def test_ner_termo_reconhecido_pelas_regras_vai_para_confirmados(ner_falso):
    ner_falso([("infarto", "Disorder", 0.97), ("AAS", "ChemicalDrugs", 0.95),
               ("colecistectomia videolaparoscópica", "Procedures", 0.99)])
    r = analisar_texto_clinico("Teve infarto há 2 anos, em uso de AAS. Fará colecistectomia videolaparoscópica.")
    assert _textos(r["ner_review"]["confirmados"]) == ["infarto", "AAS", "colecistectomia videolaparoscópica"]
    assert r["ner_review"]["nao_reconhecidos"] == []


def test_ner_comparacao_por_palavra_inteira(ner_falso):
    # "ic" foi reconhecido pelas regras, mas não pode confirmar "insuficiência renal crônica".
    ner_falso([("insuficiência renal crônica", "Disorder", 0.99)])
    r = analisar_texto_clinico("Paciente com IC e insuficiência renal crônica.")
    assert _textos(r["ner_review"]["nao_reconhecidos"]) == ["insuficiência renal crônica"]


def test_ner_termo_negado_vem_marcado(ner_falso):
    ner_falso([("AVC", "Disorder", 0.99), ("dispneia", "Disorder", 0.99), ("coronariopatia", "Disorder", 0.99)])
    r = analisar_texto_clinico("Nega AVC, nega dispneia, sem coronariopatia. Hipertenso.")
    nao_reconhecidos = {i["text"]: i["negado"] for i in r["ner_review"]["nao_reconhecidos"]}
    confirmados = {i["text"]: i["negado"] for i in r["ner_review"]["confirmados"]}
    assert nao_reconhecidos == {"dispneia": True, "coronariopatia": True}
    # As regras ignoram a negação e usam "AVC"; a conferência marca o termo como negado.
    assert confirmados == {"AVC": True}


def test_ner_score_baixo_e_termo_curto_sao_descartados(ner_falso):
    ner_falso([("coronariopata", "Disorder", 0.59), ("DM", "Disorder", 0.99), ("bócio", "Disorder", 0.60)])
    r = analisar_texto_clinico("Paciente coronariopata, DM, bócio.")
    assert _textos(r["ner_review"]["nao_reconhecidos"]) == ["bócio"]
    # `entities` continua trazendo tudo o que o modelo devolveu.
    assert len(r["entities"]) == 3


def test_ner_entidade_repetida_aparece_uma_vez(ner_falso):
    # Mesmo termo duas vezes no texto e em dois modelos: um aviso só, com o maior score.
    ner_falso([("bisoprolol", "ChemicalDrugs", 0.91)], modelos=("modelo-a", "modelo-b"))
    r = analisar_texto_clinico("Usa bisoprolol pela manhã. Bisoprolol mantido no dia da cirurgia.")
    assert len(r["entities"]) == 2
    assert _textos(r["ner_review"]["nao_reconhecidos"]) == ["bisoprolol"]


def test_ner_trecho_contido_em_outro_aviso_nao_se_repete(ner_falso):
    ner_falso([("DAOP", "Procedures", 0.90), ("DAOP com claudicação", "Disorder", 0.99)])
    r = analisar_texto_clinico("Homem de 57 anos, DAOP com claudicação.")
    assert _textos(r["ner_review"]["nao_reconhecidos"]) == ["DAOP com claudicação"]


def test_ner_todos_os_termos_da_mesma_regra_sao_confirmados(ner_falso):
    # A regra da doença coronariana casa "dac" e "iam"; nenhum dos dois pode virar aviso.
    ner_falso([("DAC", "Disorder", 0.99), ("IAM", "Disorder", 0.99)])
    r = analisar_texto_clinico("Homem de 72 anos, DAC, IAM há 4 meses.")
    assert _textos(r["ner_review"]["confirmados"]) == ["DAC", "IAM"]
    assert r["ner_review"]["nao_reconhecidos"] == []


def test_ner_entidades_trazem_posicao_trecho_original_e_modelo(ner_falso):
    ner_falso([("Coronariopata", "Disorder", 0.99)], modelos=("modelo-a",))
    texto = "Coronariopata em uso de AAS."
    entidade = analisar_texto_clinico(texto)["entities"][0]
    assert entidade == {"text": "Coronariopata", "label": "Disorder", "score": 0.99,
                        "start": 0, "end": 13, "model": "modelo-a"}
    assert texto[entidade["start"]:entidade["end"]] == entidade["text"]


@pytest.mark.parametrize("texto", [CASO_1, CASO_2, CASO_3, CASO_4, CASO_5, CASO_6],
                         ids=["caso1", "caso2", "caso3", "caso4", "caso5", "caso6"])
def test_ner_ligado_nao_altera_o_preenchimento(texto, monkeypatch):
    sem_ner = analisar_texto_clinico(texto)
    assert sem_ner["ner_review"] == {"nao_reconhecidos": [], "confirmados": []}
    assert sem_ner["entities"] == []
    assert sem_ner["model"]["status"] == "fallback"

    achados = [("hipertensão arterial", "Disorder", 0.99), ("diabetes", "Disorder", 0.99),
               ("dispneia", "Disorder", 0.99), ("lesão", "Disorder", 0.99), ("infarto", "Disorder", 0.99),
               ("programação", "Procedures", 0.99)]
    monkeypatch.setattr(clinical_nlp, "ENABLE_NER", True)
    monkeypatch.setattr(clinical_nlp, "MODEL_NAMES", ["modelo-falso"])
    monkeypatch.setattr(clinical_nlp, "_obter_pipeline_ner", lambda nome_modelo=None: (_pipeline_falso(achados), None))
    com_ner = analisar_texto_clinico(texto)

    for campo in ("autofill", "missing_critical", "findings", "summary", "context"):
        assert com_ner[campo] == sem_ner[campo]
    assert com_ner["ner_review"]["nao_reconhecidos"]


def test_ner_sem_transformers_instalado_devolve_avisos_vazios(monkeypatch):
    monkeypatch.setattr(clinical_nlp, "ENABLE_NER", True)
    monkeypatch.setattr(clinical_nlp, "pipeline", None)
    monkeypatch.setattr(clinical_nlp, "_NER_PIPELINES", {})
    monkeypatch.setattr(clinical_nlp, "_NER_ERRORS", {})
    r = analisar_texto_clinico(CASO_1)
    assert r["ner_review"] == {"nao_reconhecidos": [], "confirmados": []}
    assert r["model"]["status"] == "fallback"
    assert "transformers não está instalado" in r["model"]["detail"]
    assert r["autofill"]["usa_aas"] is True


def test_ner_modelos_lidos_do_ambiente(monkeypatch):
    monkeypatch.setenv("CARDIORISK_NER_MODELS", "a/um, b/dois ,a/um")
    monkeypatch.setenv("CARDIORISK_NER_MODEL", "c/antigo")
    assert clinical_nlp._modelos_do_ambiente() == ["a/um", "b/dois"]
    monkeypatch.delenv("CARDIORISK_NER_MODELS")
    assert clinical_nlp._modelos_do_ambiente() == ["c/antigo"]
    monkeypatch.delenv("CARDIORISK_NER_MODEL")
    assert clinical_nlp._modelos_do_ambiente() == list(clinical_nlp.DEFAULT_NER_MODELS)


def test_ner_texto_longo_e_dividido_sem_perder_posicoes():
    texto = "Paciente com coronariopatia grave. " * 80
    trechos = clinical_nlp._dividir_em_trechos(texto)
    assert len(trechos) > 1
    assert "".join(t for _, t in trechos) == texto
    assert all(len(t) <= 1000 and texto[ini:ini + len(t)] == t for ini, t in trechos)
