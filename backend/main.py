"""
CardioRisk Periop - Backend API
Perioperative Cardiovascular Risk Calculator
Based on: Diretriz Brasileira de Avaliação Cardiovascular Perioperatória,
          RCRI (Lee Index), VSG Cardiac Risk Index
"""

from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from calculator import calculate_risk
from chat_service import (
    chat as chat_service,
    extract_report_data,
    preload_chat_runtime,
)

app = FastAPI(
    title="CardioRisk Periop API",
    description="Perioperative cardiovascular risk calculator based on RCRI, VSG, and Brazilian guidelines.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def preload_chat_models_on_startup():
    """Optional warmup to remove first chat latency after backend boot."""
    raw = os.environ.get("CARDIORISK_CHAT_PRELOAD", "false").strip().lower()
    if raw in ("1", "true", "yes", "y", "on"):
        preload_chat_runtime()


class PatientData(BaseModel):
    # Step 1: Patient info
    name: Optional[str] = Field(None, description="Patient name or identifier")
    age: Optional[int] = Field(None, ge=0, le=120, description="Patient age in years")

    # Comorbidities
    obesity: bool = Field(False)
    known_hf: bool = Field(False, description="Known or suspected heart failure")
    known_valvular_disease: bool = Field(False, description="Known or suspected valvular disease")
    known_cad: bool = Field(False, description="Known or suspected coronary artery disease")

    # Medications
    uses_aas: bool = Field(False)
    aas_prevention: str = Field("", description="'primary' or 'secondary'")
    uses_clopidogrel: bool = Field(False)
    uses_ticagrelor: bool = Field(False)
    uses_prasugrel: bool = Field(False)
    uses_warfarin: bool = Field(False)
    warfarin_indication: str = Field("", description="'af', 'vte', 'mechanical_valve', 'rheumatic'")
    warfarin_chadsvasc: Optional[int] = Field(None, ge=0, le=9)
    warfarin_stroke_3m: bool = Field(False, description="Stroke/TIA in last 3 months")
    warfarin_vte_timing: str = Field("", description="'recent', '3_12m', 'over_12m'")
    warfarin_thrombophilia: str = Field("", description="'severe', 'mild', 'none'")
    warfarin_active_neoplasia: bool = Field(False)

    # Functional capacity
    functional_activities: list[str] = Field(default_factory=list, description="List of checked activity IDs")
    mets: float = Field(4, ge=1, le=12, description="Estimated METs")

    # Step 2: Surgery & cardiovascular conditions
    surgery_type: str = Field("", description="Surgery type identifier")
    surgery_risk: str = Field("", description="'low', 'intermediate', or 'high'")
    is_vascular: bool = Field(False)

    cv_acute_coronary: bool = Field(False)
    cv_unstable_aortic: bool = Field(False)
    cv_acute_pulmonary_edema: bool = Field(False)
    cv_cardiogenic_shock: bool = Field(False)
    cv_hf_nyha_3_4: bool = Field(False)
    cv_angina_ccs_3_4: bool = Field(False)
    cv_severe_arrhythmia: bool = Field(False)
    cv_uncontrolled_hypertension: bool = Field(False)
    cv_af_high_rate: bool = Field(False)
    cv_pulmonary_hypertension: bool = Field(False)
    cv_severe_valvular: bool = Field(False)

    # Step 3: RCRI criteria
    rcri_high_risk_surgery: bool = Field(False)
    rcri_ischemic_heart: bool = Field(False)
    rcri_heart_failure: bool = Field(False)
    rcri_cerebrovascular: bool = Field(False)
    rcri_insulin_diabetes: bool = Field(False)
    rcri_creatinine_above_2: bool = Field(False)

    # Step 3: VSG-CRI criteria (Tabela 6)
    vsg_age_range: str = Field("", description="'lt60', '60_69', '70_79', 'gte80'")
    vsg_cad: bool = Field(False)
    vsg_chf: bool = Field(False)
    vsg_copd: bool = Field(False)
    vsg_creatinine_over_1_8: bool = Field(False)
    vsg_smoking: bool = Field(False)
    vsg_insulin_diabetes: bool = Field(False)
    vsg_chronic_beta_blocker: bool = Field(False)
    vsg_prior_revasc: bool = Field(False)


@app.get("/")
def root():
    return {
        "app": "CardioRisk Periop API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.post("/calculate")
def calculate(patient: PatientData):
    """
    Calculate perioperative cardiovascular risk.
    Returns RCRI score, MACE risk percentage, risk class, and clinical recommendations.
    """
    result = calculate_risk(patient.model_dump())
    return result


@app.get("/health")
def health():
    return {"status": "ok"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatReportRequest(BaseModel):
    messages: list[ChatMessage]


@app.post("/chat/report")
def chat_report(payload: ChatReportRequest):
    """
    Extract structured patient data from chat conversation and generate a risk report.
    Returns {result: RiskResult, patient: {name, age}} ready for PDF generation.
    """
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    extracted = extract_report_data(messages)

    if not extracted:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Não foi possível extrair dados clínicos suficientes da conversa. "
                   "Certifique-se de informar pelo menos: tipo de cirurgia, presença de "
                   "comorbidades (IC, DAC, DCV, diabetes com insulina, creatinina) e "
                   "capacidade funcional.",
        )

    result = calculate_risk(extracted)

    # Use the free-text surgery name from extraction for a richer label
    surgery_name = extracted.get("surgery_name", "")
    if surgery_name:
        result["surgery_label"] = surgery_name

    return {
        "result": result,
        "patient": {
            "name": extracted.get("name"),
            "age": extracted.get("age"),
        },
    }


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Conversation history")


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    RAG-augmented chat endpoint for perioperative cardiovascular risk Q&A.
    Uses local Ollama model by default (no API key needed).
    """
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    reply = chat_service(msgs)
    return ChatResponse(content=reply)
