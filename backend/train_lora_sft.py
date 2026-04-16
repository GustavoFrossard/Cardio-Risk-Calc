#!/usr/bin/env python3
"""
LoRA SFT training script for CardioRisk domain adaptation.

Requires additional packages (see requirements-train.txt).

Example:
  python train_lora_sft.py \
    --model Qwen/Qwen2.5-1.5B-Instruct \
    --dataset data/sft_cardiorisk.jsonl \
    --output-dir outputs/cardiorisk-lora
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train LoRA adapter for CardioRisk chat")
    p.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    p.add_argument("--train-dataset", default="data/sft_cardiorisk_train.jsonl")
    p.add_argument("--eval-dataset", default="data/sft_cardiorisk_val.jsonl")
    p.add_argument("--output-dir", default="outputs/cardiorisk-lora")
    p.add_argument("--num-epochs", type=float, default=3.0)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-seq-len", type=int, default=2048)
    p.add_argument("--warmup-steps", type=int, default=10)
    p.add_argument("--logging-steps", type=int, default=10)
    p.add_argument("--save-steps", type=int, default=100)
    p.add_argument("--eval-steps", type=int, default=50)
    p.add_argument("--max-steps", type=int, default=-1)
    return p.parse_args()


def main() -> None:
    args = parse_args()

    try:
        load_dataset = importlib.import_module("datasets").load_dataset
        LoraConfig = importlib.import_module("peft").LoraConfig
        trl_mod = importlib.import_module("trl")
        SFTConfig = trl_mod.SFTConfig
        SFTTrainer = trl_mod.SFTTrainer
    except ModuleNotFoundError as e:
        missing = str(e).split("'")[-2] if "'" in str(e) else str(e)
        raise RuntimeError(
            "Dependência de treino ausente: "
            f"{missing}. Instale com: pip install -r requirements-train.txt"
        ) from e

    train_path = Path(args.train_dataset)
    eval_path = Path(args.eval_dataset)
    if not train_path.exists():
        raise FileNotFoundError(f"Dataset de treino não encontrado: {train_path}")
    if not eval_path.exists():
        raise FileNotFoundError(f"Dataset de validação não encontrado: {eval_path}")

    train_dataset = load_dataset("json", data_files=str(train_path), split="train")
    eval_dataset = load_dataset("json", data_files=str(eval_path), split="train")

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def format_row(row: dict) -> dict:
        text = tokenizer.apply_chat_template(
            row["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    train_dataset = train_dataset.map(format_row, remove_columns=train_dataset.column_names)
    eval_dataset = eval_dataset.map(format_row, remove_columns=eval_dataset.column_names)

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype="auto",
        device_map="auto",
    )

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"],
    )

    use_bf16 = bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())
    use_fp16 = bool(torch.cuda.is_available() and not use_bf16)

    sft_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.num_epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_steps=args.warmup_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        bf16=use_bf16,
        fp16=use_fp16,
        max_length=args.max_seq_len,
        packing=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=peft_config,
        args=sft_args,
    )

    trainer.train()
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print(f"OK LoRA salvo em: {args.output_dir}")


if __name__ == "__main__":
    main()
