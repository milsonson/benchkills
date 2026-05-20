# Runner UI checkpoint

1. `python -m py_compile web_runner.py eval_core.py run_eval.py scorer.py` 通过。
2. 已参考 `benchmark-runner/references/runner_reference.py` 的交互流程；存在 `web_runner.py`，且提供本地交互入口；不得生成 `web/index.html`、`web/app.html`、`web/*.html` 或其它 HTML runner 文件。
3. 交互入口可填写或覆盖：`base_url`、模型列表、`max_tokens`、`concurrency`、`temperature`、seed 列表、输出目录；`Output Dir` 默认来自 config 且可修改。
4. `web_runner.py` 调用 `eval_core.py` 的 `plan_runs(...)` / `run_eval_job(...)` 或等价公共入口；如果入口名是 `run_evaluation(...)`，它必须是 `eval_core.py` 内基于 `plan_runs(...)` / `run_eval_job(...)` 的薄封装；没有复制一整套独立评测、评分、并发、落盘逻辑。
5. API key 是单一凭证模式切换：默认 env var，可切换到 paste key；不是两个并列同级输入框。
6. 运行前 preview 基于当前 `Output Dir`，能显示已有 manifest、已有 run 数、每个计划模型/seed 的 completed/remaining/total、resume/new；修改 Output Dir、模型或 seeds 后能重新检查。
7. Start 前后端做 validation；缺 base_url、凭证、模型、非法并发/max_tokens、output dir 不可写时不启动。
8. 有模型发现功能，能查询 OpenAI-compatible `/models`，失败信息展示给用户且不阻塞手动填写。
9. 有启动、状态查询、停止/取消、恢复/继续已完成输出的交互操作。
10. 交互界面重点显示每个模型/seed 已跑多少题、还剩多少题、错误数、截断数、token 用量、耗时或 ETA；截断需区分有可评分输出、无 final answer、空输出。
11. 交互界面实时显示最近 5 条样本输出，含 id、model/seed、status、score、latency、tokens、错误或截断类型，并能看出是否有 `scoreable_text`/final answer marker。
12. README 或交互帮助说明中断和异常：进程/服务中断后用同一 Output Dir 可 resume；单题 API 异常写记录并继续，整轮异常保留已落盘输出。
13. 输出格式默认是 `outputs/runs/<run_id>/{predictions.jsonl,scores.json,usage.json,run_config.redacted.json}` 和 `outputs/run_manifest.json`；用户改 Output Dir 时路径同步变化。
14. README 写明完整 venv-aware 启动命令：创建/激活 `.venv`、安装 `requirements.txt`、运行 `python web_runner.py --config config.yaml`，并说明本地 URL。不得只写 `python3 web_runner.py`。说明 API key 推荐用环境变量，粘贴 key 不写入 config、manifest、报告或日志。
15. `requirements.txt` 包含 runner 所需依赖。

1–8、12–15 必过；9–11 允许 1 项轻微瑕疵。
