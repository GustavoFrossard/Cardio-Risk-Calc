#!/usr/bin/env python3
"""
Build SFT dataset for CardioRisk chat fine-tuning (Portuguese, clinical domain).

Output format: JSONL with `messages` list (chat-style), ready for TRL SFTTrainer.

Usage:
  python build_sft_dataset.py
  python build_sft_dataset.py --out data/sft_cardiorisk.jsonl --seed 42
"""

from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

from calculator import calculate_risk
from generate_case_examples import build_profiles


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def _status(flag: bool) -> str:
    return "Presente" if flag else "Ausente"


def _mk_rcri_answer(case_label: str, data: dict, result: dict) -> str:
    c1 = _status(bool(data.get("rcri_high_risk_surgery", False)))
    c2 = _status(bool(data.get("rcri_ischemic_heart", False)))
    c3 = _status(bool(data.get("rcri_heart_failure", False)))
    c4 = _status(bool(data.get("rcri_cerebrovascular", False)))
    c5 = _status(bool(data.get("rcri_insulin_diabetes", False)))
    c6 = _status(bool(data.get("rcri_creatinine_above_2", False)))

    return (
        f"**Cálculo RCRI — Paciente**\n\n"
        f"Contexto resumido: {case_label}.\n\n"
        f"| Critério | Resultado |\n"
        f"|---|---|\n"
        f"| C1 — Cirurgia intrap./intratorácica/vascular suprainguinal | {c1} |\n"
        f"| C2 — Doença isquêmica cardíaca | {c2} |\n"
        f"| C3 — Insuficiência cardíaca congestiva | {c3} |\n"
        f"| C4 — Doença cerebrovascular | {c4} |\n"
        f"| C5 — Diabetes com insulinoterapia | {c5} |\n"
        f"| C6 — Creatinina > 2,0 mg/dL | {c6} |\n\n"
        f"**Pontuação total: {result['score']} ponto(s) -> Classe {result['score_class']} -> "
        f"Risco MACE estimado: {result['mace_risk_pct']}%**\n\n"
        f"Resumo: {result['risk_label']}."
    )


def _mk_vsg_answer(case_label: str, result: dict) -> str:
    criteria = ", ".join(result.get("criteria_met", [])) or "Nenhum critério pontuado"
    return (
        "Esta é uma cirurgia VASCULAR, portanto o índice correto é o VSG-CRI.\n\n"
        f"**Cálculo VSG-CRI — Paciente**\n\n"
        f"Contexto resumido: {case_label}.\n\n"
        f"- Pontuação total: {result['score']} ponto(s)\n"
        f"- Classe: {result['score_class']}\n"
        f"- Risco MACE estimado: {result['mace_risk_pct']}%\n"
        f"- Critérios pontuados: {criteria}\n\n"
        f"Resumo: {result['risk_label']}."
    )


def _mk_user_prompt(case_label: str) -> str:
    templates = [
        "Gostaria de calcular o risco perioperatório. Caso: {label}.",
        "Faça a estratificação de risco cardiovascular deste caso: {label}.",
        "Me ajude com o cálculo (RCRI/VSG-CRI) para o seguinte cenário: {label}.",
        "Pode calcular o risco cardíaco perioperatório deste paciente? {label}.",
    ]
    template = random.choice(templates)
    return template.format(label=case_label)


def _profile_to_narrative(data: dict) -> str:
    parts: list[str] = []

    age = data.get("age")
    if isinstance(age, int):
        parts.append(f"Paciente de {age} anos")
    else:
        parts.append("Paciente adulto")

    comorb: list[str] = []
    if data.get("rcri_cerebrovascular"):
        comorb.append("antecedente de AVC/AIT")
    if data.get("rcri_ischemic_heart") or data.get("known_cad"):
        comorb.append("doenca arterial coronariana")
    if data.get("rcri_heart_failure") or data.get("known_hf"):
        comorb.append("insuficiencia cardiaca")
    if data.get("rcri_insulin_diabetes"):
        comorb.append("diabetes em uso de insulina")
    if data.get("obesity"):
        comorb.append("obesidade")
    if comorb:
        parts.append("com " + ", ".join(comorb))

    if data.get("is_vascular"):
        parts.append("em programacao de cirurgia vascular")
    elif data.get("rcri_high_risk_surgery"):
        parts.append("em programacao de cirurgia intraperitoneal/intratoracica")
    else:
        parts.append("em programacao de cirurgia nao vascular")

    if data.get("rcri_creatinine_above_2"):
        parts.append("creatinina pre-operatoria acima de 2,0 mg/dL")
    elif data.get("vsg_creatinine_over_1_8"):
        parts.append("creatinina acima de 1,8 mg/dL")

    mets = data.get("mets")
    if isinstance(mets, (int, float)):
        parts.append(f"capacidade funcional estimada em {mets} METs")

    meds: list[str] = []
    if data.get("uses_aas"):
        meds.append("AAS")
    if data.get("uses_clopidogrel"):
        meds.append("clopidogrel")
    if data.get("uses_ticagrelor"):
        meds.append("ticagrelor")
    if data.get("uses_prasugrel"):
        meds.append("prasugrel")
    if data.get("uses_warfarin"):
        meds.append("varfarina")
    if meds:
        parts.append("em uso de " + ", ".join(meds))

    return "; ".join(parts) + "."


