#!/usr/bin/env python3
"""Deterministic structural check for `04_capability_alignment.json`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "warn", "fail", "manual_review_required"}


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
    require(data.get("dimension") == "04_capability_alignment", "dimension must equal '04_capability_alignment'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    require(summary.get("verdict") in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("score"), (int, float)) and 0.0 <= float(summary["score"]) <= 1.0, "summary.score must be numeric in [0,1]", errors)
    require(isinstance(summary.get("headline"), str) and summary["headline"].strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    fams = checks.get("families_analyzed")
    require(isinstance(fams, list), "checks.families_analyzed must be list", errors)
    if isinstance(fams, list):
        for i, f in enumerate(fams):
            require(isinstance(f, dict) and f.get("family"), f"families_analyzed[{i}].family required", errors)
            if not isinstance(f, dict):
                continue
            ordered = f.get("ordered_runs")
            require(isinstance(ordered, list) and len(ordered) >= 1, f"families_analyzed[{i}].ordered_runs must be a non-empty list", errors)
            if isinstance(ordered, list):
                last_size = -1.0
                for j, r in enumerate(ordered):
                    require(isinstance(r, dict) and r.get("run_id"), f"families_analyzed[{i}].ordered_runs[{j}].run_id required", errors)
                    sz = r.get("size_b") if isinstance(r, dict) else None
                    require(isinstance(sz, (int, float)) and float(sz) > 0, f"families_analyzed[{i}].ordered_runs[{j}].size_b must be positive number", errors)
                    if isinstance(sz, (int, float)):
                        if float(sz) < last_size - 1e-9:
                            errors.append(f"families_analyzed[{i}].ordered_runs not sorted ascending by size_b at index {j}")
                        last_size = float(sz)
            require("monotone_overall" in f and isinstance(f["monotone_overall"], bool), f"families_analyzed[{i}].monotone_overall must be boolean", errors)
            inversions = f.get("inversions_overall")
            require(isinstance(inversions, list), f"families_analyzed[{i}].inversions_overall must be list", errors)
            if isinstance(inversions, list):
                for k, inv in enumerate(inversions):
                    require(isinstance(inv, dict), f"families_analyzed[{i}].inversions_overall[{k}] must be object", errors)
                    if not isinstance(inv, dict):
                        continue
                    require(isinstance(inv.get("smaller_run"), str) and inv["smaller_run"], f"inversions_overall[{k}].smaller_run required", errors)
                    require(isinstance(inv.get("bigger_run"), str) and inv["bigger_run"], f"inversions_overall[{k}].bigger_run required", errors)
                    require(isinstance(inv.get("gap"), (int, float)), f"inversions_overall[{k}].gap must be numeric", errors)
                    pval = inv.get("p_value")
                    require(isinstance(pval, (int, float)) and 0.0 <= float(pval) <= 1.0, f"inversions_overall[{k}].p_value must be in [0,1]", errors)
                    require(isinstance(inv.get("significant"), bool), f"inversions_overall[{k}].significant must be boolean", errors)
            if f.get("monotone_overall") is True and isinstance(inversions, list) and len(inversions) > 0:
                errors.append(f"families_analyzed[{i}] contradiction: monotone_overall=true but inversions_overall is non-empty")
            ljc = f.get("llm_judge_comparison") or {}
            require(isinstance(ljc.get("used"), bool), f"families_analyzed[{i}].llm_judge_comparison.used must be boolean", errors)
            require(isinstance(ljc.get("monotone_overall"), bool), f"families_analyzed[{i}].llm_judge_comparison.monotone_overall must be boolean", errors)
            require(isinstance(ljc.get("inversions_overall"), list), f"families_analyzed[{i}].llm_judge_comparison.inversions_overall must be list", errors)

    require(p.with_suffix(".md").exists(), f"companion markdown report missing: {p.with_suffix('.md').name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_04_capability_alignment_report.py <path-to-04_capability_alignment.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
