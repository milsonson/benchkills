---
name: benchmark-audit-01-validity
description: Use when auditing the validity dimension of an LLM benchmark quality audit as a dispatched SubAgent.
---

# SubAgent — Dimension 01: Validity

Audit whether the benchmark is **legal, unambiguous, and fairly graded** — a score you can trust.

## Inputs

- `<bench>/data/problems.jsonl` — requires `id, problem, answer, topic, difficulty`.
- `<bench>/scorer.py`, `<bench>/prompts/cot.txt`.
- `<bench>/audit/audit_manifest.json` + each run's `predictions.jsonl`.
- `<bench>/audit/derived/llm_judge_scores.json` if present.

Also read anything in `manifest.data.auxiliary_artifacts[]` relevant here (README, prior validity audits, scorer unit tests, alternate answer keys). Cite the relative path when an extra artifact informs a conclusion. Required files stay authoritative.

## Checks (all of them)

1. **Schema integrity** — all required fields present, non-empty, correct types, unique `id`s.
2. **Answer uniqueness** — sample ≥30 items (or all) with `random.Random(0)` and read them. Flag items with multiple defensible answers not covered by the rubric.
3. **Ambiguity** — missing units, unstated assumptions, multiple defensible interpretations.
4. **Duplicates** — exact and near-duplicate `problem` strings.
5. **Contamination signals** — verbatim well-known problems, dataset boilerplate ("Problem from AIME 2003"), URLs, leaked solutions in the text.
6. **Scoring modes** — compare script scores and judge scores when available. Note where either scoring mode exposes rubric or item issues.
7. **Implementation notes** — mention script scorer limitations only when they affect interpretation of benchmark results.

Every flagged problem must cite an `id`. Implementation-specific scorer notes should be concise and cite `scorer.py:LINE` only when needed.

## Output schema — `01_validity.json`

```json
{
  "dimension": "01_validity",
  "schema_version": "1.0",
  "summary": {"verdict": "pass|warn|fail|manual_review_required", "score": 0.0, "headline": ""},
  "checks": {
    "schema_integrity": {"num_problems": 0, "missing_field_ids": [], "duplicate_ids": [], "passed": true},
    "answer_uniqueness": {"sampled_ids": [], "non_unique_answer_ids": [], "passed": true},
    "ambiguity": {"sampled_ids": [], "ambiguous_ids": [], "examples": [{"id": "", "reason": ""}]},
    "duplicates": {"exact_duplicate_clusters": [["id1","id2"]], "near_duplicate_clusters": [["id1","id3"]]},
    "contamination_signals": {"suspect_ids": [], "examples": [{"id": "", "signal": ""}]},
    "scoring_modes": {
      "script_view": {"usable": true, "notes": ""},
      "judge_view": {"usable": true, "notes": ""},
      "differences": [{"problem_id": "", "run_id": "", "script_score": 0.0, "judge_score": 0.0, "interpretation": ""}]
    },
    "implementation_notes": [{"location": "scorer.py:LINE", "note": ""}]
  },
  "evidence": {
    "sampling_seed": 0,
    "sample_size_per_check": {"answer_uniqueness": 0, "ambiguity": 0, "scoring_mode_examples": 0}
  },
  "recommendations": [{"priority": "high|med|low", "action": ""}]
}
```

`01_validity.md` mirrors the JSON with sections `## Verdict`, `## Headline numbers`, `## Findings` (one subsection per check with cited IDs), `## Recommendations`.

## Verdict

- `fail`: schema/gold/rubric problems make benchmark scores untrustworthy.
- `warn`: ≥3 ambiguous items, any contamination signal, or scoring-mode differences that reveal unclear rubric/item design.
- `pass`: otherwise.

Stop when both files exist and verdict is applied.