def _mk_user_prompt_from_profile(data: dict, case_label: str) -> str:
    narrative = _profile_to_narrative(data)
    templates = [
        "{narrative} Calcule o risco perioperatorio cardiovascular e mostre RCRI/VSG-CRI com pontuacao final.",
        "Tenho este caso clinico: {narrative} Quero o calculo completo do indice correto e o risco MACE.",
        "Analise este paciente para risco perioperatorio: {narrative} Indique criterios positivos e negativos.",
        "{narrative} Faça a estratificacao conforme SBC 2024.",
    ]
    template = random.choice(templates)
    return template.format(narrative=narrative, label=case_label)


def _hard_cases() -> list[dict]:
    """Curated hard cases targeting common model confusions."""
    return [
        {
            "prompt": (
                "Paciente de 67 anos, HAS e diabetes com insulinoterapia, AVC isquemico previo, "
                "em programacao de colecistectomia laparoscopica. Calcule o risco perioperatorio."
            ),
            "data": {
                "is_vascular": False,
                "surgery_type": "intraperitoneal",
                "surgery_risk": "intermediate",
                "mets": 4,
                "rcri_high_risk_surgery": True,
                "rcri_ischemic_heart": False,
                "rcri_heart_failure": False,
                "rcri_cerebrovascular": True,
                "rcri_insulin_diabetes": True,
                "rcri_creatinine_above_2": False,
                "uses_aas": True,
                "aas_prevention": "secondary",
            },
        },
        {
            "prompt": (
                "Colecistectomia por videolaparoscopia e paciente com AVC antigo e insulinoterapia. "
                "Qual indice usar e qual o risco?"
            ),
            "data": {
                "is_vascular": False,
                "surgery_type": "intraperitoneal",
                "surgery_risk": "intermediate",
                "mets": 4,
                "rcri_high_risk_surgery": True,
                "rcri_ischemic_heart": False,
                "rcri_heart_failure": False,
                "rcri_cerebrovascular": True,
                "rcri_insulin_diabetes": True,
                "rcri_creatinine_above_2": False,
            },
        },
        {
            "prompt": (
                "Paciente de 72 anos para bypass femoropopliteo, com DAC e DPOC. "
                "Calcule o risco corretamente."
            ),
            "data": {
                "is_vascular": True,
                "surgery_type": "peripheral_open",
                "surgery_risk": "high",
                "mets": 4,
                "vsg_age_range": "70_79",
                "vsg_cad": True,
                "vsg_chf": False,
                "vsg_copd": True,
                "vsg_creatinine_over_1_8": False,
                "vsg_smoking": False,
                "vsg_insulin_diabetes": False,
                "vsg_chronic_beta_blocker": False,
                "vsg_prior_revasc": False,
            },
        },
        {
            "prompt": (
                "Paciente com AIT previo, sem DAC, sem IC, cirurgia ortopedica de quadril. "
                "Apresente criterios e score."
            ),
            "data": {
                "is_vascular": False,
                "surgery_type": "orthopedic_major",
                "surgery_risk": "intermediate",
                "mets": 4,
                "rcri_high_risk_surgery": False,
                "rcri_ischemic_heart": False,
                "rcri_heart_failure": False,
                "rcri_cerebrovascular": True,
                "rcri_insulin_diabetes": False,
                "rcri_creatinine_above_2": False,
            },
        },
        {
            "prompt": (
                "Paciente de 58 anos com creatinina 3,2 mg/dL para histerectomia abdominal. "
                "Qual score e classe?"
            ),
            "data": {
                "is_vascular": False,
                "surgery_type": "intraperitoneal",
                "surgery_risk": "intermediate",
                "mets": 4,
                "rcri_high_risk_surgery": True,
                "rcri_ischemic_heart": False,
                "rcri_heart_failure": False,
                "rcri_cerebrovascular": False,
                "rcri_insulin_diabetes": False,
                "rcri_creatinine_above_2": True,
            },
        },
        {
            "prompt": (
                "Paciente para cirurgia de catarata, HAS isolada, sem DAC, sem IC, sem AVC, sem DM. "
                "Calcule o risco perioperatorio."
            ),
            "data": {
                "is_vascular": False,
                "surgery_type": "eye",
                "surgery_risk": "low",
                "mets": 5,
                "rcri_high_risk_surgery": False,
                "rcri_ischemic_heart": False,
                "rcri_heart_failure": False,
                "rcri_cerebrovascular": False,
                "rcri_insulin_diabetes": False,
                "rcri_creatinine_above_2": False,
            },
        },
    ]


