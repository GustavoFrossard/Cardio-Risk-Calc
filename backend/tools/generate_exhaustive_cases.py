"""Generate synthetic test cases and run the calculator on them.

Produces:
 - backend/data/sft_cardiorisk_test_exhaustive.jsonl
 - backend/data/sft_cardiorisk_test_exhaustive_results.jsonl
 - backend/data/sft_cardiorisk_test_exhaustive_summary.csv

This script creates 1000 varied cases covering edge conditions and random
combinations to exercise the calculator logic.
"""
from pathlib import Path
import json
import random
import csv

from backend.calculator import calculate_risk

OUT_DIR = Path(__file__).resolve().parents[1] / 'data'
OUT_DIR.mkdir(parents=True, exist_ok=True)

N = 1000
random.seed(42)

ages = [18, 30, 45, 55, 65, 75, 82]
sexes = ['Masculino', 'Feminino']
surgery_risks = ['low', 'intermediate', 'high']
is_vascular_options = [False, True]
mets_values = [1, 2.7, 2.75, 3.5, 4.5, 5.25, 5.5, 6, 7.5, 8]
creatinine_values = [0.7, 1.0, 1.6, 1.9, 2.1, 3.0]
clcr_values = [90, 60, 45, 30, 15]

meds_pool = ['warfarin', 'doac', 'aas', 'clopidogrel', 'ticagrelor', 'prasugrel']


def make_case(i):
    case = {}
    case['id'] = i
    case['patient_name'] = f'TestCase{i}'
    case['age'] = random.choice(ages)
    case['sex'] = random.choice(sexes)
    case['surgery_risk'] = random.choices(surgery_risks, weights=[0.2,0.6,0.2])[0]
    case['is_vascular'] = random.choices(is_vascular_options, weights=[0.8,0.2])[0]
    case['mets'] = random.choice(mets_values)

    # RCRI boolean criteria (6 items) — create some edge cases
    # We'll sometimes force high-score cases
    if i < 10:
        # ensure some high RCRI (>=3)
        case.update({
            'rcri_high_risk_surgery': True,
            'rcri_ischemic_heart': True,
            'rcri_heart_failure': True,
            'rcri_cerebrovascular': False,
            'rcri_insulin_diabetes': False,
            'rcri_creatinine_above_2': False,
        })
    else:
        case['rcri_high_risk_surgery'] = random.random() < 0.15
        case['rcri_ischemic_heart'] = random.random() < 0.12
        case['rcri_heart_failure'] = random.random() < 0.08
        case['rcri_cerebrovascular'] = random.random() < 0.05
        case['rcri_insulin_diabetes'] = random.random() < 0.1
        case['rcri_creatinine_above_2'] = random.random() < 0.03

    # VSG fields (only meaningful if is_vascular)
    if case['is_vascular']:
        case['vsg_age_range'] = random.choice(['<60','60_69','70_79','gte80'])
        case['vsg_cad'] = random.random() < 0.15
        case['vsg_chf'] = random.random() < 0.08
        case['vsg_copd'] = random.random() < 0.1
        case['vsg_creatinine_over_1_8'] = random.choice([False, True]) if random.random() < 0.08 else False
        case['vsg_smoking'] = random.random() < 0.2
        case['vsg_insulin_diabetes'] = random.random() < 0.1
        case['vsg_chronic_beta_blocker'] = random.random() < 0.05
        case['vsg_prior_revasc'] = random.random() < 0.03
    else:
        # keep keys absent or False
        case.update({
            'vsg_age_range': '', 'vsg_cad': False, 'vsg_chf': False,
            'vsg_copd': False, 'vsg_creatinine_over_1_8': False,
            'vsg_smoking': False, 'vsg_insulin_diabetes': False,
            'vsg_chronic_beta_blocker': False, 'vsg_prior_revasc': False,
        })

    # Active cardiovascular conditions — rare but included
    case['cv_acute_coronary'] = random.random() < 0.01
    case['cv_unstable_aortic'] = random.random() < 0.005
    case['cv_acute_pulmonary_edema'] = random.random() < 0.005
    case['cv_cardiogenic_shock'] = random.random() < 0.002
    case['cv_hf_nyha_3_4'] = random.random() < 0.01
    case['cv_angina_ccs_3_4'] = random.random() < 0.01
    case['cv_severe_arrhythmia'] = random.random() < 0.005
    case['cv_uncontrolled_hypertension'] = random.random() < 0.01
    case['cv_af_high_rate'] = random.random() < 0.01
    case['cv_pulmonary_hypertension'] = random.random() < 0.003
    case['cv_severe_valvular'] = random.random() < 0.005

    # medications
    meds = set()
    if random.random() < 0.08:
        meds.add('warfarin')
        case['uses_warfarin'] = True
        # give some warfarin context
        case['warfarin_indication'] = random.choice(['af','vte','mechanical_valve','rheumatic',''])
        case['warfarin_chadsvasc'] = random.choice([0,1,2,3,4,5,6])
        case['warfarin_stroke_3m'] = random.random() < 0.05
    else:
        case['uses_warfarin'] = False

    if random.random() < 0.12:
        meds.add('doac')
        case['doac'] = True
        case['uses_doac'] = True
    else:
        case['uses_doac'] = False

    if random.random() < 0.15:
        meds.add('aas')
        case['uses_aas'] = True
        case['aas_prevention'] = random.choice(['primary','secondary'])
    else:
        case['uses_aas'] = False

    if random.random() < 0.03:
        meds.add('clopidogrel'); case['uses_clopidogrel'] = True
    else:
        case['uses_clopidogrel'] = False

    if random.random() < 0.02:
        meds.add('ticagrelor'); case['uses_ticagrelor'] = True
    else:
        case['uses_ticagrelor'] = False

    if random.random() < 0.01:
        meds.add('prasugrel'); case['uses_prasugrel'] = True
    else:
        case['uses_prasugrel'] = False

    case['medications'] = list(meds)

    # kidney markers
    case['creatinine'] = random.choice(creatinine_values)
    case['clcr'] = random.choice(clcr_values)

    return case


