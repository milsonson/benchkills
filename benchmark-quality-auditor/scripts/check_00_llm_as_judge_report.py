#!/usr/bin/env python3
"""Deterministic structural check for `00_llm_as_judge.json`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "warn", "fail", "manual_review_required"}


def fail(errors: list[str]) -> None:
    print("FAIL")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)


def require(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def load_json(path: Path, label: str, errors: list[str]) -> dict:
    if not path.exists():
        errors.append(f"{label} not found: {path}")
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"{label} invalid JSON: {exc}")
        return {}


def require_number(value, msg: str, errors: list[str], min_value: float | None = None, max_value: float | None = None) -> None:
    if not isinstance(value, (int, float)):
        errors.append(msg)
        return
    if min_value is not None and float(value) < min_value:
        errors.append(msg)
    if max_value is not None and float(value) > max_value:
        errors.append(msg)


def main(path: str) -> None:
    report_path = Path(path)
    errors: list[str] = []
    data = load_json(report_path, "report", errors)

    require(data.get("dimension") == "00_llm_as_judge", "dimension must equal '00_llm_as_judge'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    require(summary.get("verdict") in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require_number(summary.get("score"), "summary.score must be numeric in [0,1]", errors, 0.0, 1.0)
    require(isinstance(summary.get("headline"), str) and summary.get("headline", "").strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    for key in ["coverage", "rankings", "judge_evaluation", "score_source_notes"]:
        require(key in checks, f"checks.{key} missing", errors)

    coverage = checks.get("coverage") or {}
    require(isinstance(coverage.get("ok_runs"), int) and coverage.get("ok_runs", -1) >= 0, "coverage.ok_runs must be non-negative int", errors)
    require(isinstance(coverage.get("judged_items"), int) and coverage.get("judged_items", -1) >= 0, "coverage.judged_items must be non-negative int", errors)
    require(isinstance(coverage.get("skipped_items"), int) and coverage.get("skipped_items", -1) >= 0, "coverage.skipped_items must be non-negative int", errors)
    require_number(coverage.get("coverage_rate"), "coverage.coverage_rate must be in [0,1]", errors, 0.0, 1.0)

    rankings = checks.get("rankings") or {}
    require(isinstance(rankings.get("script_top_model"), str), "rankings.script_top_model must be string", errors)
    require(isinstance(rankings.get("judge_top_model"), str), "rankings.judge_top_model must be string", errors)
    require(isinstance(rankings.get("ranking_changed"), bool), "rankings.ranking_changed must be boolean", errors)
    require(isinstance(rankings.get("judge_model_ranking"), list), "rankings.judge_model_ranking must be list", errors)

    judge_eval = checks.get("judge_evaluation") or {}
    require(isinstance(judge_eval.get("supports_benchmark_signal"), bool), "judge_evaluation.supports_benchmark_signal must be boolean", errors)
    require_number(judge_eval.get("score_spread"), "judge_evaluation.score_spread must be non-negative number", errors, 0.0)
    require(isinstance(judge_eval.get("ranking_usable"), bool), "judge_evaluation.ranking_usable must be boolean", errors)
    require(isinstance(judge_eval.get("reason"), str) and judge_eval.get("reason", "").strip(), "judge_evaluation.reason must be non-empty string", errors)

    source_notes = checks.get("score_source_notes") or {}
    require_number(source_notes.get("mean_abs_delta"), "score_source_notes.mean_abs_delta must be in [0,1]", errors, 0.0, 1.0)
    require(isinstance(source_notes.get("large_difference_count"), int) and source_notes.get("large_difference_count", -1) >= 0, "score_source_notes.large_difference_count must be non-negative int", errors)
    require_number(source_notes.get("large_difference_rate"), "score_source_notes.large_difference_rate must be in [0,1]", errors, 0.0, 1.0)
    require(isinstance(source_notes.get("notes"), str), "score_source_notes.notes must be string", errors)

    evidence = data.get("evidence") or {}
    derived_rel = evidence.get("derived_path")
    require(isinstance(derived_rel, str) and derived_rel == "audit/derived/llm_judge_scores.json", "evidence.derived_path must be audit/derived/llm_judge_scores.json", errors)
    require_number(evidence.get("large_delta_threshold"), "evidence.large_delta_threshold must be numeric", errors, 0.0, 1.0)

    require(isinstance(data.get("recommendations"), list), "recommendations must be list", errors)
    require(report_path.with_suffix(".md").exists(), f"companion markdown report missing: {report_path.with_suffix('.md').name}", errors)

    bench_root = report_path.parent.parent.parent
    derived_path = bench_root / "audit" / "derived" / "llm_judge_scores.json"
    derived = load_json(derived_path, "derived judge scores", errors)
    if derived:
        require(derived.get("schema_version") == "1.0", "derived.schema_version must equal '1.0'", errors)
        require(isinstance(derived.get("judge"), dict), "derived.judge must be object", errors)
        judge = derived.get("judge") or {}
        require(judge.get("blind_judging") is True, "derived.judge.blind_judging must be true", errors)
        for key in ["run_scores", "model_ranking", "item_scores", "disagreements", "skipped"]:
            require(isinstance(derived.get(key), list), f"derived.{key} must be list", errors)

        for i, item in enumerate(derived.get("item_scores") or []):
            require(isinstance(item, dict), f"item_scores[{i}] must be object", errors)
            if not isinstance(item, dict):
                continue
            for key in ["run_id", "problem_id", "reason"]:
                require(isinstance(item.get(key), str) and item.get(key, "").strip(), f"item_scores[{i}].{key} required", errors)
            for key in ["script_score", "judge_score", "delta"]:
                require_number(item.get(key), f"item_scores[{i}].{key} must be numeric", errors)

            reason = item.get("reason", "")
            if isinstance(reason, str):
                lower = reason.lower()
                banned = [
                    "matched ",
                    "requirements matched",
                    "scorer requirements",
                    "script score",
                    "scorer rationale",
                    "passed=true",
                    "passed=false",
                    "pass/fail",
                ]
                for phrase in banned:
                    require(phrase not in lower, f"item_scores[{i}].reason appears to rely on post-hoc scorer signal: {phrase}", errors)

        threshold = evidence.get("large_delta_threshold")
        if isinstance(threshold, (int, float)):
            for i, item in enumerate(derived.get("disagreements") or []):
                delta = item.get("delta") if isinstance(item, dict) else None
                require(isinstance(delta, (int, float)) and abs(float(delta)) >= float(threshold), f"disagreements[{i}].delta must meet threshold", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_00_llm_as_judge_report.py <path-to-00_llm_as_judge.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
