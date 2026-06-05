"""Clinical text parsing for CardioRisk.

This module combines:
1) Optional NER inference with `pucpr/clinicalnerpt-medical` (Hugging Face)
2) Rule-based extraction tailored to CardioRisk calculator fields
"""

from __future__ import annotations

import os
import re
import threading
import unicodedata
import warnings
from typing import Any

MODEL_NAME = os.getenv("CARDIORISK_NER_MODEL", "pucpr/clinicalnerpt-medical")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if _as_bool(os.getenv("CARDIORISK_SUPPRESS_MODEL_WARNINGS"), default=False):
    warnings.filterwarnings(
        "ignore",
        message=r".*unauthenticated requests to the HF Hub.*",
    )

ENABLE_NER = _as_bool(os.getenv("CARDIORISK_ENABLE_NER"), default=True)

try:
    from transformers import (  # type: ignore
        AutoModelForTokenClassification,
        AutoTokenizer,
        pipeline,
    )
except Exception:  # pragma: no cover - optional dependency for local/dev environments
    AutoModelForTokenClassification = None
    AutoTokenizer = None
    pipeline = None


_NER_PIPELINE = None
_NER_ERROR: str | None = None
_NER_LOCK = threading.Lock()


SURGERY_TYPE_MAP: dict[str, dict[str, Any]] = {
    "intraperitoneal": {
        "risk": "intermediate",
        "vascular": False,
        "aliases": [
            "colecistectomia",
            "hernia hiatal",
            "herniorrafia hiatal",
            "esplenectomia",
            "intraperitoneal",
            "laparotomia",
        ],
    },
    "intrathoracic": {
        "risk": "intermediate",
        "vascular": False,
        "aliases": ["intratoracica", "toracotomia", "cirurgia toracica"],
    },
    "neurologic": {
        "risk": "intermediate",
        "vascular": False,
        "aliases": ["neurocirurgia", "cirurgia neurologica", "craniana"],
    },
    "aortic_vascular_major": {
        "risk": "high",
        "vascular": True,
        "aliases": ["aorta", "vascular major", "aneurisma de aorta aberta"],
    },
    "endovascular_aortic": {
        "risk": "intermediate",
        "vascular": True,
        "aliases": ["endovascular", "aneurisma de aorta endovascular", "evaar"],
    },
    "peripheral_angioplasty": {
        "risk": "intermediate",
        "vascular": True,
        "aliases": [
            "angioplastia arterial periferica",
            "angioplastia periferica",
            "angioplastia de arteria periferica",
        ],
    },
    "orthopedic_major": {
        "risk": "intermediate",
        "vascular": False,
        "aliases": ["artroplastia", "ortopedica major", "protese de quadril", "protese de joelho"],
    },
    "urologic_major": {
        "risk": "intermediate",
        "vascular": False,
        "aliases": ["urologica major", "nefrectomia", "prostatectomia radical"],
    },
    "eye": {
        "risk": "low",
        "vascular": False,
        "aliases": ["ocular", "catarata", "retina"],
    },
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def _build_ner_pipeline():
    if pipeline is None or AutoTokenizer is None or AutoModelForTokenClassification is None:
        raise RuntimeError("transformers não está instalado no ambiente")

    load_kwargs: dict[str, Any] = {}
    if HF_TOKEN:
        load_kwargs["token"] = HF_TOKEN

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, **load_kwargs)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME, **load_kwargs)
    return pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")


def _get_ner_pipeline():
    global _NER_PIPELINE, _NER_ERROR

    if not ENABLE_NER:
        return None, "NER desativado por CARDIORISK_ENABLE_NER=false"

    with _NER_LOCK:
        if _NER_PIPELINE is not None:
            return _NER_PIPELINE, None
        if _NER_ERROR is not None:
            return None, _NER_ERROR

        try:
            _NER_PIPELINE = _build_ner_pipeline()
            return _NER_PIPELINE, None
        except Exception as exc:  # pragma: no cover - depends on runtime/dependencies
            _NER_ERROR = str(exc)
            return None, _NER_ERROR


