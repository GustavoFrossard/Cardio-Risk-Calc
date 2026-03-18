# CardioRisk Periop

Calculadora de risco cardiovascular perioperatório.
Baseado no **Índice de Lee (RCRI)** e nas **diretrizes AHA/ACC 2014**.

---

## Estrutura do Projeto

```
cardiorisk/
├── backend/               # API Python (FastAPI)
│   ├── main.py            # Rotas, modelos Pydantic, CORS
│   ├── calculator.py      # Toda a lógica clínica
│   └── requirements.txt
│
└── frontend/              # App React + TypeScript (Vite)
    ├── src/
    │   ├── types/         # Tipos TypeScript compartilhados
    │   │   └── index.ts
    │   ├── services/      # Camada de comunicação com a API
    │   │   └── api.ts
    │   ├── hooks/         # Lógica de estado do wizard
    │   │   └── useWizard.ts
    │   ├── components/
    │   │   ├── ui/        # Componentes reutilizáveis (Toggle, Card, Input...)
    │   │   │   └── index.tsx
    │   │   ├── steps/     # Telas do wizard
    │   │   │   ├── StepPatientData.tsx
    │   │   │   ├── StepRCRI.tsx
    │   │   │   ├── StepComorbidities.tsx
    │   │   │   └── StepResult.tsx
    │   │   ├── AppHeader.tsx
    │   │   └── BottomBar.tsx
    │   ├── App.tsx        # Orquestrador principal
    │   └── main.tsx       # Entry point + estilos globais
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.json
    └── package.json
```

---

## Setup — Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API disponível em: `http://localhost:8000`
Docs Swagger: `http://localhost:8000/docs`

---

## Setup — Frontend

```bash
cd frontend
cp .env.example .env.local   # configure VITE_API_URL se necessário
npm install
npm run dev
```

App disponível em: `http://localhost:5173`

---

## Arquitetura

### Backend (`calculator.py`)

| Função | Responsabilidade |
|---|---|
| `score_rcri()` | Pontua os 6 critérios do Índice de Lee |
| `adjust_risk()` | Aplica ajustes baseados em AHA/ACC (tipo de cirurgia, METs, urgência) |
| `classify_risk()` | Classifica o risco em Baixo / Intermediário / Alto |
| `analyze_labs()` | Detecta alterações laboratoriais clinicamente relevantes |
| `build_recommendations()` | Gera recomendações clínicas contextuais |
| `calculate_risk()` | Orquestra o pipeline completo |

### Frontend

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Estado | `useWizard.ts` | Navegação entre etapas, submissão para API |
| API | `services/api.ts` | Comunicação HTTP com o backend |
| UI base | `components/ui/` | Componentes reutilizáveis (Toggle, Card, Input, etc.) |
| Telas | `components/steps/` | Uma tela por etapa do wizard |
| Tipos | `types/index.ts` | Contratos TypeScript compartilhados |

---

## Endpoint Principal

**POST `/calculate`**

```json
{
  "surgery_risk": "high",
  "urgency": "elective",
  "mets": 3,
  "rcri_coronary_artery_disease": true,
  "rcri_heart_failure": true,
  "rcri_renal_insufficiency": true,
  ...
}
```

**Resposta:**

```json
{
  "rcri_score": 3,
  "rcri_class": "III",
  "mace_risk_pct": 8.42,
  "risk_class": "high",
  "risk_label": "Risco Alto",
  "recommendations": [...],
  "risk_factors": [...],
  "lab_flags": []
}
```

---

## Referências Clínicas

- Lee TH et al. *Derivation and prospective validation of a simple index for prediction of cardiac risk of major noncardiac surgery*. Circulation. 1999;100:1043–1049.
- Fleisher LA et al. *2014 ACC/AHA Guideline on Perioperative Cardiovascular Evaluation and Management*. J Am Coll Cardiol. 2014.
