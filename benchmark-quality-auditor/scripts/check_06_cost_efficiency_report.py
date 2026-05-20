#!/usr/bin/env python3
"""Deterministic structural check for `06_cost_efficiency.json`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "warn", "fail", "manual_review_required"}
VALID_COMPLETENESS = {"full", "partial"}


def fail(errors: list[str]) -> None:
    print("FAIL")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)


def require(cond, msg, errors):
    if not cond:
        errors.append(msg)


def main(path: str) -> None:
    p = Path(path)
    if not p.exists():
        fail([f"report not found: {path}"])
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        fail([f"invalid JSON: {e}"])

    errors: list[str] = []
    require(data.get("dimension") == "06_cost_efficiency", "dimension must equal '06_cost_efficiency'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    verdict = summary.get("verdict")
    require(verdict in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("score"), (int, float)) and 0.0 <= float(summary["score"]) <= 1.0, "summary.score must be numeric in [0,1]", errors)
    require(isinstance(summary.get("headline"), str) and summary["headline"].strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    for key in ["totals", "per_item_cost", "cost_of_signal", "pruning", "llm_judge_comparison"]:
        require(key in checks, f"checks.{key} missing", errors)

    totals = checks.get("totals") or {}
    completeness = totals.get("completeness")
    require(completeness in VALID_COMPLETENESS, f"totals.completeness must be one of {VALID_COMPLETENESS}", errors)
    for k in ["tokens_in_total", "tokens_out_total", "wallclock_s_total"]:
        v = totals.get(k)
        require(isinstance(v, (int, float)) and float(v) >= 0, f"totals.{k} must be a non-negative number", errors)
    missing = totals.get("missing_token_runs")
    require(isinstance(missing, list), "totals.missing_token_runs must be list", errors)
    if completeness == "full" and isinstance(missing, list) and len(missing) > 0:
        errors.append("totals.completeness='full' but missing_token_runs is non-empty")
    if completeness == "partial" and isinstance(missing, list) and len(missing) == 0:
        errors.append("totals.completeness='partial' but missing_token_runs is empty")

    pic = checks.get("per_item_cost") or {}
    require(isinstance(pic.get("mean_tokens_out"), (int, float)) and float(pic.get("mean_tokens_out", -1)) >= 0, "per_item_cost.mean_tokens_out must be non-negative number", errors)
    top5 = pic.get("top5_expensive_items")
    require(isinstance(top5, list), "per_item_cost.top5_expensive_items must be list", errors)
    if isinstance(top5, list):
        require(len(top5) <= 5, "per_item_cost.top5_expensive_items must have at most 5 entries", errors)
        for i, it in enumerate(top5):
            require(isinstance(it, dict) and it.get("problem_id"), f"top5_expensive_items[{i}].problem_id required", errors)
            v = it.get("mean_tokens_out") if isinstance(it, dict) else None
            require(isinstance(v, (int, float)) and float(v) >= 0, f"top5_expensive_items[{i}].mean_tokens_out must be non-negative number", errors)

    cos = checks.get("cost_of_signal") or []
    require(isinstance(cos, list), "cost_of_signal must be list", errors)
    if isinstance(cos, list):
        for i, c in enumerate(cos):
            require(isinstance(c, dict) and c.get("a_run_id") and c.get("b_run_id"), f"cost_of_signal[{i}] requires a_run_id and b_run_id", errors)
            for k in ["score_gap", "tokens_combined", "cost_per_pt"]:
                require(isinstance(c.get(k), (int, float)), f"cost_of_signal[{i}].{k} must be numeric", errors)

    pruning = checks.get("pruning") or {}
    cands = pruning.get("candidates")
    require(isinstance(cands, list) and len(cands) >= 1, "pruning.candidates must be non-empty list", errors)
    any_qualifies = False
    if isinstance(cands, list):
        for i, c in enumerate(cands):
            require(isinstance(c, dict), f"pruning.candidates[{i}] must be object", errors)
            if not isinstance(c, dict):
                continue
            cut = c.get("cut_pct")
            require(isinstance(cut, (int, float)) and 0 <= float(cut) < 100, f"candidates[{i}].cut_pct must be in [0,100)", errors)
            require(isinstance(c.get("kept_items"), int) and c["kept_items"] >= 0, f"candidates[{i}].kept_items must be non-negative int", errors)
            rho = c.get("rho_vs_full")
            require(isinstance(rho, (int, float)) and -1.0 <= float(rho) <= 1.0, f"candidates[{i}].rho_vs_full must be in [-1,1]", errors)
            require(isinstance(c.get("introduces_family_inversion"), bool), f"candidates[{i}].introduces_family_inversion must be boolean", errors)
            if isinstance(rho, (int, float)) and float(rho) >= 0.95 and c.get("introduces_family_inversion") is False:
                any_qualifies = True

    rec_cut = pruning.get("recommended_cut_pct")
    require(isinstance(rec_cut, (int, float)) and 0 <= float(rec_cut) < 100, "pruning.recommended_cut_pct must be in [0,100)", errors)
    kept_ids = pruning.get("recommended_kept_item_ids")
    require(isinstance(kept_ids, list), "pruning.recommended_kept_item_ids must be list", errors)
    if isinstance(rec_cut, (int, float)) and float(rec_cut) > 0 and isinstance(kept_ids, list) and len(kept_ids) == 0:
        errors.append("recommended_cut_pct>0 but recommended_kept_item_ids is empty")
    if isinstance(rec_cut, (int, float)) and float(rec_cut) > 0 and not any_qualifies:
        errors.append("recommended_cut_pct>0 but no candidate has rho_vs_full>=0.95 and no family inversion")

    ljc = checks.get("llm_judge_comparison") or {}
    require(isinstance(ljc.get("used"), bool), "llm_judge_comparison.used must be boolean", errors)
    require(isinstance(ljc.get("cost_of_signal"), list), "llm_judge_comparison.cost_of_signal must be list", errors)
    ljc_cut = ljc.get("recommended_cut_pct")
    require(isinstance(ljc_cut, (int, float)) and 0 <= float(ljc_cut) < 100, "llm_judge_comparison.recommended_cut_pct must be in [0,100)", errors)

    if completeness == "partial" and isinstance(missing, list) and isinstance(totals.get("tokens_in_total"), (int, float)):
        ok_run_count_hint = len(missing) + 0
        if ok_run_count_hint > 0 and verdict != "manual_review_required":
            pass

    require(p.with_suffix(".md").exists(), f"companion markdown report missing: {p.with_suffix('.md').name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_06_cost_efficiency_report.py <path-to-06_cost_efficiency.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
