"""Clinical text parsing for CardioRisk.

This module combines:
1) Rule-based extraction tailored to CardioRisk calculator fields. The rules are
   the only thing that fills form fields.
2) Optional NER inference with the `pucpr/clinicalnerpt-*` models (Hugging Face),
   used only to review the rules: clinical terms the models find and no rule
   recognized are returned in `ner_review` so the physician can check them.
"""

from __future__ import annotations

import os
import re
import threading
import unicodedata
import warnings
from contextvars import ContextVar
from typing import Any

# Modelos de NER usados por padrão: doenças, medicamentos e procedimentos.
DEFAULT_NER_MODELS = (
    "pucpr/clinicalnerpt-disorder",
    "pucpr/clinicalnerpt-chemical",
    "pucpr/clinicalnerpt-procedure",
)


def _modelos_do_ambiente() -> list[str]:
    # CARDIORISK_NER_MODELS (lista separada por vírgula) tem prioridade;
    # CARDIORISK_NER_MODEL (um modelo) continua valendo por compatibilidade.
    bruto = os.getenv("CARDIORISK_NER_MODELS") or os.getenv("CARDIORISK_NER_MODEL") or ""
    nomes: list[str] = []
    for nome in bruto.split(","):
        nome = nome.strip()
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes or list(DEFAULT_NER_MODELS)


MODEL_NAMES = _modelos_do_ambiente()
NER_SCORE_MINIMO = 0.60
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")


