# Verify-and-route — 06 Cost Efficiency

After SubAgent writes `audit/reports/06_cost_efficiency.{json,md}`:

**Script**: `python <skill-root>/scripts/check_06_cost_efficiency_report.py <bench>/audit/reports/06_cost_efficiency.json` — log to `audit/logs/06__attempt<K>.log`.

**Checklist**:

- [ ] `cost_of_signal` adjacent pairs come from `audit/derived/model_ranking.json`'s **model-level** ranking. Two seeds of the same model never appear as a pair.
- [ ] No `cost_of_signal` entry has `score_gap == 0`. Zero-gap pairs omitted, never filled with `inf`/`null`/sentinel. All pairs zero-gap → `cost_of_signal=[]` and headline says so.
- [ ] If judge scores exist, cost-of-signal or pruning impact is summarized for both scoring modes.
- [ ] `totals.completeness == "full"` only if every `ok` run has both `tokens_in` and `tokens_out`; otherwise `partial` with `missing_token_runs` filled.
- [ ] `top5_expensive_items` has exactly 5 entries (or all items if fewer).
- [ ] Each pruning candidate reports `kept_items` and `rho_vs_full`. `kept_items = round((1 - cut_pct/100) * n_items)`.
- [ ] `recommended_cut_pct` justified in MD: chosen because ρ ≥0.95 and no inversion. Neither candidate qualifies → `recommended_cut_pct=0`.
- [ ] `recommended_kept_item_ids` non-empty when `recommended_cut_pct > 0`; length = `kept_items` for that candidate.
- [ ] Verdict obeys skill `benchmark-audit-06-cost-efficiency`. `partial` token data for >50% of runs → forced `manual_review_required`.
- [ ] No suggestion to physically delete items from `data/problems.jsonl` — subset recommendation only.

**Route**: pass → mark dimension complete for Phase 2 aggregate; fail → re-dispatch the SubAgent with skill `benchmark-audit-06-cost-efficiency`, failing report paths, the script log, and the failed checklist items. Retry cap 3.
