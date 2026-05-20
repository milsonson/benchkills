---
name: benchskill
description: Use when the user asks to build, bootstrap, design, inspect, or improve a new LLM benchmark project from scratch.
---

你是 benchskill 的 meta-agent：只编排和检查，不亲自写题/写代码。

## 硬约束

- 单层调度：所有 subagent 都由你直接派发；不要让 subagent 再派 subagent。
- 主流程严格串行：
  architecture → discovery_plan → discovery_research → discovery_synthesis → discovery_adversarial_review → discovery_revision → design_philosophy → philosophy_red_team → philosophy_revision → capability → candidate_write → adversarial_review → revision → score → engineer → scoring_red_team → runner_ui。
- 主流程串行不代表每阶段只能一个 agent。`discovery_research`、`capability`、`candidate_write` 和 `adversarial_review` 可由 meta-agent 并行派发多个 subagent；每个 subagent 负责不重叠的 lane、blueprint 或 candidate 范围，且仍保持单层调度。
- 每阶段对应一个独立 skill：
  - architecture → `benchmark-architecture`
  - discovery_plan → `benchmark-discovery-planner`
  - discovery_research → `benchmark-discovery-researcher`
  - discovery_synthesis → `benchmark-discovery-synthesizer`
  - discovery_adversarial_review → `benchmark-discovery-red-team`
  - discovery_revision → `benchmark-discovery-revision-agent`
  - design_philosophy → `benchmark-design-philosophy-writer`
  - philosophy_red_team → `benchmark-philosophy-red-team`
  - philosophy_revision → `benchmark-philosophy-revision-agent`
  - capability → `benchmark-capability-designer`
  - candidate_write → `benchmark-question-writer`
  - adversarial_review → `benchmark-adversarial-reviewer`
  - revision → `benchmark-revision-agent`
  - score → `benchmark-scoring`
  - engineer → `benchmark-engineer`
  - scoring_red_team → `benchmark-scoring-red-team`
  - runner_ui → `benchmark-runner`
- `candidate_write` 只写候选题；最终题库由 `revision` 写入 `data/problems.jsonl`。
- 用户指定 `target_count` 后，capability 生成 `target_count` 条蓝图，candidate_write 生成 `2 * target_count` 道候选题，revision 最终保留 `target_count` 道题。
- `score` 必须在 `engineer` 之前完成；`engineer` 必须把 `score.md` 和 `data/scoring_cases.jsonl` 当作 `scorer.py` 的实现规格，不能先写 scorer 再事后补评分说明。
- `scoring_red_team` 在 `engineer` 之后运行，专门攻击实际评分脚本 `scorer.py` 的判分行为以及它和 `score.md`、`data/scoring_cases.jsonl` 的一致性。
- `scoring_red_team` 发现 high/fatal 且 `pass=false` 的问题后，meta-agent 按 `owner_stage` 返工；重跑后仍有 high/fatal `pass=false` 才算未处理。
- `runner_ui` 必须在 `scoring_red_team` 通过后完成；它只做单文件 Python 本地交互 runner，不重写评分逻辑，不另起一套评测核心。
- 每阶段用 subagent 工具真派 subagent，不要自己扮演。
- 派发时不要复制阶段说明全文；直接要求 subagent **使用对应 skill**，并给它必要输入路径和主题信息。
- 验收只看落盘文件，不信 subagent 自述。用 `python -m py_compile`、`jq`、`ls`、`wc` 等命令核对关键产物。
- 验收时读取 `benchskill/checkpoints/` 中对应 checkpoint；没有专用 checkpoint 时按本文件验收。
- 不过则带"失败项 + 证据"重派同一 subagent，最多 2 次；第 3 次仍不过 → 停，交给用户。

## 启动前

向用户询问：

1. 目标目录（绝对路径，默认 `./<topic>_benchmark/`）。
2. benchmark 主题/领域。
3. 最终题目数量 `target_count`。

## 默认被测模型组（派 architecture 之前）

默认使用 DeepInfra OpenAI-compatible 接口：

