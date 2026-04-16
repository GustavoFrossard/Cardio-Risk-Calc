#!/usr/bin/env python3
"""
Clinical holdout evaluation for CardioRisk LoRA model.

Loads base model + LoRA adapter (if provided), runs generation on test prompts,
and computes exact-match metrics for:
- risk_index (rcri/vsg)
- score
- score_class

Usage:
  python evaluate_lora_clinical.py \
    --base-model Qwen/Qwen2.5-0.5B-Instruct \
    --adapter outputs/cardiorisk-lora \
    --test-dataset data/sft_cardiorisk_test.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate clinical correctness on holdout set")
    p.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--adapter", default="outputs/cardiorisk-lora")
    p.add_argument("--test-dataset", default="data/sft_cardiorisk_test.jsonl")
    p.add_argument("--max-samples", type=int, default=40)
    p.add_argument("--max-new-tokens", type=int, default=320)
    p.add_argument("--out", default="outputs/clinical_eval.json")
    return p.parse_args()


def load_rows(path: Path, max_samples: int) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows[:max_samples]


def parse_pred(text: str) -> dict:
    t = text.lower()

    if "vsg" in t or "vsg-cri" in t:
        idx = "vsg"
    elif "rcri" in t:
        idx = "rcri"
    elif "cirurgia vascular" in t:
        idx = "vsg"
    else:
        idx = "rcri"

    score_match = re.search(r"pontua[çc][aã]o\s*total\s*[:\-]?\s*(\d+)", t)
    if not score_match:
        score_match = re.search(r"\b(\d+)\s*ponto", t)
    score = int(score_match.group(1)) if score_match else None

    class_match = re.search(r"classe\s*([ivx]+|alto|intermedi[áa]rio|baixo)", t)
    score_class = class_match.group(1).upper() if class_match else None

    return {
        "risk_index": idx,
        "score": score,
        "score_class": score_class,
    }


def normalize_class(v: str | None) -> str | None:
    if v is None:
        return None
    table = {
        "I": "I",
        "II": "II",
        "III": "III",
        "IV": "IV",
        "BAIXO": "BAIXO",
        "INTERMEDIARIO": "INTERMEDIARIO",
        "INTERMEDIÁRIO": "INTERMEDIARIO",
        "ALTO": "ALTO",
    }
    key = v.strip().upper()
    return table.get(key, key)


def main() -> None:
    args = parse_args()

    test_path = Path(args.test_dataset)
    if not test_path.exists():
        raise FileNotFoundError(f"Dataset de teste não encontrado: {test_path}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )

    adapter_path = Path(args.adapter)
    if adapter_path.exists():
        model = PeftModel.from_pretrained(model, str(adapter_path))

    model.eval()
    rows = load_rows(test_path, args.max_samples)

    n = len(rows)
    hit_index = 0
    hit_score = 0
    hit_class = 0

    details: list[dict] = []

    for row in rows:
        msgs = row["messages"]
        labels = row.get("labels", {})

        # Prompt only up to user turn; model must generate assistant answer.
        prompt = tokenizer.apply_chat_template(msgs[:2], tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=0.0,
                repetition_penalty=1.05,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        gen = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        pred = parse_pred(gen)

        exp_idx = labels.get("risk_index")
        exp_score = labels.get("score")
        exp_class = normalize_class(str(labels.get("score_class")))
        pred_class = normalize_class(pred.get("score_class"))

        ok_idx = pred.get("risk_index") == exp_idx
        ok_score = pred.get("score") == exp_score
        ok_class = pred_class == exp_class

        hit_index += int(ok_idx)
        hit_score += int(ok_score)
        hit_class += int(ok_class)

        details.append(
            {
                "case": row.get("meta", {}).get("case_label", ""),
                "expected": {
                    "risk_index": exp_idx,
                    "score": exp_score,
                    "score_class": exp_class,
                },
                "predicted": pred,
                "ok": {
                    "risk_index": ok_idx,
                    "score": ok_score,
                    "score_class": ok_class,
                },
            }
        )

    metrics = {
        "samples": n,
        "accuracy_risk_index": (hit_index / n) if n else 0.0,
        "accuracy_score": (hit_score / n) if n else 0.0,
        "accuracy_score_class": (hit_class / n) if n else 0.0,
    }

    out = {
        "metrics": metrics,
        "details": details,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OK avaliação clínica concluída")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Relatório: {out_path}")


if __name__ == "__main__":
    main()
