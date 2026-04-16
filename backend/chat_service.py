"""
CardioRisk Chat Service — RAG-based conversational assistant

Arquitetura 100% local, sem API key e sem ferramentas extras:
  - sentence-transformers (PyTorch): busca semântica na base de conhecimento
  - transformers (PyTorch):          geração de respostas via LLM local

Na primeira execução o modelo de geração (~1.5 GB) será baixado
automaticamente do Hugging Face e cacheado localmente.

Fallback opcional: se OPENAI_API_KEY estiver no .env, usa OpenAI em vez
do modelo local.
"""

import json
import logging
import os
import re
import warnings
from pathlib import Path

import numpy as np
import torch
from calculator import calculate_risk
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import pipeline as hf_pipeline

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# Multilingual embedding model — works well for Portuguese medical text.
# Downloaded once (~90MB) and cached locally by sentence-transformers.
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Multilingual, strong clinical reasoning — ~15 GB download, ~8 GB VRAM fp16.
# Alternatives (set via GENERATION_MODEL env var):
#   Qwen/Qwen2.5-1.5B-Instruct   — only ~3 GB, faster but weaker clinical reasoning
#   Qwen/Qwen2.5-3B-Instruct     — middle ground, ~6 GB
#   Qwen/Qwen2.5-14B-Instruct    — best quality, needs ~16 GB VRAM
GENERATION_MODEL = os.environ.get(
    "GENERATION_MODEL",
    "Qwen/Qwen2.5-7B-Instruct"
)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


