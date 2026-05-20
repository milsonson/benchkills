# Engineer checkpoint

1. `python -m py_compile eval_core.py run_eval.py scorer.py` 通过。
2. `run_eval.py` 读 `config.yaml` + `data/problems.jsonl` + `prompts/cot.txt`，调用 `eval_core.py`，按模型产出 `outputs/runs/<run_id>/` 结果文件。
3. 断点续跑：能看到按 id 跳过已完成样本的逻辑。
4. 并发控制：`asyncio.Semaphore` / `ThreadPoolExecutor(max_workers=...)` / config 并发字段三选一可见。
5. `eval_core.py` 有 `plan_runs(...)` 和 `run_eval_job(...)` 或等价公共入口；runner 无需重写核心逻辑即可做 preview、进度、停止和 resume。
6. 错误分流：截断（max_tokens/length）不重试；api_error/network 指数退避重试。
7. 保存字段含 think/reasoning/thinking、最终回答、`combined_output_text`、`scoreable_text`，并尽量保留可 JSON 化的 raw message/choice 摘要。
8. 截断状态不能混成正常 completed；能看到 `truncated_with_scoreable_output` / `truncated_no_final_answer` / `truncated_empty_output` 或等价分类。默认 resume 不应反复重跑这些 terminal bad generations，但统计里必须暴露。
9. `scorer.py` 抽取格式与 `prompts/cot.txt` 输出格式对齐；评测核心调用 scorer 时不得只依赖可能为空的 `response_text`，应使用 `scoreable_text` 或等价合并文本。
10. `scorer.py` 明显读取或实现了 `score.md` 中的评分口径，并支持 `data/scoring_cases.jsonl` 自检。
11. 判分逻辑不是全文精确匹配；能看到按题型归一化/等价判断/部分分/错误原因输出。
12. 每个 run 输出 `predictions.jsonl`、`scores.json`、`usage.json`；`scores.json` 含 per-problem correctness；`outputs/run_manifest.json` 记录 run 元数据、模型 metadata、相对路径、token、耗时、总分。
13. README 说明 scoring cases 自检命令，或 `scorer.py`/`run_eval.py` 提供可运行的自检入口。

1–13 必过。
