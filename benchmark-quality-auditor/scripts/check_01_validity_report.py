#!/usr/bin/env python3
"""Deterministic structural check for `01_validity.json`.

Exit code 0 = pass. Nonzero = fail; reasons printed to stdout.
Used by MetaAgent before semantic review.
"""
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


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def get(d, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def main(path: str) -> None:
    p = Path(path)
    if not p.exists():
        fail([f"report not found: {path}"])

    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        fail([f"invalid JSON: {e}"])

    errors: list[str] = []
    require(data.get("dimension") == "01_validity", "dimension must equal '01_validity'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    require(summary.get("verdict") in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("headline"), str) and summary.get("headline", "").strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    for key in ["schema_integrity", "answer_uniqueness", "ambiguity", "duplicates", "contamination_signals", "scoring_modes", "implementation_notes"]:
        require(key in checks, f"checks.{key} missing", errors)

    si = checks.get("schema_integrity") or {}
    require(isinstance(si.get("num_problems"), int) and si["num_problems"] >= 0, "schema_integrity.num_problems must be non-negative int", errors)
    require(isinstance(si.get("missing_field_ids"), list), "schema_integrity.missing_field_ids must be list", errors)
    require(isinstance(si.get("duplicate_ids"), list), "schema_integrity.duplicate_ids must be list", errors)

    au = checks.get("answer_uniqueness") or {}
    require(isinstance(au.get("sampled_ids"), list), "answer_uniqueness.sampled_ids must be list", errors)
    require(isinstance(au.get("non_unique_answer_ids"), list), "answer_uniqueness.non_unique_answer_ids must be list", errors)

    modes = checks.get("scoring_modes") or {}
    for mode_key in ["script_view", "judge_view"]:
        mode = modes.get(mode_key) or {}
        require(isinstance(mode.get("usable"), bool), f"scoring_modes.{mode_key}.usable must be boolean", errors)
        require(isinstance(mode.get("notes"), str), f"scoring_modes.{mode_key}.notes must be string", errors)
    differences = modes.get("differences")
    require(isinstance(differences, list), "scoring_modes.differences must be list", errors)
    if isinstance(differences, list):
        for i, entry in enumerate(differences):
            require(isinstance(entry, dict), f"scoring_modes.differences[{i}] must be object", errors)
            if not isinstance(entry, dict):
                continue
            require(isinstance(entry.get("problem_id"), str), f"scoring_modes.differences[{i}].problem_id must be string", errors)
            require(isinstance(entry.get("interpretation"), str), f"scoring_modes.differences[{i}].interpretation must be string", errors)

    notes = checks.get("implementation_notes")
    require(isinstance(notes, list), "implementation_notes must be list", errors)

    evidence = data.get("evidence") or {}
    require("sampling_seed" in evidence, "evidence.sampling_seed required (for reproducibility)", errors)

    recs = data.get("recommendations")
    require(isinstance(recs, list), "recommendations must be list", errors)
    if isinstance(recs, list):
        for i, r in enumerate(recs):
            require(isinstance(r, dict) and r.get("priority") in {"high", "med", "low"}, f"recommendations[{i}].priority must be high|med|low", errors)
            require(isinstance(r.get("action"), str) and r.get("action", "").strip(), f"recommendations[{i}].action must be non-empty string", errors)

    if summary.get("verdict") == "fail":
        schema_pass = (checks.get("schema_integrity") or {}).get("passed", True)
        ambiguity = (checks.get("ambiguity") or {}).get("ambiguous_ids") or []
        non_unique = (checks.get("answer_uniqueness") or {}).get("non_unique_answer_ids") or []
        if schema_pass and not ambiguity and not non_unique:
            errors.append("verdict 'fail' but no schema, ambiguity, or answer/rubric validity trigger is present")

    md = p.with_suffix(".md")
    require(md.exists(), f"companion markdown report missing: {md.name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_01_validity_report.py <path-to-01_validity.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
