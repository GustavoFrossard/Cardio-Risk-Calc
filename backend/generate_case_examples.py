#!/usr/bin/env python3
"""
generate_case_examples.py
==========================
Gera knowledge/calculator_cases.json com casos clínicos concretos cobrindo
sistematicamente todas as combinações relevantes da calculadora:

  • RCRI 0-6 (scores individuais e combinados) × 3 riscos cirúrgicos
  • Cada critério RCRI isolado
  • VSG-CRI: todas as faixas etárias × comorbidades × fatores extras
  • Cada uma das 11 condições cardiovasculares ativas isoladas e combinadas
  • METs 1-8 em diferentes contextos
  • AAS: prevenção primária e secundária × tipos de cirurgia (inclusive exceções)
  • Clopidogrel, ticagrelor, prasugrel em vários cenários
  • Varfarina FA × todos os scores CHA₂DS₂-VASc (0-7) × AVC recente
  • Varfarina TEV × timing (recente/3-12m/> 12m) × trombofilia × neoplasia
  • Varfarina prótese valvar mecânica e doença valvar reumática
  • Combinações de múltiplos medicamentos
  • Obesidade, IC, DAC, doença valvar em diferentes cenários
  • Capacidade funcional: cada nível de METs com diferentes cenários

Execute sempre que o calculator.py mudar:
  python generate_case_examples.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calculator import calculate_risk

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
OUT = KNOWLEDGE_DIR / "calculator_cases.json"

# ---------------------------------------------------------------------------
# Helpers para construir perfis base
# ---------------------------------------------------------------------------

def _rcri_base(surgery_risk="intermediate", mets=4, **flags):
    base = {
        "surgery_type": "abdominal_major" if surgery_risk == "high" else "abdominal_minor",
        "surgery_risk": surgery_risk,
        "is_vascular": False,
        "mets": mets,
        "rcri_high_risk_surgery": False,
        "rcri_ischemic_heart": False,
        "rcri_heart_failure": False,
        "rcri_cerebrovascular": False,
        "rcri_insulin_diabetes": False,
        "rcri_creatinine_above_2": False,
    }
    base.update(flags)
    return base


def _vsg_base(age_range="70_79", mets=4, **flags):
    base = {
        "surgery_type": "vascular_peripheral",
        "surgery_risk": "high",
        "is_vascular": True,
        "mets": mets,
        "vsg_age_range": age_range,
        "vsg_cad": False,
        "vsg_chf": False,
        "vsg_copd": False,
        "vsg_creatinine_over_1_8": False,
        "vsg_smoking": False,
        "vsg_insulin_diabetes": False,
        "vsg_chronic_beta_blocker": False,
        "vsg_prior_revasc": False,
    }
    base.update(flags)
    return base


# ---------------------------------------------------------------------------
# Geracao sistematica de perfis
# ---------------------------------------------------------------------------

def build_profiles():
    profiles = []

    def add(label, data):
        profiles.append({"_label": label, **data})

    # =========================================================================
    # 1. RCRI - cada criterio isolado
    # =========================================================================
    add("RCRI criterio isolado: cirurgia de alto risco (suprainguinal/intratoracica), sem outros",
        _rcri_base(surgery_risk="intermediate", mets=5, rcri_high_risk_surgery=True))
    add("RCRI criterio isolado: doenca isquemica cardiaca (DAC estavel), herniorrafia",
        _rcri_base(surgery_risk="intermediate", mets=5, rcri_ischemic_heart=True, known_cad=True))
    add("RCRI criterio isolado: insuficiencia cardiaca congestiva (ICC compensada), colecistectomia",
        _rcri_base(surgery_risk="intermediate", mets=4, rcri_heart_failure=True, known_hf=True))
    add("RCRI criterio isolado: doenca cerebrovascular (AVC previo), cirurgia ortopedica",
        _rcri_base(surgery_risk="intermediate", mets=4, rcri_cerebrovascular=True,
                   surgery_type="orthopedic_major"))
    add("RCRI criterio isolado: diabetes com insulinoterapia, tireoidectomia",
        _rcri_base(surgery_risk="low", mets=5, rcri_insulin_diabetes=True,
                   surgery_type="endocrine"))
    add("RCRI criterio isolado: creatinina > 2.0 mg/dL, cirurgia abdominal",
        _rcri_base(surgery_risk="intermediate", mets=4, rcri_creatinine_above_2=True))

    # =========================================================================
    # 2. RCRI - scores 0 a 6 com cirurgias de diferentes riscos
    # =========================================================================
    for s_risk, s_type in [("low", "eye"), ("intermediate", "abdominal_minor"), ("high", "thoracic")]:
        label_risk = {"low": "Baixo", "intermediate": "Intermediario", "high": "Alto"}[s_risk]
        add(f"RCRI Score 0 - cirurgia {label_risk} risco, paciente sem fatores, METs adequado",
            _rcri_base(surgery_risk=s_risk, mets=6, surgery_type=s_type))

    add("RCRI Score 1 - 1 ponto (DAC), cirurgia intermediaria, METs 5",
        _rcri_base(surgery_risk="intermediate", mets=5, rcri_ischemic_heart=True))
    add("RCRI Score 1 - 1 ponto (ICC), cirurgia intermediaria, METs 4",
        _rcri_base(surgery_risk="intermediate", mets=4, rcri_heart_failure=True, known_hf=True))
    add("RCRI Score 1 - 1 ponto (DM insulina), cirurgia baixo risco",
        _rcri_base(surgery_risk="low", mets=5, rcri_insulin_diabetes=True, surgery_type="eye"))

    add("RCRI Score 2 - DAC + cirurgia alto risco, METs 4",
        _rcri_base(surgery_risk="high", mets=4, rcri_high_risk_surgery=True,
                   rcri_ischemic_heart=True, known_cad=True))
    add("RCRI Score 2 - ICC + creatinina > 2, cirurgia intermediaria, METs 3",
        _rcri_base(surgery_risk="intermediate", mets=3,
                   rcri_heart_failure=True, rcri_creatinine_above_2=True, known_hf=True))
    add("RCRI Score 2 - DM insulina + AVC previo, cirurgia de cabeca/pescoco",
        _rcri_base(surgery_risk="intermediate", mets=4,
                   rcri_insulin_diabetes=True, rcri_cerebrovascular=True,
                   surgery_type="head_neck"))

    add("RCRI Score 3 - DAC + ICC + DM insulina, cirurgia intermediaria, METs 3",
        _rcri_base(surgery_risk="intermediate", mets=3,
                   rcri_ischemic_heart=True, rcri_heart_failure=True,
                   rcri_insulin_diabetes=True, known_hf=True, known_cad=True))
    add("RCRI Score 3 - cirurgia alto risco + creatinina > 2 + AVC, METs 4",
        _rcri_base(surgery_risk="high", mets=4,
                   rcri_high_risk_surgery=True, rcri_creatinine_above_2=True,
                   rcri_cerebrovascular=True))
    add("RCRI Score 3 - DAC + AVC + DM insulina, cirurgia alto risco, METs 2",
        _rcri_base(surgery_risk="high", mets=2,
                   rcri_ischemic_heart=True, rcri_cerebrovascular=True,
                   rcri_insulin_diabetes=True, known_cad=True))

    add("RCRI Score 4 - DAC + ICC + cirurgia alto risco + creatinina, METs 2",
        _rcri_base(surgery_risk="high", mets=2,
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True,
                   rcri_heart_failure=True, rcri_creatinine_above_2=True,
                   known_hf=True, known_cad=True))
    add("RCRI Score 4 - DM + AVC + ICC + creatinina, cirurgia alto risco, METs 1",
        _rcri_base(surgery_risk="high", mets=1,
                   rcri_insulin_diabetes=True, rcri_cerebrovascular=True,
                   rcri_heart_failure=True, rcri_creatinine_above_2=True, known_hf=True))

    add("RCRI Score 5 - 5 criterios (todos exceto AVC), esofagectomia, METs 1",
        _rcri_base(surgery_risk="high", mets=1, surgery_type="thoracic",
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True,
                   rcri_heart_failure=True, rcri_insulin_diabetes=True,
                   rcri_creatinine_above_2=True, known_hf=True, known_cad=True))

    add("RCRI Score 6 - todos os 6 criterios, cirurgia de alto risco, METs 1",
        _rcri_base(surgery_risk="high", mets=1, surgery_type="thoracic",
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True,
                   rcri_heart_failure=True, rcri_cerebrovascular=True,
                   rcri_insulin_diabetes=True, rcri_creatinine_above_2=True,
                   known_hf=True, known_cad=True))

    # =========================================================================
    # 3. RCRI - variacoes de capacidade funcional (todos os niveis de METs)
    # =========================================================================
    for mets_val, desc in [(1, "acamado/sem atividade"), (2, "muito limitado"),
                           (3, "limitado - nao sobe escada"), (4, "limite - sobe escada"),
                           (5, "moderado - jardim"), (7, "bom - esportes"), (8, "excelente")]:
        add(f"RCRI Score 1 (DAC), METs {mets_val} ({desc}), cirurgia intermediaria",
            _rcri_base(surgery_risk="intermediate", mets=mets_val,
                       rcri_ischemic_heart=True, known_cad=True))

    add("RCRI Score 2 + METs 2 (muito limitado), cirurgia alto risco - teste funcional indicado",
        _rcri_base(surgery_risk="high", mets=2,
                   rcri_ischemic_heart=True, rcri_high_risk_surgery=True, known_cad=True))
    add("RCRI Score 0 + METs 1 (acamado), cirurgia intermediaria - capacidade reduzida sem cardiopatia",
        _rcri_base(surgery_risk="intermediate", mets=1))

    # =========================================================================
    # 4. Condicoes cardiovasculares ativas - cada uma isolada
    # =========================================================================
    active_conditions = [
        ("cv_acute_coronary",            "Sindrome coronariana aguda"),
        ("cv_unstable_aortic",           "Doenca instavel da aorta toracica"),
        ("cv_acute_pulmonary_edema",     "Edema agudo de pulmao"),
        ("cv_cardiogenic_shock",         "Choque cardiogenico"),
        ("cv_hf_nyha_3_4",               "IC NYHA III/IV"),
        ("cv_angina_ccs_3_4",            "Angina CCS III/IV"),
        ("cv_severe_arrhythmia",         "Arritmia grave (BAVT/TV)"),
        ("cv_uncontrolled_hypertension", "HAS nao controlada PA > 180x110"),
        ("cv_af_high_rate",              "FA com alta resposta ventricular FC > 120"),
        ("cv_pulmonary_hypertension",    "Hipertensao pulmonar sintomatica"),
        ("cv_severe_valvular",           "Estenose aortica/mitral grave sintomatica"),
    ]
    for field, desc in active_conditions:
        add(f"Condicao ativa isolada: {desc} - cirurgia eletiva abdominal",
            _rcri_base(surgery_risk="intermediate", mets=3, **{field: True}))

    # Combinacoes de condicoes ativas
    add("Condicoes ativas combinadas: sindrome coronariana aguda + IC NYHA III",
        _rcri_base(surgery_risk="intermediate", mets=2,
                   cv_acute_coronary=True, cv_hf_nyha_3_4=True, known_hf=True))
    add("Condicoes ativas combinadas: HAS nao controlada + FA alta resposta ventricular",
        _rcri_base(surgery_risk="intermediate", mets=3,
                   cv_uncontrolled_hypertension=True, cv_af_high_rate=True))
    add("Condicoes ativas combinadas: estenose aortica grave + IC NYHA III/IV",
        _rcri_base(surgery_risk="intermediate", mets=1,
                   cv_severe_valvular=True, cv_hf_nyha_3_4=True,
                   known_valvular_disease=True, known_hf=True))
    add("Condicoes ativas: angina CCS III + HAS nao controlada + RCRI 2 pontos",
        _rcri_base(surgery_risk="high", mets=2,
                   cv_angina_ccs_3_4=True, cv_uncontrolled_hypertension=True,
                   rcri_ischemic_heart=True, rcri_high_risk_surgery=True, known_cad=True))

    # =========================================================================
    # 5. VSG-CRI - faixas etarias x comorbidades
    # =========================================================================
    # Idade como unico fator
    for age_range, desc in [("lt60", "<60 anos"), ("60_69", "60-69 anos"),
                              ("70_79", "70-79 anos"), ("gte80", ">=80 anos")]:
        add(f"VSG-CRI idade {desc}, sem outras comorbidades, endarterectomia carotida",
            _vsg_base(age_range=age_range, mets=5))

    # DAC em diferentes idades
    for age_range, desc in [("60_69", "60-69"), ("70_79", "70-79"), ("gte80", ">=80")]:
        add(f"VSG-CRI {desc} anos + DAC, bypass aorto-femoral, METs 4",
            _vsg_base(age_range=age_range, mets=4, vsg_cad=True, known_cad=True))

    # ICC
    add("VSG-CRI 70-79 anos + ICC, cirurgia vascular periferica, METs 2",
        _vsg_base(age_range="70_79", mets=2, vsg_chf=True, known_hf=True))
    add("VSG-CRI >=80 anos + ICC + creatinina > 1.8, bypass, METs 2",
        _vsg_base(age_range="gte80", mets=2, vsg_chf=True, vsg_creatinine_over_1_8=True,
                  known_hf=True))

    # DPOC
    add("VSG-CRI 70-79 anos + DPOC, aneurisma aortico, METs 3",
        _vsg_base(age_range="70_79", mets=3, vsg_copd=True))
    add("VSG-CRI 70-79 anos + DPOC + tabagismo + betabloqueador, aneurisma aortico, METs 3",
        _vsg_base(age_range="70_79", mets=3, vsg_copd=True, vsg_smoking=True,
                  vsg_chronic_beta_blocker=True))

    # Tabagismo e DM isolados
    add("VSG-CRI 60-69 anos + tabagismo ativo, bypass aorto-femoral, METs 5",
        _vsg_base(age_range="60_69", mets=5, vsg_smoking=True))
    add("VSG-CRI 70-79 anos + DM insulina, endarterectomia, METs 4",
        _vsg_base(age_range="70_79", mets=4, vsg_insulin_diabetes=True))
    add("VSG-CRI 70-79 anos + betabloqueador cronico, cirurgia periferica, METs 5",
        _vsg_base(age_range="70_79", mets=5, vsg_chronic_beta_blocker=True))

    # Revascularizacao previa (fator protetor -1)
    add("VSG-CRI 70-79 anos + DAC + revascularizacao previa (-1 ponto), bypass",
        _vsg_base(age_range="70_79", mets=5, vsg_cad=True, vsg_prior_revasc=True, known_cad=True))
    add("VSG-CRI >=80 anos + DAC + DPOC + revascularizacao previa, METs 3",
        _vsg_base(age_range="gte80", mets=3, vsg_cad=True, vsg_copd=True,
                  vsg_prior_revasc=True, known_cad=True))

    # Score alto VSG (>=7)
    add("VSG-CRI Score alto (>=7): >=80 anos + DAC + ICC + DPOC, bypass, METs 2",
        _vsg_base(age_range="gte80", mets=2,
                  vsg_cad=True, vsg_chf=True, vsg_copd=True, known_hf=True, known_cad=True))
    add("VSG-CRI Score maximo: 70-79 anos + todas comorbidades exceto revascularizacao, METs 1",
        _vsg_base(age_range="70_79", mets=1,
                  vsg_cad=True, vsg_chf=True, vsg_copd=True, vsg_creatinine_over_1_8=True,
                  vsg_smoking=True, vsg_insulin_diabetes=True, vsg_chronic_beta_blocker=True,
                  known_hf=True, known_cad=True))
    add("VSG-CRI Score alto: 60-69 anos + DAC + ICC + tabagismo + creatinina, METs 2",
        _vsg_base(age_range="60_69", mets=2,
                  vsg_cad=True, vsg_chf=True, vsg_smoking=True, vsg_creatinine_over_1_8=True,
                  known_hf=True, known_cad=True))

    # =========================================================================
    # 6. AAS - todas combinacoes de indicacao x tipo de cirurgia
    # =========================================================================
    # Prevencao primaria
    for s_type, s_risk, desc in [
        ("abdominal_minor", "low",          "colecistectomia laparoscopica"),
        ("orthopedic_major", "intermediate", "artroplastia de quadril"),
        ("thoracic", "high",                "lobectomia pulmonar"),
        ("eye", "low",                      "cirurgia de catarata"),
    ]:
        add(f"AAS prevencao primaria - {desc} (risco {s_risk})",
            _rcri_base(surgery_risk=s_risk, mets=5, surgery_type=s_type,
                       uses_aas=True, aas_prevention="primary"))

    # Prevencao secundaria - cirurgias que MANTEM AAS
    for s_type, s_risk, desc in [
        ("abdominal_minor", "intermediate", "herniorrafia"),
        ("orthopedic_major", "intermediate", "artroplastia"),
        ("thoracic", "high",                "cirurgia toracica"),
        ("abdominal_major", "high",         "colectomia aberta"),
        ("abdominal_minor", "low",          "colecistectomia laparoscopica"),
    ]:
        add(f"AAS prevencao secundaria - MANTER - {desc}",
            _rcri_base(surgery_risk=s_risk, mets=5, surgery_type=s_type,
                       uses_aas=True, aas_prevention="secondary",
                       rcri_ischemic_heart=True, known_cad=True))

    # Prevencao secundaria - EXCECOES (suspender)
    for s_type, desc in [
        ("neurologic",    "neurocirurgia intracraniana"),
        ("urologic_minor", "RTU de prostata"),
        ("eye",           "cirurgia de retina"),
    ]:
        add(f"AAS prevencao secundaria - SUSPENDER (excecao) - {desc}",
            _rcri_base(surgery_risk="high", mets=5, surgery_type=s_type,
                       uses_aas=True, aas_prevention="secondary",
                       rcri_ischemic_heart=True, known_cad=True))

    # =========================================================================
    # 7. P2Y12 - clopidogrel, ticagrelor, prasugrel em diferentes contextos
    # =========================================================================
    for s_risk, desc in [("low", "cirurgia de baixo risco (catarata)"),
                          ("intermediate", "cirurgia intermediaria"),
                          ("high", "cirurgia de alto risco")]:
        s_type = "eye" if s_risk == "low" else "abdominal_minor"
        add(f"Clopidogrel pos-stent coronariano - {desc}",
            _rcri_base(surgery_risk=s_risk, mets=5, surgery_type=s_type,
                       rcri_ischemic_heart=True, uses_clopidogrel=True, known_cad=True))

    add("Ticagrelor pos-IAM < 6 meses - cirurgia intermediaria, METs 5",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   rcri_ischemic_heart=True, uses_ticagrelor=True, known_cad=True))
    add("Ticagrelor + AAS (dupla antiagregacao pos-stent) - cirurgia eletiva intermediaria",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   rcri_ischemic_heart=True, uses_ticagrelor=True,
                   uses_aas=True, aas_prevention="secondary", known_cad=True))
    add("Ticagrelor + AAS (dupla antiagregacao) - cirurgia de alto risco",
        _rcri_base(surgery_risk="high", mets=4,
                   rcri_ischemic_heart=True, rcri_high_risk_surgery=True,
                   uses_ticagrelor=True, uses_aas=True, aas_prevention="secondary",
                   known_cad=True))

    add("Prasugrel pos-stent coronariano - cirurgia eletiva ortopedica",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   rcri_ischemic_heart=True, uses_prasugrel=True,
                   surgery_type="orthopedic_major", known_cad=True))
    add("Prasugrel + AAS (dupla antiagregacao) - cirurgia de alto risco",
        _rcri_base(surgery_risk="high", mets=4,
                   rcri_ischemic_heart=True, rcri_high_risk_surgery=True,
                   uses_prasugrel=True, uses_aas=True, aas_prevention="secondary",
                   known_cad=True))
    add("Prasugrel (sem clopidogrel) - cirurgia de baixo risco",
        _rcri_base(surgery_risk="low", mets=6, surgery_type="eye",
                   rcri_ischemic_heart=True, uses_prasugrel=True, known_cad=True))

    # =========================================================================
    # 8. Varfarina + FA - todos os scores CHA2DS2-VASc (0 a 7)
    # =========================================================================
    for score in range(0, 8):
        add(f"Varfarina por FA - CHA2DS2-VASc {score}, cirurgia abdominal eletiva",
            _rcri_base(surgery_risk="intermediate", mets=4,
                       uses_warfarin=True, warfarin_indication="af",
                       warfarin_chadsvasc=score, warfarin_stroke_3m=False))

    # AVC/AIT recente (<3 meses) com diferentes scores
    for score in [1, 2, 3, 4, 5, 6]:
        add(f"Varfarina FA - CHA2DS2-VASc {score} + AVC ha 6 semanas (< 3 meses) - ponte obrigatoria",
            _rcri_base(surgery_risk="intermediate", mets=3,
                       rcri_cerebrovascular=True,
                       uses_warfarin=True, warfarin_indication="af",
                       warfarin_chadsvasc=score, warfarin_stroke_3m=True))

    # =========================================================================
    # 9. Varfarina + TEV - timing x trombofilia x neoplasia
    # =========================================================================
    for timing, desc in [("recent", "recente < 3 meses"),
                          ("3_12m", "entre 3 e 12 meses"),
                          ("over_12m", "mais de 12 meses")]:
        add(f"Varfarina TEV {desc} - sem trombofilia, sem neoplasia",
            _rcri_base(surgery_risk="intermediate", mets=5,
                       uses_warfarin=True, warfarin_indication="vte",
                       warfarin_vte_timing=timing, warfarin_thrombophilia="none",
                       warfarin_active_neoplasia=False))

    add("Varfarina TEV 3-12 meses + trombofilia leve (fator V Leiden heterozigoto)",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="3_12m", warfarin_thrombophilia="mild",
                   warfarin_active_neoplasia=False))
    add("Varfarina TEV 3-12 meses + neoplasia ativa (cancer em tratamento)",
        _rcri_base(surgery_risk="intermediate", mets=3,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="3_12m", warfarin_thrombophilia="none",
                   warfarin_active_neoplasia=True))
    add("Varfarina TEV 3-12 meses + trombofilia leve + neoplasia ativa",
        _rcri_base(surgery_risk="intermediate", mets=3,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="3_12m", warfarin_thrombophilia="mild",
                   warfarin_active_neoplasia=True))
    add("Varfarina TEV recente + RCRI 1 ponto (DM), cirurgia ortopedica",
        _rcri_base(surgery_risk="intermediate", mets=4, surgery_type="orthopedic_major",
                   rcri_insulin_diabetes=True,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="recent", warfarin_thrombophilia="none",
                   warfarin_active_neoplasia=False))

    # =========================================================================
    # 10. Varfarina + protese valvar mecanica e doenca reumatica
    # =========================================================================
    for s_risk, desc in [("low", "baixo"), ("intermediate", "intermediario"), ("high", "alto")]:
        add(f"Varfarina por protese valvar mecanica - cirurgia risco {desc}",
            _rcri_base(surgery_risk=s_risk, mets=4,
                       uses_warfarin=True, warfarin_indication="mechanical_valve",
                       known_valvular_disease=True))

    add("Varfarina por doenca valvar reumatica (estenose mitral + FA), cirurgia eletiva",
        _rcri_base(surgery_risk="intermediate", mets=4,
                   uses_warfarin=True, warfarin_indication="rheumatic",
                   known_valvular_disease=True))
    add("Varfarina por protese valvar mecanica + RCRI 2 pontos (ICC + DM), cirurgia alto risco",
        _rcri_base(surgery_risk="high", mets=2,
                   rcri_high_risk_surgery=True, rcri_heart_failure=True, rcri_insulin_diabetes=True,
                   uses_warfarin=True, warfarin_indication="mechanical_valve",
                   known_valvular_disease=True, known_hf=True))

    # =========================================================================
    # 11. Combinacoes de multiplos medicamentos
    # =========================================================================
    add("AAS secundaria + clopidogrel (dupla antiagregacao pos-stent), cirurgia intermediaria",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   rcri_ischemic_heart=True, uses_aas=True, aas_prevention="secondary",
                   uses_clopidogrel=True, known_cad=True))
    add("Varfarina FA (CHA2 3) + AAS secundaria (DAC + FA), RCRI 1, cirurgia intermediaria",
        _rcri_base(surgery_risk="intermediate", mets=4,
                   rcri_ischemic_heart=True,
                   uses_warfarin=True, warfarin_indication="af",
                   warfarin_chadsvasc=3, warfarin_stroke_3m=False,
                   uses_aas=True, aas_prevention="secondary", known_cad=True))
    add("Varfarina TEV + clopidogrel (TEV + stent coronariano), cirurgia eletiva",
        _rcri_base(surgery_risk="intermediate", mets=5,
                   rcri_ischemic_heart=True,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="3_12m", warfarin_thrombophilia="none",
                   warfarin_active_neoplasia=False,
                   uses_clopidogrel=True, known_cad=True))
    add("AAS primaria + RCRI 0 + cirurgia de baixo risco - suspender AAS",
        _rcri_base(surgery_risk="low", mets=6, surgery_type="eye",
                   uses_aas=True, aas_prevention="primary"))

    # =========================================================================
    # 12. Comorbidades extras - obesidade, IC, DAC, doenca valvar
    # =========================================================================
    add("Obesidade isolada, sem outros fatores, cirurgia abdominal intermediaria, METs 3",
        _rcri_base(surgery_risk="intermediate", mets=3, obesity=True))
    add("Obesidade + DM insulina + RCRI 1, cirurgia intermediaria",
        _rcri_base(surgery_risk="intermediate", mets=3, obesity=True, rcri_insulin_diabetes=True))
    add("Obesidade + ICC + creatinina > 2 + RCRI 2, cirurgia ortopedica maior",
        _rcri_base(surgery_risk="intermediate", mets=2, obesity=True,
                   surgery_type="orthopedic_major",
                   rcri_heart_failure=True, rcri_creatinine_above_2=True, known_hf=True))
    add("Obesidade + DAC + RCRI 2, cirurgia alto risco, METs 3",
        _rcri_base(surgery_risk="high", mets=3, obesity=True,
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True, known_cad=True))
    add("IC conhecida/suspeita sem criterio RCRI formal, cirurgia de baixo risco",
        _rcri_base(surgery_risk="low", mets=4, surgery_type="eye", known_hf=True))
    add("IC conhecida + RCRI ICC + METs 2, cirurgia alto risco",
        _rcri_base(surgery_risk="high", mets=2,
                   rcri_high_risk_surgery=True, rcri_heart_failure=True, known_hf=True))
    add("DAC conhecida + RCRI 1, cirurgia baixo risco (catarata), METs 5",
        _rcri_base(surgery_risk="low", mets=5, surgery_type="eye",
                   rcri_ischemic_heart=True, known_cad=True))
    add("DAC conhecida + RCRI 2 (DAC + cirurgia alto risco), METs 3",
        _rcri_base(surgery_risk="high", mets=3,
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True, known_cad=True))
    add("Doenca valvar leve conhecida, sem criterio RCRI, cirurgia ortopedica menor",
        _rcri_base(surgery_risk="low", mets=6, surgery_type="orthopedic_minor",
                   known_valvular_disease=True))
    add("Doenca valvar grave + IC + condicao ativa - cirurgia deve ser adiada",
        _rcri_base(surgery_risk="intermediate", mets=1,
                   cv_severe_valvular=True, known_valvular_disease=True,
                   rcri_heart_failure=True, known_hf=True))

    # =========================================================================
    # 13. Cirurgia de BAIXO risco - prosseguir sempre (exceto condicao ativa)
    # =========================================================================
    for s_type, desc in [("eye", "catarata"), ("abdominal_minor", "colecistectomia laparoscopica"),
                          ("endocrine", "tireoidectomia"), ("breast", "mastectomia simples"),
                          ("orthopedic_minor", "artroscopia de joelho")]:
        add(f"Cirurgia baixo risco intrinseco - {desc}, paciente sem fatores cardiovasculares",
            _rcri_base(surgery_risk="low", mets=7, surgery_type=s_type))

    add("Cirurgia baixo risco + RCRI 2 pontos - prosseguir (risco cirurgico prevalece)",
        _rcri_base(surgery_risk="low", mets=4, surgery_type="eye",
                   rcri_ischemic_heart=True, rcri_creatinine_above_2=True, known_cad=True))
    add("Cirurgia baixo risco + RCRI 3 pontos - prosseguir (risco cirurgico baixo < 1%)",
        _rcri_base(surgery_risk="low", mets=3, surgery_type="eye",
                   rcri_ischemic_heart=True, rcri_heart_failure=True,
                   rcri_insulin_diabetes=True, known_hf=True, known_cad=True))

    # =========================================================================
    # 14. Casos complexos e realistas
    # =========================================================================
    add("Homem 72 anos, IAM ha 3 meses (DAC), DM insulina, creatinina 2.5, colectomia aberta - RCRI 4",
        _rcri_base(surgery_risk="high", mets=3,
                   rcri_high_risk_surgery=True, rcri_ischemic_heart=True,
                   rcri_insulin_diabetes=True, rcri_creatinine_above_2=True,
                   uses_aas=True, aas_prevention="secondary",
                   uses_clopidogrel=True, known_cad=True))

    add("Mulher 80 anos, IC NYHA II, FA (CHA2DS2 5), DM insulina, obesa, cirurgia ortopedica urgente",
        _rcri_base(surgery_risk="intermediate", mets=2, surgery_type="orthopedic_major",
                   rcri_heart_failure=True, rcri_insulin_diabetes=True,
                   uses_warfarin=True, warfarin_indication="af",
                   warfarin_chadsvasc=5, warfarin_stroke_3m=False,
                   known_hf=True, obesity=True))

    add("Homem 65 anos, DAC + stent ha 4 meses (clopidogrel+AAS), DPOC, obeso, hernia inguinal",
        _rcri_base(surgery_risk="intermediate", mets=4,
                   rcri_ischemic_heart=True,
                   uses_clopidogrel=True, uses_aas=True, aas_prevention="secondary",
                   obesity=True, known_cad=True))

    add("Mulher 58 anos, TVP ha 6 semanas (TEV recente) + varfarina, colecistectomia urgente",
        _rcri_base(surgery_risk="low", mets=5,
                   uses_warfarin=True, warfarin_indication="vte",
                   warfarin_vte_timing="recent", warfarin_thrombophilia="none",
                   warfarin_active_neoplasia=False))

    add("Homem 78 anos, protese valvar mecanica + AAS secundario + IC + DM, esofagectomia - RCRI 4",
        _rcri_base(surgery_risk="high", mets=2, surgery_type="thoracic",
                   rcri_high_risk_surgery=True, rcri_heart_failure=True, rcri_insulin_diabetes=True,
                   uses_warfarin=True, warfarin_indication="mechanical_valve",
                   uses_aas=True, aas_prevention="secondary",
                   known_hf=True, known_valvular_disease=True))

    add("VSG-CRI complexo: homem 75 anos, aneurisma aortico, DAC + DPOC + tabagismo + betabloqueador, METs 3",
        _vsg_base(age_range="70_79", mets=3, surgery_type="aortic",
                  vsg_cad=True, vsg_copd=True, vsg_smoking=True, vsg_chronic_beta_blocker=True,
                  known_cad=True))

    add("VSG-CRI complexo: mulher 82 anos, bypass fem-popliteo, ICC + creatinina 2.1 + DM + tabagista, METs 1",
        _vsg_base(age_range="gte80", mets=1,
                  vsg_chf=True, vsg_creatinine_over_1_8=True,
                  vsg_insulin_diabetes=True, vsg_smoking=True, known_hf=True))

    add("Paciente jovem 38 anos, saudavel, METs 8, laparoscopia diagnostica - risco minimo",
        _rcri_base(surgery_risk="low", mets=8, surgery_type="abdominal_minor"))

    add("Paciente com todos os criterios RCRI mas cirurgia de baixo risco - prosseguir",
        _rcri_base(surgery_risk="low", mets=2, surgery_type="eye",
                   rcri_ischemic_heart=True, rcri_heart_failure=True, rcri_cerebrovascular=True,
                   rcri_insulin_diabetes=True, rcri_creatinine_above_2=True,
                   known_hf=True, known_cad=True))

    add("Idoso 85 anos, RCRI 3, METs 1, creatinina 2.5, ICC, cirurgia abdominal alto risco",
        _rcri_base(surgery_risk="high", mets=1,
                   rcri_high_risk_surgery=True, rcri_heart_failure=True,
                   rcri_creatinine_above_2=True, known_hf=True))

    add("Mulher 55 anos, saudavel, BNP normal, METs 7, mastectomia - risco baixo sem restricoes",
        _rcri_base(surgery_risk="low", mets=7, surgery_type="breast"))

    add("Homem 70 anos, AVC ha 2 meses + varfarina FA (CHA2DS2 4) + RCRI 1, cirurgia ortopedica",
        _rcri_base(surgery_risk="intermediate", mets=3, surgery_type="orthopedic_major",
                   rcri_cerebrovascular=True,
                   uses_warfarin=True, warfarin_indication="af",
                   warfarin_chadsvasc=4, warfarin_stroke_3m=True))

    return profiles


# ---------------------------------------------------------------------------
# Formatacao do resultado como texto legivel
# ---------------------------------------------------------------------------

def _fmt_med(m: dict) -> str:
    color = {"green": "[OK]", "amber": "[!]", "red": "[X]"}.get(m.get("type", ""), "-")
    return f"  {color} {m['medication']}: {m['action']} -- {m['detail']}"


def _fmt_rec(r: dict) -> str:
    return f"  {r.get('icon', '-')} {r['title']}: {r['body']}"


def format_case(label: str, data: dict, result: dict) -> str:
    lines = [f"CASO CLINICO: {label}", ""]

    # Score
    idx = result["risk_index"].upper()
    lines.append(f"INDICE UTILIZADO: {idx}")
    lines.append(f"PONTUACAO: {result['score']} ponto(s) -- Classe {result['score_class']}")
    lines.append(f"RISCO DE MACE ESTIMADO: {result['mace_risk_pct']}%")
    lines.append(f"NIVEL DE RISCO: {result['risk_label']}")
    lines.append("")

    # Condicoes ativas
    active = result.get("active_conditions", [])
    if active:
        lines.append("CONDICOES CARDIOVASCULARES ATIVAS (adiar cirurgia eletiva):")
        for c in active:
            lines.append(f"  [!] {c}")
        lines.append("")

    # Recomendacoes gerais
    recs = result.get("recommendations", [])
    if recs:
        lines.append("RECOMENDACOES:")
        for r in recs:
            lines.append(_fmt_rec(r))
        lines.append("")

    # Medicamentos
    meds = result.get("medication_advice", [])
    if meds:
        lines.append("CONDUTA MEDICAMENTOSA:")
        for m in meds:
            lines.append(_fmt_med(m))
        lines.append("")

    # Exames
    exams = result.get("recommended_exams", [])
    if exams:
        lines.append("EXAMES PRE-OPERATORIOS:")
        for e in exams:
            lines.append(f"  - {e}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    profiles = build_profiles()
    chunks = []

    for profile in profiles:
        label = profile.pop("_label")
        try:
            result = calculate_risk(profile)
            text = format_case(label, profile, result)
            chunks.append({"page": len(chunks) + 1, "text": text})
        except Exception as e:
            print(f"  [!] {label[:70]}  ->  ERRO: {e}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"OK Gerado: {OUT.name}  ({len(chunks)} casos de {len(profiles)} perfis)")


if __name__ == "__main__":
    main()
