# Verify-and-route — 02 Discriminability

After SubAgent writes `audit/reports/02_discriminability.{json,md}`:

**Script**: `python <skill-root>/scripts/check_02_discriminability_report.py <bench>/audit/reports/02_discriminability.json` — log to `audit/logs/02__attempt<K>.log`.

**Checklist**:

- [ ] `n_runs` matches count of `ok` experiments in the manifest.
- [ ] Bin counts sum to `n_runs`; `max_bin_share` recomputes consistently.
- [ ] Spearman ρ reported **per family**, never pooled.
- [ ] `gap_proportionality.proxy_used` is stated explicitly (`reference_rank` preferred, `size_b` fallback).
- [ ] If judge scores exist, score spread and gap proportionality summarize both scoring modes and their combined diagnostic meaning.
- [ ] `all_correct + all_wrong + informative ≤ n_items`.
- [ ] Verdict cites the numeric trigger (e.g., "fail because qwen2.5 ρ=0.32 < 0.4").
- [ ] MD includes a labeled distribution view (bin table or histogram).

**Route**: pass → mark dimension complete for Phase 2 aggregate; fail → re-dispatch the SubAgent with skill `benchmark-audit-02-discriminability`, failing report paths, the script log, and the failed checklist items. Retry cap 3.
