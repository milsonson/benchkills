---
name: benchmark-quality-auditor
description: Use when a user points at an LLM benchmark directory with completed run outputs and asks for a benchmark quality audit, critique, or "is this benchmark good" report across completed scoring outputs and six quality dimensions.
---

# Benchmark Quality Auditor — MetaAgent Playbook

Act as the **MetaAgent**: orchestrate, don't compute. Inspect → import completed results → run LLM-as-judge SubAgent → dispatch dimension SubAgents in parallel → validate → re-inject on failure → aggregate.

## Hard constraints (non-negotiable)

- **Never modify the original benchmark.** No edits to `run_eval.py`, `scorer.py`, `config.yaml`, `data/*`, `prompts/*`, or `outputs/*`.
- **Write only under `<bench>/audit/`.** `audit/{derived,imported_runs,reports,logs}` may be silently `mkdir -p`.
- **Do not run external model APIs.** Do not ask for `base_url`, API keys, org IDs, deployment IDs, or other credentials. The 00 SubAgent judges with its own LLM reasoning over completed outputs.
- **Never edit a SubAgent's report by hand** — re-inject and let it fix it. Never skip the script check.
- All report paths are relative to `<bench>` so the audit is portable.

## Benchmark layout

```
<bench>/
├── data/problems.jsonl       # {id, problem, answer, topic, difficulty}
├── prompts/cot.txt
├── run_eval.py
├── scorer.py
├── config.yaml
├── requirements.txt
└── outputs/
    ├── run_manifest.json       # preferred completed-run index
    └── runs/<run_id>/{predictions.jsonl,scores.json,usage.json}
```

Missing required benchmark files or completed outputs → halt and list what's missing. `config.yaml` may override a path (e.g. `problems_path: data/v2/...`); trust it and record the actual path in the manifest.

## Workspace layout (this skill writes only here)

```
<bench>/audit/
├── audit_manifest.json
├── derived/model_ranking.json
├── derived/llm_judge_scores.json
├── imported_runs/<run_id>/...   # optional normalized copies/symlinks only if needed
├── reports/00_llm_as_judge.{json,md} + 0{1..6}_<name>.{json,md} + final_report.md
└── logs/<dim>__attempt<NN>.log
```

## Manifest — single source of truth

Written Phase 0 from completed outputs. All SubAgents read it.

```json
{
  "manifest_version": "1.0",
  "benchmark_path": "<abs path>",
  "created_at": "<iso8601>",
  "data": {
    "problems_path": "data/problems.jsonl",
    "num_problems": 0,
    "scorer_path": "scorer.py",
    "prompt_template_path": "prompts/cot.txt",
    "source_run_manifest_path": "outputs/run_manifest.json",
    "auxiliary_artifacts": [{"path": "", "relevance": ""}]
  },
  "experiments": [
    {"run_id": "qwen2_5_7b__seed1", "model": "Qwen2.5-7B-Instruct", "family": "qwen2.5",
     "size_b": 7.0, "seed": 1, "status": "ok|failed|import_error",
     "source": "imported",
     "predictions_path": "outputs/runs/qwen2_5_7b__seed1/predictions.jsonl",
     "scores_path": "outputs/runs/qwen2_5_7b__seed1/scores.json",
     "usage_path": "outputs/runs/qwen2_5_7b__seed1/usage.json",
     "tokens_in": 0, "tokens_out": 0, "wallclock_s": 0, "score_overall": 0.0}
  ],
  "capability_groups": [{"family": "qwen2.5", "ordered_runs": ["..."]}],
  "stability_groups": [{"model": "Qwen2.5-7B-Instruct", "run_ids": ["..."]}],
  "reference_rankings": []
}
```

`reference_rankings` empty → dim 03 falls back per its skill file.

`predictions_path`, `scores_path`, and `usage_path` may point at `outputs/runs/...` directly or at normalized files under `audit/imported_runs/...`; use relative paths either way.

## Derived ranking — shared dependency

Write `audit/derived/model_ranking.json` during Phase 0 so dimensions 03 and 06 do not depend on each other:

```json
{
  "schema_version": "1.0",
  "produced_ranking": [{"rank": 1, "run_id": "", "model": "", "score": 0.0, "n_runs_aggregated": 1}],
  "method": "mean score_overall across ok seeds; representative run is lowest seed"
}
```

## Workflow

### Phase 0 — Inspect and import completed results

1. Verify required benchmark inputs exist. If `config.yaml` overrides paths, record the resolved relative paths.

2. Locate completed results. Prefer `outputs/run_manifest.json`. If absent, ask the user for the result manifest or runs directory. Do not ask for credentials or offer to run models.

3. Import each run into `audit/audit_manifest.json`. Validate that each `ok` run has readable `predictions.jsonl`, `scores.json`, and preferably `usage.json`; missing usage becomes `null` with an import note. Runs with missing predictions or scores become `status="import_error"` and remain visible in the manifest.

