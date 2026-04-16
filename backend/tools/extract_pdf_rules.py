import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

BASE = Path(__file__).resolve().parents[1]
PDF_PATH = BASE / "data" / "instruções.pdf"
OUT_TEXT = BASE / "data" / "instrucoes_extracted.txt"
OUT_JSON = BASE / "data" / "instrucoes_rules.json"

KEYHEADINGS = [
    "varfarina", "warfarin", "doac", "anticoag", "anticoagulação",
    "aas", "aspirina", "clopidogrel", "ticagrelor", "prasugrel",
    "cirurgia vascular", "vascular", "procedimentos vasculares",
    "lista de cirurgias", "cirurgias"
]


def extract_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    reader = PdfReader(str(pdf_path))
    parts = []
    for p in reader.pages:
        try:
            txt = p.extract_text() or ""
        except Exception:
            txt = ""
        parts.append(txt)
    return "\n\n".join(parts)


def find_sections(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines()]
    joined = "\n".join(lines)

    rules = {"full_text": text, "medication_sections": {}, "vascular_surgeries": []}

    # Find paragraphs containing key headings
    for key in KEYHEADINGS:
        pattern = re.compile(r"(.{0,100}\b" + re.escape(key) + r"\b.{0,200})", flags=re.IGNORECASE)
        matches = pattern.findall(joined)
        if matches:
            rules["medication_sections"][key] = list(dict.fromkeys([m.strip() for m in matches]))

    # Heuristic: collect lines that mention 'vascular' or common vascular procedures
    vascular_keywords = ["vascular", "aorta", "carótida", "carotid", "revasculariza", "bypass", "iliac", "femoral", "arterial", "endarterectomia", "aneurisma", "embolectomia"]
    found = set()
    for ln in lines:
        low = ln.lower()
        for k in vascular_keywords:
            if k in low:
                found.add(ln)
    rules["vascular_surgeries"] = sorted(found)

    # Also capture bullet-like lists (lines starting with - or •)
    bullets = [l for l in lines if l.startswith("-") or l.startswith("•")]
    if bullets:
        rules["bullets"] = bullets

    return rules


def main():
    text = extract_text(PDF_PATH)
    with open(OUT_TEXT, "w", encoding="utf-8") as f:
        f.write(text)

    rules = find_sections(text)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    print("Extracted text to:", OUT_TEXT)
    print("Saved rules JSON to:", OUT_JSON)


if __name__ == '__main__':
    main()