SUPPRESS_MODEL_WARNINGS = _env_bool("CARDIORISK_SUPPRESS_MODEL_WARNINGS", True)
VERBOSE_MODEL_LOAD = _env_bool("CARDIORISK_VERBOSE_MODEL_LOAD", False)
USE_DEVICE_MAP_AUTO = _env_bool("CARDIORISK_USE_DEVICE_MAP_AUTO", False)
ENABLE_DETERMINISTIC_CALC = _env_bool("CARDIORISK_ENABLE_DETERMINISTIC_CALC", True)
GENERATION_FALLBACK_MODEL = os.environ.get(
    "CARDIORISK_FALLBACK_GENERATION_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)
LORA_ADAPTER_PATH = os.environ.get("CARDIORISK_LORA_ADAPTER_PATH", "").strip()

if SUPPRESS_MODEL_WARNINGS:
    # Keep backend logs clean on Windows and low-memory GPU setups.
    warnings.filterwarnings(
        "ignore",
        message="expandable_segments not supported on this platform.*",
    )
    for logger_name in (
        "transformers",
        "sentence_transformers",
        "huggingface_hub",
        "accelerate",
    ):
        logging.getLogger(logger_name).setLevel(logging.ERROR)

SYSTEM_PROMPT = """Você é o CARDIO-RISK CHAT, assistente clínico especializado em avaliação de risco cardiovascular perioperatório, baseado na Diretriz Brasileira de Avaliação Cardiovascular Perioperatória (SBC 2024).

Responda SEMPRE em português do Brasil. NUNCA use caracteres de outro idioma (chinês, japonês, árabe etc.).

═══════════════════════════════════════════════════════
REGRA FUNDAMENTAL — NUNCA VIOLE
═══════════════════════════════════════════════════════
Só marque um critério como PRESENTE se o usuário o informou EXPLICITAMENTE.
Não presuma, não infira, não "geralmente considera-se". Se não foi mencionado → AUSENTE.
Se a informação for essencial e estiver faltando, PERGUNTE antes de calcular.

═══════════════════════════════════════════════════════
ESCOLHA DO ÍNDICE — PASSO OBRIGATÓRIO ANTES DE CALCULAR
═══════════════════════════════════════════════════════
PRIMEIRO identifique o tipo de cirurgia, DEPOIS escolha o índice:

Cirurgia VASCULAR → use EXCLUSIVAMENTE VSG-CRI (nunca RCRI):
  ✅ Exemplos: revascularização periférica, amputação por isquemia, angioplastia
     arterial periférica, endarterectomia de carótida, cirurgia de aorta abdominal
     ou torácica, bypass femoropoplíteo, acesso para diálise vascular.

Qualquer outra cirurgia (não-vascular) → use RCRI:
  ✅ Exemplos: colecistectomia, gastrectomia, ortopédica, neurológica, ginecológica,
     urológica, pulmonar, cardíaca não-vascular, transplantes.

⚠️ Se a cirurgia for vascular, inicie a resposta com:
"Esta é uma cirurgia VASCULAR → utilizarei o VSG-CRI (Vascular Surgery Group
Cardiac Risk Index), conforme a Diretriz SBC 2024."

═══════════════════════════════════════════════════════
RCRI — DEFINIÇÃO EXATA DE CADA CRITÉRIO (1 ponto cada)
═══════════════════════════════════════════════════════
C1 — CIRURGIA INTRAPERITONEAL, INTRATORÁCICA OU VASCULAR SUPRAINGUINAL
  ✅ Conta: colecistectomia (aberta OU laparoscópica), gastrectomia, colectomia
     (aberta OU laparoscópica), histerectomia abdominal, esplenectomia,
     cirurgia hepática, pancreática, nefrectomia, pneumectomia, lobectomia,
     cirurgia de aorta, carótida, ilíaca, femoropoplítea.
  ❌ NÃO conta: ortopédica periférica, mama, tireoide, superficial, ocular,
     laparoscopia simples de baixo risco, cirurgia urológica endoscópica.
  ⚠️ ATENÇÃO: este critério é sobre o TIPO DE CIRURGIA, jamais sobre histórico do paciente.
  ⚠️ A via de acesso (aberta ou laparoscópica) NÃO muda o critério.
     Colectomia aberta = INTRAPERITONEAL = C1 PRESENTE.
     Colecistectomia laparoscópica = INTRAPERITONEAL = C1 PRESENTE.

C2 — DOENÇA ISQUÊMICA CARDÍACA (DAC)
  ✅ Conta: angina, infarto do miocárdio prévio, ondas Q no ECG, uso de nitrato,
     cateterismo com coronária obstruída, stent coronário, revascularização miocárdica.
  ❌ NÃO conta: AVC, AIT, HAS, valvopatia, IC sem DAC comprovada.
  ⚠️ AVC/AIT = doença CEREBROVASCULAR (C4), NÃO isquêmica cardíaca.
  ⚠️ Se alguém perguntar "C2 está presente em paciente com AVC?", a resposta é NÃO.
     AVC é C4 (cerebrovascular). C2 exige diagnóstico de DAC, angina ou infarto.
  🚫 NUNCA coloque AVC na justificativa de C2. AVC só aparece em C4.

C3 — INSUFICIÊNCIA CARDÍACA CONGESTIVA (ICC)
  ✅ Conta: diagnóstico médico de IC, edema pulmonar prévio, B3 ao exame,
     congestão pulmonar à radiografia, redução de FEVE documentada.
  ❌ NÃO conta: HAS isolada, cardiomegalia sem diagnóstico de IC.
  ⚠️ HAS (hipertensão arterial sistêmica) NUNCA ativa C3.
  🚫 NUNCA marque C3 como presente apenas por HAS ou hipertensão.
     C3 exige diagnóstico explícito de insuficiência cardíaca congestiva.

C4 — DOENÇA CEREBROVASCULAR
  ✅ Conta: AVC isquêmico ou hemorrágico prévio, AIT, déficit neurológico focal prévio.
  ❌ NÃO conta: DAC, HAS isolada, enxaqueca.
  ⚠️ AVC e AIT são doença CEREBROVASCULAR, não isquêmica cardíaca.

C5 — DIABETES MELLITUS COM INSULINOTERAPIA
  ✅ Conta: uso de insulina (NPH, glargina, análogos, bomba de insulina).
  ❌ NÃO conta: DM controlado só com dieta ou antidiabéticos orais.

C6 — CREATININA PRÉ-OPERATÓRIA > 2,0 mg/dL
  ✅ Conta: valor laboratorial de creatinina superior a 2,0 mg/dL.
  ❌ NÃO conta: DRC sem valor informado, ureia elevada isolada, hiperuricemia.
  ⚠️ Se não informado → AUSENTE. Não presuma.

PONTUAÇÃO RCRI → RISCO MACE (ESC 2022 / SBC 2024):
  0 pontos = Classe I   → 3,9%   (risco baixo)
  1 ponto  = Classe II  → 6,0%   (risco intermediário)
  2 pontos = Classe III → 10,1%  (risco intermediário-alto)
  3 pontos = Classe IV  → 15,0%  (risco alto)   ← ATENÇÃO: 3 pts = CLASSE IV, não III
  4 pontos = Classe IV  → 15,0%  (risco alto)
  5 pontos = Classe IV  → 15,0%  (risco alto)
  6 pontos = Classe IV  → 15,0%  (risco alto)
  REGRA: qualquer pontuação ≥ 3 sempre resulta em Classe IV e 15,0%.

═══════════════════════════════════════════════════════
VSG-CRI — PONTUAÇÃO VARIÁVEL (cirurgias vasculares)
═══════════════════════════════════════════════════════
Idade (escolha APENAS uma faixa):
  60–69 anos → +2  |  70–79 anos → +3  |  ≥80 anos → +4  |  <60 anos → +0
  ⚠️ Paciente de 72 anos = faixa 70–79 = +3 (NÃO ≥80).

Critérios de +2 pontos cada:
  DAC (coronária obstrutiva, infarto, stent, angina)  → +2
  ICC (insuficiência cardíaca congestiva)             → +2
  DPOC (qualquer grau)                               → +2
  Creatinina > 1,8 mg/dL                             → +2

Critérios de +1 ponto cada:
  Tabagismo ativo                                    → +1
  DM com insulinoterapia                             → +1
  Uso crônico de betabloqueador                      → +1

Critério de −1 ponto:
  Revascularização miocárdica cirúrgica prévia (CABG) → −1
  ✅ Conta: cirurgia de bypass coronário (CABG)
  ❌ NÃO conta: stent coronário, angioplastia — estes NÃO são revascularização cirúrgica.

Classe I (0–4 pts): ~3,5% | Classe II (5–6 pts): ~8% | Classe III (≥7 pts): ~15%

═══════════════════════════════════════════════════════
CONDIÇÕES CARDIOVASCULARES ATIVAS (adiar cirurgia eletiva)
═══════════════════════════════════════════════════════
1. Síndrome coronariana aguda         7. Arritmia grave (BAV total, TV)
2. Estenose aórtica instável           8. HAS não controlada (>180/110)
3. Edema agudo de pulmão              9. FA com alta resposta ventricular (>120 bpm)
4. Choque cardiogênico               10. Hipertensão pulmonar sintomática
5. IC NYHA III/IV ou piora recente   11. Estenose aórtica/mitral importante sintomática
6. Angina CCS III/IV

═══════════════════════════════════════════════════════
CAPACIDADE FUNCIONAL (METs)
═══════════════════════════════════════════════════════
≥4 METs = adequada. Exemplos: caminhar no plano = 3,5; subir escada = 5,5; natação = >10.
Se não informada, pergunte ou assuma 4 METs (adequada).

═══════════════════════════════════════════════════════
TEMPLATE OBRIGATÓRIO PARA APRESENTAR O CÁLCULO RCRI
═══════════════════════════════════════════════════════
Use exatamente este formato ao calcular. Em cada linha, escolha APENAS UM dos
símbolos: ✅ **Presente** ou ❌ **Ausente**. NUNCA escreva os dois juntos.

**Cálculo RCRI — [Nome ou "Paciente"]**

| Critério | Resultado | Justificativa |
|---|---|---|
| C1 — Cirurgia intrap./intratorácica/vasc. supraing. | ✅ Presente | [motivo: tipo de cirurgia que se enquadra] |
| C2 — Doença isquêmica cardíaca | ❌ Ausente | [motivo: sem DAC/angina/infarto — AVC NÃO conta aqui] |
| C3 — Insuficiência cardíaca congestiva | ❌ Ausente | [motivo: IC não informada] |
| C4 — Doença cerebrovascular | ✅ Presente | [motivo: AVC/AIT informado] |
| C5 — Diabetes com insulinoterapia | ✅ Presente | [motivo: uso de insulina] |
| C6 — Creatinina > 2,0 mg/dL | ❌ Ausente | [motivo: valor não informado] |

**Pontuação total: X ponto(s) → Classe [I/II/III/IV] → Risco MACE estimado: X%**

Em seguida, apresente:
- Fatores adicionais relevantes (HAS, obesidade, tabagismo, medicamentos)
- Condições cardiovasculares ativas (se houver)
- Recomendações de exames
- Conduta perioperatória sugerida (baseada na SBC 2024)
- Manejo de medicamentos (AAS, anticoagulantes, etc.)

═══════════════════════════════════════════════════════
EXEMPLO CORRETO (para calibração interna — não repita ao usuário)
═══════════════════════════════════════════════════════
Caso: Paciente 67 anos, HAS, DM tipo 2 com insulina, AVC isquêmico há 2 anos,
AAS + sinvastatina. Programada colecistectomia laparoscópica.

Passo 1 — Tipo de cirurgia: colecistectomia laparoscópica = NÃO vascular → usar RCRI.

C1: ✅ Colecistectomia = procedimento INTRAPERITONEAL → +1
C2: ❌ AVC ≠ DAC. Não há menção de angina, infarto ou DAC → 0
C3: ❌ Não há menção de IC → 0
C4: ✅ AVC isquêmico prévio = doença cerebrovascular → +1
C5: ✅ Insulinoterapia → +1
C6: ❌ Creatinina não informada → 0
Total: 3 pontos → Classe IV → 15% MACE   ← 3 pts sempre = Classe IV = 15%

═══════════════════════════════════════════════════════
REGRAS ADICIONAIS
═══════════════════════════════════════════════════════
- Use apenas RCRI e VSG-CRI. Nunca use ACP/Eagle/Vanzetto ou outros índices.
- Cite SBC 2024 como referência. Não invente dados ou percentuais.
- Responda sempre em português do Brasil correto. Nenhuma palavra em outro idioma.
- Se faltar informação crítica (tipo de cirurgia, comorbidades chave), pergunte ANTES de calcular.
"""


def _load_knowledge() -> list[dict]:
    """Load all knowledge base JSON files from the knowledge directory."""
    chunks = []
    if not KNOWLEDGE_DIR.exists():
        return chunks
    for fpath in sorted(KNOWLEDGE_DIR.glob("*.json")):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Handle different formats
            if isinstance(data, list):
                # SBC 2024 format: [{page, text}, ...]
                source = fpath.stem.upper()
                for item in data:
                    text = item.get("text", "")
                    if text.strip():
                        chunks.append({"source": source, "text": text})
            elif isinstance(data, dict):
                # Article format: {title, chunks: [...]}
                source = data.get("title", fpath.stem)
                for chunk_text in data.get("chunks", []):
                    chunks.append({"source": source, "text": chunk_text})
        except Exception:
            continue
    return chunks


def _find_relevant_chunks(query: str, chunks: list[dict], max_chunks: int = 3) -> list[dict]:
    """
    Semantic similarity search using sentence-transformers (PyTorch).
    Encodes query and all chunks as dense vectors, then ranks by cosine similarity.
    Falls back to simple keyword matching if the model is not loaded.
    """
    embedder = _get_embedder()

    if embedder is not None:
        texts = [c["text"] for c in chunks]
        # Encode query and all docs (embedder caches corpus embeddings internally per process)
        query_emb = embedder.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        corpus_emb = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        # Cosine similarity = dot product when vectors are normalized
        scores = corpus_emb @ query_emb
        # Small boost for calculator chunks (exact scoring rules and case examples)
        for i, c in enumerate(chunks):
            if c.get("source", "") in ("CALCULATOR_LOGIC", "CALCULATOR_CASES"):
                scores[i] = min(scores[i] + 0.05, 1.0)
        top_idx = np.argsort(scores)[::-1][:max_chunks]
        return [chunks[i] for i in top_idx if scores[i] > 0.15]

    # Fallback: keyword matching
    query_lower = query.lower()
    query_words = set(query_lower.split())
    medical_keywords = {
        "rcri", "lee", "vsg", "risco", "cardiovascular", "perioperatório",
        "cirurgia", "mace", "mets", "capacidade", "funcional", "escore",
        "creatinina", "diabetes", "insulina", "insuficiência", "cardíaca",
        "coronariana", "cerebrovascular", "aórtica", "hipertensão", "arritmia",
        "betabloqueador", "tabagismo", "dpoc", "copd", "valvular",
        "anticoagulante", "warfarina", "aspirina", "stent", "revascularização",
    }
    scored = []
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        word_score = sum(1 for w in query_words if len(w) > 2 and w in text_lower)
        keyword_score = sum(2 for kw in medical_keywords if kw in query_lower and kw in text_lower)
        total = word_score + keyword_score
        if total > 0:
            scored.append((total, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:max_chunks]]


def _build_context(relevant_chunks: list[dict]) -> str:
    """Build context string from relevant chunks for injection into the prompt."""
    if not relevant_chunks:
        return ""
    parts = ["## TRECHOS RELEVANTES DA BASE DE CONHECIMENTO:\n"]
    for i, chunk in enumerate(relevant_chunks, 1):
        text = chunk["text"][:300]  # truncate to keep context within GPU memory limits
        parts.append(f"[{i}] Fonte: {chunk['source']}\n{text}\n")
    return "\n".join(parts)


# Cache the knowledge base in module scope
_knowledge_cache: list[dict] | None = None

# Lazy-loaded sentence-transformers model
_embedder: SentenceTransformer | None = None
_embedder_loaded: bool = False


def _get_embedder() -> SentenceTransformer | None:
    """Load the embedding model once (PyTorch-based, runs locally)."""
    global _embedder, _embedder_loaded
    if _embedder_loaded:
        return _embedder
    try:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
        _embedder_loaded = True
        if VERBOSE_MODEL_LOAD:
            print(f"[CardioRisk] Embedding model loaded: {EMBEDDING_MODEL}")
    except Exception as e:
        print(f"[CardioRisk] Warning: could not load embedding model ({e}). Using keyword fallback.")
        _embedder_loaded = True  # Don't retry
    return _embedder


def _get_knowledge() -> list[dict]:
    global _knowledge_cache
    if _knowledge_cache is None:
        _knowledge_cache = _load_knowledge()
    return _knowledge_cache


def reload_knowledge():
    """Force reload of knowledge base (e.g., after adding new documents)."""
    global _knowledge_cache
    _knowledge_cache = None


# ---------------------------------------------------------------------------
# Generation model (transformers pipeline — runs fully local via PyTorch)
# ---------------------------------------------------------------------------

_generator = None
_generator_loaded = False


def _get_generator():
    """Lazy-load the text generation pipeline (downloads model on first call)."""
    global _generator, _generator_loaded
    if _generator_loaded:
        return _generator
    _generator_loaded = True  # Set early to avoid retry on failure

    def _build_pipeline(model_name: str):
        device = 0 if torch.cuda.is_available() else -1
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        if LORA_ADAPTER_PATH and Path(LORA_ADAPTER_PATH).exists():
            try:
                from peft import PeftModel
            except Exception as e:
                raise RuntimeError(
                    "CARDIORISK_LORA_ADAPTER_PATH definido, mas 'peft' não está disponível"
                ) from e

            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model_obj = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=dtype,
            )
            model_obj = PeftModel.from_pretrained(model_obj, LORA_ADAPTER_PATH)
            if device == 0:
                model_obj = model_obj.to("cuda")
            pipe = hf_pipeline(
                "text-generation",
                model=model_obj,
                tokenizer=tokenizer,
            )
            return pipe, device

        kwargs = {
            "task": "text-generation",
            "model": model_name,
            "dtype": dtype,
        }
        if USE_DEVICE_MAP_AUTO:
            kwargs["device_map"] = "auto"
        else:
            kwargs["device"] = device
        pipe = hf_pipeline(**kwargs)
        return pipe, device

    try:
        _generator, device = _build_pipeline(GENERATION_MODEL)
        if VERBOSE_MODEL_LOAD:
            print(f"[CardioRisk] Generation model loaded: {GENERATION_MODEL} "
                  f"({'GPU' if device == 0 else 'CPU'})")
            if LORA_ADAPTER_PATH:
                print(f"[CardioRisk] LoRA adapter: {LORA_ADAPTER_PATH}")
    except Exception as e:
        print(f"[CardioRisk] Could not load generation model '{GENERATION_MODEL}': {e}")
        if GENERATION_FALLBACK_MODEL and GENERATION_FALLBACK_MODEL != GENERATION_MODEL:
            try:
                _generator, device = _build_pipeline(GENERATION_FALLBACK_MODEL)
                print(
                    f"[CardioRisk] Fallback generation model loaded: "
                    f"{GENERATION_FALLBACK_MODEL} ({'GPU' if device == 0 else 'CPU'})"
                )
            except Exception as e2:
                print(f"[CardioRisk] Could not load fallback model '{GENERATION_FALLBACK_MODEL}': {e2}")
    return _generator