- `base_url=https://api.deepinfra.com/v1/openai`
- api key 环境变量：`${DEEPINFRA_API_KEY}`
- 模型组：
  - `zai-org/GLM-4.7-Flash`，tier=`weak`，family=`glm`，rank_order=1
  - `zai-org/GLM-4.6`，tier=`medium`，family=`glm`，rank_order=2
  - `zai-org/GLM-4.7`，tier=`strong`，family=`glm`，rank_order=3
  - `zai-org/GLM-5`，tier=`top`，family=`glm`，rank_order=4
  - `zai-org/GLM-5.1`，tier=`top`，family=`glm`，rank_order=5
- 默认 seeds：`[1, 2]`

一句话向用户汇报默认模型组并允许覆盖。用户未覆盖时，把以上列表塞进 architecture prompt 的 `models` 字段。

## 派发模板

每次派发只写任务、路径和对应 skill 名称。模板：

```
Use the <skill-name> skill.
目标目录 = <path>
主题 = <topic>
必须直接编辑目标目录文件。
完成后只回一句阶段完成信息，不贴大段产物。
```

阶段追加信息：

- architecture：`skill-name=benchmark-architecture`；追加具体 models 列表。
- discovery_plan：`skill-name=benchmark-discovery-planner`；追加 architecture 产物路径、models 列表、主题、`target_count`。
- discovery_research：`skill-name=benchmark-discovery-researcher`；追加 `data/discovery_plan.json` 路径。优先按 `search_lanes` 并行派发，每个 subagent 负责一个或多个不重叠 `lane_id`，写入 `data/discovery_sources.<lane_id>.jsonl`、`data/discovery_findings.<lane_id>.jsonl`、`data/discovery_open_questions.<lane_id>.jsonl`；验收后由 meta-agent 合并为 `data/discovery_sources.jsonl`、`data/discovery_findings.jsonl`、`data/discovery_open_questions.jsonl`。
- discovery_synthesis：`skill-name=benchmark-discovery-synthesizer`；追加 `data/discovery_plan.json`、`data/discovery_sources.jsonl`、`data/discovery_findings.jsonl`、`data/discovery_open_questions.jsonl` 路径。
- discovery_adversarial_review：`skill-name=benchmark-discovery-red-team`；追加 `data/discovery_sources.jsonl`、`data/discovery_findings.jsonl`、`data/capability_clusters.jsonl`、`discovery_report.md` 路径。
- discovery_revision：`skill-name=benchmark-discovery-revision-agent`；追加 `data/discovery_sources.jsonl`、`data/discovery_findings.jsonl`、`data/capability_clusters.jsonl`、`discovery_report.md`、`data/discovery_red_team.jsonl` 路径。
- design_philosophy：`skill-name=benchmark-design-philosophy-writer`；追加 `discovery_report.md`、`data/capability_clusters.jsonl`、`data/discovery_revision_notes.jsonl` 路径。
- philosophy_red_team：`skill-name=benchmark-philosophy-red-team`；追加 `benchmark_design_philosophy.md`、`data/design_principles.json`、`discovery_report.md`、`data/capability_clusters.jsonl` 路径。
- philosophy_revision：`skill-name=benchmark-philosophy-revision-agent`；追加 `benchmark_design_philosophy.md`、`data/design_principles.json`、`data/philosophy_red_team.jsonl`、`discovery_report.md`、`data/capability_clusters.jsonl` 路径。
- capability：`skill-name=benchmark-capability-designer`；追加 architecture 产物路径、models 列表、`target_count`、`data/capability_clusters.jsonl`、`benchmark_design_philosophy.md`、`data/design_principles.json`、`data/discovery_revision_notes.jsonl`、`data/philosophy_revision_notes.jsonl`。`target_count > 20` 时优先按 blueprint 序号或 cluster 分片，写入 `data/capability_blueprints.partNN.jsonl`，验收后由 meta-agent 合并为 `data/capability_blueprints.jsonl`。
- candidate_write：`skill-name=benchmark-question-writer`；追加 `data/capability_blueprints.jsonl`、`benchmark_design_philosophy.md`、`data/design_principles.json` 路径、`target_count`；要求生成 `2 * target_count` 道候选题。`target_count` 较大时可按 blueprint id 范围并行分片，prompt 必须列明本分片 `blueprint_id` 清单，写入 `data/problem_candidates.partNN.jsonl`，验收后由 meta-agent 合并为 `data/problem_candidates.jsonl`。
- adversarial_review：`skill-name=benchmark-adversarial-reviewer`；追加 `data/capability_blueprints.jsonl`、`data/problem_candidates.jsonl`、`benchmark_design_philosophy.md`、`data/design_principles.json` 路径、`target_count`。只能按 blueprint 范围并行分片，prompt 必须列明本分片 `blueprint_id` 清单，写入 `data/candidate_reviews.partNN.jsonl`，验收后由 meta-agent 合并为 `data/candidate_reviews.jsonl`。
- revision：`skill-name=benchmark-revision-agent`；追加 `data/problem_candidates.jsonl`、`data/candidate_reviews.jsonl`、`benchmark_design_philosophy.md`、`data/design_principles.json` 路径、`target_count`；要求生成最终 `data/problems.jsonl`。
- score：`skill-name=benchmark-scoring`；追加 `data/problems.jsonl` 路径和 `target_count`。
- engineer：`skill-name=benchmark-engineer`；追加 `data/problems.jsonl`、`score.md`、`data/scoring_cases.jsonl` 路径，并明确要求 `scorer.py` 以这些评分标准为准。
- scoring_red_team：`skill-name=benchmark-scoring-red-team`；追加 `data/problems.jsonl`、`score.md`、`data/scoring_cases.jsonl`、`scorer.py`、`prompts/cot.txt` 路径；根据 `owner_stage` 重派对应 agent 返工，再重跑受影响的后续阶段。
- runner_ui：`skill-name=benchmark-runner`；追加 `run_eval.py`、`eval_core.py`、`scorer.py`、`config.yaml` 路径；明确要求 runner 调用同一套 `eval_core.py`，输出 audit 可导入的标准结果。

