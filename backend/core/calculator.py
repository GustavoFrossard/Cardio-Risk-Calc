"""
CardioRisk Periop - Risk Calculation Engine
============================================
Perioperative cardiovascular risk assessment based on:
  - Diretriz Brasileira de Avaliação Cardiovascular Perioperatória
  - RCRI (Lee Index) for non-vascular surgery
  - VSG Cardiac Risk Index for vascular surgery
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SurgeryRisk(str, Enum):
    LOW = "low"
    INTERMEDIATE = "intermediate"
    HIGH = "high"


class RiskClass(str, Enum):
    LOW = "low"
    INTERMEDIATE = "intermediate"
    HIGH = "high"


class RecommendationType(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# ---------------------------------------------------------------------------
# RCRI Risk Table (Duceppe et al, CMAJ 2017 / Diretriz SBC)
# ---------------------------------------------------------------------------

RCRI_TABLE: dict[int, tuple[str, float]] = {
    0: ("I",   3.9),
    1: ("II",  6.0),
    2: ("III", 10.1),
}
# ≥3 factors → Class IV, 15.0% (ESC 2022 / Diretriz SBC 2024)


def _get_rcri_risk(score: int) -> tuple[str, float]:
    if score >= 3:
        return ("IV", 15.0)
    return RCRI_TABLE.get(score, ("I", 3.9))


# ---------------------------------------------------------------------------
# VSG Cardiac Risk Index Table (Bertges et al / Diretriz SBC)
# ---------------------------------------------------------------------------

def _get_vsg_risk(score: int) -> tuple[str, float]:
    """VSG-CRI risk classification (Tabela 7).

    A diretriz SBC 2024 não fornece percentuais específicos para o VSG-CRI,
    apenas as classes. Os valores estimados abaixo foram derivados de Bertges
    et al. para fins de visualização no gauge.
    """
    if score >= 7:
        return ("Alto", 15.0)
    elif score >= 5:
        return ("Intermediário", 8.0)
    else:
        return ("Baixo", 3.5)


# ---------------------------------------------------------------------------
# METs Labels (pt-BR)
# ---------------------------------------------------------------------------

METS_LABELS: dict[float, str] = {
    1:    "Nenhuma atividade / acamado",
    2.7:  "Trabalhos leves em casa (juntar lixo, lavar louça)",
    2.75: "Cuidar de si mesmo / caminhar uma quadra no plano",
    3.5:  "Trabalhos moderados em casa (aspirador, varrer, carregar mantimentos)",
    4.5:  "Trabalhos no jardim/quintal (rastelo, cortar grama)",
    5.25: "Atividade sexual",
    5.5:  "Subir um lance de escadas ou caminhar em subida",
    6:    "Atividades recreacionais moderadas (boliche, dança, tênis em dupla)",
    7.5:  "Esportes (natação, tênis individual, futebol)",
    8:    "Trabalhos pesados em casa / correr distância curta",
}

SURGERY_LABELS: dict[str, str] = {
    "low":          "Baixo Risco",
    "intermediate": "Risco Intermediário",
    "high":         "Alto Risco",
}


# ---------------------------------------------------------------------------
# RCRI Scoring
# ---------------------------------------------------------------------------

def score_rcri(data: dict) -> tuple[int, list[str]]:
    criteria: list[tuple[bool, str]] = [
        (data.get("rcri_high_risk_surgery", False),
         "Operação intraperitoneal, intratorácica ou vascular suprainguinal"),
        (data.get("rcri_ischemic_heart", False),
         "Doença arterial coronária (ondas Q, sintomas de isquemia, teste+, uso de nitrato)"),
        (data.get("rcri_heart_failure", False),
         "Insuficiência cardíaca congestiva (clínica, RX tórax com congestão)"),
        (data.get("rcri_cerebrovascular", False),
         "Doença cerebrovascular"),
        (data.get("rcri_insulin_diabetes", False),
         "Diabetes com insulinoterapia"),
        (data.get("rcri_creatinine_above_2", False),
         "Creatinina pré-operatória > 2,0 mg/dL"),
    ]
    met = [label for active, label in criteria if active]
    return len(met), met


# ---------------------------------------------------------------------------
# VSG Scoring
# ---------------------------------------------------------------------------

def score_vsg(data: dict) -> tuple[int, list[str]]:
    """VSG-CRI scoring per Tabela 6 — variable points per criterion."""
    total = 0
    met: list[str] = []

    # Age (variable points)
    age_range = data.get("vsg_age_range", "")
    if age_range == "gte80":
        total += 4; met.append("Idade ≥ 80 anos (+4)")
    elif age_range == "70_79":
        total += 3; met.append("Idade 70–79 anos (+3)")
    elif age_range == "60_69":
        total += 2; met.append("Idade 60–69 anos (+2)")

    # 2-point criteria
    two_pt: list[tuple[bool, str]] = [
        (data.get("vsg_cad", False),                "Doença arterial coronariana (+2)"),
        (data.get("vsg_chf", False),                "Insuficiência cardíaca (+2)"),
        (data.get("vsg_copd", False),               "DPOC (+2)"),
        (data.get("vsg_creatinine_over_1_8", False),"Creatinina > 1,8 mg/dL (+2)"),
    ]
    for active, label in two_pt:
        if active:
            total += 2; met.append(label)

    # 1-point criteria
    one_pt: list[tuple[bool, str]] = [
        (data.get("vsg_smoking", False),             "Tabagismo (+1)"),
        (data.get("vsg_insulin_diabetes", False),    "Diabetes com insulina (+1)"),
        (data.get("vsg_chronic_beta_blocker", False),"Uso crônico de betabloqueador (+1)"),
    ]
    for active, label in one_pt:
        if active:
            total += 1; met.append(label)

    # -1 point criterion
    if data.get("vsg_prior_revasc", False):
        total -= 1; met.append("Revascularização miocárdica prévia (−1)")

    return max(total, 0), met


# ---------------------------------------------------------------------------
# Active Cardiovascular Conditions (Tabela 2)
# ---------------------------------------------------------------------------

def check_active_conditions(data: dict) -> list[str]:
    conditions: list[tuple[bool, str]] = [
        (data.get("cv_acute_coronary", False),
         "Síndrome coronariana aguda"),
        (data.get("cv_unstable_aortic", False),
         "Doenças instáveis da aorta torácica"),
        (data.get("cv_acute_pulmonary_edema", False),
         "Edema agudo dos pulmões"),
        (data.get("cv_cardiogenic_shock", False),
         "Choque cardiogênico"),
        (data.get("cv_hf_nyha_3_4", False),
         "Insuficiência cardíaca classe funcional III/IV (NYHA)"),
        (data.get("cv_angina_ccs_3_4", False),
         "Angina classe funcional CCS III/IV"),
        (data.get("cv_severe_arrhythmia", False),
         "Bradiarritmias ou taquiarritmias graves (BAVT, TV)"),
        (data.get("cv_uncontrolled_hypertension", False),
         "HAS não controlada (PA > 180 x 110 mmHg)"),
        (data.get("cv_af_high_rate", False),
         "Fibrilação atrial de alta resposta ventricular (FC > 120 bpm)"),
        (data.get("cv_pulmonary_hypertension", False),
         "Hipertensão arterial pulmonar sintomática"),
        (data.get("cv_severe_valvular", False),
         "Estenose aórtica/mitral importante sintomática"),
    ]
    return [label for active, label in conditions if active]


# ---------------------------------------------------------------------------
# Risk Classification
# ---------------------------------------------------------------------------

def classify_risk(pct: float) -> tuple[str, str]:
    if pct < 5.0:
        return RiskClass.LOW, "Risco Baixo"
    elif pct < 10.0:
        return RiskClass.INTERMEDIATE, "Risco Intermediário"
    else:
        return RiskClass.HIGH, "Risco Alto"


# ---------------------------------------------------------------------------
# Medication Advice
# ---------------------------------------------------------------------------

def _determine_warfarin_bridging(data: dict) -> dict:
    indication = data.get("warfarin_indication", "")

    if indication == "mechanical_valve":
        return {
            "action": "Suspender + Ponte com heparina",
            "detail": "Prótese valvar mecânica: realizar ponte com heparina de baixo peso molecular.",
            "type": RecommendationType.RED,
        }

    if indication == "rheumatic":
        return {
            "action": "Suspender + Ponte com heparina",
            "detail": "Doença valvar reumática: realizar ponte com heparina de baixo peso molecular.",
            "type": RecommendationType.RED,
        }

    if indication == "af":
        chadsvasc = data.get("warfarin_chadsvasc") or 0
        stroke_3m = data.get("warfarin_stroke_3m", False)

        if chadsvasc >= 5 or stroke_3m:
            extra = " e AVC/AIT < 3 meses" if stroke_3m else ""
            return {
                "action": "Suspender + Ponte com heparina",
                "detail": f"FA com CHA₂DS₂-VASc {chadsvasc}{extra}: realizar ponte com heparina.",
                "type": RecommendationType.RED,
            }
        elif chadsvasc >= 3:
            return {
                "action": "Considerar ponte com heparina",
                "detail": f"FA com CHA₂DS₂-VASc {chadsvasc}: considerar ponte com heparina.",
                "type": RecommendationType.AMBER,
            }
        else:
            return {
                "action": "Suspender sem ponte",
                "detail": f"FA com CHA₂DS₂-VASc {chadsvasc} sem AVC/AIT recente: não realizar ponte.",
                "type": RecommendationType.GREEN,
            }

    if indication == "vte":
        timing = data.get("warfarin_vte_timing", "")
        thrombophilia = data.get("warfarin_thrombophilia", "")
        neoplasia = data.get("warfarin_active_neoplasia", False)

        if timing == "recent":
            return {
                "action": "Suspender + Ponte com heparina",
                "detail": "TEV recente: realizar ponte com heparina.",
                "type": RecommendationType.RED,
            }
        elif timing == "3_12m":
            parts = []
            if thrombophilia == "mild":
                parts.append("trombofilia leve")
            if neoplasia:
                parts.append("neoplasia ativa")
            extra = f" com {' e '.join(parts)}" if parts else ""
            return {
                "action": "Considerar ponte com heparina",
                "detail": f"TEV 3–12 meses{extra}: considerar ponte com heparina.",
                "type": RecommendationType.AMBER,
            }
        else:
            return {
                "action": "Suspender sem ponte",
                "detail": "TEV > 12 meses: não realizar ponte com heparina.",
                "type": RecommendationType.GREEN,
            }

    return {
        "action": "Avaliar individualmente",
        "detail": "Varfarina: suspender 5 dias antes. Avaliar necessidade de ponte com heparina.",
        "type": RecommendationType.AMBER,
    }


def build_medication_advice(data: dict) -> list[dict]:
    advice: list[dict] = []
    surgery_type = data.get("surgery_type", "")

    # AAS
    if data.get("uses_aas"):
        prevention = data.get("aas_prevention", "")
        if prevention == "primary":
            advice.append({
                "medication": "AAS",
                "action": "Suspender 7 dias antes",
                "detail": "Prevenção primária: suspender AAS 7 dias antes do procedimento.",
                "type": RecommendationType.AMBER,
            })
        elif prevention == "secondary":
            high_bleeding = surgery_type in ("neurologic", "urologic_minor", "eye")
            if high_bleeding:
                advice.append({
                    "medication": "AAS",
                    "action": "Suspender 7 dias antes",
                    "detail": "Prevenção secundária: suspender por neurocirurgia, RTU de próstata ou cirurgia de retina.",
                    "type": RecommendationType.RED,
                })
            else:
                advice.append({
                    "medication": "AAS",
                    "action": "Manter",
                    "detail": "Prevenção secundária: manter AAS (exceto neurocirurgia, RTU de próstata ou cirurgia de retina).",
                    "type": RecommendationType.GREEN,
                })

    # Clopidogrel
    if data.get("uses_clopidogrel"):
        advice.append({
            "medication": "Clopidogrel",
            "action": "Suspender 5 dias antes",
            "detail": "Suspender 5 dias antes. Manter apenas se monoterapia em procedimentos de baixo risco de sangramento.",
            "type": RecommendationType.AMBER,
        })

    # Ticagrelor
    if data.get("uses_ticagrelor"):
        advice.append({
            "medication": "Ticagrelor",
            "action": "Suspender 5 dias antes",
            "detail": "Suspender ticagrelor 5 dias antes do procedimento.",
            "type": RecommendationType.AMBER,
        })

    # Prasugrel
    if data.get("uses_prasugrel"):
        advice.append({
            "medication": "Prasugrel",
            "action": "Suspender 7 dias antes",
            "detail": "Suspender prasugrel 7 dias antes do procedimento.",
            "type": RecommendationType.AMBER,
        })

    # DOACs: Rivaroxabana / Apixabana
    # Suspender 24-48h antes e retornar no 1º ou 2º PO dependendo do risco de sangramento
    if data.get("uses_rivaroxaban") or data.get("uses_apixaban"):
        med_name = "Rivaroxabana" if data.get("uses_rivaroxaban") else "Apixabana"
        advice.append({
            "medication": med_name,
            "action": "Suspender 24-48h antes",
            "detail": (
                f"{med_name}: suspender 24–48 horas antes do procedimento. "
                "Retornar no 1º ou 2º dia pós-operatório conforme risco de sangramento e hemostasia garantida."
            ),
            "type": RecommendationType.AMBER,
        })

    # Dabigatrana: depende da depuração (ClCr) e risco de sangramento
    if data.get("uses_dabigatran"):
        clcr = data.get("clcr")
        high_bleeding = data.get("high_bleeding_risk", False)
        if isinstance(clcr, (int, float)) and clcr < 50 and high_bleeding:
            advice.append({
                "medication": "Dabigatrana",
                "action": "Suspender 4 dias antes",
                "detail": (
                    "Dabigatrana com ClCr < 50 e alto risco de sangramento: suspender 4 dias antes. "
                    "Retornar no 2º dia pós-operatório se hemostasia garantida."
                ),
                "type": RecommendationType.AMBER,
            })
        else:
            advice.append({
                "medication": "Dabigatrana",
                "action": "Suspender 24-48h antes",
                "detail": (
                    "Dabigatrana (ClCr >= 50 ou sem risco aumentado): suspender 24–48 horas antes. "
                    "Retornar no 1º ou 2º dia pós-operatório conforme risco de sangramento e hemostasia garantida."
                ),
                "type": RecommendationType.AMBER,
            })

    # Warfarin
    if data.get("uses_warfarin"):
        bridging = _determine_warfarin_bridging(data)
        advice.append({
            "medication": "Varfarina",
            "action": bridging["action"],
            "detail": bridging["detail"],
            "type": bridging["type"],
        })

    return advice


# ---------------------------------------------------------------------------
# Recommended Exams
# ---------------------------------------------------------------------------

def build_exam_recommendations(
    data: dict,
    risk_class: str,
    score: int,
    has_active: bool,
) -> list[str]:
    exams: list[str] = []
    surgery_risk = data.get("surgery_risk", "")
    mets = data.get("mets", 4)

    if surgery_risk != "low" or score > 0:
        exams.append("ECG de 12 derivações")

    if data.get("known_hf") or data.get("known_valvular_disease") or has_active:
        exams.append("Ecocardiograma transtorácico")

    if (
        data.get("cv_acute_pulmonary_edema") or data.get("cv_cardiogenic_shock")
        or data.get("cv_hf_nyha_3_4")
    ) and "Ecocardiograma transtorácico" not in exams:
        exams.append("Ecocardiograma transtorácico")

    is_vascular = data.get("is_vascular", False)
    intermediate_score = score >= 5 if is_vascular else score >= 2
    if mets < 4 and surgery_risk in ("intermediate", "high") and intermediate_score:
        exams.append("Teste funcional (ergometria / cintilografia / eco de estresse)")

    if surgery_risk in ("intermediate", "high"):
        exams.append("Hemograma completo")

    if data.get("uses_warfarin"):
        exams.append("Coagulograma (INR, TAP, TTPa)")

    if score > 0 or surgery_risk == "high":
        exams.append("Função renal (creatinina, ureia)")

    if risk_class == RiskClass.HIGH or data.get("known_hf"):
        exams.append("BNP ou NT-proBNP")

    if data.get("rcri_insulin_diabetes") or data.get("vsg_insulin_diabetes"):
        exams.append("Glicemia de jejum / HbA1c")

    return exams


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def build_recommendations(
    risk_class: str,
    score: int,
    mets: int,
    surgery_risk: str,
    has_active: bool,
    active_conditions: list[str],
    is_vascular: bool,
    data: dict,
) -> list[dict]:
    recs: list[dict] = []

    # Active conditions take priority
    if has_active:
        recs.append({
            "type": RecommendationType.RED,
            "icon": "🚨",
            "title": "Condições cardíacas ativas detectadas",
            "body": (
                "Foram identificadas condições cardíacas ativas que requerem "
                "avaliação e tratamento antes do procedimento cirúrgico: "
                + ", ".join(active_conditions) + "."
            ),
        })

    # Low-risk surgery shortcut
    if surgery_risk == SurgeryRisk.LOW and not has_active:
        recs.append({
            "type": RecommendationType.GREEN,
            "icon": "✅",
            "title": "Cirurgia de baixo risco",
            "body": (
                "Risco cardíaco estimado < 1%. Prosseguir com a cirurgia. "
                "Monitorização padrão perioperatória é suficiente."
            ),
        })
        return recs

    # Risk-based recommendation
    if risk_class == RiskClass.LOW:
        recs.append({
            "type": RecommendationType.GREEN,
            "icon": "✅",
            "title": "Prosseguir com cirurgia",
            "body": "Risco cardíaco perioperatório baixo. Monitorização padrão é suficiente.",
        })
    elif risk_class == RiskClass.INTERMEDIATE:
        recs.append({
            "type": RecommendationType.AMBER,
            "icon": "⚠️",
            "title": "Considerar avaliação adicional",
            "body": (
                "Risco intermediário. Avalie benefício de consulta cardiológica. "
                "Solicite ECG pré-operatório e considere dosagem de BNP."
            ),
        })
    else:
        recs.append({
            "type": RecommendationType.RED,
            "icon": "🚨",
            "title": "Avaliação cardiológica indicada",
            "body": (
                "Risco elevado. Recomenda-se avaliação cardiológica formal. "
                "Discuta relação risco/benefício com equipe cirúrgica e paciente."
            ),
        })

    # Functional capacity
    if mets < 4:
        recs.append({
            "type": RecommendationType.AMBER,
            "icon": "🏃",
            "title": "Capacidade funcional reduzida",
            "body": (
                "METs < 4 é preditor independente de eventos. "
                "Considere teste funcional antes de cirurgia eletiva."
            ),
        })

    # High-risk surgery
    if surgery_risk == SurgeryRisk.HIGH:
        recs.append({
            "type": RecommendationType.RED,
            "icon": "🔪",
            "title": "Cirurgia de alto risco",
            "body": (
                "Procedimento com risco cardíaco intrínseco > 5%. "
                "Considere monitorização invasiva e cuidados intensivos pós-operatórios."
            ),
        })

    # High score optimization
    if score >= 3:
        recs.append({
            "type": RecommendationType.RED,
            "icon": "💊",
            "title": "Otimização farmacológica",
            "body": (
                f"Score ≥ 3: considere betabloqueadores e estatinas conforme indicação. "
                "Avalie profilaxia antitrombótica."
            ),
        })

    # Comorbidity-specific
    if data.get("known_hf"):
        recs.append({
            "type": RecommendationType.AMBER,
            "icon": "🫀",
            "title": "IC conhecida / suspeita",
            "body": "Avaliação ecocardiográfica recomendada. Otimize tratamento da IC antes do procedimento.",
        })

    if data.get("known_valvular_disease"):
        recs.append({
            "type": RecommendationType.AMBER,
            "icon": "🫀",
            "title": "Doença valvar conhecida / suspeita",
            "body": "Solicite ecocardiograma para avaliação da gravidade valvar.",
        })

    if data.get("known_cad"):
        recs.append({
            "type": RecommendationType.AMBER,
            "icon": "❤️",
            "title": "DAC conhecida / suspeita",
            "body": "Avalie controle da doença coronariana. Considere teste funcional se indicado.",
        })

    return recs


# ---------------------------------------------------------------------------
# Risk Factor Tags
# ---------------------------------------------------------------------------

def build_risk_factors(data: dict, criteria_met: list[str], mets: int) -> list[str]:
    factors = list(criteria_met)
    if mets < 4:
        factors.append("Cap. funcional ↓")
    if data.get("obesity"):
        factors.append("Obesidade")
    if data.get("known_hf"):
        factors.append("IC conhecida/suspeita")
    if data.get("known_valvular_disease"):
        factors.append("Doença valvar")
    if data.get("known_cad"):
        factors.append("DAC conhecida/suspeita")
    return factors


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def calculate_risk(data: dict) -> dict:
    mets: float = data.get("mets", 4)
    surgery_risk: str = data.get("surgery_risk", "intermediate")
    surgery_type: str = data.get("surgery_type", "")
    # Accept multiple indicators for vascular surgery and infer from surgery_type
    is_vascular: bool = (
        bool(data.get("is_vascular", False))
        or bool(data.get("surgery_is_vascular", False))
        or (str(surgery_type).lower().find("vascular") >= 0)
    )

    # 1. Check active cardiovascular conditions (Tabela 2)
    active_conditions = check_active_conditions(data)
    has_active = len(active_conditions) > 0

    # 2. Score using RCRI or VSG
    if is_vascular:
        risk_index = "vsg"
        score, criteria_met = score_vsg(data)
        score_class, mace_pct = _get_vsg_risk(score)
    else:
        risk_index = "rcri"
        score, criteria_met = score_rcri(data)
        score_class, mace_pct = _get_rcri_risk(score)

    # 3. Override for low-risk surgery
    # Keep the low-surgery cap, but do NOT apply it when the calculated score
    # already indicates high procedural risk (e.g., RCRI score >= 3).
    if surgery_risk == SurgeryRisk.LOW and not has_active and score < 3:
        mace_pct = min(mace_pct, 1.0)

    # 4. Classify risk
    risk_class, risk_label = classify_risk(mace_pct)

    # If active conditions, always high risk
    if has_active:
        risk_class = RiskClass.HIGH
        risk_label = "Risco Alto (Condições Ativas)"

    # 5. Build recommendations
    recommendations = build_recommendations(
        risk_class=risk_class,
        score=score,
        mets=mets,
        surgery_risk=surgery_risk,
        has_active=has_active,
        active_conditions=active_conditions,
        is_vascular=is_vascular,
        data=data,
    )

    # 6. Build medication advice
    medication_advice = build_medication_advice(data)

    # 7. Recommended exams
    recommended_exams = build_exam_recommendations(
        data=data,
        risk_class=risk_class,
        score=score,
        has_active=has_active,
    )

    # 8. Risk factor tags
    risk_factors = build_risk_factors(data, criteria_met, mets)

    return {
        "risk_index": risk_index,
        "score": score,
        "score_class": score_class,
        "mace_risk_pct": round(mace_pct, 1),
        "risk_class": risk_class,
        "risk_label": risk_label,
        "has_active_conditions": has_active,
        "active_conditions": active_conditions,
        "criteria_met": criteria_met,
        "risk_factors": risk_factors if risk_factors else ["Sem fatores de risco identificados"],
        "recommendations": recommendations,
        "medication_advice": medication_advice,
        "recommended_exams": recommended_exams,
        "mets": mets,
        "mets_label": METS_LABELS.get(mets, f"{mets} METs"),
        "surgery_type": surgery_type,
        "surgery_risk": surgery_risk,
        "surgery_label": SURGERY_LABELS.get(surgery_risk, "—"),
        "is_vascular": is_vascular,
        "functional_capacity_adequate": mets >= 4,
    }
