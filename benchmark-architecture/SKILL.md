---
name: benchmark-architecture
description: Use when creating the initial file layout, config, prompt placeholder, runner/scorer placeholders, and README for a new LLM benchmark project.
---

你是 benchmark 架构师 subagent。搭骨架，不写业务。

## 产出

```
<benchmark_dir>/
├── discovery_report.md        # 空占位
├── benchmark_design_philosophy.md # 空占位
├── data/discovery_plan.json   # 空占位
├── data/discovery_sources.jsonl # 空占位
├── data/discovery_findings.jsonl # 空占位
├── data/discovery_open_questions.jsonl # 空占位
├── data/capability_clusters.jsonl # 空占位
├── data/discovery_red_team.jsonl # 空占位
├── data/discovery_revision_notes.jsonl # 空占位
├── data/design_principles.json # 空占位
├── data/philosophy_red_team.jsonl # 空占位
├── data/philosophy_revision_notes.jsonl # 空占位
├── data/capability_blueprints.jsonl # 空占位
├── data/problem_candidates.jsonl    # 空占位
├── data/candidate_reviews.jsonl     # 空占位
├── data/revision_notes.jsonl        # 空占位
├── data/problems.jsonl        # 空占位
├── data/scoring_cases.jsonl   # 空占位
├── data/scoring_red_team.jsonl # 空占位
├── prompts/cot.txt            # 可直接使用的通用 CoT prompt，含稳定 final answer 输出标记
├── outputs/                   # 空目录（.gitkeep）
├── outputs/runs/              # 空目录（.gitkeep）
├── eval_core.py               # 占位评测核心，能过 py_compile
├── run_eval.py                # CLI 占位 main，能过 py_compile，后续调用 eval_core
├── web_runner.py              # 单文件 Python 本地交互 runner 占位，能过 py_compile
├── scorer.py                  # 同上
├── config.yaml
├── requirements.txt
├── score.md                   # 空占位
└── README.md                  # 目录说明 + 如何运行
```

## config.yaml 硬性

- `models` 字段**写入 meta-agent prompt 中提供的具体模型 ID 列表**，不得留 `model-name-here` / `TODO` / `example-model` 之类占位符。
- 每条至少包含 `name`、`provider`、`tier`、`family`、`rank_order`、`base_url`（如需）、`max_tokens`；知道参数规模时加 `size_b`。
- `tier` 使用 `weak` / `medium` / `strong` / `top`，供后续运行结果分组分析。
- 默认 provider 用 `deepinfra`。
- 默认 `base_url` 用 `https://api.deepinfra.com/v1/openai`。
- 默认 api key 引用 `${DEEPINFRA_API_KEY}`。
- 若 meta-agent 未提供模型列表，使用默认模型组：`zai-org/GLM-4.7-Flash`、`zai-org/GLM-4.6`、`zai-org/GLM-4.7`、`zai-org/GLM-5`、`zai-org/GLM-5.1`。
- 写入用户指定的 `target_count`；不得硬编码题目数量。
- 默认写入顶层 `seeds` 列表，至少 2 个 seed，例如 `[1, 2]`；不要写成单数 `seed`，单数只能由后续代码作为兼容别名读取。
- api key 必须用 `${ENV_VAR}` 引用，不得硬编码。
- 并发必须大于32。
- 包含 `runtime.output_dir: outputs`、`runtime.runs_dir: outputs/runs`、`runtime.run_manifest_path: outputs/run_manifest.json`、`runtime.concurrency`。不要再维护第二套顶层输出路径。

## prompt 硬性

- `prompts/cot.txt` 必须要求模型把最终答案放在稳定、易抽取的标记下，例如 `Final answer:`。
- prompt 应要求模型尽早输出可见的 `Final answer:`，避免把全部 token 花在 hidden reasoning/thinking 中；可以简短解释，但最终答案必须可见。

## 交付

落盘后回一句 "架构已完成，路径：<path>"。不贴报告。
