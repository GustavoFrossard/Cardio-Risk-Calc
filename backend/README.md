# CardioRisk Periop — Backend API

FastAPI backend for perioperative cardiovascular risk calculation.

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | App info |
| GET | `/health` | Health check |
| POST | `/calculate` | Calculate perioperative risk |
| GET | `/docs` | Interactive Swagger UI |

## Architecture

```
backend/
├── main.py          # FastAPI app, routes, request/response models
├── calculator.py    # Clinical logic: RCRI scoring, risk adjustment, recommendations
└── requirements.txt
```

### calculator.py modules
- `score_rcri()` — Computes Lee Index score (0–6) and RCRI class (I–IV)
- `adjust_risk()` — Applies AHA/ACC-based adjustments (surgery type, METs, urgency)
- `classify_risk()` — Maps risk % to Low / Intermediate / High
- `analyze_labs()` — Flags abnormal lab values
- `build_recommendations()` — Generates evidence-based clinical recommendations
- `calculate_risk()` — Orchestrates the full pipeline

## References
- Lee TH et al. *Circulation* 1999;100:1043–1049
- Fleisher LA et al. ACC/AHA 2014 Perioperative Guideline. *JACC* 2014
