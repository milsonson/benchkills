# Verify-and-route — 03 Ranking Consistency

After SubAgent writes `audit/reports/03_ranking_consistency.{json,md}`:

**Script**: `python <skill-root>/scripts/check_03_ranking_consistency_report.py <bench>/audit/reports/03_ranking_consistency.json` — log to `audit/logs/03__attempt<K>.log`.

**Checklist**:

- [ ] `produced_ranking` is model-level — each `model` appears exactly once; seeds aggregated (mean `score_overall`, `n_runs_aggregated` set). A per-seed ranking belongs to dim 05.
- [ ] `produced_ranking` sorted strictly by `score` descending.
- [ ] `inversions` excludes ties (`|Δscore| < 1e-9`). MD must not narrate ties as inversions.
- [ ] Each `references_used` entry has a non-empty `source` — cite-able, not "internal lore".
- [ ] If `proxy_fallback.used == true`, no reference is reported alongside.
- [ ] `status: insufficient_overlap` → no correlation reported for that reference.
- [ ] Each inversion cites both `a_run_id`, `b_run_id`, and reference name.
- [ ] If judge scores exist, script ranking and judge ranking are both compared with references/proxies.
- [ ] Verdict cites the threshold from skill `benchmark-audit-03-ranking-consistency`.
- [ ] `manual_review_required` used only when no references AND no family has ≥3 models.

**Route**: pass → mark dimension complete for Phase 2 aggregate; fail → re-dispatch the SubAgent with skill `benchmark-audit-03-ranking-consistency`, failing report paths, the script log, and the failed checklist items. Retry cap 3.
