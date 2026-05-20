---
name: benchmark-audit-04-capability-alignment
description: Use when auditing the capability alignment dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 04: Capability Alignment

Audit whether **a stronger model in the same family beats a weaker one**. Within-family inversions are the loudest red flag — they can't be excused by training-data differences.

## Inputs

- `<bench>/audit/audit_manifest.json` — `capability_groups[*]` and `experiments[*]`.
- Per-run `scores.json` (for per-difficulty / per-topic correctness).
- `<bench>/audit/derived/llm_judge_scores.json` if present.
- `manifest.data.auxiliary_artifacts[]` may include prior within-family comparison tables or per-bucket stats — use them; use `predictions.jsonl` if `scores.json` lacks bucket correctness.

**Only compare within one family. Never across families** — that's dim 03's job.

## Checks

1. **Within-family monotonicity** — sort each `capability_groups[*]` by `size_b` ascending. Check monotonicity under each available scoring mode. Inversion = bigger model has strictly lower overall (or bucket) score than a smaller one in the same family.
2. **Inversion magnitude** — per inversion, report score gap in percentage points. 0.5pt is noise; 5pt is a real signal.
3. **Per-difficulty alignment** — repeat check 1 inside each `difficulty` bucket.
4. **Per-topic alignment** — same, by `topic`. Inversions concentrated in one topic hint at topic-specific benchmark or scoring-mode issues.
5. **Significance of each inversion** — McNemar on per-item correctness: discordant pairs `b` (bigger correct / smaller wrong) and `c` (smaller correct / bigger wrong). Use exact binomial when `b+c < 25`. Insignificant (p > 0.05) = warning; significant = fail.

## Output schema — `04_capability_alignment.json`

```json
{
  "dimension": "04_capability_alignment",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "families_analyzed": [{
      "family": "qwen2.5",
      "ordered_runs": [{"run_id": "", "size_b": 0.0, "score": 0.0}],
      "monotone_overall": true,
      "inversions_overall": [{"smaller_run": "", "bigger_run": "", "gap": 0.0, "p_value": 0.0, "significant": false}],
      "per_difficulty": [{"difficulty": "", "monotone": true, "inversions": []}],
      "per_topic": [{"topic": "", "monotone": true, "inversions": []}],
      "llm_judge_comparison": {"used": true, "monotone_overall": true, "inversions_overall": []}
    }]
  },
  "evidence": {"significance_threshold": 0.05, "min_inversion_gap_to_report_pct": 0.5},
  "recommendations": []
}
```

`04_capability_alignment.md` sections: `## Verdict`, `## Per-family results` (each with an ascii size→score table), `## Inversions (with significance)`, `## Recommendations`.

## Verdict

- `fail`: ≥1 statistically significant within-family inversion at the overall level.
- `warn`: any inversion with ≥1pt gap (significant or not), or significant inversions only in a difficulty/topic bucket.
- `pass`: no inversions, or only sub-0.5pt ones.
- `manual_review_required`: no family has ≥3 runs.

Stop when both files exist. Don't modify manifest or scores.