def _para_booleano(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if _para_booleano(os.getenv("CARDIORISK_SUPPRESS_MODEL_WARNINGS"), default=False):
    warnings.filterwarnings(
        "ignore",
        message=r".*unauthenticated requests to the HF Hub.*",
    )

ENABLE_NER = _para_booleano(os.getenv("CARDIORISK_ENABLE_NER"), default=True)

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


_NER_PIPELINES: dict[str, Any] = {}
_NER_ERRORS: dict[str, str] = {}
_NER_LOCK = threading.Lock()

# Termos que as regras reconheceram na chamada em curso (None fora de uma análise).
_TERMOS_RECONHECIDOS: ContextVar[list[str] | None] = ContextVar("termos_reconhecidos", default=None)


def _chave_termo(termo: str) -> str:
    return re.sub(r"\s+", " ", _normalizar(termo)).strip(" ,.;:()-")


def _anotar_termo(termo: str | None) -> None:
    termos = _TERMOS_RECONHECIDOS.get()
    if termos is None or not termo:
        return
    termo = _chave_termo(termo)
    if termo and termo not in termos:
        termos.append(termo)


SURGERY_TYPE_MAP: dict[str, dict[str, Any]] = {
    # ── Baixo risco (<1%) ──────────────────────────────────────────────
    "breast": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["mastectomia", "quadrantectomia", "tumorectomia de mama", "nodulectomia mamaria", "biopsia de mama", "setorectomia"],
    },
    "dental": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["procedimento dentario", "cirurgia odontologica", "extracao dentaria", "cirurgia oral"],
    },
    "thyroid": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["tireoidectomia", "cirurgia de tireoide", "nodulectomia de tireoide"],
    },
    "eye": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["ocular", "catarata", "retina", "facectomia", "cirurgia oftalmologica", "vitrectomia", "glaucoma"],
    },
    "gynecologic_minor": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["curetagem", "histeroscopia", "laqueadura tubaria", "conizacao", "ginecologica minor", "ginecologica menor"],
    },
    "orthopedic_minor": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["artroscopia", "meniscectomia", "retirada de material de sintese", "liberacao do tunel do carpo", "ortopedica minor", "ortopedica menor"],
    },
    "reconstructive": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["cirurgia plastica reconstrutiva", "reconstrucao mamaria", "enxerto de pele", "retalho cutaneo"],
    },
    "superficial": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["lipoma", "cisto sebaceo", "biopsia de pele", "excisao de lesao de pele", "drenagem de abscesso", "cirurgia de superficie"],
    },
    "urologic_minor": {
        "risco": "baixo",
        "vascular": False,
        "aliases": ["ressecao transuretral", "rtu de prostata", "rtu de bexiga", "circuncisao", "postectomia", "vasectomia", "cistoscopia", "urologica minor", "urologica menor"],
    },
    "vats_minor": {
        "risco": "baixo",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["vats minor", "cirurgia toracica videoassistida diagnostica", "biopsia pulmonar por vats"],
    },

    # ── Risco intermediário (1–5%) ─────────────────────────────────────
    "carotid_asymptomatic": {
        "risco": "intermediario",
        "vascular": True,
        "aliases": ["endarterectomia de carotida assintomatica", "carotida assintomatica"],
    },
    "carotid_endarterectomy": {
        "risco": "intermediario",
        "vascular": True,
        "aliases": ["endarterectomia de carotida", "endarterectomia carotidea"],
    },
    "peripheral_angioplasty": {
        "risco": "intermediario",
        "vascular": True,
        "aliases": [
            "angioplastia arterial periferica",
            "angioplastia periferica",
            "angioplastia de arteria periferica",
        ],
    },
    "endovascular_aortic": {
        "risco": "intermediario",
        "vascular": True,
        "aliases": ["endovascular", "aneurisma de aorta endovascular", "evar", "correcao endovascular de aneurisma"],
    },
    "head_neck": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["cirurgia de cabeca e pescoco", "laringectomia", "esvaziamento cervical", "parotidectomia"],
    },
    "intraperitoneal": {
        "risco": "intermediario",
        "vascular": False,
        "intracavitaria": True,
        "aliases": [
            "colecistectomia",
            "hernia hiatal",
            "herniorrafia hiatal",
            "herniorrafia umbilical",
            "hernioplastia umbilical",
            "hernia umbilical",
            "herniorrafia incisional",
            "hernioplastia incisional",
            "hernia incisional",
            "esplenectomia",
            "intraperitoneal",
            "laparotomia",
            "apendicectomia",
            "gastrectomia parcial",
            "colectomia",
        ],
    },
    "intrathoracic": {
        "risco": "intermediario",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["intratoracica", "toracotomia", "cirurgia toracica nao major", "mediastinoscopia", "biopsia pulmonar aberta"],
    },
    "neurologic": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["neurocirurgia", "cirurgia neurologica", "craniana", "craniotomia", "laminectomia", "descompressao medular", "cirurgia de coluna", "artrodese de coluna"],
    },
    "orthopedic_major": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": [
            "artroplastia",
            "ortopedica major",
            "ortopedica maior",
            "ortopedica de grande porte",
            "protese de quadril",
            "protese de joelho",
            "osteossintese",
            "fratura de femur",
            "fratura de quadril",
            "fratura de bacia",
            "artroplastia de quadril",
            "artroplastia de joelho",
            "fixacao de fratura",
            "haste femoral",
            "haste intramedular",
        ],
    },
    "renal_transplant": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["transplante renal", "transplante de rim"],
    },
    "urologic_major": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["urologica major", "urologica maior", "nefrectomia", "prostatectomia radical", "nefrectomia parcial", "nefrectomia radical"],
    },
    "gynecologic_major": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["histerectomia", "histerectomia total", "cirurgia ginecologica oncologica", "ooforectomia", "ginecologica major", "ginecologica maior"],
    },
    "total_cystectomy": {
        "risco": "intermediario",
        "vascular": False,
        "aliases": ["cistectomia total", "cistectomia radical"],
    },

    # ── Alto risco (>5%) ────────────────────────────────────────────────
    "aortic_vascular_major": {
        "risco": "alto",
        "vascular": True,
        "aliases": ["aorta", "vascular major", "vascular maior", "aneurisma de aorta aberta", "cirurgia de aorta aberta", "bypass aortobifemoral"],
    },
    "peripheral_open": {
        "risco": "alto",
        "vascular": True,
        "aliases": ["revascularizacao periferica aberta", "isquemia arterial aguda", "amputacao de membro", "bypass femoropopliteo"],
    },
    "carotid_angioplasty": {
        "risco": "alto",
        "vascular": True,
        "aliases": ["angioplastia de carotida", "angioplastia carotidea", "stent de carotida", "stent carotideo"],
    },
    "adrenal_resection": {
        "risco": "alto",
        "vascular": False,
        "aliases": ["adrenalectomia", "ressecao adrenal", "ressecao de adrenal"],
    },
    "pancreatic": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["pancreatectomia", "duodenopancreatectomia", "cirurgia de whipple", "whipple"],
    },
    "liver_biliary": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["hepatectomia", "ressecao hepatica", "cirurgia de vias biliares", "coledocotomia"],
    },
    "esophagectomy": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["esofagectomia"],
    },
    "pneumectomy": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["pneumectomia", "pneumonectomia", "lobectomia pulmonar"],
    },
    "lung_transplant": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["transplante pulmonar", "transplante de pulmao"],
    },
    "liver_transplant": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["transplante hepatico", "transplante de figado"],
    },
    "bowel_perforation": {
        "risco": "alto",
        "vascular": False,
        "intracavitaria": True,
        "aliases": ["perfuracao intestinal", "reparo de perfuracao intestinal", "perfuracao de viscera oca"],
    },
}


