# Verify-and-route — 04 Capability Alignment

After SubAgent writes `audit/reports/04_capability_alignment.{json,md}`:

**Script**: `python <skill-root>/scripts/check_04_capability_alignment_report.py <bench>/audit/reports/04_capability_alignment.json` — log to `audit/logs/04__attempt<K>.log`.

**Checklist**:

- [ ] Comparisons stay **within one family**. Any cross-family inversion list = reject (#1 mistake).
- [ ] `ordered_runs` sorted by `size_b` ascending in every family block.
- [ ] Every inversion carries `p_value` and `significant`. Missing significance = reject.
- [ ] Per-difficulty / per-topic inversions cite the bucket name (no "some difficulty").
- [ ] If judge scores exist, within-family monotonicity is checked under both scoring modes.
- [ ] Gap magnitudes in score percentage points, not raw correct counts.
- [ ] Verdict obeys the rules in skill `benchmark-audit-04-capability-alignment`. A 0.3pt insignificant easy-bucket inversion is not a `fail`.
- [ ] Recommendation names the specific within-family comparison to investigate when failing.

**Route**: pass → mark dimension complete for Phase 2 aggregate; fail → re-dispatch the SubAgent with skill `benchmark-audit-04-capability-alignment`, failing report paths, the script log, and the failed checklist items. Retry cap 3.
