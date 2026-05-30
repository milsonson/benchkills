# Question checkpoint

This checkpoint is for the strong-model-hard question chain: capability blueprints, candidates, adversarial reviews, revision notes, and final `data/problems.jsonl`. User `target_count` is a hard final delivery count. The pipeline must fill it by parallel generation and regeneration, not by lowering the strong-model-hard threshold.

## Capability Blueprints

Check `data/capability_blueprints.jsonl`:

1. Legal JSONL; row count equals `target_count`.
2. Each row has non-empty `strong_model_wrong_path`, `why_strong_model_takes_it`, `nonlocal_correction`, `dependency_chain`, `non_collapsible_dependencies`, `coupled_constraints`, `one_sentence_shallow_answer`, `why_shallow_answer_fails`.
3. `non_collapsible_dependencies` has at least 3 items.
4. `coupled_constraints` has at least 2 items.
5. `difficulty == 5`.
6. Sample 3 rows manually: the wrong path must be plausible for a strong model, not a weak-model mistake or generic “missed condition”.

## Problem Candidates

Check `data/problem_candidates.jsonl`:

1. Legal JSONL; row count equals `2 * target_count`.
2. Each row has non-empty `strong_model_wrong_path`, `why_strong_model_takes_it`, `nonlocal_correction`, `where_local_reasoning_fails`, `coupled_conditions`, `condition_removal_effects`, `shortest_correct_path`, `shortest_correct_path_step_count`, `strong_model_easy_route`, `why_easy_route_fails`.
3. `coupled_conditions` has at least 2 items.
4. `shortest_correct_path_step_count >= 4`.
5. `reasoning_steps` has at least 6 items and must not be mostly generic meta-steps such as “明确目标 / 检查前提 / 复核结论”.
6. Sample 3–5 candidates manually: if the task is mainly yes/no, correctness judgment, sign judgment, or first-error identification, it must still contain dual-model competition, nonlocal correction, mutually constrained representations, or intermediate-state construction.

## Adversarial Reviews

Check `data/candidate_reviews.jsonl`:

1. Legal JSONL; row count equals `2 * target_count`.
2. Every candidate has exactly one review.
3. Each review has `shortest_correct_path`, `shortest_correct_path_step_count`, `uses_single_rule_or_definition`, `strong_model_wrong_path`, `why_strong_model_takes_it`, `nonlocal_correction`, `knockout_reason`, `strong_model_failure_point`.
4. Any review with `shortest_correct_path_step_count <= 3` must have `selected=false`.
5. Any review with `uses_single_rule_or_definition=true` must have `selected=false`.
6. Selected count must equal `target_count` before progression. If selected count is below target, stop before revision, identify the missing blueprint ids, and re-run candidate generation plus adversarial review for those blueprints in parallel. Replace old candidates/reviews for those blueprints; do not append third candidates and do not lower the threshold.
7. Sample selected reviews manually: `strong_model_wrong_path` must describe a high-confidence plausible wrong route, not just a common weak-model shortcut.

## Final Problems

Check `data/problems.jsonl` and `data/revision_notes.jsonl`:

1. Legal JSONL; row count must equal `target_count`. If revision cannot produce exactly `target_count` strong-model-hard problems, this checkpoint fails and the meta-agent must return to candidate/review or capability for the missing blueprints.
2. Required final fields: `id`, `candidate_id`, `blueprint_id`, `topic`, `difficulty`, `problem`, `answer`, `answer_type`, `acceptable_variants`, `scoring_notes`, `reasoning_steps`.
3. Strong-model-hard audit fields should be preserved unless explicitly forbidden: `strong_model_wrong_path`, `why_strong_model_takes_it`, `nonlocal_correction`, `coupled_conditions`, `shortest_correct_path`, `difficulty_gate_decision`.
4. `id == candidate_id`; `difficulty == 5`; ids unique.
5. `reasoning_steps` has at least 6 concrete, problem-specific steps.
6. `revision_notes` must include `difficulty_gate_decision`, `shallow_pass_test`, `strong_model_hardness_check`, and `actual_hardening_change`.
7. `actual_hardening_change` may not be only “保留 / 压缩字段 / 固定 difficulty / 补 reasoning_steps”.
8. Sample 3–5 final problems manually: a strong model’s likely wrong path must be visible and plausible, and the correct answer must require nonlocal correction rather than a single known rule.

Any failure above blocks progression to scoring. Re-dispatch the owning stage with the failed item ids and evidence.