def _normalizar(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def _construir_pipeline_ner(nome_modelo: str):
    if pipeline is None or AutoTokenizer is None or AutoModelForTokenClassification is None:
        raise RuntimeError("transformers não está instalado no ambiente")

    load_kwargs: dict[str, Any] = {}
    if HF_TOKEN:
        load_kwargs["token"] = HF_TOKEN

    tokenizer = AutoTokenizer.from_pretrained(nome_modelo, **load_kwargs)
    model = AutoModelForTokenClassification.from_pretrained(nome_modelo, **load_kwargs)
    # "first" agrega por palavra. Com "simple" estes modelos devolvem pedaços de
    # palavra ("corona", "rio", "pata" em vez de "coronariopata").
    return pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="first")


def _obter_pipeline_ner(nome_modelo: str | None = None):
    nome_modelo = nome_modelo or MODEL_NAMES[0]

    if not ENABLE_NER:
        return None, "NER desativado por CARDIORISK_ENABLE_NER=false"

    with _NER_LOCK:
        if nome_modelo in _NER_PIPELINES:
            return _NER_PIPELINES[nome_modelo], None
        if nome_modelo in _NER_ERRORS:
            return None, _NER_ERRORS[nome_modelo]

        try:
            _NER_PIPELINES[nome_modelo] = _construir_pipeline_ner(nome_modelo)
            return _NER_PIPELINES[nome_modelo], None
        except Exception as exc:  # pragma: no cover - depends on runtime/dependencies
            _NER_ERRORS[nome_modelo] = str(exc)
            return None, _NER_ERRORS[nome_modelo]


# O BERT aceita 512 tokens; textos longos são analisados em trechos menores.
_NER_TAMANHO_TRECHO = 1000


def _dividir_em_trechos(text: str) -> list[tuple[int, str]]:
    """Divide o texto em trechos de até 1000 caracteres, cortando de preferência em fim de frase."""
    trechos: list[tuple[int, str]] = []
    inicio = 0
    while inicio < len(text):
        fim = min(len(text), inicio + _NER_TAMANHO_TRECHO)
        if fim < len(text):
            janela = text[inicio:fim]
            cortes = [m.end() for m in re.finditer(r"[\.;!?\n]\s+", janela)] or [
                m.end() for m in re.finditer(r"\s+", janela)
            ]
            if cortes:
                fim = inicio + cortes[-1]
        trechos.append((inicio, text[inicio:fim]))
        inicio = fim
    return trechos