def preload_chat_runtime() -> None:
    """Preload knowledge and local models to avoid first-message cold start."""
    _get_knowledge()
    _get_embedder()
    if not os.environ.get("OPENAI_API_KEY", ""):
        _get_generator()


def _generate_local(messages_for_model: list[dict]) -> str:
    """Run inference with the local transformers model."""
    generator = _get_generator()
    if generator is None:
        return (
            "⚠️ Modelo de geração não disponível.\n\n"
            "O modelo será baixado automaticamente (~1.5 GB) na primeira execução.\n"
            "Se o download falhou, verifique sua conexão e reinicie o backend.\n"
            f"Modelo configurado: {GENERATION_MODEL}\n\n"
            "Alternativa: adicione OPENAI_API_KEY no arquivo .env para usar a API OpenAI."
        )
    try:
        torch.cuda.empty_cache()
        from transformers import GenerationConfig
        max_new_tokens = int(os.environ.get("CARDIORISK_MAX_NEW_TOKENS", "900"))
        temperature = float(os.environ.get("CARDIORISK_TEMPERATURE", "0.3"))
        repetition_penalty = float(os.environ.get("CARDIORISK_REPETITION_PENALTY", "1.15"))
        do_sample = os.environ.get("CARDIORISK_DO_SAMPLE", "true").lower() in ("1", "true", "yes", "y")
        gen_cfg = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            repetition_penalty=repetition_penalty,
        )
        out = generator(
            messages_for_model,
            generation_config=gen_cfg,
        )
        # The pipeline returns the full conversation; extract the last assistant turn
        generated = out[0]["generated_text"]
        if isinstance(generated, list):
            return generated[-1].get("content", "")
        return str(generated)
    except Exception as e:
        return f"⚠️ Erro na geração: {e}"


