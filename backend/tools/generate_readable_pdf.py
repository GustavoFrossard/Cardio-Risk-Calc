"""Generate a reader-friendly PDF report highlighting key errors and summaries.

Outputs: `backend/reports/exhaustive_report_readable.pdf`
"""
from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)

REPORT_JSON = DATA / 'exhaustive_discrepancy_report.json'
RESULTS_JL = DATA / 'sft_cardiorisk_test_exhaustive_results.jsonl'
OUT_PDF = REPORTS / 'exhaustive_report_readable.pdf'


def load_json(p):
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))


def load_sample_records(ids, results_path=RESULTS_JL):
    samples = {}
    if not results_path.exists():
        return samples
    lookup = set(ids)
    with results_path.open(encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if obj.get('id') in lookup:
                samples[obj['id']] = obj
                if len(samples) == len(lookup):
                    break
    return samples


def mk_paragraph(text, style):
    return Paragraph(text.replace('\n', '<br/>'), style)


def build_pdf():
    report = load_json(REPORT_JSON) or {}

    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                            rightMargin=20*mm,leftMargin=20*mm,
                            topMargin=20*mm,bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=8)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=14, leading=18, spaceAfter=6)
    body = ParagraphStyle('body', parent=styles['BodyText'], fontSize=11, leading=14)
    mono = ParagraphStyle('mono', parent=styles['Code'], fontSize=9, leading=11)

    story = []

    # Title
    story.append(mk_paragraph('Relatório — Testes Exaustivos da Calculadora CardioRisk', h1))
    story.append(Spacer(1,6))

    # Executive summary
    total = report.get('counts', {}).get('total_cases', 'N/A')
    by_risk = report.get('counts', {}).get('by_risk_class', {})
    summary_lines = [f'<b>Casos avaliados:</b> {total}']
    summary_lines.append(f'<b>Distribuição (risk_class):</b> ' + ', '.join(f'{k}: {v}' for k,v in by_risk.items()))
    story.append(mk_paragraph('<br/>'.join(summary_lines), body))
    story.append(Spacer(1,8))

    # Key Errors section
    story.append(mk_paragraph('Principais Erros Identificados', h2))
    disc = report.get('discrepancies', {})
    if not disc:
        story.append(mk_paragraph('Nenhuma discrepância detectada.', body))
    else:
        # create a small table of discrepancy counts
        data = [['Erro', 'Contagem']]
        for k,v in disc.items():
            data.append([k, str(v.get('count'))])
        t = Table(data, colWidths=[120*mm, 40*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(1,0),colors.HexColor('#d9d9d9')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1,6))

        # For each discrepancy, show up to 3 examples with brief input->output highlights
        for k,v in disc.items():
            story.append(mk_paragraph(f'<b>{k}</b> — {v.get("count")} casos (amostras):', body))
            sample_items = v.get('samples', [])[:3]
            ids = [s.get('id') for s in sample_items]
            samples = load_sample_records(ids)
            for s in sample_items:
                sid = s.get('id')
                rec = samples.get(sid)
                if not rec:
                    continue
                inp = rec.get('input', {})
                out = rec.get('output', {})
                # create a concise bullet-like paragraph
                line = f'ID {sid}: score={out.get("score")} ({out.get("score_class")}), risk_class={out.get("risk_class")}, has_active={out.get("has_active_conditions")}.'
                story.append(mk_paragraph(line, body))
            story.append(Spacer(1,4))

    story.append(Spacer(1,8))

    # Recommendations
    story.append(mk_paragraph('Recomendações Prioritárias', h2))
    recs = [
        '1) Corrigir classificação quando score ≥ 3 resultar em classe diferente de "high" (prioridade alta).',
        '2) Revisar lógica que escolhe entre VSG e RCRI quando `is_vascular=True`.',
        '3) Garantir emissão de condutas para pacientes em uso de varfarina.',
        '4) Adicionar testes unitários cobrindo os exemplos listados.',
    ]
    for r in recs:
        story.append(mk_paragraph('• ' + r, body))

    story.append(Spacer(1,12))

    # Footer with generated file list
    story.append(mk_paragraph('Arquivos gerados: backend/data/sft_cardiorisk_test_exhaustive.jsonl, backend/data/sft_cardiorisk_test_exhaustive_results.jsonl, backend/data/exhaustive_discrepancy_report.json', ParagraphStyle('foot', parent=body, fontSize=9)))

    doc.build(story)
    print('Wrote readable PDF:', OUT_PDF)


if __name__ == '__main__':
    build_pdf()