def main():
    out_jl = OUT_DIR / 'sft_cardiorisk_test_exhaustive.jsonl'
    results_jl = OUT_DIR / 'sft_cardiorisk_test_exhaustive_results.jsonl'
    summary_csv = OUT_DIR / 'sft_cardiorisk_test_exhaustive_summary.csv'

    cases = [make_case(i) for i in range(1, N+1)]

    # write cases
    with out_jl.open('w', encoding='utf-8') as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    # run calculator and collect summary
    with results_jl.open('w', encoding='utf-8') as rf, summary_csv.open('w', newline='', encoding='utf-8') as sf:
        writer = csv.writer(sf)
        writer.writerow(['id','risk_index','score','score_class','mace_risk_pct','risk_class','has_active','uses_warfarin','uses_doac','mets','surgery_risk'])
        for c in cases:
            # prepare input mapping expected by calculator
            inp = dict(c)  # shallow copy
            # ensure types
            inp['mets'] = float(inp.get('mets', 4))
            inp['is_vascular'] = bool(inp.get('is_vascular', False))
            try:
                out = calculate_risk(inp)
            except Exception as e:
                out = {'error': str(e)}
            rf.write(json.dumps({'id': c['id'], 'input': inp, 'output': out}, ensure_ascii=False) + '\n')
            if 'error' in out:
                writer.writerow([c['id'],'error','error','error','error','error',str(out.get('error')),c.get('uses_warfarin'),c.get('uses_doac'),c.get('mets'),c.get('surgery_risk')])
            else:
                writer.writerow([c['id'], out.get('risk_index'), out.get('score'), out.get('score_class'), out.get('mace_risk_pct'), out.get('risk_class'), out.get('has_active_conditions'), c.get('uses_warfarin'), c.get('uses_doac'), out.get('mets'), out.get('surgery_risk')])

    # simple distribution print
    print('Wrote', out_jl)
    print('Wrote', results_jl)
    print('Wrote', summary_csv)


if __name__ == '__main__':
    main()