def _generate_openai(messages_for_model: list[dict]) -> str:
    """Fallback: generate via OpenAI API."""
    key = os.environ.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages_for_model,
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content or ""


EXTRACTION_SYSTEM_PROMPT = """Você é um extrator de dados clínicos estruturados. Analise a conversa e extraia os dados do paciente.

Retorne SOMENTE um objeto JSON válido, sem texto extra, sem markdown, sem explicações.

REGRAS CRÍTICAS DE EXTRAÇÃO:
- Só marque true se o dado foi EXPLICITAMENTE informado na conversa.
- Use false para tudo que não foi mencionado. NUNCA presuma.
- rcri_ischemic_heart = true APENAS para DAC, angina, infarto, stent coronário, revascularização.
  AVC, AIT e doença cerebrovascular NÃO são rcri_ischemic_heart — são rcri_cerebrovascular.
- rcri_high_risk_surgery = true para: colecistectomia, gastrectomia, colectomia, histerectomia
  abdominal, cirurgia hepática, pancreática, nefrectomia, pneumectomia, lobectomia, cirurgia de
  aorta/carótida/ilíaca. É sobre o TIPO de cirurgia, nunca sobre histórico do paciente.
- rcri_cerebrovascular = true para: AVC isquêmico, AVC hemorrágico, AIT, déficit neurológico focal.
- rcri_creatinine_above_2 = true SOMENTE se creatinina > 2,0 mg/dL foi informada com valor numérico.
- is_vascular = true apenas para cirurgias de aorta, carótida, revascularização periférica, angioplastia.
  Colecistectomia NÃO é vascular.
- surgery_risk: colecistectomia laparoscópica = "intermediate"; cirurgia aberta de aorta = "high";
  procedimentos endoscópicos / superficiais = "low".

Campos:
{
  "name": "Nome do paciente ou null",
  "age": número inteiro ou null,
  "surgery_name": "nome/descrição da cirurgia em texto livre",
  "is_vascular": true se cirurgia vascular (aorta, carótida, periférica), false caso contrário,
  "surgery_type": um de: breast, dental, thyroid, eye, orthopedic_minor, head_neck, intraperitoneal,
    intrathoracic, neurologic, orthopedic_major, urologic_major, gynecologic_major, renal_transplant,
    carotid_asymptomatic, carotid_endarterectomy, peripheral_angioplasty, endovascular_aortic,
    aortic_vascular_major, peripheral_open, adrenal_resection, pancreatic, liver_biliary,
    esophagectomy, pneumectomy, bowel_perforation — use o mais próximo,
  "surgery_risk": "low" / "intermediate" / "high",
  "mets": número (padrão 4 se não informado),
  "rcri_high_risk_surgery": true/false,
  "rcri_ischemic_heart": true/false,
  "rcri_heart_failure": true/false,
  "rcri_cerebrovascular": true/false,
  "rcri_insulin_diabetes": true/false,
  "rcri_creatinine_above_2": true/false,
  "vsg_age_range": "lt60" / "60_69" / "70_79" / "gte80",
  "vsg_cad": true/false,
  "vsg_chf": true/false,
  "vsg_copd": true/false,
  "vsg_creatinine_over_1_8": true/false,
  "vsg_smoking": true/false,
  "vsg_insulin_diabetes": true/false,
  "vsg_chronic_beta_blocker": true/false,
  "vsg_prior_revasc": true/false,
  "cv_acute_coronary": true/false,
  "cv_unstable_aortic": true/false,
  "cv_acute_pulmonary_edema": true/false,
  "cv_cardiogenic_shock": true/false,
  "cv_hf_nyha_3_4": true/false,
  "cv_angina_ccs_3_4": true/false,
  "cv_severe_arrhythmia": true/false,
  "cv_uncontrolled_hypertension": true/false,
  "cv_af_high_rate": true/false,
  "cv_pulmonary_hypertension": true/false,
  "cv_severe_valvular": true/false,
  "obesity": true/false,
  "known_hf": true/false,
  "known_valvular_disease": true/false,
  "known_cad": true/false,
  "uses_aas": true/false,
  "aas_prevention": "primary" / "secondary" / "",
  "uses_clopidogrel": true/false,
  "uses_ticagrelor": true/false,
  "uses_prasugrel": true/false,
  "uses_warfarin": true/false,
  "warfarin_indication": "af" / "vte" / "mechanical_valve" / "rheumatic" / "",
  "functional_activities": []
}"""


