#!/usr/bin/env python3
"""Deterministic structural check for `02_discriminability.json`."""
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
    require(data.get("dimension") == "02_discriminability", "dimension must equal '02_discriminability'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    require(summary.get("verdict") in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("headline"), str) and summary["headline"].strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    for key in ["score_distribution", "ceiling_floor", "bin_uniformity", "gap_proportionality", "item_information_value", "per_difficulty"]:
        require(key in checks, f"checks.{key} missing", errors)

    sdist = checks.get("score_distribution") or {}
    n_runs = sdist.get("n_runs")
    require(isinstance(n_runs, int) and n_runs >= 0, "score_distribution.n_runs must be non-negative int", errors)
    for k in ["min", "max", "mean", "std"]:
        require(isinstance(sdist.get(k), (int, float)), f"score_distribution.{k} must be numeric", errors)
    if all(isinstance(sdist.get(k), (int, float)) for k in ["min", "max", "mean"]):
        if not (sdist["min"] <= sdist["mean"] <= sdist["max"]):
            errors.append(f"score_distribution arithmetic: min={sdist['min']} <= mean={sdist['mean']} <= max={sdist['max']} violated")

    bu = checks.get("bin_uniformity") or {}
    bins = bu.get("bins") or {}
    expected_bin_keys = {"0-20", "20-40", "40-60", "60-80", "80-100"}
    require(set(bins.keys()) == expected_bin_keys, f"bin_uniformity.bins must have exactly keys {sorted(expected_bin_keys)}", errors)
    if set(bins.keys()) == expected_bin_keys and isinstance(n_runs, int) and n_runs >= 0:
        total = sum(bins.values())
        if total != n_runs:
            errors.append(f"bin counts sum to {total} but n_runs={n_runs}")
        max_share_reported = bu.get("max_bin_share")
        if isinstance(max_share_reported, (int, float)) and n_runs > 0:
            expected_max = max(bins.values()) / n_runs
            if abs(float(max_share_reported) - expected_max) > 1e-6:
                errors.append(f"bin_uniformity.max_bin_share={max_share_reported} but max(bins)/n_runs={expected_max}")

    gp = checks.get("gap_proportionality") or {}
    require(gp.get("proxy_used") in {"size_b", "reference_rank"}, "gap_proportionality.proxy_used must be 'size_b' or 'reference_rank'", errors)
    require(isinstance(gp.get("per_family"), list), "gap_proportionality.per_family must be list", errors)
    if isinstance(gp.get("per_family"), list):
        for i, fam in enumerate(gp["per_family"]):
            require(isinstance(fam, dict) and fam.get("family"), f"per_family[{i}].family required", errors)
            rho = fam.get("spearman_rho")
            require(isinstance(rho, (int, float)) and -1.0 <= float(rho) <= 1.0, f"per_family[{i}].spearman_rho must be in [-1,1]", errors)
            require(isinstance(fam.get("n_models"), int) and fam["n_models"] >= 0, f"per_family[{i}].n_models must be non-negative int", errors)

    iiv = checks.get("item_information_value") or {}
    for k in ["n_items", "all_correct", "all_wrong", "informative"]:
        require(isinstance(iiv.get(k), int) and iiv[k] >= 0, f"item_information_value.{k} must be non-negative int", errors)
    if all(isinstance(iiv.get(k), int) for k in ["n_items", "all_correct", "all_wrong", "informative"]):
        if iiv["all_correct"] + iiv["all_wrong"] + iiv["informative"] > iiv["n_items"]:
            errors.append("item_information_value: all_correct + all_wrong + informative exceeds n_items")
    share = iiv.get("informative_share")
    if isinstance(share, (int, float)) and isinstance(iiv.get("n_items"), int) and iiv["n_items"] > 0:
        expected_share = iiv["informative"] / iiv["n_items"]
        if abs(float(share) - expected_share) > 1e-6:
            errors.append(f"item_information_value.informative_share={share} but informative/n_items={expected_share}")

    require(p.with_suffix(".md").exists(), f"companion markdown report missing: {p.with_suffix('.md').name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_02_discriminability_report.py <path-to-02_discriminability.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