def _mk_guideline_answer(bullets: list[str], source: str) -> str:
    body = "\n".join([f"- {b}" for b in bullets])
    return (
        "Segundo a Diretriz SBC 2024:\n\n"
        f"{body}\n\n"
        f"Referência: {source}."
    )


def _guideline_facts() -> list[dict]:
    """Structured guideline facts to ground the model on SBC 2024 content."""
    return [
        {
            "prompts": [
                "Quais sao os criterios do RCRI na diretriz SBC 2024?",
                "Liste os 6 componentes do indice RCRI para perioperatorio.",
            ],
            "bullets": [
                "C1: cirurgia intraperitoneal, intratoracica ou vascular suprainguinal.",
                "C2: doenca isquemica cardiaca.",
                "C3: insuficiencia cardiaca congestiva.",
                "C4: doenca cerebrovascular (AVC/AIT).",
                "C5: diabetes em uso de insulina.",
                "C6: creatinina pre-operatoria > 2,0 mg/dL.",
            ],
            "source": "SBC 2024, Figura Central e Tabela 4",
        },
        {
            "prompts": [
                "Como classificar o RCRI em baixo, intermediario e alto risco?",
                "Qual a faixa de classes de risco do RCRI segundo a diretriz?",
            ],
            "bullets": [
                "Risco baixo: RCRI 0-1 (Classes I/II).",
                "Risco intermediario: RCRI 2 (Classe III).",
                "Risco alto: RCRI 3-6 (Classe IV).",
            ],
            "source": "SBC 2024, Figura Central e Tabela 5",
        },
        {
            "prompts": [
                "Quando usar VSG-CRI ao inves de RCRI?",
                "Em qual tipo de cirurgia a diretriz prefere VSG-CRI?",
            ],
            "bullets": [
                "A diretriz recomenda uso preferencial de RCRI na maioria das cirurgias nao cardiacas.",
                "Para cirurgias vasculares arteriais, preferir VSG-CRI por melhor discriminacao de risco.",
                "A escolha do indice deve considerar a natureza vascular ou nao vascular da cirurgia.",
            ],
            "source": "SBC 2024, secao 2.1.4 e Figura Central",
        },
        {
            "prompts": [
                "Qual e a pontuacao por idade no VSG-CRI?",
                "Como a idade entra no VSG-CRI da diretriz?",
            ],
            "bullets": [
                "60-69 anos: +2 pontos.",
                "70-79 anos: +3 pontos.",
                ">= 80 anos: +4 pontos.",
                "< 60 anos: 0 ponto por idade.",
            ],
            "source": "SBC 2024, Tabela 6",
        },
        {
            "prompts": [
                "Quais criterios valem +2 no VSG-CRI?",
                "No VSG-CRI, quais variaveis pontuam dois pontos?",
            ],
            "bullets": [
                "Doenca arterial coronariana: +2.",
                "Insuficiencia cardiaca: +2.",
                "DPOC: +2.",
                "Creatinina > 1,8 mg/dL: +2.",
            ],
            "source": "SBC 2024, Tabela 6",
        },
        {
            "prompts": [
                "Quais criterios valem +1 e -1 no VSG-CRI?",
                "No VSG-CRI, quais sao os fatores de 1 ponto e o fator protetor?",
            ],
            "bullets": [
                "Tabagismo: +1.",
                "Diabetes com insulina: +1.",
                "Uso cronico de betabloqueador: +1.",
                "Revascularizacao miocardica previa: -1.",
            ],
            "source": "SBC 2024, Tabela 6",
        },
        {
            "prompts": [
                "Como classificar o VSG-CRI em baixo, intermediario e alto?",
                "Qual e a classe de risco do VSG-CRI por pontuacao?",
            ],
            "bullets": [
                "Risco baixo: 0-4 pontos.",
                "Risco intermediario: 5-6 pontos.",
                "Risco alto: >= 7 pontos.",
            ],
            "source": "SBC 2024, Figura Central e Tabela 7",
        },
        {
            "prompts": [
                "Quais sao as condicoes cardiovasculares graves/instaveis que podem adiar cirurgia eletiva?",
                "Liste condicoes ativas perioperatorias de alto risco da diretriz.",
            ],
            "bullets": [
                "Sindrome coronariana aguda.",
                "Doencas instaveis da aorta toracica.",
                "Edema agudo de pulmao e choque cardiogenico.",
                "IC NYHA III/IV e angina CCS III/IV.",
                "Estenose aortica/mitral importante sintomatica.",
                "Bradiarritmias/taquiarritmias graves e FA com FC > 120 bpm.",
                "HAS nao controlada > 180 x 110 mmHg.",
                "Hipertensao pulmonar sintomatica.",
            ],
            "source": "SBC 2024, Tabela 2",
        },
        {
            "prompts": [
                "Quando a capacidade funcional deve ser avaliada no pre-operatorio?",
                "Qual e a recomendacao de capacidade funcional na SBC 2024?",
            ],
            "bullets": [
                "Avaliar capacidade funcional em cirurgias de risco intermediario ou alto durante anamnese.",
                "A habilidade de subir dois lances de escada e um marcador pratico recomendado.",
                "Baixa capacidade funcional e associada a maior chance de complicacoes perioperatorias.",
            ],
            "source": "SBC 2024, Quadro 1 e secao 2.1.3",
        },
        {
            "prompts": [
                "Quando pedir ECG pre-operatorio segundo a diretriz?",
                "Quais sao indicacoes principais de eletrocardiograma no pre-operatorio?",
            ],
            "bullets": [
                "Historia/exame fisico sugestivo de doenca cardiovascular.",
                "Cirurgias de risco intrinseco intermediario ou alto.",
                "Pacientes com risco intermediario/alto pelos algoritmos.",
                "Presenca de diabetes melito.",
            ],
            "source": "SBC 2024, Quadro 3",
        },
        {
            "prompts": [
                "Quando solicitar ecocardiograma pre-operatorio?",
                "Quais indicacoes de eco no pre-operatorio de cirurgia nao cardiaca?",
            ],
            "bullets": [
                "IC conhecida/suspeita sem avaliacao recente ou com piora clinica em cirurgia de risco intermediario/alto.",
                "Valvopatia moderada/importante sem avaliacao recente ou com piora clinica.",
                "Candidatos a transplante hepatico.",
                "Nao indicar eco de rotina em assintomaticos sem suspeita de IC/valvopatia relevante.",
            ],
            "source": "SBC 2024, Quadro 4",
        },
        {
            "prompts": [
                "Quando considerar prova funcional para isquemia no pre-operatorio?",
                "Quais sao as recomendacoes para teste funcional com imagem?",
            ],
            "bullets": [
                "Em baixa capacidade funcional e risco intermediario/alto, quando resultado pode mudar conduta.",
                "Nao pedir de rotina em pacientes de baixo risco ou em cirurgia de baixo risco intrinseco.",
                "Solicitacao deve ser criteriosa para evitar atraso desnecessario da cirurgia.",
            ],
            "source": "SBC 2024, Quadro 5 e Quadro 6",
        },
        {
            "prompts": [
                "A cineangiocoronariografia deve ser de rotina antes de cirurgia nao cardiaca?",
                "Quando indicar coronariografia invasiva no pre-operatorio?",
            ],
            "bullets": [
                "Nao e recomendada rotineiramente antes de cirurgia nao cardiaca.",
                "Indicar em SCA de alto risco ou isquemia extensa em prova funcional.",
                "Nao usar em pacientes estaveis submetidos a cirurgia de baixo risco.",
            ],
            "source": "SBC 2024, Quadro 7",
        },
        {
            "prompts": [
                "Qual a conduta da diretriz para cirurgia eletiva com PA 185x112 mmHg?",
                "Quando adiar cirurgia eletiva por pressao arterial?",
            ],
            "bullets": [
                "Em cirurgias eletivas de alto risco, considerar adiar se PAS >= 180 mmHg e/ou PAD >= 110 mmHg.",
                "Durante todo o perioperatorio, evitar hipotensao e otimizar volemia.",
                "Reiniciar anti-hipertensivos no pos-operatorio o mais precocemente possivel.",
            ],
            "source": "SBC 2024, Quadro 9",
        },
        {
            "prompts": [
                "Como manejar anti-hipertensivos cronicos no perioperatorio segundo SBC 2024?",
                "A diretriz recomenda manter ou suspender IECA/BRA, BCC, diureticos e clonidina?",
            ],
            "bullets": [
                "IECA/BRA cronicos podem ser mantidos; suspensao e permitida em casos selecionados.",
                "Bloqueadores de canal de calcio cronicos podem ser mantidos; suspensao selecionada e aceitavel.",
                "Diureticos cronicos podem ser mantidos; suspensao selecionada e aceitavel.",
                "Clonidina cronica deve ser mantida para evitar rebote.",
            ],
            "source": "SBC 2024, Quadro 10",
        },
        {
            "prompts": [
                "AAS em prevencao secundaria deve ser suspenso em toda cirurgia dermatologica?",
                "Qual a orientacao da diretriz para AAS em cirurgia dermatologica?",
            ],
            "bullets": [
                "Nao: para procedimentos dermatologicos, AAS em prevencao secundaria deve ser mantido.",
                "Se DAPT por stent fora de periodo de maior risco trombotico: manter AAS e suspender segundo antiplaquetario.",
                "Em geral, avaliar equilibrio risco trombotico versus risco de sangramento.",
            ],
            "source": "SBC 2024, Quadro 12",
        },
        {
            "prompts": [
                "Quais recomendacoes da diretriz para antitromboticos em procedimentos endoscopicos?",
                "Como manejar antiplaquetarios e anticoagulantes na endoscopia?",
            ],
            "bullets": [
                "Em procedimento endoscopico de baixo risco de sangramento: manter antiplaquetarios e varfarina.",
                "Em alto risco de sangramento: suspender anticoagulacao com varfarina/DOAC.",
                "Monoterapia com AAS para prevencao secundaria geralmente e mantida.",
                "Se DAPT recente e procedimento de alto risco nao pode adiar: manter AAS e suspender segundo antiplaquetario.",
            ],
            "source": "SBC 2024, Quadro 13",
        },
        {
            "prompts": [
                "Quais pacientes se beneficiam de peptideos natriureticos no pre-operatorio?",
                "Quando dosar BNP/NT-proBNP segundo a diretriz?",
            ],
            "bullets": [
                "Pacientes > 65 anos submetidos a cirurgia nao cardiaca.",
                "Pacientes de 45-64 anos com doenca cardiovascular estabelecida ou fator de risco cardiovascular.",
                "A recomendacao e para cirurgia nao cardiaca no contexto de estratificacao perioperatoria.",
            ],
            "source": "SBC 2024, Tabela 1 (Biomarcadores)",
        },
        {
            "prompts": [
                "Qual e a recomendacao de betabloqueador no perioperatorio?",
                "Devo iniciar betabloqueador em alta dose na vespera da cirurgia?",
            ],
            "bullets": [
                "Em uso cronico, betabloqueador deve ser mantido no perioperatorio.",
                "Nao iniciar ou titular em alta dose muito proximo da cirurgia sem tempo de ajuste.",
                "Introducao, quando indicada, deve ter antecedencia para titulacao segura.",
            ],
            "source": "SBC 2024, secao 4.1.1 e Quadro 18",
        },
    ]