def _run_ner(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ner, error = _get_ner_pipeline()
    if ner is None:
        return [], {
            "name": MODEL_NAME,
            "status": "fallback",
            "detail": f"NER indisponível: {error}",
        }

    try:
        entities = ner(text)
        cleaned = [
            {
                "text": item.get("word", ""),
                "label": item.get("entity_group", "UNKNOWN"),
                "score": round(float(item.get("score", 0.0)), 4),
            }
            for item in entities
        ]
        return cleaned, {"name": MODEL_NAME, "status": "loaded", "detail": "ok"}
    except Exception as exc:  # pragma: no cover - depends on runtime/dependencies
        return [], {
            "name": MODEL_NAME,
            "status": "fallback",
            "detail": f"Falha na inferência NER: {exc}",
        }


def _match_any(normalized_text: str, terms: list[str]) -> bool:
    for term in terms:
        if re.search(rf"\b{re.escape(_normalize(term))}\b", normalized_text):
            return True
    return False


def _is_negated(normalized_text: str, term: str) -> bool:
    norm_term = _normalize(term)
    patterns = [
        rf"\bsem\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
        rf"\bnega\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
        rf"\bnao\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
    ]
    return any(re.search(p, normalized_text) for p in patterns)


def _extract_age(text: str) -> int | None:
    m = re.search(r"\b(\d{1,3})\s*anos?\b", text, flags=re.IGNORECASE)
    if not m:
        return None
    age = int(m.group(1))
    if 0 <= age <= 120:
        return age
    return None


def _clean_name(candidate: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", candidate).strip(" ,.;:-")
    cleaned = re.sub(r"^(sr\.?|sra\.?|srta\.?)\s+", "", cleaned, flags=re.IGNORECASE)
    if len(cleaned) < 3:
        return None
    if any(ch.isdigit() for ch in cleaned):
        return None
    if len(cleaned.split()) < 1:
        return None
    if _normalize(cleaned) in {"paciente", "doente", "usuario", "cliente"}:
        return None
    return cleaned


def _extract_name(text: str) -> str | None:
    patterns = [
        r"\bnome\s*(?:do\s+paciente)?\s*[:=-]\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\- ]{2,80})",
        r"\bpaciente\s*[:=-]\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{1,80}?)(?=\s*,\s*\d{1,3}\s*anos\b|\s*,\s*(?:com|portador[ao])\b|[\.;]|$)",
        r"\bpaciente\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{1,80}?)(?=\s+de\s+\d{1,3}\s+anos\b|\s*,\s*\d{1,3}\s*anos\b|\s*,\s*(?:com|portador[ao])\b|[\.;]|$)",
        r"\b(?:pt|pac)\s*[:=-]\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bpaciente\s+chama-se\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bpaciente\s+e\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bpaciente\s+eh\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bpaciente\s+é\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bchama-se\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\.\- ]{2,80})",
        r"\bpaciente\s*[:=-]?\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][A-Za-zÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇáàâãéèêíïóôõöúç'\- ]{2,80}?)(?=\s*,\s*(?:de\s+\d{1,3}\s+anos|portador[ao]|com)\b|[\.;]|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            cleaned = _clean_name(match.group(1))
            if cleaned:
                return cleaned
    return None


def _extract_mets(text: str) -> float | None:
    m = re.search(r"\b(\d+(?:[\.,]\d+)?)\s*(?:mets?|met)\b", text, flags=re.IGNORECASE)
    if not m:
        return None
    value = float(m.group(1).replace(",", "."))
    return max(1.0, min(12.0, value))


def _infer_mets_from_activity(normalized_text: str) -> float | None:
    # Heuristic fallback for common free-text functional capacity descriptions.
    activity_map: list[tuple[float, list[str]]] = [
        (8.0, ["corre distancia curta", "corrida curta", "esporte intenso"]),
        (7.5, ["natacao", "futebol", "tenis individual"]),
        (6.0, ["danca", "boliche", "tenis em dupla"]),
        (5.5, ["sobe um lance de escada", "subir um lance de escada", "subir escadas", "sobe escada", "caminha em subida"]),
        (4.5, ["trabalhos no quintal", "jardinagem", "corta grama"]),
        (3.5, ["aspirador de po", "varrer o chao", "carregar mantimentos"]),
        (2.75, ["caminha uma quadra", "caminhar uma quadra", "caminhar apenas uma quadra", "caminha no plano", "cuida de si"]),
        (1.0, ["acamado", "restrito ao leito", "nao deambula"]),
    ]
    for mets, phrases in activity_map:
        if _match_any(normalized_text, phrases):
            return mets
    return None


def _extract_creatinine(text: str) -> float | None:
    m = re.search(
        r"(?:creatinina|creat)[^\d]{0,30}(\d+(?:[\.,]\d+)?)\s*(?:mg/?d?l)?",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _extract_egfr(text: str) -> float | None:
    m = re.search(
        r"(?:tfg|egfr|filtracao\s+glomerular)[^\d]{0,25}(\d+(?:[\.,]\d+)?)\s*(?:ml/?min(?:/1\.73m2)?)?",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _extract_surgery(normalized_text: str) -> dict[str, Any] | None:
    for surgery_id, payload in SURGERY_TYPE_MAP.items():
        if _match_any(normalized_text, payload["aliases"]):
            return {
                "surgery_type": surgery_id,
                "surgery_risk": payload["risk"],
                "is_vascular": payload["vascular"],
            }
    return None


def analyze_clinical_text(text: str, current_data: dict[str, Any] | None = None) -> dict[str, Any]:
    current_data = current_data or {}
    normalized = _normalize(text)

    autofill: dict[str, Any] = {}
    findings: dict[str, list[str]] = {
        "diagnoses": [],
        "medications": [],
        "procedures": [],
    }

    age = _extract_age(text)
    if age is not None:
        autofill["age"] = age

    name = _extract_name(text)
    if name:
        autofill["name"] = name

    surgery = _extract_surgery(normalized)
    if surgery:
        autofill.update(surgery)
        findings["procedures"].append(surgery["surgery_type"])

    if _match_any(normalized, ["insulina", "insulinoterapia", "nph", "glargina"]):
        autofill["rcri_insulin_diabetes"] = True
        autofill["vsg_insulin_diabetes"] = True
        findings["medications"].append("insulina")

    if _match_any(normalized, ["aas", "acido acetilsalicilico", "aspirina"]):
        autofill["uses_aas"] = True
        findings["medications"].append("aas")

    if _match_any(normalized, ["clopidogrel"]):
        autofill["uses_clopidogrel"] = True
        findings["medications"].append("clopidogrel")

    if _match_any(normalized, ["ticagrelor"]):
        autofill["uses_ticagrelor"] = True
        findings["medications"].append("ticagrelor")

    if _match_any(normalized, ["prasugrel"]):
        autofill["uses_prasugrel"] = True
        findings["medications"].append("prasugrel")

    if _match_any(normalized, ["varfarina", "marevan"]):
        autofill["uses_warfarin"] = True
        findings["medications"].append("varfarina")

    if _match_any(normalized, ["fibrilacao atrial"]) or re.search(r"\bfa\b", normalized):
        autofill["warfarin_indication"] = "af"

    if _match_any(normalized, ["tev", "tromboembolismo venoso", "trombose venosa", "tep"]):
        autofill["warfarin_indication"] = "vte"

    if _match_any(normalized, ["avc", "ait", "acidente vascular cerebral", "avci"]):
        autofill["rcri_cerebrovascular"] = True
        findings["diagnoses"].append("doenca_cerebrovascular")

    if _match_any(normalized, ["dac", "doenca coronariana", "angina", "infarto", "iam"]):
        autofill["known_cad"] = True
        autofill["rcri_ischemic_heart"] = True
        autofill["vsg_cad"] = True
        findings["diagnoses"].append("doenca_coronariana")

    if _match_any(normalized, ["insuficiencia cardiaca", "ic", "icc"]):
        autofill["known_hf"] = True
        autofill["rcri_heart_failure"] = True
        autofill["vsg_chf"] = True
        findings["diagnoses"].append("insuficiencia_cardiaca")

    if _match_any(normalized, ["dpoc"]):
        autofill["vsg_copd"] = True
        findings["diagnoses"].append("dpoc")

    if _match_any(normalized, ["tabagista", "tabagismo", "fumante"]):
        autofill["vsg_smoking"] = True

    if _match_any(normalized, ["obesidade", "obeso", "obesa"]):
        autofill["obesity"] = True

    if _match_any(normalized, ["beta bloqueador", "beta-bloqueador", "betabloqueador", "atenolol", "metoprolol", "carvedilol"]):
        autofill["vsg_chronic_beta_blocker"] = True
        findings["medications"].append("betabloqueador")

    has_revasc = _match_any(normalized, ["revascularizacao", "angioplastia coronaria", "ponte de safena"])
    if has_revasc and not _is_negated(normalized, "revascularizacao"):
        autofill["vsg_prior_revasc"] = True

    mets = _extract_mets(text)
    if mets is None:
        mets = _infer_mets_from_activity(normalized)
    if mets is not None:
        autofill["mets"] = mets

    creatinine = _extract_creatinine(text)
    if creatinine is not None:
        if creatinine > 2.0:
            autofill["rcri_creatinine_above_2"] = True
        if creatinine > 1.8:
            autofill["vsg_creatinine_over_1_8"] = True

    egfr = _extract_egfr(text)

    merged = {**current_data, **autofill}
    missing_critical: list[dict[str, str]] = []

    if merged.get("age") is None:
        missing_critical.append(
            {
                "field": "age",
                "label": "Idade",
                "reason": "A idade é necessária para pontuação VSG e interpretação global de risco.",
                "question": "Qual a idade do paciente?",
            }
        )

    if not merged.get("surgery_type"):
        missing_critical.append(
            {
                "field": "surgery_type",
                "label": "Tipo de cirurgia",
                "reason": "Sem o procedimento não é possível determinar o risco cirúrgico basal.",
                "question": "Qual procedimento cirúrgico será realizado?",
            }
        )

    mets_is_missing = merged.get("mets") is None
    if not mets_is_missing:
        mets_is_default = (current_data.get("mets") in (None, "", 1)) and not current_data.get("functional_activities")
        mets_is_missing = mets is None and mets_is_default

    if mets_is_missing:
        missing_critical.append(
            {
                "field": "mets",
                "label": "Capacidade funcional (METs)",
                "reason": "A capacidade funcional impacta a estratificação perioperatória.",
                "question": "Qual a estimativa de METs ou atividade máxima tolerada?",
            }
        )

    if creatinine is None and egfr is None:
        missing_critical.append(
            {
                "field": "renal_function",
                "label": "Função renal (creatinina ou TFG)",
                "reason": "Creatinina/TFG são dados críticos para classificar risco renal e critérios RCRI/VSG.",
                "question": "Informe creatinina pré-operatória (mg/dL) ou TFG estimada.",
            }
        )

    entities, model_info = _run_ner(text)

    summary = {
        "autofill_fields": sorted(autofill.keys()),
        "autofill_count": len(autofill),
        "missing_critical_count": len(missing_critical),
    }

    context = {
        "creatinine_mg_dl": creatinine,
        "egfr": egfr,
    }

    return {
        "autofill": autofill,
        "missing_critical": missing_critical,
        "findings": findings,
        "entities": entities,
        "model": model_info,
        "summary": summary,
        "context": context,
    }
