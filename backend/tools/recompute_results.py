import json
from pathlib import Path
import sys
sys.path.append(r'c:\cardiorisk-project\cardiorisk')
from backend.calculator import calculate_risk

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INPUT = DATA_DIR / "sft_cardiorisk_test_exhaustive.jsonl"
OUT = DATA_DIR / "sft_cardiorisk_test_exhaustive_results.jsonl"

if not INPUT.exists():
    print("Input JSONL not found:", INPUT)
    raise SystemExit(1)

with open(INPUT, "r", encoding="utf-8") as inf, open(OUT, "w", encoding="utf-8") as outf:
    for line in inf:
        rec = json.loads(line)
        res = calculate_risk(rec)
        # keep id/case_id if present
        out = {"id": rec.get("id") or rec.get("case_id"), "input": rec, "output": res}
        outf.write(json.dumps(out, ensure_ascii=False) + "\n")

print("Recomputed results ->", OUT)
