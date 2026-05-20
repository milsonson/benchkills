---
name: benchmark-audit-03-ranking-consistency
description: Use when auditing the ranking consistency dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 03: Ranking Consistency

Audit whether the benchmark **ranks models the way mainstream references do**. Anti-correlation with the broader picture is suspicious unless the benchmark targets a niche.

## Inputs

- `<bench>/audit/audit_manifest.json` — `experiments[*].model, score_overall` and `reference_rankings` (may be empty: `{name, source, ordered_models, scores?}`).
- `<bench>/audit/derived/model_ranking.json` — canonical produced ranking shared with dim 06.
- `<bench>/audit/derived/llm_judge_scores.json` if present.
- `manifest.data.auxiliary_artifacts[]` may surface reference dumps or docs describing target capabilities. Only promote an artifact into `references_used` if it names its source and model list explicitly. Never invent references.

## Checks

1. **Produced rankings (model-level)** — read `audit/derived/model_ranking.json` for script scores and `audit/derived/llm_judge_scores.json` when available. Compare each available ranking with references or proxy. **Never** emit a per-seed ranking — per-seed variance is dim 05's territory.
2. **Correlation with each reference** — Spearman ρ and Kendall τ per reference. Require ≥3 model overlap; otherwise report `insufficient_overlap` and compute nothing. Consistent = ρ ≥ 0.7.
3. **Proxy fallback** — no references? Use `size_b` within each family as a coarse proxy and mark it as fallback.
4. **Inversions** — adjacent pairs `(rank_i, rank_{i+1})` that disagree with the reference (or proxy). **Exclude strict ties** (`|score_A − score_B| < 1e-9`) — a tie is an arbitrary tie-break, not an inversion. Cite representative run_ids.
5. **Cross-family sanity** — low-confidence check: a 7B from a strong family vs. 7B from a weaker one. Note, don't conclude hard.

Cite each reference's `source` field verbatim.

## Output schema — `03_ranking_consistency.json`

```json
{
  "dimension": "03_ranking_consistency",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "produced_ranking": [{"rank": 1, "run_id": "", "model": "", "score": 0.0, "n_runs_aggregated": 1}],
    "references_used": [{"name": "", "source": "", "n_overlap": 0, "spearman_rho": 0.0, "kendall_tau": 0.0, "status": "computed|insufficient_overlap"}],
    "proxy_fallback": {"used": false, "per_family": [{"family": "", "spearman_rho_size_vs_score": 0.0, "n_models": 0}]},
    "inversions": [{"a_run_id": "", "b_run_id": "", "produced_order": "A>B", "reference_order": "B>A", "reference": ""}],
    "llm_judge_comparison": {"used": true, "ranking_changed": false, "judge_top_model": ""}
  },
  "evidence": {"min_correlation_threshold": 0.7, "min_overlap_for_correlation": 3},
  "recommendations": []
}
```

`03_ranking_consistency.md` sections: `## Verdict`, `## Produced ranking`, `## Reference comparisons`, `## Inversions`, `## Recommendations`.

## Verdict

- `fail`: any computed reference correlation <0.4, OR (no references AND all family proxy ρ <0.4).
- `warn`: any correlation in `[0.4, 0.7)`, OR proxy fallback is the only source.
- `pass`: ≥1 reference with ρ ≥0.7 and no computed correlation <0.4.
- `manual_review_required`: no references AND no family has ≥3 models.

Stop when both files exist.