4. Infer or record `family`, `size_b`, and `seed` from the run manifest/config/model names. If inference is uncertain, ask the user for a small model metadata table. Same-family ladders strengthen dim 04/05; incomplete metadata should not block validity/discriminability.

5. Build `capability_groups`, `stability_groups`, and `reference_rankings` if supplied by config or user. Empty `reference_rankings` is allowed.

6. Write `audit/derived/model_ranking.json` from `ok` runs. One row per unique model; score is mean `score_overall` across ok seeds; representative run is lowest seed.

7. Halt before SubAgents if there are fewer than 2 ok runs, or if no ok run has both predictions and scores.

### Phase 1a — LLM-as-judge audit (00)

Dispatch `00_llm_as_judge` after Phase 0 and before any 01-06 SubAgent.

1. **Dispatch SubAgent** with:

   > Invoke `benchmark-audit-00-llm-as-judge`. Inputs: `<bench>/audit/audit_manifest.json` and `<bench>/`. Outputs: `<bench>/audit/derived/llm_judge_scores.json` and `<bench>/audit/reports/00_llm_as_judge.{json,md}`. Touch no other files. Do not request external APIs or credentials.

2. **Script check**: `python <skill-root>/scripts/check_00_llm_as_judge_report.py <bench>/audit/reports/00_llm_as_judge.json`, log to `audit/logs/00__attempt<K>.log`.

3. **Semantic check**: apply `<skill-root>/references/00-llm-as-judge-check.md`.

4. **Branch**:

   - Both pass → continue to Phase 1b.
   - Either fails → re-dispatch `benchmark-audit-00-llm-as-judge` with the script log and failed checklist items.
   - Retry cap **3**. On the 3rd failure, stub `00_llm_as_judge.json` with `summary.verdict="manual_review_required"` and continue; later dimensions must state that judge data is unavailable.

### Phase 1b — Per-dimension audits (parallel 01–06)

Dispatch all six dimensions in parallel after Phase 1a finishes. Each dimension reads `<bench>/audit/audit_manifest.json`, `<bench>/audit/derived/model_ranking.json` when needed, `<bench>/audit/derived/llm_judge_scores.json` when available, and benchmark files.

Each SubAgent must invoke the real Codex skill for its dimension:

| Dimension | Skill |
| --- | --- |
| `01_validity` | `benchmark-audit-01-validity` |
| `02_discriminability` | `benchmark-audit-02-discriminability` |
| `03_ranking_consistency` | `benchmark-audit-03-ranking-consistency` |
| `04_capability_alignment` | `benchmark-audit-04-capability-alignment` |
| `05_robustness_stability` | `benchmark-audit-05-robustness-stability` |
| `06_cost_efficiency` | `benchmark-audit-06-cost-efficiency` |

For each dimension `NN`, manage its validation independently:

1. **Dispatch SubAgent** with:
   
   > Invoke `<dimension-skill>`. Inputs: `<bench>/audit/audit_manifest.json`, `<bench>/audit/derived/llm_judge_scores.json` if present, and `<bench>/`. Outputs: `<bench>/audit/reports/<NN>_<name>.{json,md}`. Touch no other files. Stop when both exist.

2. **Script check**: `python <skill-root>/scripts/check_<NN>_<name>_report.py <bench>/audit/reports/<NN>_<name>.json`, log to `audit/logs/<NN>__attempt<K>.log`. Exit 0 = structural pass.

3. **Semantic check**: apply `<skill-root>/references/<NN>-<name>-check.md`.

4. **Branch**:
   
   - Both pass → mark that dimension complete.
   - Either fails → re-dispatch the same dimension skill with: failing report paths, the script log, and the list of failed checklist items.
   - Retry cap **3** (dispatch errors count toward the cap). On the 3rd failure, stub `<NN>_<name>.json` with `summary.verdict="manual_review_required"` and `_failure_log` covering every attempt, then advance.

Do not wait for dimensions in numeric order. Validate and re-inject each dimension as soon as it finishes. Aggregation waits for dimensions 01-06 to have a passed report or a manual-review stub.

### Phase 2 — Aggregate

1. Load `00_llm_as_judge.json` and all six 01-06 `<NN>_*.json`.
2. Surface cross-dimension conflicts explicitly (e.g., dim 03 says rankings agree but dim 04 finds within-family inversions → flag both; don't silently reconcile).
3. Include a short "Evidence Across Scoring Modes" section: script-score signal, judge-score signal, agreement/disagreement, and what that means for the benchmark.
4. Base the overall verdict on the combined evidence from data quality, score signals, ranking/alignment, stability, and cost. Do not let one scoring component dominate unless it is the only usable signal.
5. Write `audit/reports/final_report.md`: one-line overall verdict + headline numbers, per-dimension verdicts with the single most important finding each, cross-cutting issues, prioritized recommendations, cost-vs-quality table.
6. Surface the path to the user.