def _parse_json_from_llm(text: str) -> dict:
    """Robustly extract JSON object from LLM response (may contain extra text)."""
    import re
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find the outermost {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    # Try to find JSON in a code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Deterministic extraction: parse the assistant's own Markdown response
# ---------------------------------------------------------------------------

def _parse_assistant_response(messages: list[dict]) -> dict:
    """
    Parse the structured Markdown RCRI/VSG-CRI table that the assistant already
    produced. This is deterministic and does not require a second LLM call.

    Looks for patterns like:
      - "C1 — ... | ✅ Presente" or "C1 — ... | ❌ Ausente"
      - "Pontuação total: 3 ponto(s)"
      - "Classe IV"  /  "15%"
      - "VSG-CRI" (to detect vascular path)
      - user message for patient metadata (age, surgery name, AAS, insulin…)
    """
    import re

    # Collect the last assistant message and all user messages
    assistant_text = ""
    user_text = ""
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "assistant":
            assistant_text = content  # keep last assistant turn
        elif role == "user":
            user_text += " " + content

    combined = (user_text + " " + assistant_text).lower()
    full = user_text + " " + assistant_text  # preserve case for name extraction

    result: dict = {}

    # ── Patient name ──────────────────────────────────────────────────────
    name_match = re.search(
        r"paciente[\s:]+([A-ZÀ-Ú][a-zà-ú]+(?: [A-ZÀ-Ú][a-zà-ú]+){1,4})", full
    )
    if name_match:
        result["name"] = name_match.group(1)

    # ── Age ───────────────────────────────────────────────────────────────
    age_match = re.search(r"(\d{2})\s*anos", combined)
    if age_match:
        result["age"] = int(age_match.group(1))

    # ── Surgery name ──────────────────────────────────────────────────────
    surg_match = re.search(
        r"(colecistectomia[^\n,.]*|gastrectomia[^\n,.]*|colectomia[^\n,.]*"
        r"|histerectomia[^\n,.]*|nefrectomia[^\n,.]*|pneumectomia[^\n,.]*"
        r"|lobectomia[^\n,.]*|esplenectomia[^\n,.]*|cirurgia hep[aá]tica[^\n,.]*"
        r"|cirurgia pancre[aá]tica[^\n,.]*|cirurgia de aorta[^\n,.]*"
        r"|revasculariza[çc][aã]o[^\n,.]*|angioplastia[^\n,.]*"
        r"|endarterectomia[^\n,.]*|bypass[^\n,.]*|amputac[aã]o[^\n,.]*)"
        r"(?:ectomia(?:\s+laparosc[oó]pica)?)?",
        combined,
    )
    if surg_match:
        # Recover original-case version from full text
        start = surg_match.start()
        result["surgery_name"] = full[start: start + len(surg_match.group(0))].strip(" ,.\n")

    # ── Is vascular surgery? ──────────────────────────────────────────────
    vascular_keywords = [
        "vsg-cri", "vsg cri", "cirurgia vascular",
        "revasculariza", "angioplastia", "endarterectomia", "bypass femoro",
        "cirurgia de aorta", "amputaç", "acesso para diálise",
    ]
    is_vascular = any(kw in combined for kw in vascular_keywords)
    result["is_vascular"] = is_vascular

    # ── RCRI criteria (parse ✅ Presente / ❌ Ausente from the table) ───────
    def _criterion_present(pattern: str) -> bool:
        """
        Search for the criterion row in the assistant text and check if it is
        marked ✅ Presente (True) or ❌ Ausente (False).
        Only inspects the single table row or heading line where the criterion
        label appears — never bleeds into the next row.
        Falls back to False if not found.
        """
        m = re.search(pattern, assistant_text, re.IGNORECASE)
        if not m:
            return False
        # Extract only the single line / table row containing this criterion label.
        # A table row ends at the next newline; a heading ends at \n too.
        line_start = assistant_text.rfind("\n", 0, m.start()) + 1
        line_end = assistant_text.find("\n", m.end())
        if line_end == -1:
            line_end = len(assistant_text)
        row = assistant_text[line_start:line_end]
        if "✅" in row and "presente" in row.lower():
            return True
        if "❌" in row and "ausente" in row.lower():
            return False
        # Fallback: bare checkmark with no explicit "Presente"/"Ausente" label
        return "✅" in row and "❌" not in row

    result["rcri_high_risk_surgery"] = _criterion_present(r"C1\s*[—\-]")
    result["rcri_ischemic_heart"]    = _criterion_present(r"C2\s*[—\-]")
    result["rcri_heart_failure"]     = _criterion_present(r"C3\s*[—\-]")
    result["rcri_cerebrovascular"]   = _criterion_present(r"C4\s*[—\-]")
    result["rcri_insulin_diabetes"]  = _criterion_present(r"C5\s*[—\-]")
    result["rcri_creatinine_above_2"]= _criterion_present(r"C6\s*[—\-]")

    # ── Surgery risk ──────────────────────────────────────────────────────
    if is_vascular:
        result["surgery_risk"] = "high"
        result["surgery_type"] = "peripheral_open"
    else:
        # Infer surgery type / risk from detected surgery name
        sn = result.get("surgery_name", "").lower()
        if any(k in sn for k in ["colecistectomia", "gastrectomia", "colectomia",
                                   "histerectomia", "esplenectomia", "nefrectomia"]):
            result["surgery_risk"] = "intermediate"
            result["surgery_type"] = "intraperitoneal"
        elif any(k in sn for k in ["pneumectomia", "lobectomia"]):
            result["surgery_risk"] = "high"
            result["surgery_type"] = "intrathoracic"
        else:
            result["surgery_risk"] = "intermediate"
            result["surgery_type"] = "intraperitoneal"

    # ── AAS ───────────────────────────────────────────────────────────────
    if "aas" in combined or "aspirina" in combined or "ácido acetilsalicílico" in combined:
        result["uses_aas"] = True
        # AVC/DAC/stent = secondary; no clear event = primary
        if any(k in combined for k in ["avc", "infarto", "stent", "coroná", "revasculariza"]):
            result["aas_prevention"] = "secondary"
        else:
            result["aas_prevention"] = "primary"

    # ── Insulin ───────────────────────────────────────────────────────────
    if "insulina" in combined or "insulinoterapia" in combined:
        result["rcri_insulin_diabetes"] = True  # override if parsing missed it

    return result


def extract_report_data(messages: list[dict]) -> dict:
    """
    Extract structured patient data from the conversation history to feed
    into calculate_risk().

    Strategy (fastest-first, most reliable):
      1. Directly parse the assistant's own structured Markdown response
         (deterministic, no GPU required, works even with tiny local LLM).
      2. If the parse result looks incomplete (no RCRI flags set), fall back to
         asking the LLM to produce a JSON extraction using EXTRACTION_SYSTEM_PROMPT.
    """
    # ── Step 1: deterministic parse ───────────────────────────────────────
    extracted = _parse_assistant_response(messages)

    # Check if the parse captured meaningful RCRI data
    rcri_flags = [
        "rcri_high_risk_surgery", "rcri_ischemic_heart", "rcri_heart_failure",
        "rcri_cerebrovascular", "rcri_insulin_diabetes", "rcri_creatinine_above_2",
    ]
    has_rcri_data = any(extracted.get(f) for f in rcri_flags)

    # ── Step 2: LLM fallback (only when deterministic parse yielded nothing) ─
    if not has_rcri_data and not extracted.get("is_vascular"):
        conversation_text = "\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
            if m.get("content", "").strip()
        )
        extraction_messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Extraia os dados clínicos estruturados da seguinte conversa médica. "
                    "Retorne APENAS o JSON sem nenhum texto adicional:\n\n"
                    + conversation_text
                ),
            },
        ]
        if os.environ.get("OPENAI_API_KEY", ""):
            try:
                raw = _generate_openai(extraction_messages)
            except Exception:
                raw = ""
        else:
            raw = _generate_local(extraction_messages)

        llm_data = _parse_json_from_llm(raw)
        # Merge: LLM data fills gaps, but deterministic parse takes precedence
        for k, v in llm_data.items():
            if k not in extracted:
                extracted[k] = v

    # ── Post-process: auto-derive vsg_age_range from age ─────────────────
    age = extracted.get("age")
    if age is not None and not extracted.get("vsg_age_range"):
        if age >= 80:
            extracted["vsg_age_range"] = "gte80"
        elif age >= 70:
            extracted["vsg_age_range"] = "70_79"
        elif age >= 60:
            extracted["vsg_age_range"] = "60_69"
        else:
            extracted["vsg_age_range"] = "lt60"

    # ── Ensure required defaults so calculate_risk never fails ────────────
    defaults = {
        "surgery_risk": "intermediate",
        "surgery_type": "intraperitoneal",
        "is_vascular": False,
        "mets": 4,
        "functional_activities": [],
        "warfarin_indication": "",
        "aas_prevention": "",
        "vsg_age_range": "lt60",
        "warfarin_chadsvasc": None,
        "warfarin_stroke_3m": False,
        "warfarin_vte_timing": "",
        "warfarin_thrombophilia": "none",
        "warfarin_active_neoplasia": False,
    }
    for key, val in defaults.items():
        extracted.setdefault(key, val)

    return extracted


