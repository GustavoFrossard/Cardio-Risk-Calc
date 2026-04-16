"""Generate a comprehensive Markdown report from exhaustive test results.

Outputs: backend/reports/exhaustive_report.md

Run: python backend/tools/generate_exhaustive_report.py
"""
from pathlib import Path
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)

RES_JL = DATA / 'sft_cardiorisk_test_exhaustive_results.jsonl'
DISCREP = DATA / 'exhaustive_discrepancy_report.json'
OUT_MD = REPORTS / 'exhaustive_report.md'


def load_results(path):
    recs = []
    with path.open(encoding='utf-8') as f:
        for line in f:
            recs.append(json.loads(line))
    return recs


def short(obj, depth=1):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2) if depth>0 else str(obj)
    except Exception:
        return str(obj)


def main():
    if not RES_JL.exists():
        print('Results file missing:', RES_JL)
        return 1
    results = load_results(RES_JL)

    # basic aggregations
    total = len(results)
    by_risk = Counter()
    by_index = Counter()
    by_score = Counter()
    errors = []

    for r in results:
        out = r.get('output', {})
        if 'error' in out:
            errors.append({'id': r.get('id'), 'error': out.get('error')})
            continue
        by_risk[out.get('risk_class')] += 1
        by_index[out.get('risk_index')] += 1
        by_score[out.get('score')] += 1

    # load discrepancy report if present
    disc = {}
    if DISCREP.exists():
        disc = json.loads(DISCREP.read_text(encoding='utf-8'))

    # pick sample records for each discrepancy type
    samples = {}
    disc_types = disc.get('discrepancies', {}).keys()
    id_map = {r.get('id'): r for r in results}
    for d in disc_types:
        samples[d] = []
        for s in disc['discrepancies'][d]['samples'][:10]:
            rid = s.get('id')
            rec = id_map.get(rid)
            if rec:
                samples[d].append(rec)

    # build markdown
    md = []
    md.append('# Relatório Completo — Testes Exaustivos da Calculadora CardioRisk')
    md.append('')
    md.append('## Sumário Executivo')
    md.append(f'- Casos avaliados: **{total}**')
    md.append(f'- Erros de execução: **{len(errors)}**')
    md.append('')
    md.append('## Distribuições')
    md.append('### Por `risk_class`')
    md.append('| risk_class | count |')
    md.append('|---:|---:|')
    for k,v in by_risk.items():
        md.append(f'| {k} | {v} |')
    md.append('')
    md.append('### Por `risk_index`')
    md.append('| risk_index | count |')
    md.append('|---:|---:|')
    for k,v in by_index.items():
        md.append(f'| {k} | {v} |')
    md.append('')
    md.append('### Por `score` (top)')
    md.append('| score | count |')
    md.append('|---:|---:|')
    for k,v in sorted(by_score.items(), key=lambda x: -x[1])[:20]:
        md.append(f'| {k} | {v} |')
    md.append('')
    md.append('## Discrepâncias detectadas')
    if not disc:
        md.append('Nenhuma discrepância detectada (arquivo de discrepâncias ausente).')
    else:
        for dname, ddata in disc.get('discrepancies', {}).items():
            md.append(f'### {dname} — count: {ddata.get("count")}')
            md.append('Amostras:')
            md.append('')
            md.append('```json')
            for sample in samples.get(dname, []):
                md.append(json.dumps(sample, ensure_ascii=False))
                md.append('')
            md.append('```')
            md.append('')

    md.append('## Erros de execução (amostras)')
    if errors:
        md.append('```json')
        for e in errors[:10]:
            md.append(json.dumps(e, ensure_ascii=False))
        md.append('```')
    else:
        md.append('- Nenhum erro de execução registrado.')

    md.append('')
    md.append('## Recomendações e Ações Prioritárias')
    md.append('- Verificar **casos com score ≥ 3** que não classificaram como `high` (prioridade alta).')
    md.append('- Conferir lógica de seleção de índice `vsg` vs `rcri` para casos `is_vascular=True`.')
    md.append('- Auditar condutas farmacológicas: casos com `uses_warfarin` sem orientação de varfarina.')
    md.append('- Adicionar testes unitários para os cenários exemplificados neste relatório.')
    md.append('')
    md.append('## Arquivos gerados')
    md.append('- `backend/data/sft_cardiorisk_test_exhaustive.jsonl` — casos gerados')
    md.append('- `backend/data/sft_cardiorisk_test_exhaustive_results.jsonl` — resultados brutos')
    md.append('- `backend/data/exhaustive_discrepancy_report.json` — relatório de discrepâncias (origem deste documento)')
    md.append('- `backend/data/sft_cardiorisk_test_exhaustive_summary.csv` — CSV resumo (distribuições)')

    OUT_MD.write_text('\n'.join(md), encoding='utf-8')
    print('Wrote report to', OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