def _build_guideline_examples(seed: int) -> list[dict]:
    random.seed(seed + 1000)
    examples: list[dict] = []
    fact_rows = _guideline_facts()

    for fact in fact_rows:
        for prompt in fact["prompts"]:
            examples.append(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Você é assistente clínico da Diretriz SBC 2024. "
                                "Responda em português brasileiro, de forma objetiva e fiel ao texto da diretriz."
                            ),
                        },
                        {"role": "user", "content": prompt},
                        {
                            "role": "assistant",
                            "content": _mk_guideline_answer(fact["bullets"], fact["source"]),
                        },
                    ],
                    "labels": {
                        "risk_index": "guideline",
                        "score": -1,
                        "score_class": "N/A",
                        "mace_risk_pct": -1.0,
                    },
                    "meta": {
                        "case_label": "guideline_fact",
                        "is_vascular": False,
                        "source": fact["source"],
                    },
                }
            )

    return examples


def build_examples(seed: int) -> list[dict]:
    random.seed(seed)
    profiles = build_profiles()
    examples: list[dict] = []

    for raw in profiles:
        item = copy.deepcopy(raw)
        label = item.pop("_label")
        result = calculate_risk(item)

        if result.get("risk_index") == "vsg":
            assistant = _mk_vsg_answer(label, result)
        else:
            assistant = _mk_rcri_answer(label, item, result)

        user = _mk_user_prompt_from_profile(item, label)
        examples.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é assistente clínico de avaliação cardiovascular perioperatória. "
                            "Responda em português brasileiro e use somente RCRI para não-vascular "
                            "e VSG-CRI para vascular."
                        ),
                    },
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": assistant},
                ],
                "labels": {
                    "risk_index": result["risk_index"],
                    "score": result["score"],
                    "score_class": str(result["score_class"]),
                    "mace_risk_pct": float(result["mace_risk_pct"]),
                },
                "meta": {
                    "case_label": label,
                    "is_vascular": bool(result["risk_index"] == "vsg"),
                },
            }
        )

    # Inject curated hard cases with varied user wording.
    for hard in _hard_cases():
        data = copy.deepcopy(hard["data"])
        result = calculate_risk(data)
        if result.get("risk_index") == "vsg":
            assistant = _mk_vsg_answer("Caso dificil curado", result)
        else:
            assistant = _mk_rcri_answer("Caso dificil curado", data, result)

        examples.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é assistente clínico de avaliação cardiovascular perioperatória. "
                            "Responda em português brasileiro e use somente RCRI para não-vascular "
                            "e VSG-CRI para vascular."
                        ),
                    },
                    {"role": "user", "content": hard["prompt"]},
                    {"role": "assistant", "content": assistant},
                ],
                "labels": {
                    "risk_index": result["risk_index"],
                    "score": result["score"],
                    "score_class": str(result["score_class"]),
                    "mace_risk_pct": float(result["mace_risk_pct"]),
                },
                "meta": {
                    "case_label": "hard_case_curated",
                    "is_vascular": bool(result["risk_index"] == "vsg"),
                },
            }
        )

    # Add guideline-first QA pairs to anchor model behavior in SBC 2024 text.
    examples.extend(_build_guideline_examples(seed))

    return examples


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SFT dataset for CardioRisk")
    parser.add_argument("--out", default="data/sft_cardiorisk.jsonl", help="Output JSONL path (full set)")
    parser.add_argument("--out-train", default="data/sft_cardiorisk_train.jsonl")
    parser.add_argument("--out-val", default="data/sft_cardiorisk_val.jsonl")
    parser.add_argument("--out-test", default="data/sft_cardiorisk_test.jsonl")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for prompt variation")
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    args = parser.parse_args()

    out_path = Path(args.out)
    rows = build_examples(seed=args.seed)
    random.Random(args.seed).shuffle(rows)

    n = len(rows)
    n_test = int(n * args.test_ratio)
    n_val = int(n * args.val_ratio)
    n_train = n - n_val - n_test
    if n_train <= 0:
        raise ValueError("Split inválido: treino ficou vazio")

    train_rows = rows[:n_train]
    val_rows = rows[n_train:n_train + n_val]
    test_rows = rows[n_train + n_val:]

    write_jsonl(out_path, rows)
    write_jsonl(Path(args.out_train), train_rows)
    write_jsonl(Path(args.out_val), val_rows)
    write_jsonl(Path(args.out_test), test_rows)

    print(f"OK dataset completo: {out_path} ({len(rows)} exemplos)")
    print(f"OK train: {args.out_train} ({len(train_rows)})")
    print(f"OK val:   {args.out_val} ({len(val_rows)})")
    print(f"OK test:  {args.out_test} ({len(test_rows)})")


if __name__ == "__main__":
    main()
