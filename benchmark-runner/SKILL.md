---
name: benchmark-runner
description: Use when adding a single-file Python local runner for a benchmark so users can configure API/model settings, preview resume state, run evaluations, and export audit-compatible outputs.
---

你是 benchmark 本地 runner subagent。把现有 CLI 评测核心包装成一个本地网站。runner 逻辑只放在 `web_runner.py`；HTML/CSS/JS 内嵌在这个 `.py` 文件里，不生成独立 HTML 文件，不改题库、评分标准或另写一套评测逻辑。可更新 `requirements.txt` 和 `README.md`。

## 输入

- `eval_core.py`：唯一评测核心，runner 必须调用它。
- `run_eval.py`：CLI 入口，用于对齐参数含义。
- `scorer.py`：评分逻辑，不要重写。
- `config.yaml`：默认配置来源。

## 示例

`references/runner_reference.py`：参考交互结构；不要照抄其中的 HTML 或静态文件部分。

## 硬性

- **共享核心**：`web_runner.py` 必须调用 `eval_core.py` 的 `plan_runs(...)` / `run_eval_job(...)` 或等价公共入口；不得复制粘贴一份并发、重试、评分、落盘逻辑。
- **配置入口**：交互入口至少支持填写/覆盖 `base_url`、模型列表、`max_tokens`、`concurrency`、`temperature`、seed 列表、输出目录。
- **默认配置**：默认读取 `config.yaml` 中的 DeepInfra OpenAI-compatible 设置；默认 `base_url` 应显示为 `https://api.deepinfra.com/v1/openai`，默认凭证环境变量为 `DEEPINFRA_API_KEY`。
- **并行要求：不仅支持并行，还支持跨模型的并行。**
- **并发上限**：runner 调用共享核心时，跨模型、跨 seed、跨题目的同时 API 请求总数不得超过 `concurrency`；复用 client 不能把任务变成串行。
- **Output Dir 是单一来源**：`Output Dir` 默认来自 `config.yaml runtime.output_dir`，用户可修改。运行前检查、已跑状态、resume preview、已有 manifest、最近输出、最终写入位置都必须基于当前 `Output Dir` 输入框，而不是写死 `outputs/`。
- **运行前预览**：Start 前必须基于当前 Output Dir 显示已有多少 run、每个计划模型/seed 已完成多少题、还剩多少题、哪些会 resume、哪些是 new、已有 `run_manifest.json` 的时间和 run 数。用户修改 Output Dir、模型或 seeds 后应重新检查。
- **启动前校验**：Start 前必须校验 `base_url`、凭证模式、模型列表、output dir 可写或可创建、`concurrency`、`max_tokens`、预计 run 数；失败时不启动并直接显示原因。
- **模型发现**：提供模型发现动作。填写 `base_url` 和凭证后，由 `web_runner.py` 请求 OpenAI-compatible `/models`，返回全部模型 ID 列表供用户选择或复制；失败时显示原因，不影响手动填写。
- **运行控制**：提供启动、查看状态、停止/取消（尽力而为即可）、继续/恢复已完成输出的入口。
- **进度可见**：交互入口重点显示每个模型/seed 已跑多少题、还剩多少题、错误数、截断数、token 用量、耗时或 ETA；不要堆太细的内部指标。
- **截断可见**：不要只显示 generic truncated。状态里区分有可评分输出的截断、无 final answer 的截断、空输出截断、API error。截断视为已完成样本，不自动重跑；如用户手动 rerun，仅提示可调整 max_tokens、prompt 或模型参数。
- **最近输出**：交互入口实时显示最近 5 条样本输出，含 problem id、model/seed、status、score、latency、token 数、error、截断类型，以及是否有 `scoreable_text`/final answer marker。
- **最近输出去重**：同一 run/problem 多次落盘时，只显示最新记录，避免旧 api_error 覆盖后续成功结果。
- **中断恢复**：说明并实现断点续跑。浏览器关闭、服务重启或手动 Stop 后，再用同一 Output Dir、模型和 seed 启动时，必须跳过已完成题目继续跑；truncated 样本也算已完成。
- **异常处理**：单题 API error/断连不应杀死整轮；写入错误记录并继续。整轮级错误要在交互入口展示，保留已落盘输出，下一次可 resume。
- **结果可审计**：默认输出是 `outputs/runs/<run_id>/{predictions.jsonl,scores.json,usage.json}` 和 `outputs/run_manifest.json`；用户改 Output Dir 后，对应改为 `<output_dir>/runs/...` 和 `<output_dir>/run_manifest.json`。
- **可读摘要**：每个 run 目录保留 `run_config.redacted.json`，交互入口显示 manifest、run 目录、predictions/scores/usage 路径。
- **凭证安全**：README 明确建议使用环境变量；如果支持在交互入口输入 API key，只能进入本地进程内存，不写入 `config.yaml`、manifest、报告或日志。
- **依赖最小**：优先 FastAPI/Flask 二选一；`requirements.txt` 补齐依赖。
- **可启动**：README 必须给出完整 venv-aware 命令：`python3 -m venv .venv`、`source .venv/bin/activate`、`python -m pip install -r requirements.txt`、`python web_runner.py --config config.yaml`，并说明本地 URL。不要只写 `python3 web_runner.py` 或系统 Python 命令。

## 交互要求

- 默认标题用 `Benchmark Runs` 或同等任务导向标题。
- 第一屏/主菜单同时能看到配置、已跑状态、运行状态、最近输出；不要把已跑状态藏在深层菜单。
- 文案短小明确，所有失败原因直接显示。

## 交付

- `web_runner.py`
- 更新 `requirements.txt`
- 更新 `README.md` 的 runner 运行说明

落盘后回一句 "本地 runner 已完成"。不贴代码。
