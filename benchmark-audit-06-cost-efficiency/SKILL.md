---
name: benchmark-audit-06-cost-efficiency
description: Use when auditing the cost efficiency dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 06: Cost Efficiency

Audit whether the benchmark **gets its signal cheaply**, and recommend a pruned subset that preserves the ranking but cuts cost.

## Inputs

- `<bench>/audit/audit_manifest.json` — `tokens_in, tokens_out, wallclock_s, score_overall` per run.
- `<bench>/audit/derived/model_ranking.json` — canonical model-level ranking produced during import.
- `<bench>/audit/derived/llm_judge_scores.json` if present.
- Per-run `predictions.jsonl` for per-item token usage.
- `manifest.data.auxiliary_artifacts[]` may hold `usage.json` exports or prior cost/pruning work.

Pruning analysis is read-only. Never delete items from `data/problems.jsonl` — only propose subsets.

## Checks

1. **Totals** — sum `tokens_in`, `tokens_out`, `wallclock_s` across runs. If any `ok` run is missing either token field, mark `completeness="partial"` and list the runs.
2. **Per-item cost** — mean `tokens_out` per problem across runs; top 5 most expensive items.
3. **Cost-of-signal** — compute adjacent-pair cost per score point for each available model-level ranking. Use the representative run's tokens (or the mean across that model's ok seeds — state which in the MD). **Skip any pair with `|score_A − score_B| == 0`** — the ratio is undefined, don't fill with a sentinel. Never pair two seeds of the same model (that's dim 05).
4. **Pruning proposal** — information score per item combining: (a) per-item pass-rate variance across runs (higher = more informative), (b) within-family discrimination (pass rate rises with size; negative correlation is anti-informative), (c) per-item token cost (lower = better). Propose 20% and 50% cuts, **recompute the full-run ranking on the subset**, and report Spearman ρ vs. full-set ranking. Good = ρ ≥0.95 at 50%.
5. **Recommendation** — the largest cut where subset-vs-full ρ ≥0.95 AND no within-family inversion is introduced.

## Output schema — `06_cost_efficiency.json`

```json
{
  "dimension": "06_cost_efficiency",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "totals": {"tokens_in_total": 0, "tokens_out_total": 0, "wallclock_s_total": 0, "completeness": "full|partial", "missing_token_runs": []},
    "per_item_cost": {"mean_tokens_out": 0.0, "top5_expensive_items": [{"problem_id": "", "mean_tokens_out": 0.0}]},
    "cost_of_signal": [{"a_run_id": "", "b_run_id": "", "score_gap": 0.0, "tokens_combined": 0, "cost_per_pt": 0.0}],
    "pruning": {
      "candidates": [
        {"cut_pct": 20, "kept_items": 0, "rho_vs_full": 0.0, "introduces_family_inversion": false},
        {"cut_pct": 50, "kept_items": 0, "rho_vs_full": 0.0, "introduces_family_inversion": false}
      ],
      "recommended_cut_pct": 0,
      "recommended_kept_item_ids": []
    },
    "llm_judge_comparison": {"used": true, "cost_of_signal": [], "recommended_cut_pct": 0}
  },
  "evidence": {"preserve_rho_threshold": 0.95},
  "recommendations": []
}
```

`06_cost_efficiency.md` sections: `## Verdict`, `## Total cost`, `## Most expensive items`, `## Pruning analysis`, `## Recommendation`.

## Verdict

- `fail`: every pruning candidate either drops ρ below 0.9 or introduces a family inversion.
- `warn`: best preserving cut is <20%.
- `pass`: ≥20% cut preserves ρ ≥0.95 without introducing inversions.
- `manual_review_required`: token data is `partial` for >50% of runs.

Stop when both files exist.