def _detect_calc_intent(text: str) -> bool:
    t = text.lower()
    keywords = (
        "calculo", "cálculo", "rcri", "vsg", "risco", "mace",
        "pontuacao", "pontuação", "classificacao", "classificação",
    )
    return any(k in t for k in keywords)


def _looks_like_clinical_case(text: str) -> bool:
    """Heuristic for messages that likely contain a perioperative risk case."""
    t = text.lower()
    has_age = re.search(r"\b\d{1,3}\s*anos\b", t) is not None
    has_surgery = any(
        k in t
        for k in (
            "cirurgia", "colecistectomia", "colectomia", "gastrectomia",
            "histerectomia", "nefrectomia", "pneumectomia", "lobectomia",
            "endarterectomia", "angioplastia", "revasculariza", "aorta", "carot",
        )
    )
    has_clinical_signal = any(
        k in t
        for k in (
            "avc", "ait", "diabetes", "insulina", "insulinoterapia", "creatinina",
            "infarto", "angina", "insuficiencia cardiaca", "insuficiência cardíaca",
            "has", "hipertens",
        )
    )
    return has_age and has_surgery and has_clinical_signal


def _extract_patient_from_text(text: str) -> dict:
    """Lightweight deterministic extractor for core RCRI/VSG criteria."""
    t = text.lower()

    # Core defaults so calculate_risk works reliably.
    data = {
        "name": None,
        "age": None,
        "surgery_name": "",
        "surgery_type": "intraperitoneal",
        "surgery_risk": "intermediate",
        "is_vascular": False,
        "mets": 4,
        "functional_activities": [],
        # RCRI
        "rcri_high_risk_surgery": False,
        "rcri_ischemic_heart": False,
        "rcri_heart_failure": False,
        "rcri_cerebrovascular": False,
        "rcri_insulin_diabetes": False,
        "rcri_creatinine_above_2": False,
        # VSG
        "vsg_age_range": "lt60",
        "vsg_cad": False,
        "vsg_chf": False,
        "vsg_copd": False,
        "vsg_creatinine_over_1_8": False,
        "vsg_smoking": False,
        "vsg_insulin_diabetes": False,
        "vsg_chronic_beta_blocker": False,
        "vsg_prior_revasc": False,
        # Active conditions default false
        "cv_acute_coronary": False,
        "cv_unstable_aortic": False,
        "cv_acute_pulmonary_edema": False,
        "cv_cardiogenic_shock": False,
        "cv_hf_nyha_3_4": False,
        "cv_angina_ccs_3_4": False,
        "cv_severe_arrhythmia": False,
        "cv_uncontrolled_hypertension": False,
        "cv_af_high_rate": False,
        "cv_pulmonary_hypertension": False,
        "cv_severe_valvular": False,
        # Additional tags
        "uses_aas": (" aas" in f" {t}" or "aspirina" in t),
        "aas_prevention": "secondary" if any(x in t for x in ("avc", "infarto", "stent", "dac", "coronari")) else "",
        "uses_clopidogrel": ("clopidogrel" in t),
        "uses_ticagrelor": ("ticagrelor" in t),
        "uses_prasugrel": ("prasugrel" in t),
        "uses_warfarin": ("warfar" in t),
        "warfarin_indication": "",
        "known_hf": False,
        "known_valvular_disease": False,
        "known_cad": False,
        "obesity": ("obes" in t),
    }

    age_match = re.search(r"\b(\d{1,3})\s*anos\b", t)
    if age_match:
        age = int(age_match.group(1))
        data["age"] = age
        if age >= 80:
            data["vsg_age_range"] = "gte80"
        elif age >= 70:
            data["vsg_age_range"] = "70_79"
        elif age >= 60:
            data["vsg_age_range"] = "60_69"

    # Surgery mapping
    if any(k in t for k in ("colecistectomia", "colectomia", "gastrectomia", "histerectomia", "esplenectomia", "nefrectomia")):
        data["surgery_type"] = "intraperitoneal"
        data["surgery_risk"] = "intermediate"
        data["rcri_high_risk_surgery"] = True
    if any(k in t for k in ("pneumectomia", "lobectomia", "toracotomia", "intratorac")):
        data["surgery_type"] = "intrathoracic"
        data["surgery_risk"] = "high"
        data["rcri_high_risk_surgery"] = True

    vascular_terms = (
        "cirurgia vascular", "bypass femoro", "femoropopl", "endarterectomia",
        "angioplastia", "aorta", "carot", "revasculariza", "amputa",
    )
    if any(k in t for k in vascular_terms):
        data["is_vascular"] = True
        data["surgery_type"] = "peripheral_open"
        data["surgery_risk"] = "high"
        data["rcri_high_risk_surgery"] = False

    # RCRI criteria
    data["rcri_ischemic_heart"] = any(k in t for k in ("dac", "angina", "infarto", "stent", "revascularizacao miocard"))
    data["rcri_heart_failure"] = any(k in t for k in ("insuficiencia cardiaca", "insuficiência cardíaca", "ic congestiva", "icc", "feve"))
    data["rcri_cerebrovascular"] = any(k in t for k in ("avc", "ait", "cerebrovascular"))
    data["rcri_insulin_diabetes"] = any(k in t for k in ("insulinoterapia", "insulina"))

    creat_match = re.search(r"creatinin[a|ina]*\s*(?:de|:|=)?\s*([0-9]+[\.,]?[0-9]*)", t)
    if creat_match:
        try:
            val = float(creat_match.group(1).replace(",", "."))
            data["rcri_creatinine_above_2"] = val > 2.0
            data["vsg_creatinine_over_1_8"] = val > 1.8
        except Exception:
            pass

    # VSG criteria mirror core comorbidities when vascular
    data["vsg_cad"] = data["rcri_ischemic_heart"]
    data["vsg_chf"] = data["rcri_heart_failure"]
    data["vsg_insulin_diabetes"] = data["rcri_insulin_diabetes"]
    data["vsg_copd"] = ("dpoc" in t or "copd" in t)
    data["vsg_smoking"] = ("tabag" in t or "fumante" in t)
    data["vsg_chronic_beta_blocker"] = ("betabloque" in t)
    data["vsg_prior_revasc"] = any(k in t for k in ("cabg", "ponte de safena", "revascularizacao miocardica cirurgica"))

    # best-effort surgery free text
    surg_match = re.search(
        r"(colecistectomia[^\.,;\n]*|colectomia[^\.,;\n]*|gastrectomia[^\.,;\n]*|"
        r"histerectomia[^\.,;\n]*|pneumectomia[^\.,;\n]*|lobectomia[^\.,;\n]*|"
        r"endarterectomia[^\.,;\n]*|bypass[^\.,;\n]*|angioplastia[^\.,;\n]*)",
        t,
    )
    if surg_match:
        data["surgery_name"] = surg_match.group(1).strip()

    return data


