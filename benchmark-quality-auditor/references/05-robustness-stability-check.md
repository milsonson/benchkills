# Verify-and-route — 05 Robustness / Stability

After SubAgent writes `audit/reports/05_robustness_stability.{json,md}`:

**Script**: `python <skill-root>/scripts/check_05_robustness_stability_report.py <bench>/audit/reports/05_robustness_stability.json` — log to `audit/logs/05__attempt<K>.log`.

**Checklist**:

- [ ] Every `stability_groups[*]` from the manifest appears in `checks.groups`.
- [ ] `n_seeds` matches manifest `run_ids` count per group.
- [ ] `score_min ≤ score_mean ≤ score_max`.
- [ ] `noise_vs_signal_ratio` reported with the `nearest_capability_gap` used. Unstated or zero gap = reject.
- [ ] Any group with `n_seeds < 2` → overall verdict must be `manual_review_required`.
- [ ] If judge scores exist, seed stability includes both script-score and judge-score spread when data permits.
- [ ] Per-difficulty and per-topic stability present when those fields exist in predictions.
- [ ] MD names the noisiest difficulty and noisiest topic in plain English.

**Route**: pass → mark dimension complete for Phase 2 aggregate; fail → re-dispatch the SubAgent with skill `benchmark-audit-05-robustness-stability`, failing report paths, the script log, and the failed checklist items. Retry cap 3.
