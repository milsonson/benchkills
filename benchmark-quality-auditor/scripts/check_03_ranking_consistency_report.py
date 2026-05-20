#!/usr/bin/env python3
"""Deterministic structural check for `03_ranking_consistency.json`."""
from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "warn", "fail", "manual_review_required"}
VALID_STATUS = {"computed", "insufficient_overlap"}


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
    require(data.get("dimension") == "03_ranking_consistency", "dimension must equal '03_ranking_consistency'", errors)
    require("schema_version" in data, "missing schema_version", errors)

    summary = data.get("summary") or {}
    require(summary.get("verdict") in VALID_VERDICTS, f"summary.verdict must be one of {VALID_VERDICTS}", errors)
    require(isinstance(summary.get("score"), (int, float)) and 0.0 <= float(summary["score"]) <= 1.0, "summary.score must be numeric in [0,1]", errors)
    require(isinstance(summary.get("headline"), str) and summary["headline"].strip(), "summary.headline must be non-empty string", errors)

    checks = data.get("checks") or {}
    for key in ["produced_ranking", "references_used", "proxy_fallback", "inversions", "llm_judge_comparison"]:
        require(key in checks, f"checks.{key} missing", errors)

    pr = checks.get("produced_ranking") or []
    require(isinstance(pr, list) and len(pr) > 0, "produced_ranking must be a non-empty list", errors)
    pr_score_by_run: dict = {}
    if isinstance(pr, list):
        run_ids_seen = set()
        models_seen = set()
        prev_score = None
        prev_rank = 0
        for i, entry in enumerate(pr):
            require(isinstance(entry, dict), f"produced_ranking[{i}] must be object", errors)
            if not isinstance(entry, dict):
                continue
            rid = entry.get("run_id")
            require(isinstance(rid, str) and rid, f"produced_ranking[{i}].run_id required", errors)
            if rid in run_ids_seen:
                errors.append(f"produced_ranking has duplicate run_id: {rid}")
            run_ids_seen.add(rid)
            model = entry.get("model")
            require(isinstance(model, str) and model, f"produced_ranking[{i}].model required", errors)
            if isinstance(model, str) and model:
                if model in models_seen:
                    errors.append(f"produced_ranking has duplicate model '{model}' — must aggregate stability seeds into one entry")
                models_seen.add(model)
            rank = entry.get("rank")
            require(isinstance(rank, int) and rank == prev_rank + 1, f"produced_ranking[{i}].rank must equal {prev_rank+1}", errors)
            prev_rank = rank if isinstance(rank, int) else prev_rank + 1
            score = entry.get("score")
            require(isinstance(score, (int, float)), f"produced_ranking[{i}].score must be numeric", errors)
            if isinstance(score, (int, float)) and prev_score is not None:
                if float(score) > float(prev_score) + 1e-9:
                    errors.append(f"produced_ranking not sorted descending at index {i}: {score} > previous {prev_score}")
            if isinstance(score, (int, float)):
                prev_score = score
                if isinstance(rid, str):
                    pr_score_by_run[rid] = float(score)
            n_agg = entry.get("n_runs_aggregated")
            require(isinstance(n_agg, int) and n_agg >= 1, f"produced_ranking[{i}].n_runs_aggregated must be int ≥ 1", errors)

    refs = checks.get("references_used") or []
    require(isinstance(refs, list), "references_used must be list", errors)
    if isinstance(refs, list):
        for i, r in enumerate(refs):
            require(isinstance(r, dict), f"references_used[{i}] must be object", errors)
            if not isinstance(r, dict):
                continue
            require(isinstance(r.get("name"), str) and r["name"], f"references_used[{i}].name required", errors)
            require(isinstance(r.get("source"), str) and r["source"], f"references_used[{i}].source required", errors)
            require(r.get("status") in VALID_STATUS, f"references_used[{i}].status must be one of {VALID_STATUS}", errors)
            require(isinstance(r.get("n_overlap"), int) and r["n_overlap"] >= 0, f"references_used[{i}].n_overlap must be non-negative int", errors)
            if r.get("status") == "computed":
                for k in ["spearman_rho", "kendall_tau"]:
                    v = r.get(k)
                    require(isinstance(v, (int, float)) and -1.0 <= float(v) <= 1.0, f"references_used[{i}].{k} must be in [-1,1] when status=computed", errors)
                require(isinstance(r.get("n_overlap"), int) and r["n_overlap"] >= 3, f"references_used[{i}] has n_overlap<3 but status=computed", errors)

    pf = checks.get("proxy_fallback") or {}
    require(isinstance(pf.get("used"), bool), "proxy_fallback.used must be boolean", errors)
    if pf.get("used") is True:
        require(isinstance(pf.get("per_family"), list) and len(pf.get("per_family") or []) > 0, "proxy_fallback.per_family must be non-empty when used=true", errors)

    inv = checks.get("inversions") or []
    require(isinstance(inv, list), "inversions must be list", errors)
    if isinstance(inv, list):
        for i, x in enumerate(inv):
            require(isinstance(x, dict) and x.get("a_run_id") and x.get("b_run_id") and x.get("reference"), f"inversions[{i}] requires a_run_id, b_run_id, reference", errors)
            if isinstance(x, dict):
                a_id, b_id = x.get("a_run_id"), x.get("b_run_id")
                if isinstance(a_id, str) and isinstance(b_id, str) and a_id in pr_score_by_run and b_id in pr_score_by_run:
                    if abs(pr_score_by_run[a_id] - pr_score_by_run[b_id]) < 1e-9:
                        errors.append(f"inversions[{i}] reports tied scores ({a_id}={pr_score_by_run[a_id]}, {b_id}={pr_score_by_run[b_id]}) — ties are not inversions")

    ljc = checks.get("llm_judge_comparison") or {}
    require(isinstance(ljc.get("used"), bool), "llm_judge_comparison.used must be boolean", errors)
    require(isinstance(ljc.get("ranking_changed"), bool), "llm_judge_comparison.ranking_changed must be boolean", errors)
    require(isinstance(ljc.get("judge_top_model"), str), "llm_judge_comparison.judge_top_model must be string", errors)

    require(p.with_suffix(".md").exists(), f"companion markdown report missing: {p.with_suffix('.md').name}", errors)

    if errors:
        fail(errors)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_03_ranking_consistency_report.py <path-to-03_ranking_consistency.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