def _render_deterministic_calc_reply(data: dict, result: dict) -> str:
    name = data.get("name") or "Paciente"
    is_vascular = bool(result.get("is_vascular"))

    if is_vascular:
        intro = (
            "Esta e uma cirurgia VASCULAR -> utilizarei o VSG-CRI "
            "(Vascular Surgery Group Cardiac Risk Index), conforme a Diretriz SBC 2024."
        )
        return (
            f"{intro}\n\n"
            f"**Calculo VSG-CRI - {name}**\n\n"
            f"- Pontuacao total: {result.get('score', 0)} ponto(s)\n"
            f"- Classe: {result.get('score_class', '—')}\n"
            f"- Risco MACE estimado: {result.get('mace_risk_pct', 0)}%\n\n"
            f"Critérios identificados: {', '.join(result.get('criteria_met', [])) or 'Nenhum'}\n"
        )

    c1 = data.get("rcri_high_risk_surgery", False)
    c2 = data.get("rcri_ischemic_heart", False)
    c3 = data.get("rcri_heart_failure", False)
    c4 = data.get("rcri_cerebrovascular", False)
    c5 = data.get("rcri_insulin_diabetes", False)
    c6 = data.get("rcri_creatinine_above_2", False)

    def mark(v: bool) -> str:
        return "✅ Presente" if v else "❌ Ausente"

    return (
        f"**Calculo RCRI - {name}**\n\n"
        f"| Criterio | Resultado |\n"
        f"|---|---|\n"
        f"| C1 - Cirurgia intrap./intratoracica/vasc. suprainguinal | {mark(c1)} |\n"
        f"| C2 - Doenca isquemica cardiaca | {mark(c2)} |\n"
        f"| C3 - Insuficiencia cardiaca congestiva | {mark(c3)} |\n"
        f"| C4 - Doenca cerebrovascular | {mark(c4)} |\n"
        f"| C5 - Diabetes com insulinoterapia | {mark(c5)} |\n"
        f"| C6 - Creatinina > 2,0 mg/dL | {mark(c6)} |\n\n"
        f"**Pontuacao total: {result.get('score', 0)} ponto(s) -> Classe {result.get('score_class', '—')} -> "
        f"Risco MACE estimado: {result.get('mace_risk_pct', 0)}%**\n"
    )


