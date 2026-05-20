---
name: benchmark-audit-02-discriminability
description: Use when auditing the discriminability dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 02: Discriminability

Audit whether the benchmark **separates strong and weak models smoothly**. Score gaps should track capability gaps — not collapse into a ceiling/floor or split into saturated cliffs.

## Inputs

- `<bench>/audit/audit_manifest.json` + per-run `scores.json` (per-problem correctness).
- `<bench>/audit/derived/llm_judge_scores.json` if present.
- Anything in `manifest.data.auxiliary_artifacts[]` useful here (per-difficulty/topic pass-rate tables, cached histograms). Use `predictions.jsonl` if `scores.json` lacks per-item correctness.

All numbers come from existing files. Do not re-run models.

## Checks

1. **Score spread** — min / max / mean / std across `ok` runs for each available scoring mode.
2. **Ceiling / floor** — count runs at ≥95% and ≤5%.
3. **Bin uniformity** — bucket into `[0-20, 20-40, 40-60, 60-80, 80-100]`. Max bin share quantifies clustering.
4. **Gap proportionality** — within each `capability_groups[*]`, Spearman ρ between `size_b` and score for each available scoring mode. State the proxy used (reference rank preferred, `size_b` as fallback). Pool **per family**, never across families.
5. **Per-item information** — count items all runs got right, all wrong, and items with pass rate in `[0.2, 0.8]` (informative). Report the informative share.
6. **Per-difficulty** — same spread analysis restricted to each `difficulty` bucket.

## Output schema — `02_discriminability.json`

```json
{
  "dimension": "02_discriminability",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "score_distribution": {"n_runs": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
    "ceiling_floor": {"ceiling_runs": [], "floor_runs": [], "passed": true},
    "bin_uniformity": {"bins": {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}, "max_bin_share": 0.0},
    "gap_proportionality": {
      "proxy_used": "size_b|reference_rank",
      "per_family": [{"family": "qwen2.5", "spearman_rho": 0.0, "n_models": 0, "monotone": true}]
    },
    "item_information_value": {"n_items": 0, "all_correct": 0, "all_wrong": 0, "informative": 0, "informative_share": 0.0},
    "per_difficulty": [{"difficulty": "easy", "n_items": 0, "mean_pass_rate": 0.0, "std_across_runs": 0.0}],
    "llm_judge_comparison": {"used": true, "score_std": 0.0, "max_bin_share": 0.0, "informative_share": 0.0}
  },
  "evidence": {"informative_band": [0.2, 0.8]},
  "recommendations": []
}
```

`02_discriminability.md` sections: `## Verdict`, `## Score distribution` (with the bin table), `## Gap proportionality`, `## Per-item information`, `## Per-difficulty`, `## Recommendations`.

## Verdict

- `fail`: max bin share ≥0.6, OR informative_share <0.3, OR any family ρ <0.4.
- `warn`: max bin share in `[0.4, 0.6)`, OR informative_share in `[0.3, 0.5)`, OR any family ρ in `[0.4, 0.7)`.
- `pass`: otherwise.

Stop when both files exist. Don't edit predictions or scores.
