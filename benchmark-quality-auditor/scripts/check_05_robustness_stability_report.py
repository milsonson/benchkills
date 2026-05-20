#!/usr/bin/env python3
"""Deterministic structural check for `05_robustness_stability.json`."""
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
    require(data.get("dimension") == "05_robustness_stability", "dimension must equal '05_robustness_stability'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    verdict = summary.get("verdict")
    require(verdict in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("score"), (int, float)) and 0.0 <= float(summary["score"]) <= 1.0, "summary.score must be numeric in [0,1]", errors)
    require(isinstance(summary.get("headline"), str) and summary["headline"].strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    groups = checks.get("groups")
    require(isinstance(groups, list), "checks.groups must be list", errors)
    has_insufficient = False
    if isinstance(groups, list):
        for i, g in enumerate(groups):
            require(isinstance(g, dict) and g.get("model"), f"groups[{i}].model required", errors)
            if not isinstance(g, dict):
                continue
            n_seeds = g.get("n_seeds")
            require(isinstance(n_seeds, int) and n_seeds >= 0, f"groups[{i}].n_seeds must be non-negative int", errors)
            if isinstance(n_seeds, int) and n_seeds < 2:
                has_insufficient = True
            for k in ["score_min", "score_max", "score_mean", "score_std"]:
                require(isinstance(g.get(k), (int, float)), f"groups[{i}].{k} must be numeric", errors)
            if all(isinstance(g.get(k), (int, float)) for k in ["score_min", "score_mean", "score_max"]):
                if not (g["score_min"] <= g["score_mean"] <= g["score_max"]):
                    errors.append(f"groups[{i}] arithmetic: score_min={g['score_min']} <= score_mean={g['score_mean']} <= score_max={g['score_max']} violated")
            agree = g.get("all_seeds_agree_rate")
            require(isinstance(agree, (int, float)) and 0.0 <= float(agree) <= 1.0, f"groups[{i}].all_seeds_agree_rate must be in [0,1]", errors)
            require(isinstance(g.get("flipped_items"), int) and g["flipped_items"] >= 0, f"groups[{i}].flipped_items must be non-negative int", errors)
            ratio = g.get("noise_vs_signal_ratio")
            gap = g.get("nearest_capability_gap")
            require(isinstance(ratio, (int, float)), f"groups[{i}].noise_vs_signal_ratio must be numeric", errors)
            require(isinstance(gap, (int, float)), f"groups[{i}].nearest_capability_gap must be numeric", errors)
            ljc = g.get("llm_judge_comparison") or {}
            require(isinstance(ljc.get("used"), bool), f"groups[{i}].llm_judge_comparison.used must be boolean", errors)
            for k in ["judge_score_std", "judge_noise_vs_signal_ratio"]:
                require(isinstance(ljc.get(k), (int, float)), f"groups[{i}].llm_judge_comparison.{k} must be numeric", errors)

    if has_insufficient and verdict != "manual_review_required":
        errors.append("at least one group has n_seeds<2 but verdict is not 'manual_review_required'")

    require(p.with_suffix(".md").exists(), f"companion markdown report missing: {p.with_suffix('.md').name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_05_robustness_stability_report.py <path-to-05_robustness_stability.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
