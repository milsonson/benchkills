---
name: benchmark-audit-05-robustness-stability
description: Use when auditing the robustness and stability dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 05: Robustness / Stability

Audit whether **the same model with the same prompt produces a stable score across repeated runs**. High variance means the benchmark is measuring noise, not capability.

## Inputs

- `<bench>/audit/audit_manifest.json` — `stability_groups[*]` (same model, multiple seeds).
- Per-run `scores.json` and `predictions.jsonl` for per-item analysis.
- `<bench>/audit/derived/llm_judge_scores.json` if present.
- `manifest.data.auxiliary_artifacts[]` may carry prior temperature/seed sweeps, flip-rate tables, or notes about unstable topics.

This dimension is read-only over imported run outputs — never re-run models.

Group with `n_seeds < 2` → emit `insufficient_data` and verdict `manual_review_required`.

## Checks

1. **Per-item agreement** — fraction of items where all seeds agree (all right or all wrong). Report per group.
2. **Score spread** — `min / max / mean / std` per group under each available scoring mode. `score_std` is the headline.
3. **Flip count** — items that flipped across seeds (the practical measure of how many items would need re-running).
4. **Per-difficulty stability** — 1–3 inside each difficulty bucket.
5. **Per-topic stability** — same, by topic.
6. **Noise vs. signal** — compare inter-seed std to the gap between this model and its nearest neighbor in the same family's `capability_groups` (e.g. Qwen2.5-7B vs. 14B, using the canonical seed=1 run). Report `noise_vs_signal_ratio = score_std / nearest_capability_gap`. Ratio ≥1 means the benchmark can't distinguish those two models.

## Output schema — `05_robustness_stability.json`

```json
{
  "dimension": "05_robustness_stability",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "groups": [{
      "model": "Qwen2.5-7B-Instruct",
      "n_seeds": 0,
      "score_min": 0.0, "score_max": 0.0, "score_mean": 0.0, "score_std": 0.0,
      "all_seeds_agree_rate": 0.0,
      "flipped_items": 0,
      "per_difficulty": [{"difficulty": "", "agree_rate": 0.0, "flipped": 0}],
      "per_topic": [{"topic": "", "agree_rate": 0.0, "flipped": 0}],
      "noise_vs_signal_ratio": 0.0,
      "nearest_capability_gap": 0.0,
      "llm_judge_comparison": {"used": true, "judge_score_std": 0.0, "judge_noise_vs_signal_ratio": 0.0}
    }]
  },
  "evidence": {"min_seeds_required": 2, "noise_signal_warn_threshold": 0.5, "noise_signal_fail_threshold": 1.0},
  "recommendations": []
}
```

`05_robustness_stability.md` sections: `## Verdict`, `## Per-group stability`, `## Noise vs. signal`, `## Recommendations`.

## Verdict

- `fail`: any group `noise_vs_signal_ratio ≥1.0`, OR `score_std ≥3pt`.
- `warn`: any group ratio in `[0.5, 1.0)`, OR `score_std` in `[1pt, 3pt)`.
- `pass`: otherwise.
- `manual_review_required`: any stability group has <2 seeds.

Stop when both files exist.
