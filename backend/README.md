# CardioRisk Periop — Backend API

FastAPI backend for perioperative cardiovascular risk calculation.

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Chat Startup And Logs

Para reduzir o atraso na primeira mensagem do chat e diminuir logs verbosos,
configure no `.env`:

```bash
CARDIORISK_CHAT_PRELOAD=true
CARDIORISK_VERBOSE_MODEL_LOAD=false
CARDIORISK_SUPPRESS_MODEL_WARNINGS=true
```

Se aparecer aviso de requisição não autenticada ao Hugging Face, você pode
definir também:

```bash
HF_TOKEN=hf_xxx
```

## Fine-Tuning LoRA (Sem Hard Code)

Este backend inclui um pipeline para adaptar o modelo ao domínio CardioRisk
com treino supervisionado (SFT + LoRA):

1. Gere o dataset com split train/val/test a partir dos casos sintéticos da calculadora:

```bash
cd backend
python build_sft_dataset.py \
	--out data/sft_cardiorisk.jsonl \
	--out-train data/sft_cardiorisk_train.jsonl \
	--out-val data/sft_cardiorisk_val.jsonl \
	--out-test data/sft_cardiorisk_test.jsonl
```

2. Instale dependências de treino:

```bash
pip install -r requirements-train.txt
```

3. Treine o adaptador LoRA:

```bash
python train_lora_sft.py \
	--model Qwen/Qwen2.5-0.5B-Instruct \
	--train-dataset data/sft_cardiorisk_train.jsonl \
	--eval-dataset data/sft_cardiorisk_val.jsonl \
	--output-dir outputs/cardiorisk-lora \
	--num-epochs 2 \
	--max-steps 120
```

4. Avalie no holdout clínico:

```bash
python evaluate_lora_clinical.py \
	--base-model Qwen/Qwen2.5-0.5B-Instruct \
	--adapter outputs/cardiorisk-lora \
	--test-dataset data/sft_cardiorisk_test.jsonl \
	--out outputs/clinical_eval.json
```

5. (Opcional) Mescle adaptador + modelo base para inferência final.

Observação: em Windows, ajuste batch/grad-accum conforme VRAM disponível.

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
