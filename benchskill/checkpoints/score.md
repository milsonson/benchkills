# Score checkpoint

读 `<benchmark_dir>/score.md` 和 `<benchmark_dir>/data/scoring_cases.jsonl`：

1. `score.md` 存在且非空，基于当前题库实际题型，不是泛泛模板。
2. 讲清总分刻度、完全正确 / 基本正确 / 部分正确 / 方向对答案错 / 完全错等档位。
3. 按 `answer_type` 说明抽取、归一化、等价判断和过程分，覆盖数字、符号/文本、列表/结构化、推理证明等实际出现的类型。
4. 明确鲁棒性规则：格式、措辞、大小写、空白、LaTeX、合理精度、单位换算、表达式等价、列表顺序等非实质差异不得误判为错。
5. 明确实质错误与特殊情况：截断、拒答、解析失败、多个冲突答案、只给推理不落最终答案。
6. `data/scoring_cases.jsonl` 存在、每行合法 JSON，字段齐：`id`, `problem_id`, `case_type`, `model_answer`, `expected_extracted_answer`, `expected_min_score`, `expected_max_score`, `why`。
7. 设题目数为 `N`：scoring cases 至少 `min(max(12, N), 2*N)` 行，覆盖至少 `min(N, max(6, ceil(N/2)))` 道题；每种实际出现的 `answer_type` 至少 3 条 case；并包含“正确但格式/表达不同”的正例、“部分正确”、“方向对但最终错”、“完全错”。

1–7 必过；否则重派 score subagent。
