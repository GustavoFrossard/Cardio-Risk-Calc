import json
import csv
from pathlib import Path
import math

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_jsonl(path):
    objs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            objs.append(json.loads(line))
    return objs


def simple_expected_checks(input_rec, result_rec):
    """
    Return list of discrepancy messages based on simple deterministic checks:
    - If score >=3 then risk_class should be 'high'
    - If surgery_is_vascular True then risk_index expected 'vsg'
    - If uses_warfarin True, medication_advice should mention 'warfarin' or 'acenocoumarol' or 'anticoag'
    """
    errs = []

    # support result objects that wrap output under 'output'
    if isinstance(result_rec, dict) and "output" in result_rec:
        result_obj = result_rec["output"]
    else:
        result_obj = result_rec

    score = result_obj.get("score")
    risk_class = result_obj.get("risk_class")
    if score is not None:
        try:
            s = float(score)
            # Determine expected class according to index-specific rules
            risk_index_local = result_obj.get("risk_index") or ("vsg" if input_rec.get("is_vascular") else "rcri")
            if risk_index_local == "rcri":
                if s >= 3 and (risk_class != "high"):
                    errs.append(f"score_ge_3_but_not_high (score={s}, class={risk_class})")
            elif risk_index_local == "vsg":
                # VSG thresholds: >=7 -> high, 5-6 -> intermediate, <5 -> low
                if s >= 7 and (risk_class != "high"):
                    errs.append(f"vsg_score_ge_7_but_not_high (score={s}, class={risk_class})")
                elif 5 <= s < 7 and (risk_class != "intermediate"):
                    errs.append(f"vsg_score_5_6_but_not_intermediate (score={s}, class={risk_class})")
                elif s < 5 and (risk_class != "low"):
                    errs.append(f"vsg_score_lt_5_but_not_low (score={s}, class={risk_class})")
        except Exception:
            pass

    # vascular surgery vs vsg
    surgery_vascular = input_rec.get("surgery_is_vascular") or (str(input_rec.get("surgery_type","")) or "").lower().find("vascular")>=0
    risk_index = result_obj.get("risk_index")
    if surgery_vascular and risk_index != "vsg":
        errs.append(f"vascular_surgery_but_not_vsg (surgery_is_vascular={surgery_vascular}, risk_index={risk_index})")

    # warfarin advice presence (support Portuguese 'varfarina' and list structures)
    meds = input_rec.get("medications") or []
    uses_warfarin = input_rec.get("uses_warfarin") or any([
        "warf" in str(m).lower() or "varf" in str(m).lower() or "acenoc" in str(m).lower()
        for m in meds
    ])

    med_adv_raw = result_rec.get("medication_advice") or result_rec.get("recommendations") or ""
    # normalize medication advice to a single string for search
    if isinstance(med_adv_raw, list):
        parts = []
        for item in med_adv_raw:
            if isinstance(item, dict):
                for k in ("medication", "action", "detail", "title", "body"):
                    v = item.get(k)
                    if v:
                        parts.append(str(v))
            else:
                parts.append(str(item))
        med_adv_l = " ".join(parts).lower()
    else:
        med_adv_l = str(med_adv_raw).lower()

    if uses_warfarin:
        if not ("warf" in med_adv_l or "varf" in med_adv_l or "acenoc" in med_adv_l or "anticoag" in med_adv_l):
            errs.append("uses_warfarin_but_no_warfarin_advice")

    # Antiplatelets / P2Y12 checks
    uses_clop = input_rec.get("uses_clopidogrel") or any(["clop" in str(m).lower() for m in meds])
    uses_tica = input_rec.get("uses_ticagrelor") or any(["ticag" in str(m).lower() for m in meds])
    uses_prasu = input_rec.get("uses_prasugrel") or any(["pras" in str(m).lower() for m in meds])
    uses_aas = input_rec.get("uses_aas") or any(["aspir" in str(m).lower() or "aas" in str(m).lower() for m in meds])

    if uses_clop and "clopidogrel" not in med_adv_l:
        errs.append("uses_clopidogrel_but_no_clopidogrel_advice")
    if uses_tica and "ticagrelor" not in med_adv_l:
        errs.append("uses_ticagrelor_but_no_ticagrelor_advice")
    if uses_prasu and "prasugrel" not in med_adv_l:
        errs.append("uses_prasugrel_but_no_prasugrel_advice")
    if uses_aas and "aas" not in med_adv_l and "aspir" not in med_adv_l:
        errs.append("uses_aas_but_no_aas_advice")

    # DOACs checks (rivaroxaban / apixaban)
    uses_riva = input_rec.get("uses_rivaroxaban") or any(["rivar" in str(m).lower() for m in meds])
    uses_apix = input_rec.get("uses_apixaban") or any(["apix" in str(m).lower() for m in meds])
    uses_dabi = input_rec.get("uses_dabigatran") or any(["dabig" in str(m).lower() for m in meds])

    if uses_riva and "rivaroxab" not in med_adv_l:
        errs.append("uses_rivaroxaban_but_no_advice")
    if uses_apix and "apixab" not in med_adv_l:
        errs.append("uses_apixaban_but_no_advice")

    # Dabigatran specific: check ClCr-driven rule if provided
    if uses_dabi:
        # prefer explicit clcr field in input
        clcr = input_rec.get("clcr")
        high_bleeding = input_rec.get("high_bleeding_risk", False)
        if isinstance(clcr, (int, float)) and clcr < 50 and high_bleeding:
            # expect explicit '4 dias' recommendation
            if "4 dias" not in med_adv_l and "4 dia" not in med_adv_l:
                errs.append("dabigatran_low_clcr_high_bleeding_but_no_4d_advice")
        else:
            # expect 24 or 48h mention
            if not ("24" in med_adv_l or "48" in med_adv_l or "24-48" in med_adv_l or "24–48" in med_adv_l):
                errs.append("dabigatran_no_24_48h_advice")

    return errs


