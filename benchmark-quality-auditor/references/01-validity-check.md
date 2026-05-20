# Verify-and-route — 01 Validity

After SubAgent writes `audit/reports/01_validity.{json,md}`:

**Script**: `python <skill-root>/scripts/check_01_validity_report.py <bench>/audit/reports/01_validity.json` — log to `audit/logs/01__attempt<K>.log`. Exit 0 = structural pass.

**Checklist** (each unchecked item is a re-inject reason):

- [ ] Headline matches the verdict. A `fail` headline can't say "looks clean".
- [ ] Every flagged problem carries an `id`. Findings without IDs are unverifiable.
- [ ] Validity findings focus on problem text, gold answers, rubric clarity, ambiguity, duplicates, and contamination.
- [ ] If `audit/derived/llm_judge_scores.json` exists, scoring-mode differences are used as evidence for rubric/item clarity, not as the main topic.
- [ ] Implementation notes are concise; any `scorer.py:LINE` citation supports interpretation of results.
- [ ] `sampling_seed` recorded and deterministic (default `0`).
- [ ] MD `## Findings` mirrors JSON checks — no claim in MD without a JSON counterpart.
- [ ] Recommendations prioritize benchmark/rubric fixes before scoring-component calibration unless implementation is the only material issue.
- [ ] Verdict rule from skill `benchmark-audit-01-validity` applied correctly.

**Route**: all checked AND exit 0 → mark dimension complete for Phase 2 aggregate. Otherwise re-dispatch the SubAgent with skill `benchmark-audit-01-validity`, failing report paths, the script log, the failed checklist items, and the instruction: *"Overwrite `01_validity.{json,md}` to address every item. Do not write any other files."* Retry cap 3 → stub `manual_review_required` and mark dimension complete.
