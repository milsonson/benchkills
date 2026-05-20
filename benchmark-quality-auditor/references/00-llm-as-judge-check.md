# Verify-and-route — 00 LLM-as-Judge

After SubAgent writes `audit/reports/00_llm_as_judge.{json,md}` and `audit/derived/llm_judge_scores.json`:

**Script**: `python <skill-root>/scripts/check_00_llm_as_judge_report.py <bench>/audit/reports/00_llm_as_judge.json`

**Checklist**:

- [ ] Coverage names ok runs, judged items, skipped items, and coverage rate.
- [ ] `audit/derived/llm_judge_scores.json` exists and has run scores, item scores, model ranking, disagreements, and skipped lists.
- [ ] `derived.judge.blind_judging == true`.
- [ ] Report or MD states judge scores were assigned before reading script scores/scorer rationales, and script comparison was post-hoc.
- [ ] Each item judgment has `run_id`, `problem_id`, `script_score`, `judge_score`, `delta`, and a short reason.
- [ ] Item reasons cite rubric/answer quality, not "matched N/10", script score, scorer rationale, or pass/fail as the basis.
- [ ] Report states whether judge scoring produced usable coverage, spread, and ranking.
- [ ] Script/judge score differences are concise notes for later dimensions, not the basis of the 00 verdict.
- [ ] Large score differences use `abs(delta) >= 0.25`.
- [ ] MD summarizes judge evaluation and judge ranking.
- [ ] No external judge API, credentials, or rerun of tested models is requested.

**Route**: pass → dispatch dimensions 01-06. Fail → re-dispatch `benchmark-audit-00-llm-as-judge` with the script log and failed checklist items. Retry cap 3.