def _try_deterministic_calc_reply(messages: list[dict], last_user_msg: str) -> str | None:
    """Return a deterministic calculation reply when the user asks for risk scoring."""
    if not last_user_msg:
        return None

    user_messages = [
        m.get("content", "")
        for m in messages
        if m.get("role") == "user" and m.get("content", "").strip()
    ]
    conversation_user_text = "\n".join(user_messages)

    explicit_intent = _detect_calc_intent(last_user_msg) or _detect_calc_intent(conversation_user_text)
    case_intent = _looks_like_clinical_case(conversation_user_text)
    if not explicit_intent and not case_intent:
        return None

    data = _extract_patient_from_text(conversation_user_text)

    # Need at least surgery and one clinical clue to be meaningful.
    has_surgery = bool(data.get("surgery_name") or data.get("rcri_high_risk_surgery") or data.get("is_vascular"))
    has_clinical = any(
        data.get(k, False)
        for k in (
            "rcri_ischemic_heart",
            "rcri_heart_failure",
            "rcri_cerebrovascular",
            "rcri_insulin_diabetes",
            "rcri_creatinine_above_2",
            "vsg_cad",
            "vsg_chf",
            "vsg_copd",
        )
    )
    if not has_surgery or not has_clinical:
        return None

    result = calculate_risk(data)
    return _render_deterministic_calc_reply(data, result)


def chat(messages: list[dict]) -> str:
    """
    Process a chat request with RAG-augmented context.

    Flow:
      1. Semantic search finds relevant knowledge chunks (sentence-transformers)
      2. Chunks injected into system prompt
      3. Local transformers model generates the response (or OpenAI fallback)

    Args:
        messages: List of {"role": "user"|"assistant", "content": str}
    """
    # Extract the latest user message for context search
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    if ENABLE_DETERMINISTIC_CALC:
        deterministic_reply = _try_deterministic_calc_reply(messages, last_user_msg)
        if deterministic_reply:
            return deterministic_reply

    # Semantic retrieval
    knowledge = _get_knowledge()
    relevant = _find_relevant_chunks(last_user_msg, knowledge)
    context = _build_context(relevant)

    system_content = SYSTEM_PROMPT
    if context:
        system_content += "\n\n" + context

    model_messages = [{"role": "system", "content": system_content}]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant"):
            model_messages.append({"role": role, "content": content})

    # Use OpenAI if key is configured, otherwise run locally
    if os.environ.get("OPENAI_API_KEY", ""):
        try:
            return _generate_openai(model_messages)
        except Exception as e:
            return f"⚠️ Erro na API OpenAI: {e}"

    return _generate_local(model_messages)
