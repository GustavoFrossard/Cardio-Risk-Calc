"""Parse the provided RCP Excel and produce:
 - backend/data/rcp_template.csv  (template with canonical columns)
 - backend/data/sft_cardiorisk_test_from_excel.jsonl (example record)

This is a helper script to convert the human-oriented sheets into
structured test records for batch validation of `backend/calculator.py`.

Usage: python backend/tools/parse_rcp_excel.py
"""
from pathlib import Path
import re
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
EXCEL = DATA_DIR / 'Risco Cardiovascular Perioperatório.xlsx'

TEMPLATE_COLUMNS = [
    'patient_name', 'age', 'sex', 'surgery_type', 'surgery_class', 'urgency',
    'met_value', 'comorbidities', 'medications', 'clcr', 'creatinine',
    'warfarin', 'doac', 'notes'
]


def extract_key_value_rows(df):
    """Scan dataframe rows and return a dict of detected key->value pairs.

    The sheet is formatted for human reading (labels in one column and values
    in neighbouring columns). This function joins row text and searches for
    common prefixes (e.g. 'Idade:', 'Sexo:', 'Cirurgia proposta:').
    """
    kv = {}
    text_cols = df.astype(str).fillna('').apply(lambda row: ' '.join(row.values), axis=1)
    for t in text_cols:
        # simple patterns
        m = re.search(r'Idade\s*[:\-]\s*(\d{1,3})', t, re.IGNORECASE)
        if m:
            kv['age'] = int(m.group(1))
        m = re.search(r'Nome do Paciente\s*[:\-]\s*(.+)', t, re.IGNORECASE)
        if m:
            kv['patient_name'] = m.group(1).strip()
        m = re.search(r'Sexo\s*[:\-]\s*(Masculino|Feminino|M|F)', t, re.IGNORECASE)
        if m:
            kv['sex'] = m.group(1).strip()
        m = re.search(r'Cirurgia proposta\s*[:\-]\s*(.+)', t, re.IGNORECASE)
        if m:
            kv['surgery_type'] = m.group(1).strip()
        m = re.search(r'ClCr\s*[:\-]\s*([0-9]+\.?[0-9]*)', t, re.IGNORECASE)
        if m:
            kv['clcr'] = float(m.group(1))
        m = re.search(r'Creatinina\s*[:\-]\s*([0-9]+\.?[0-9]*)', t, re.IGNORECASE)
        if m:
            kv['creatinine'] = float(m.group(1))
        # medications line
        if 'Medica' in t or 'Medicações' in t:
            # capture common anticoagulants heuristically
            meds = []
            if re.search(r'varfarina|warfarin', t, re.IGNORECASE):
                meds.append('warfarin')
                kv['warfarin'] = True
            if re.search(r'dabigatran|rivaroxaban|apixaban|edoxaban|doac', t, re.IGNORECASE):
                meds.append('doac')
                kv['doac'] = True
            if meds:
                kv['medications'] = meds
    return kv


def extract_mets(df):
    """Extract METs mapping from Página1 (question -> MET value) and return
    a reasonable MET estimate if a matching question exists later.
    """
    mets = None
    # assume last column contains MET numeric values
    for col in df.columns[::-1]:
        try:
            if pd.to_numeric(df[col], errors='coerce').notna().any():
                # build dict question->value using column 1 as question text
                mapping = {}
                for _, row in df[[df.columns[1], col]].dropna().iterrows():
                    q = str(row[df.columns[1]]).strip()
                    try:
                        v = float(row[col])
                    except Exception:
                        continue
                    mapping[q] = v
                return mapping
        except Exception:
            continue
    return {}


def build_template_and_example(extracted):
    """Create template CSV and a single example JSONL record using extracted keys."""
    template_path = DATA_DIR / 'rcp_template.csv'
    example_jl = DATA_DIR / 'sft_cardiorisk_test_from_excel.jsonl'

    # write template header if not exists
    if not template_path.exists():
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(','.join(TEMPLATE_COLUMNS) + '\n')

    # prepare example row
    row = {c: '' for c in TEMPLATE_COLUMNS}
    row.update({
        'patient_name': extracted.get('patient_name', ''),
        'age': extracted.get('age', ''),
        'sex': extracted.get('sex', ''),
        'surgery_type': extracted.get('surgery_type', ''),
        'clcr': extracted.get('clcr', ''),
        'creatinine': extracted.get('creatinine', ''),
        'medications': ';'.join(extracted.get('medications', [])) if extracted.get('medications') else '',
        'warfarin': bool(extracted.get('warfarin', False)),
        'doac': bool(extracted.get('doac', False)),
        'notes': 'Generated from RCP Excel'
    })

    # append example to CSV (as one line)
    with open(template_path, 'a', encoding='utf-8') as f:
        values = [str(row.get(c, '')).replace(',', ';') for c in TEMPLATE_COLUMNS]
        f.write(','.join(values) + '\n')

    # write JSONL example
    with open(example_jl, 'w', encoding='utf-8') as f:
        json.dump(row, f, ensure_ascii=False)
        f.write('\n')

    return template_path, example_jl


def main():
    if not EXCEL.exists():
        print(f'Excel not found at {EXCEL}. Put the file there and retry.')
        return 1

    xls = pd.read_excel(EXCEL, sheet_name=None, dtype=str)
    extracted = {}

    # parse RCRI and VSG-CRI sheets if present
    for name in ('RCRI', 'VSG-CRI'):
        if name in xls:
            kv = extract_key_value_rows(xls[name])
            extracted.update(kv)

    # parse Página1 for METs mapping
    if 'Página1' in xls:
        mets_map = extract_mets(xls['Página1'])
        extracted['mets_map'] = mets_map

    # parse Página2 for binary questions (simple approach)
    if 'Página2' in xls:
        # collect rows that look like questions and options
        qrows = xls['Página2'].astype(str).fillna('')
        flags = {}
        for _, row in qrows.iterrows():
            text = ' '.join(row.values)
            if 'Procedimento Cirúrgico de urgência' in text:
                if 'Sim' in text:
                    flags['urgency'] = True
            if 'Paciente apresenta condições cardiovasculares graves' in text:
                flags['severe_cv_condition'] = True if 'Sim' in text else False
        extracted.update(flags)

    template_path, example_jl = build_template_and_example(extracted)
    print('Wrote template:', template_path)
    print('Wrote example JSONL:', example_jl)
    print('Extracted keys:', json.dumps(extracted, ensure_ascii=False)[:1000])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
