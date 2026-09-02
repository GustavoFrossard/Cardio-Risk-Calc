"""
CardioRisk Periop - Backend API
Perioperative Cardiovascular Risk Calculator
Based on: Diretriz Brasileira de Avaliação Cardiovascular Perioperatória,
          RCRI (Lee Index), VSG Cardiac Risk Index
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Optional
from core.calculator import calcular_risco
from core.clinical_nlp import analisar_texto_clinico

app = FastAPI(
    title="CardioRisk Periop API",
    description="Perioperative cardiovascular risk calculator based on RCRI, VSG, and Brazilian guidelines.",
    version="2.0.0",
)

def _cors_origins_from_env() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS")
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://cardio-risk-calc.vercel.app",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DadosPaciente(BaseModel):
    # Step 1: Patient info
    nome: Optional[str] = Field(None, description="Nome ou identificador do paciente")
    idade: Optional[int] = Field(None, ge=0, le=120, description="Idade do paciente em anos")

    # Comorbidades
    obesidade: bool = Field(False)
    ic_conhecida: bool = Field(False, description="Insuficiência cardíaca conhecida ou suspeita")
    doenca_valvar_conhecida: bool = Field(False, description="Doença valvar conhecida ou suspeita")
    dac_conhecida: bool = Field(False, description="Doença arterial coronariana conhecida ou suspeita")
    eco_recente: bool = Field(False, description="Ecocardiograma recente (< 6 meses)")
    piora_sintomas: bool = Field(False, description="Piora dos sintomas")

    # Medicamentos
    usa_aas: bool = Field(False)
    prevencao_aas: str = Field("", description="'primary' ou 'secondary'")
    usa_clopidogrel: bool = Field(False)
    usa_ticagrelor: bool = Field(False)
    usa_prasugrel: bool = Field(False)
    usa_varfarina: bool = Field(False)
    indicacao_varfarina: str = Field("", description="'af', 'vte', 'mechanical_valve', 'rheumatic'")
    chadsvasc_varfarina: Optional[int] = Field(None, ge=0, le=9)
    avc_3m_varfarina: bool = Field(False, description="AVC/AIT nos últimos 3 meses")
    tempo_tev_varfarina: str = Field("", description="'recent', '3_12m', 'over_12m'")
    trombofilia_varfarina: str = Field("", description="'severe', 'mild', 'none'")
    neoplasia_ativa_varfarina: bool = Field(False)

    # Capacidade funcional
    atividades_funcionais: list[str] = Field(default_factory=list, description="Lista de IDs de atividades marcadas")
    mets: float = Field(4, ge=1, le=12, description="METs estimados")

    # Step 2: Cirurgia e condições cardiovasculares
    tipo_cirurgia: str = Field("", description="Identificador do tipo de cirurgia")
    risco_cirurgia: str = Field("", description="'baixo', 'intermediario' ou 'alto'")
    eh_vascular: bool = Field(False)

    cv_coronaria_aguda: bool = Field(False)
    cv_aorta_instavel: bool = Field(False)
    cv_edema_pulmonar_agudo: bool = Field(False)
    cv_choque_cardiogenico: bool = Field(False)
    cv_ic_nyha_3_4: bool = Field(False)
    cv_angina_ccs_3_4: bool = Field(False)
    cv_arritmia_grave: bool = Field(False)
    cv_has_nao_controlada: bool = Field(False)
    cv_fa_alta_resposta: bool = Field(False)
    cv_hap_sintomatica: bool = Field(False)
    cv_valvopatia_grave: bool = Field(False)

    # Step 3: Critérios RCRI
    rcri_cirurgia_alto_risco: bool = Field(False)
    rcri_doenca_coronaria: bool = Field(False)
    rcri_ic: bool = Field(False)
    rcri_cerebrovascular: bool = Field(False)
    rcri_diabetes_insulina: bool = Field(False)
    rcri_creatinina_acima_2: bool = Field(False)

    # Step 3: Critérios VSG-CRI (Tabela 6)
    vsg_faixa_etaria: str = Field("", description="'lt60', '60_69', '70_79', 'gte80'")
    vsg_dac: bool = Field(False)
    vsg_ic: bool = Field(False)
    vsg_dpoc: bool = Field(False)
    vsg_creatinina_acima_1_8: bool = Field(False)
    vsg_tabagismo: bool = Field(False)
    vsg_diabetes_insulina: bool = Field(False)
    vsg_betabloqueador_cronico: bool = Field(False)
    vsg_revasc_previa: bool = Field(False)


class RequisicaoTextoClinico(BaseModel):
    text: str = Field(..., min_length=5, description="Texto clínico livre")
    current_data: dict[str, Any] = Field(default_factory=dict)


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "app": "CardioRisk Periop API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.post("/calculate")
def calculate(paciente: DadosPaciente):
    """
    Calcula o risco cardiovascular perioperatório.
    Retorna pontuação RCRI, percentual de risco MACE, classe de risco e recomendações clínicas.
    """
    resultado = calcular_risco(paciente.model_dump())
    return resultado


@app.post("/nlp/analyze")
def analyze_clinical_case(payload: RequisicaoTextoClinico):
    """
    Analisa texto clínico livre e infere campos da calculadora.
    Retorna campos inferidos, informações críticas ausentes e entidades NER opcionais.
    """
    return analisar_texto_clinico(payload.text, payload.current_data)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
