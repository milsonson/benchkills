---
name: benchmark-audit-00-llm-as-judge
description: Use when auditing completed benchmark outputs with an LLM judge before the six benchmark quality audit dimensions run.
---

# SubAgent — Dimension 00: LLM-as-Judge

Judge existing model answers against the benchmark's own scoring spec. The SubAgent is the judge; do not call external model APIs or rerun tested models.

## Inputs

- `<bench>/audit/audit_manifest.json`
- `<bench>/data/problems.jsonl`
- `<bench>/score.md`
- Each ok run's `predictions.jsonl`
- Each ok run's `scores.json` **only after blind judging**, for post-hoc comparison

Use `score.md` as the grading rubric. If it conflicts with `scorer.py`, record the conflict and follow `score.md`.

## Blind judging rule

Judge scores must be assigned before reading script scores, scorer rationales, `scores.json`, `score_result`, or pass/fail flags.

For each item, first read only:

- problem text and reference fields from `data/problems.jsonl`
- `score.md`
- the model's visible answer from `predictions.jsonl`

Then assign `judge_score` and a short rubric-based reason. Only after all item scores are fixed may you read `scores.json` or prediction `score_result` fields to fill `script_score`, `delta`, disagreements, and score-source notes. Do not calibrate judge scores toward script scores.

## Checks

1. **Coverage** — judge every item from every ok run unless the run file is unreadable; record skipped items.
2. **Rubric fit** — assign each answer a score on the benchmark's scale, normalized to `[0,1]`.
3. **Judge rationale** — give a short reason per item; cite the main rubric point, not a long critique.
4. **Judge evaluation signal** — decide whether judge scores show usable spread, ranking, and non-saturated scores.
5. **Score-source notes** — after blind judging, compare script and judge scores briefly; flag `abs(delta) >= 0.25` for later dimensions.

## Output files

Write:

- `<bench>/audit/derived/llm_judge_scores.json`
- `<bench>/audit/reports/00_llm_as_judge.json`
- `<bench>/audit/reports/00_llm_as_judge.md`

## Derived schema — `audit/derived/llm_judge_scores.json`

```json
{
  "schema_version": "1.0",
  "judge": {"type": "subagent_llm", "rubric_path": "score.md", "score_scale": [0, 1], "blind_judging": true},
  "run_scores": [
    {"run_id": "", "model": "", "n_items": 0, "judge_score_overall": 0.0, "script_score_overall": 0.0, "mean_abs_delta": 0.0}
  ],
  "model_ranking": [
    {"rank": 1, "model": "", "judge_score": 0.0, "n_runs_aggregated": 1}
  ],
  "item_scores": [
    {"run_id": "", "problem_id": "", "script_score": 0.0, "judge_score": 0.0, "delta": 0.0, "reason": ""}
  ],
  "disagreements": [
    {"run_id": "", "problem_id": "", "script_score": 0.0, "judge_score": 0.0, "delta": 0.0, "reason": ""}
  ],
  "skipped": [{"run_id": "", "problem_id": "", "reason": ""}]
}
```

## Report schema — `00_llm_as_judge.json`

```json
{
  "dimension": "00_llm_as_judge",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "coverage": {"ok_runs": 0, "judged_items": 0, "skipped_items": 0, "coverage_rate": 0.0},
    "rankings": {
      "script_top_model": "",
      "judge_top_model": "",
      "ranking_changed": false,
      "judge_model_ranking": []
    },
    "judge_evaluation": {"supports_benchmark_signal": true, "score_spread": 0.0, "ranking_usable": true, "reason": ""},
    "score_source_notes": {"mean_abs_delta": 0.0, "large_difference_count": 0, "large_difference_rate": 0.0, "notes": ""}
  },
  "evidence": {"derived_path": "audit/derived/llm_judge_scores.json", "large_delta_threshold": 0.25},
  "recommendations": []
}
```

`00_llm_as_judge.md` sections: `## Verdict`, `## Coverage`, `## Judge Evaluation`, `## Judge Ranking`, `## Score Source Notes`, `## Recommendations`.

## Verdict

- `fail`: coverage <90% or judge cannot grade the benchmark under `score.md`.
- `warn`: coverage <100%, supports_benchmark_signal is false, or ranking_usable is false.
- `pass`: otherwise.
- `manual_review_required`: no ok runs or no readable predictions.

Script-vs-judge differences are post-hoc evidence for later dimensions. They do not determine the judge scores or the 00 verdict.

Stop when all three output files exist.