def _executar_ner(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Roda cada modelo configurado e devolve as entidades com a posição no texto original."""
    nome_conjunto = ", ".join(MODEL_NAMES)
    entidades: list[dict[str, Any]] = []
    por_modelo: list[dict[str, str]] = []

    for nome_modelo in MODEL_NAMES:
        ner, error = _obter_pipeline_ner(nome_modelo)
        if ner is None:
            por_modelo.append({"name": nome_modelo, "status": "fallback", "detail": f"NER indisponível: {error}"})
            continue

        try:
            do_modelo: list[dict[str, Any]] = []
            for deslocamento, trecho in _dividir_em_trechos(text):
                for item in ner(trecho):
                    start, end = item.get("start"), item.get("end")
                    if start is None or end is None:
                        start = end = None
                        trecho_original = str(item.get("word", ""))
                    else:
                        start, end = int(start) + deslocamento, int(end) + deslocamento
                        trecho_original = text[start:end]
                    do_modelo.append(
                        {
                            "text": trecho_original,
                            "label": item.get("entity_group", "UNKNOWN"),
                            "score": round(float(item.get("score", 0.0)), 4),
                            "start": start,
                            "end": end,
                            "model": nome_modelo,
                        }
                    )
            entidades.extend(do_modelo)
            por_modelo.append({"name": nome_modelo, "status": "loaded", "detail": "ok"})
        except Exception as exc:  # pragma: no cover - depends on runtime/dependencies
            por_modelo.append({"name": nome_modelo, "status": "fallback", "detail": f"Falha na inferência NER: {exc}"})

    carregados = [m for m in por_modelo if m["status"] == "loaded"]
    falhas = [m for m in por_modelo if m["status"] != "loaded"]
    if not carregados:
        return [], {
            "name": nome_conjunto,
            "status": "fallback",
            "detail": falhas[0]["detail"] if falhas else "NER indisponível: nenhum modelo configurado",
            "models": por_modelo,
        }

    entidades.sort(key=lambda e: e["start"] if e["start"] is not None else len(text))
    detalhe = "ok" if not falhas else "parcial: " + "; ".join(f"{m['name']}: {m['detail']}" for m in falhas)
    return entidades, {"name": nome_conjunto, "status": "loaded", "detail": detalhe, "models": por_modelo}


def _contem_palavra(texto: str, trecho: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(trecho)}(?!\w)", texto))


def _revisar_com_ner(
    texto_normalizado: str,
    entidades: list[dict[str, Any]],
    termos_reconhecidos: list[str],
) -> dict[str, list[dict[str, Any]]]:
    """Confere as entidades do NER com os termos que as regras reconheceram.

    Não preenche campo nenhum: só separa o que as regras já usaram (`confirmados`)
    do que o modelo encontrou e nenhuma regra reconheceu (`nao_reconhecidos`).
    A comparação é por palavra inteira, para "ic" não coincidir com "cronica".
    """
    termos = [t for t in (_chave_termo(t) for t in termos_reconhecidos) if t]

    # Sem duplicatas: fica a ocorrência de maior score de cada trecho.
    melhores: dict[str, dict[str, Any]] = {}
    for entidade in entidades:
        score = float(entidade.get("score", 0.0))
        if score < NER_SCORE_MINIMO:
            continue
        chave = _chave_termo(str(entidade.get("text", "")))
        if sum(ch.isalpha() for ch in chave) <= 2:
            continue
        if chave not in melhores or score > float(melhores[chave].get("score", 0.0)):
            melhores[chave] = entidade

    nao_reconhecidos: list[dict[str, Any]] = []
    confirmados: list[dict[str, Any]] = []
    for chave, entidade in melhores.items():
        item = {
            "text": str(entidade.get("text", "")).strip(),
            "label": entidade.get("label", "UNKNOWN"),
            "score": entidade.get("score", 0.0),
            "negado": _esta_negado(texto_normalizado, chave),
        }
        coincide = any(_contem_palavra(chave, termo) or _contem_palavra(termo, chave) for termo in termos)
        (confirmados if coincide else nao_reconhecidos).append(item)

    # Dois modelos podem marcar o mesmo achado com cortes diferentes ("DAOP" e
    # "DAOP com claudicação"): fica só o trecho mais longo.
    chaves = [_chave_termo(item["text"]) for item in nao_reconhecidos]
    nao_reconhecidos = [
        item
        for item, chave in zip(nao_reconhecidos, chaves)
        if not any(outra != chave and _contem_palavra(outra, chave) for outra in chaves)
    ]

    return {"nao_reconhecidos": nao_reconhecidos, "confirmados": confirmados}


def _buscar(padrao: str, texto: str, flags: int = 0) -> re.Match[str] | None:
    """re.search que anota o trecho casado como termo reconhecido pelas regras."""
    m = re.search(padrao, texto, flags)
    if m:
        _anotar_termo(m.group(0))
    return m


def _corresponde_algum(normalized_text: str, terms: list[str]) -> bool:
    # Percorre a lista inteira para anotar todos os termos presentes ("DAC, IAM há 4 meses"
    # anota "dac" e "iam"); o resultado é o mesmo de parar no primeiro.
    achou = False
    for term in terms:
        if re.search(rf"\b{re.escape(_normalizar(term))}\b", normalized_text):
            _anotar_termo(term)
            achou = True
    return achou


def _esta_negado(normalized_text: str, term: str) -> bool:
    norm_term = _normalizar(term)
    patterns = [
        rf"\bsem\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
        rf"\bnega\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
        rf"\bnao\s+[^\.,;]{{0,30}}{re.escape(norm_term)}\b",
    ]
    return any(re.search(p, normalized_text) for p in patterns)


def _extrair_idade(text: str) -> int | None:
    m = re.search(r"\b(\d{1,3})\s*anos?\b", text, flags=re.IGNORECASE)
    if not m:
        return None
    age = int(m.group(1))
    if 0 <= age <= 120:
        return age
    return None


def _limpar_nome(candidate: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", candidate).strip(" ,.;:-")
    cleaned = re.sub(r"^(sr\.?|sra\.?|srta\.?)\s+", "", cleaned, flags=re.IGNORECASE)
    if len(cleaned) < 3:
        return None
    if any(ch.isdigit() for ch in cleaned):
        return None
    if len(cleaned.split()) < 1:
        return None
    if _normalizar(cleaned) in {"paciente", "doente", "usuario", "cliente"}:
        return None
    return cleaned


def _extrair_nome(text: str) -> str | None:
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
            cleaned = _limpar_nome(match.group(1))
            if cleaned:
                return cleaned
    return None


def _extrair_mets(text: str) -> float | None:
    m = _buscar(r"\b(\d+(?:[\.,]\d+)?)\s*(?:mets?|met)\b", text, flags=re.IGNORECASE)
    if not m:
        return None
    value = float(m.group(1).replace(",", "."))
    return max(1.0, min(12.0, value))


def _inferir_mets_da_atividade(normalized_text: str) -> float | None:
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
        if _corresponde_algum(normalized_text, phrases):
            return mets
    return None


def _extrair_creatinina(text: str) -> float | None:
    m = _buscar(
        r"(?:creatinina|creat)[^\d]{0,30}(\d+(?:[\.,]\d+)?)\s*(?:mg/?d?l)?",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _extrair_egfr(text: str) -> float | None:
    m = _buscar(
        r"(?:tfg|egfr|filtracao\s+glomerular)[^\d]{0,25}(\d+(?:[\.,]\d+)?)\s*(?:ml/?min(?:/1\.73m2)?)?",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


FUNCAO_RENAL_PRESERVADA = [
    "funcao renal preservada",
    "funcao renal normal",
    "funcao renal sem alteracoes",
    "sem disfuncao renal",
    "sem insuficiencia renal",
    "creatinina normal",
]

VALVOPATIAS = [
    "estenose aortica",
    "estenose mitral",
    "insuficiencia aortica",
    "insuficiencia mitral",
    "regurgitacao aortica",
    "regurgitacao mitral",
    "dupla lesao aortica",
    "dupla lesao mitral",
    "protese valvar",
    "protese mecanica",
    "protese biologica",
    "protese aortica",
    "protese mitral",
    "protese tricuspide",
    "troca valvar",
    "valvopatia",
    "doenca valvar",
]

# Tabela 11 da diretriz: "doença valvar reumática" aparece na coluna da FA (FA valvar).
VALVOPATIA_REUMATICA = [
    "doenca valvar reumatica",
    "valvopatia reumatica",
    "estenose mitral reumatica",
    "cardiopatia reumatica",
]

PROTESE_MECANICA = r"\b(?:protese|valva|valvula)\s+(?:valvar\s+|cardiaca\s+)?(?:aortica\s+|mitral\s+)?mecanica\b"


def _extrair_chads2(normalized_text: str) -> int | None:
    # Só o CHADS2, que é o escore da Tabela 11. CHA2DS2-VASc e CHA2DS2-VA usam
    # outra escala e não podem preencher este campo.
    padrao = r"\bchads(2|₂)?(\s*-?\s*va(?:sc)?\b)?\s*(?:[:=]|de|score|escore)?\s*\(?\s*(\d)\b(?!\s*-?\s*va(?:sc)?\b)"
    for m in re.finditer(padrao, normalized_text):
        if m.group(2):
            continue
        valor = int(m.group(3))
        if valor <= 6:
            _anotar_termo(m.group(0))
            return valor
    return None


def _avc_ait_recente(normalized_text: str) -> bool:
    # AVC/AIT < 3 meses é risco tromboembólico alto na Tabela 11 (ponte indicada).
    padrao = (
        r"\b(?:avc|avci|ait|acidente vascular cerebral|ataque isquemico transitorio)\b"
        r"[^\.;]{0,15}?\bha\s+(\d+)\s*(dias?|semanas?|mes|meses)\b"
    )
    for m in re.finditer(padrao, normalized_text):
        n, unidade = int(m.group(1)), m.group(2)
        if unidade.startswith("dia"):
            meses = n / 30
        elif unidade.startswith("semana"):
            meses = n / 4.3
        else:
            meses = n
        if meses < 3:
            _anotar_termo(m.group(0))
            return True
    return False


def _estenose_importante_sintomatica(normalized_text: str) -> bool:
    # Condição ativa da Tabela 2: exige gravidade e sintomas explícitos na mesma frase.
    for frase in re.split(r"[\.;]", normalized_text):
        m = re.search(
            r"\bestenose\s+(?:valvar\s+)?(?:aortica|mitral)\s+(?:\w+\s+){0,2}?(?:importante|grave|severa|critica)\b",
            frase,
        )
        if m and re.search(r"\bsintomatica\b", frase):
            _anotar_termo(m.group(0))
            return True
    return False


def _extrair_cirurgia(normalized_text: str) -> dict[str, Any] | None:
    for surgery_id, payload in SURGERY_TYPE_MAP.items():
        if _corresponde_algum(normalized_text, payload["aliases"]):
            return {
                "tipo_cirurgia": surgery_id,
                "risco_cirurgia": payload["risco"],
                "eh_vascular": payload["vascular"],
                "rcri_cirurgia_alto_risco": payload.get("intracavitaria", False),
            }
    return None


def analisar_texto_clinico(text: str, current_data: dict[str, Any] | None = None) -> dict[str, Any]:
    # As regras anotam aqui os termos que reconheceram, para a conferência com o NER.
    termos_reconhecidos: list[str] = []
    marcador = _TERMOS_RECONHECIDOS.set(termos_reconhecidos)
    try:
        resultado = _analisar_com_regras(text, current_data or {})
    finally:
        _TERMOS_RECONHECIDOS.reset(marcador)

    # O NER só confere: nada do que ele devolve altera `autofill`.
    entities, model_info = _executar_ner(text)
    review = _revisar_com_ner(_normalizar(text), entities, termos_reconhecidos)

    return {
        "autofill": resultado["autofill"],
        "missing_critical": resultado["missing_critical"],
        "findings": resultado["findings"],
        "entities": entities,
        "model": model_info,
        "ner_review": review,
        "summary": resultado["summary"],
        "context": resultado["context"],
    }


def _analisar_com_regras(text: str, current_data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalizar(text)

    autofill: dict[str, Any] = {}
    findings: dict[str, list[str]] = {
        "diagnoses": [],
        "medications": [],
        "procedures": [],
    }

    age = _extrair_idade(text)
    if age is not None:
        autofill["idade"] = age

    name = _extrair_nome(text)
    if name:
        autofill["nome"] = name

    surgery = _extrair_cirurgia(normalized)
    if surgery:
        autofill.update(surgery)
        findings["procedures"].append(surgery["tipo_cirurgia"])

    if _corresponde_algum(normalized, ["insulina", "insulinoterapia", "nph", "glargina"]):
        autofill["rcri_diabetes_insulina"] = True
        autofill["vsg_diabetes_insulina"] = True
        findings["medications"].append("insulina")

    if _corresponde_algum(normalized, ["aas", "acido acetilsalicilico", "aspirina"]):
        autofill["usa_aas"] = True
        findings["medications"].append("aas")

    if _corresponde_algum(normalized, ["clopidogrel"]):
        autofill["usa_clopidogrel"] = True
        findings["medications"].append("clopidogrel")

    if _corresponde_algum(normalized, ["ticagrelor"]):
        autofill["usa_ticagrelor"] = True
        findings["medications"].append("ticagrelor")

    if _corresponde_algum(normalized, ["prasugrel"]):
        autofill["usa_prasugrel"] = True
        findings["medications"].append("prasugrel")

    if _corresponde_algum(normalized, ["varfarina", "marevan"]):
        autofill["usa_varfarina"] = True
        findings["medications"].append("varfarina")

    if _corresponde_algum(normalized, ["dabigatrana", "pradaxa"]):
        autofill["usa_doac"] = True
        autofill["tipo_doac"] = "dabigatrana"
        findings["medications"].append("dabigatrana")
    elif _corresponde_algum(normalized, ["rivaroxabana", "xarelto", "apixabana", "eliquis", "edoxabana", "lixiana"]):
        autofill["usa_doac"] = True
        autofill["tipo_doac"] = "rivaroxabana_apixabana_edoxabana"
        findings["medications"].append("doac")
    elif _corresponde_algum(normalized, ["doac", "noac", "anticoagulante oral direto"]):
        autofill["usa_doac"] = True
        findings["medications"].append("doac")

    tem_fa = _corresponde_algum(normalized, ["fibrilacao atrial"]) or bool(_buscar(r"\bfa\b", normalized))
    tem_tev = _corresponde_algum(normalized, ["tev", "tromboembolismo venoso", "trombose venosa", "tep"])
    tem_protese_mecanica = bool(_buscar(PROTESE_MECANICA, normalized))
    tem_fa_valvar = _corresponde_algum(normalized, ["fa valvar", "fibrilacao atrial valvar"]) or (
        tem_fa and _corresponde_algum(normalized, VALVOPATIA_REUMATICA)
    )

    # Prótese mecânica e FA valvar sempre indicam ponte (Tabela 11), então
    # prevalecem sobre TEV e FA comum quando o texto cita mais de uma.
    if tem_protese_mecanica:
        autofill["indicacao_varfarina"] = "mechanical_valve"
    elif tem_fa_valvar:
        autofill["indicacao_varfarina"] = "rheumatic"
    elif tem_tev:
        autofill["indicacao_varfarina"] = "vte"
    elif tem_fa:
        autofill["indicacao_varfarina"] = "af"

    chads2 = _extrair_chads2(normalized)
    if chads2 is not None:
        autofill["chadsvasc_varfarina"] = chads2

    if _avc_ait_recente(normalized):
        autofill["avc_3m_varfarina"] = True

    if _corresponde_algum(normalized, ["avc", "ait", "acidente vascular cerebral", "avci"]):
        autofill["rcri_cerebrovascular"] = True
        findings["diagnoses"].append("doenca_cerebrovascular")

    if _corresponde_algum(normalized, ["dac", "doenca coronariana", "angina", "infarto", "iam"]):
        autofill["dac_conhecida"] = True
        autofill["rcri_doenca_coronaria"] = True
        autofill["vsg_dac"] = True
        findings["diagnoses"].append("doenca_coronariana")

    if _corresponde_algum(normalized, ["insuficiencia cardiaca", "ic", "icc"]):
        autofill["ic_conhecida"] = True
        autofill["rcri_ic"] = True
        autofill["vsg_ic"] = True
        findings["diagnoses"].append("insuficiencia_cardiaca")

    if _corresponde_algum(normalized, ["dpoc"]):
        autofill["vsg_dpoc"] = True
        findings["diagnoses"].append("dpoc")

    if _corresponde_algum(normalized, ["tabagista", "tabagismo", "fumante"]):
        autofill["vsg_tabagismo"] = True

    if _corresponde_algum(normalized, ["obesidade", "obeso", "obesa"]):
        autofill["obesidade"] = True

    if _corresponde_algum(normalized, ["beta bloqueador", "beta-bloqueador", "betabloqueador", "atenolol", "metoprolol", "carvedilol"]):
        autofill["vsg_betabloqueador_cronico"] = True
        findings["medications"].append("betabloqueador")

    has_revasc = _corresponde_algum(normalized, ["revascularizacao", "angioplastia coronaria", "ponte de safena"])
    if has_revasc and not _esta_negado(normalized, "revascularizacao"):
        autofill["vsg_revasc_previa"] = True

    valvopatias = [t for t in VALVOPATIAS if _corresponde_algum(normalized, [t]) and not _esta_negado(normalized, t)]
    if valvopatias or tem_protese_mecanica:
        autofill["doenca_valvar_conhecida"] = True
        findings["diagnoses"].append("doenca_valvar")

    if _estenose_importante_sintomatica(normalized):
        autofill["cv_valvopatia_grave"] = True

    # AAS em quem já tem doença aterosclerótica estabelecida é prevenção secundária.
    if autofill.get("usa_aas") and not current_data.get("prevencao_aas"):
        doenca_aterosclerotica = (
            autofill.get("dac_conhecida")
            or autofill.get("rcri_cerebrovascular")
            or autofill.get("vsg_revasc_previa")
            or _corresponde_algum(normalized, [
                "stent",
                "doenca arterial periferica",
                "doenca arterial obstrutiva periferica",
                "dap",
                "doap",
                "claudicacao intermitente",
            ])
        )
        if _corresponde_algum(normalized, ["prevencao primaria"]):
            autofill["prevencao_aas"] = "primary"
        elif doenca_aterosclerotica or _corresponde_algum(normalized, ["prevencao secundaria"]):
            autofill["prevencao_aas"] = "secondary"

    mets = _extrair_mets(text)
    if mets is None:
        mets = _inferir_mets_da_atividade(normalized)
    if mets is not None:
        autofill["mets"] = mets

    creatinine = _extrair_creatinina(text)
    if creatinine is not None:
        if creatinine > 2.0:
            autofill["rcri_creatinina_acima_2"] = True
        if creatinine > 1.8:
            autofill["vsg_creatinina_acima_1_8"] = True

    egfr = _extrair_egfr(text)

    funcao_renal_preservada = (
        creatinine is None and egfr is None and _corresponde_algum(normalized, FUNCAO_RENAL_PRESERVADA)
    )
    if funcao_renal_preservada:
        autofill["rcri_creatinina_acima_2"] = False
        autofill["vsg_creatinina_acima_1_8"] = False

    merged = {**current_data, **autofill}
    missing_critical: list[dict[str, str]] = []

    if merged.get("idade") is None:
        missing_critical.append(
            {
                "campo": "idade",
                "label": "Idade",
                "reason": "A idade é necessária para pontuação VSG e interpretação global de risco.",
                "question": "Qual a idade do paciente?",
            }
        )

    if not merged.get("tipo_cirurgia"):
        missing_critical.append(
            {
                "campo": "tipo_cirurgia",
                "label": "Tipo de cirurgia",
                "reason": "Sem o procedimento não é possível determinar o risco cirúrgico basal.",
                "question": "Qual procedimento cirúrgico será realizado?",
            }
        )

    mets_is_missing = merged.get("mets") is None
    if not mets_is_missing:
        mets_is_default = (current_data.get("mets") in (None, "", 1)) and not current_data.get("atividades_funcionais")
        mets_is_missing = mets is None and mets_is_default

    if mets_is_missing:
        missing_critical.append(
            {
                "campo": "mets",
                "label": "Capacidade funcional (METs)",
                "reason": "A capacidade funcional impacta a estratificação perioperatória.",
                "question": "Qual a estimativa de METs ou atividade máxima tolerada?",
            }
        )

    if creatinine is None and egfr is None and not funcao_renal_preservada:
        missing_critical.append(
            {
                "campo": "funcao_renal",
                "label": "Função renal (creatinina ou TFG)",
                "reason": "Creatinina/TFG são dados críticos para classificar risco renal e critérios RCRI/VSG.",
                "question": "Informe creatinina pré-operatória (mg/dL) ou TFG estimada.",
            }
        )

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
        "summary": summary,
        "context": context,
    }