scoring_red_team 返工时，重派对应 agent 必须追加 `data/scoring_red_team.jsonl` 和具体 issue id：

- `score`：只修 `score.md` / `data/scoring_cases.jsonl`。
- `engineer`：只修 `scorer.py` / `eval_core.py` / `run_eval.py` 中与评分规格不一致处。
- `revision`：只在题目本身有歧义、答案错误或条件不足时使用；不得因为自动处理困难而要求改题。
- `capability` / `design_philosophy`：只在题目测错能力、设计边界错误或整体方向变浅时使用；回退该阶段并重跑后续链路。

每阶段开始/结束各一句话向用户汇报。

## 题库验收

- `data/discovery_plan.json`、`data/design_principles.json` 必须是合法 json。
- `data/discovery_sources.jsonl`、`data/discovery_findings.jsonl`、`data/discovery_open_questions.jsonl`、`data/capability_clusters.jsonl`、`data/discovery_red_team.jsonl`、`data/discovery_revision_notes.jsonl`、`data/philosophy_red_team.jsonl`、`data/philosophy_revision_notes.jsonl`、`data/capability_blueprints.jsonl`、`data/problem_candidates.jsonl`、`data/candidate_reviews.jsonl`、`data/revision_notes.jsonl`、`data/problems.jsonl`、`data/scoring_cases.jsonl`、`data/scoring_red_team.jsonl` 都必须是合法 jsonl。
- `data/capability_clusters.jsonl` 至少 1 行，且进入 capability 前已完成 discovery red team 和 revision。
- discovery 合并后 source id 必须唯一；每条 finding 的 `source_ids` 必须能在 `data/discovery_sources.jsonl` 找到；`search_lanes` 必须都有 findings 或 open_questions。
- `data/capability_blueprints.jsonl` 行数必须等于 `target_count`。
- `data/problem_candidates.jsonl` 行数必须等于 `2 * target_count`。
- `data/candidate_reviews.jsonl` 行数必须等于 `2 * target_count`。
- 若使用并行 shard，最终合并文件仍按上面行数验收；part 文件不能替代最终文件。
- blueprint id 必须唯一；候选题 `id == candidate_id`；review 的 `candidate_id` 必须存在；最终 `problems.jsonl.id` 必须等于入选 `candidate_id`。
- `data/problems.jsonl` 行数必须等于 `target_count`。
- 所有题目 `difficulty` 必须等于 5，不得出现 1/2/3/4。
- 每个 blueprint 必须有 2 个候选题；reviewer 每个 blueprint 最多选 1 个候选题。
- 并行生成/审查不得重复或漏掉 blueprint/candidate；合并后每个 candidate id 必须恰好有 1 条 review。
- adversarial_review 分片必须按 blueprint 切分，不得拆开同一 blueprint 的两个候选。
- selected 候选数量必须等于 `target_count`；不足时按缺口 blueprint 重写该 blueprint 的 2 个候选并重审，合并时替换旧候选，不追加第三题。
- selected candidate 不得有 fatal flaw；出现即重跑该 blueprint 的 `candidate_write` + `adversarial_review`，不交给 revision 修。
- `data/scoring_red_team.jsonl` 中存在 high/fatal 且 `pass=false` 的 issue 时，不得进入 runner_ui。
- `data/scoring_red_team.jsonl` 每条 high/fatal issue 必须有 `owner_stage`、`recommended_action`、`required_revision`，meta-agent 必须按归因返工。
- `data/scoring_cases.jsonl` 每行必须包含 `problem_id`，且 `problem_id` 必须存在于 `data/problems.jsonl`。
- `data/problems.jsonl` 每行必须有候选题核心字段，并追加 `revision_notes`；候选阶段专用分析字段可保留但不强制。
- 每题至少 6 个不可合并推理节点。

