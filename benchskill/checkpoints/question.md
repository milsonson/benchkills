# Question checkpoint

用 `jq` / 抽样 3–5 条检查 `data/problems.jsonl`。

1. 每行合法 JSON。
2. 行数等于 `target_count`。
3. 字段齐且非空：`id`, `blueprint_id`, `topic`, `difficulty`, `problem`, `answer`, `solution`, `key_insight`, `trap`, `why_discriminative`, `answer_type`, `acceptable_variants`, `scoring_notes`, `reasoning_steps`, `revision_notes`。
4. 每行 `id` 等于入选候选的 `candidate_id`，且 `id` 全局唯一。
5. `difficulty == 5`。
6. 每题 `reasoning_steps` 至少 6 个。
7. 抽样 2–3 道肉眼看：题意清、答案唯一或评分清，没有明显公开题模板。
8. 抽样题的 `acceptable_variants` / `scoring_notes` 能支持语义等价、格式不同但本质正确的回答，不是只写一个精确字符串。

1–6 全过 + 7–8 无明显问题 → 放行。7–8 有轻微疑虑时放行并在最终交付中提醒用户。