def compare_files(input_jsonl, results_jsonl, out_report_json, out_report_csv):
    inputs = load_jsonl(input_jsonl)
    results = load_jsonl(results_jsonl)

    # build map by id if present, else by index
    inputs_by_id = {}
    for i, rec in enumerate(inputs):
        rid = rec.get("id") or rec.get("case_id") or f"idx_{i}"
        inputs_by_id[str(rid)] = rec

    mismatches = []

    for j, res in enumerate(results):
        rid = str(res.get("id") or res.get("case_id") or f"idx_{j}")
        inp = inputs_by_id.get(rid)
        if not inp:
            # try matching by order
            try:
                inp = inputs[j]
            except Exception:
                inp = {}

        errs = simple_expected_checks(inp, res)
        if errs:
            mismatches.append({"id": rid, "errors": errs, "input": inp, "result": res})

    # write json
    with open(out_report_json, "w", encoding="utf-8") as f:
        json.dump({"total_results": len(results), "mismatch_count": len(mismatches), "mismatches": mismatches}, f, ensure_ascii=False, indent=2)

    # write csv summary
    with open(out_report_csv, "w", newline='', encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["id", "error_summary"])
        for m in mismatches:
            writer.writerow([m["id"], "; ".join(m["errors"])])

    return len(results), len(mismatches)


def main():
    # default paths (adjust if needed)
    input_jsonl = DATA_DIR / "sft_cardiorisk_test_exhaustive.jsonl"
    results_jsonl = DATA_DIR / "sft_cardiorisk_test_exhaustive_results.jsonl"
    out_json = DATA_DIR / "comparison_expected_report.json"
    out_csv = DATA_DIR / "comparison_expected_report_summary.csv"

    if not input_jsonl.exists() or not results_jsonl.exists():
        print("Input or results JSONL not found in backend/data. Please provide correct files or run the batch generator first.")
        return

    total, mism = compare_files(input_jsonl, results_jsonl, out_json, out_csv)
    print(f"Compared {total} results; found {mism} mismatches. Reports saved to:\n  {out_json}\n  {out_csv}")


if __name__ == "__main__":
    main()