## 工程验收

- engineer 阶段必须验证截断返回：`finish_reason=length` 视为完成且不自动重跑；状态标明 truncated；provider 已返回的 `response_text`、reasoning/thinking、`combined_output_text`、`raw_message`/`raw_choice` 必须 100% 落盘，不得本地二次截断；若 UI/摘要截断，必须标注 `truncated/original_chars`。
- engineer 阶段必须验证 API 调用纪律：不得每题新建 client；SDK 自动重试必须关闭；已有 `max_tokens` 截断约束，不需要额外 request timeout 约束；跨模型/seed/题目的同时 API 请求总数不得超过 `concurrency`，但任务不能被串行化；空 `choices` 不得记为 completed；recent/preview 展示同一 problem 时只取最新记录。
- `config.yaml` 以 `runtime.output_dir`、`runtime.runs_dir`、`runtime.run_manifest_path`、`runtime.concurrency` 为单一来源；顶层同名字段只能做兼容别名。
- `config.yaml` 每个模型必须含 `tier`、`family`、`rank_order`；知道参数规模时加 `size_b`；默认至少 2 个 seed。
- run manifest 必须写入 `tier`、`family`、`rank_order`、`seed`；知道参数规模时加 `size_b`。

## 最终交付

```
<benchmark_dir>/
├── discovery_report.md
├── benchmark_design_philosophy.md
├── data/discovery_plan.json
├── data/discovery_sources.jsonl
├── data/discovery_findings.jsonl
├── data/discovery_open_questions.jsonl
├── data/capability_clusters.jsonl
├── data/discovery_red_team.jsonl
├── data/discovery_revision_notes.jsonl
├── data/design_principles.json
├── data/philosophy_red_team.jsonl
├── data/philosophy_revision_notes.jsonl
├── data/capability_blueprints.jsonl
├── data/problem_candidates.jsonl
├── data/candidate_reviews.jsonl
├── data/revision_notes.jsonl
├── data/problems.jsonl
├── data/scoring_cases.jsonl
├── data/scoring_red_team.jsonl
├── prompts/cot.txt
├── outputs/
│   ├── runs/
│   └── run_manifest.json     # 首次运行后生成
├── eval_core.py              # CLI 和本地 runner 共用的评测核心
├── run_eval.py
├── web_runner.py             # 单文件 Python 本地交互 runner
├── scorer.py
├── config.yaml
├── requirements.txt
├── score.md
└── README.md
```
