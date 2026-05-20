# Benchkills

<img width="992" height="1586" alt="6aa82528716123f67eecef4a50e5c642" src="https://github.com/user-attachments/assets/fe26cb31-6294-4bfb-8823-c5351cc95dad" />

Benchkills is a coordinated collection of skills for designing, implementing, running, and auditing LLM benchmarks.

The repository is meant for Codex/Claude-style local skill systems. Each top-level directory is a skill directory containing a `SKILL.md`, and some skills include supporting scripts, references, or checkpoints.

The main orchestration skill is [`benchskill`](benchskill/SKILL.md). It coordinates the full benchmark lifecycle, from discovery to a runnable evaluator and post-run quality audit.

## Why This Exists

Many LLM benchmarks fail in predictable ways:

- they measure what is easy to score rather than what is worth measuring
- they turn deep abilities into shallow classification, extraction, or formatting tasks
- they copy the shape of public benchmarks too closely
- they rely on long prompts, noisy symbols, or awkward wording instead of real difficulty
- they have weak review loops, so shallow candidates get polished instead of rejected
- they have runnable evaluation code, but the benchmark itself lacks discriminative power

Benchkills is designed to prevent those failure modes. It separates benchmark creation into explicit phases, and each phase has a skill whose job is narrow enough to be reviewed, retried, and improved.

The core design stance is:

> Engineering constraints are guardrails. The central work is discovering, designing, and preserving deep benchmark signal.

That means the early benchmark-design skills emphasize capability depth, expert behavior, strong-model failure mechanisms, anti-template design, and candidate quality. Engineering structure still exists, but it should not dominate discovery, philosophy, blueprinting, writing, or review.

## Repository Layout

### Orchestration

- [`benchskill/`](benchskill/SKILL.md)  
  Meta-agent skill for building a benchmark from scratch. It dispatches the component skills in sequence, validates stage outputs, retries failed stages, and keeps the workflow moving.

### Benchmark Architecture And Setup

- [`benchmark-architecture/`](benchmark-architecture/SKILL.md)  
  Creates the initial benchmark project skeleton, config, prompts, placeholders, and README.

### Discovery

These skills gather and refine evidence before any benchmark philosophy or tasks are written.

- [`benchmark-discovery-planner/`](benchmark-discovery-planner/SKILL.md)  
  Plans online research around deep capabilities, failure mechanisms, expert actions, anti-template task shapes, and existing benchmark blind spots.

- [`benchmark-discovery-researcher/`](benchmark-discovery-researcher/SKILL.md)  
  Collects online evidence from papers, benchmark docs, eval reports, model cards, real workflows, issues, failures, and expert sources. Findings focus on capability implications and failure mechanisms rather than easy implementation.

- [`benchmark-discovery-synthesizer/`](benchmark-discovery-synthesizer/SKILL.md)  
  Converts raw findings into capability clusters, with explicit attention to expert behavior, deep task potential, boundary cases, and shallow proxy risks.

- [`benchmark-discovery-red-team/`](benchmark-discovery-red-team/SKILL.md)  
  Attacks discovery conclusions before they enter design. It checks whether claims are supported, too broad, benchmark-overlapping, shallow, or missing real failure mechanisms.

- [`benchmark-discovery-revision-agent/`](benchmark-discovery-revision-agent/SKILL.md)  
  Revises discovery outputs after red-team review, narrowing overclaims, deferring weak clusters, and preserving only evidence-backed directions.

### Design Philosophy

These skills translate discovery into benchmark taste.

- [`benchmark-design-philosophy-writer/`](benchmark-design-philosophy-writer/SKILL.md)  
  Writes the benchmark design philosophy and design principles. This stage decides what the benchmark should value, what it should avoid, what legitimate difficulty looks like, and what would be shallow.

- [`benchmark-philosophy-red-team/`](benchmark-philosophy-red-team/SKILL.md)  
  Attacks the design philosophy for unclear constructs, conflicting principles, weak non-goals, shallow proxy drift, overbreadth, and unsupported claims.

- [`benchmark-philosophy-revision-agent/`](benchmark-philosophy-revision-agent/SKILL.md)  
  Revises philosophy after red-team review, keeping it difficult, novel, anti-template, and discriminative.

### Blueprinting And Problem Writing

These skills convert design principles into actual benchmark items.

- [`benchmark-capability-designer/`](benchmark-capability-designer/SKILL.md)  
  Writes capability blueprints. A blueprint is not a problem statement or a format spec. It is a capability skeleton: target capability, failure mechanism, required reasoning steps, anti-template constraints, and difficulty levers.

- [`benchmark-question-writer/`](benchmark-question-writer/SKILL.md)  
  Generates two original candidate problems per blueprint. It emphasizes deep ability chains, condition sensitivity, tempting wrong shortcuts, expert moves, and unambiguous final conclusions.

- [`benchmark-adversarial-reviewer/`](benchmark-adversarial-reviewer/SKILL.md)  
  Reviews candidate problems and selects at most one per blueprint. It attacks candidates with shortest-path, template-substitution, noise-deletion, medium-model-shortcut, condition-sensitivity, expert-value, and strong-model-failure tests.

- [`benchmark-revision-agent/`](benchmark-revision-agent/SKILL.md)  
  Produces the final `data/problems.jsonl` from selected candidates, revising local ambiguity or depth issues without trying to rescue candidates with fatal flaws.

### Scoring And Engineering

These skills turn a completed problem set into a runnable evaluation pipeline.

- [`benchmark-scoring/`](benchmark-scoring/SKILL.md)  
  Writes the scoring specification and scoring cases for the final problem set.

- [`benchmark-engineer/`](benchmark-engineer/SKILL.md)  
  Implements the runnable evaluation code: model calls, concurrency, resumability, scoring, output manifests, predictions, scores, and usage logs.

- [`benchmark-scoring-red-team/`](benchmark-scoring-red-team/SKILL.md)  
  Attacks the implemented scorer and checks consistency between problems, scoring cases, `score.md`, prompts, and `scorer.py`.

- [`benchmark-runner/`](benchmark-runner/SKILL.md)  
  Adds a local runner UI around the same evaluation core.

### Quality Audit

These skills audit completed benchmark runs.

- [`benchmark-quality-auditor/`](benchmark-quality-auditor/SKILL.md)  
  Meta-agent skill for post-run quality audits. It imports completed outputs, dispatches LLM-as-judge and dimension audit skills, validates reports, and aggregates a final report.

- [`benchmark-audit-00-llm-as-judge/`](benchmark-audit-00-llm-as-judge/SKILL.md)  
  Performs blind LLM-as-judge scoring over completed predictions before comparing to script scores.

- [`benchmark-audit-01-validity/`](benchmark-audit-01-validity/SKILL.md)  
  Checks benchmark validity, schema integrity, gold quality, rubric quality, and score trustworthiness.

- [`benchmark-audit-02-discriminability/`](benchmark-audit-02-discriminability/SKILL.md)  
  Evaluates whether the benchmark separates models meaningfully.

- [`benchmark-audit-03-ranking-consistency/`](benchmark-audit-03-ranking-consistency/SKILL.md)  
  Checks whether model rankings are coherent and stable against available references or proxies.

- [`benchmark-audit-04-capability-alignment/`](benchmark-audit-04-capability-alignment/SKILL.md)  
  Checks whether measured scores align with intended capability tiers and model families.

- [`benchmark-audit-05-robustness-stability/`](benchmark-audit-05-robustness-stability/SKILL.md)  
  Evaluates run-to-run stability, seed sensitivity, and robustness.

- [`benchmark-audit-06-cost-efficiency/`](benchmark-audit-06-cost-efficiency/SKILL.md)  
  Evaluates cost, latency, token usage, and quality tradeoffs.

### Additional Experimental Or Supporting Skills

Some directories are specialized or experimental helpers:

- `benchmark-freeze-agent/`
- `benchmark-measurement-analyst/`
- `benchmark-pilot-evaluator/`
- `benchmark-solver-calibrator/`
- `benchmark-task-family-proposer/`
- `benchmark-task-family-red-team/`
- `benchmark-task-family-revision-agent/`
- `benchmark-task-family-selector/`

These can be used in expanded workflows, but `benchskill` is the main entry point for the current end-to-end benchmark pipeline.

## End-To-End Workflow

When using `benchskill`, the intended workflow is:

```text
architecture
-> discovery_plan
-> discovery_research
-> discovery_synthesis
-> discovery_adversarial_review
-> discovery_revision
-> design_philosophy
-> philosophy_red_team
-> philosophy_revision
-> capability
-> candidate_write
-> adversarial_review
-> revision
-> score
-> engineer
-> scoring_red_team
-> runner_ui
```

### 1. Architecture

Creates the project skeleton and baseline configuration.

Expected outputs include:

- `config.yaml`
- `prompts/cot.txt`
- `data/*.jsonl` placeholders
- `eval_core.py`
- `run_eval.py`
- `scorer.py`
- `web_runner.py`
- `README.md`

### 2. Discovery

The discovery phase is evidence-driven. It should answer:

- What capabilities are actually worth measuring?
- Where do strong models fail?
- What expert moves are missing from shallow tasks?
- What existing benchmarks already cover the obvious cases?
- Which task shapes have depth potential?
- Which task shapes would collapse into templates, extraction, classification, or public benchmark variants?

Discovery outputs include:

- `data/discovery_plan.json`
- `data/discovery_sources.jsonl`
- `data/discovery_findings.jsonl`
- `data/discovery_open_questions.jsonl`
- `data/capability_clusters.jsonl`
- `discovery_report.md`
- `data/discovery_red_team.jsonl`
- `data/discovery_revision_notes.jsonl`

### 3. Design Philosophy

This phase turns discovery into taste.

It should make explicit:

- what the benchmark values
- what it refuses to measure
- what counts as meaningful difficulty
- what counts as fake or dirty difficulty
- what kinds of novelty matter
- how to select between candidate directions
- what future reviewers should attack

Outputs include:

- `benchmark_design_philosophy.md`
- `data/design_principles.json`
- `data/philosophy_red_team.jsonl`
- `data/philosophy_revision_notes.jsonl`

### 4. Capability Blueprints

Each blueprint should describe the ability a problem must require.

Good blueprints:

- start from a real failure mechanism
- specify a concrete capability chain
- identify tempting wrong shortcuts
- explain why formula or template application is insufficient
- preserve room for two distinct candidate problems
- avoid writing the problem too early

Output:

- `data/capability_blueprints.jsonl`

### 5. Candidate Writing

Each blueprint gets two candidate problems.

Good candidates:

- are original
- are unambiguous
- require the intended ability chain
- contain a tempting but wrong shortcut
- have condition-sensitive answers
- are short but dense
- avoid public benchmark shapes and field extraction tasks

Output:

- `data/problem_candidates.jsonl`

### 6. Adversarial Review

The review stage selects at most one candidate per blueprint.

The reviewer should attack:

- shortest answer path
- template substitution
- removable noise
- medium-model shortcuts
- weak condition sensitivity
- missing expert value
- unclear strong-model failure mode

Output:

- `data/candidate_reviews.jsonl`

### 7. Revision

Revision produces the final problem set. It should fix local problems but not rescue fundamentally shallow candidates.

Output:

- `data/problems.jsonl`
- `data/revision_notes.jsonl`

### 8. Scoring And Engineering

Only after the problem set is finalized should scoring and engineering dominate.

Outputs include:

- `score.md`
- `data/scoring_cases.jsonl`
- `scorer.py`
- `eval_core.py`
- `run_eval.py`
- `web_runner.py`
- `outputs/run_manifest.json`
- `outputs/runs/<run_id>/predictions.jsonl`
- `outputs/runs/<run_id>/scores.json`
- `outputs/runs/<run_id>/usage.json`

### 9. Quality Audit

After runs are complete, the quality auditor imports results and evaluates the benchmark across multiple quality dimensions.

Outputs are written under:

- `audit/`

## Design Principles

The benchmark-design side of this repository follows these principles.

### Capability First

Start from what is worth measuring, not what is easiest to implement.

### Failure Mechanisms Matter

A benchmark item should make it clear how a strong model can fail. "Hard" is not enough; the failure should be attributable to a specific missed judgment, wrong abstraction, bad binding, false shortcut, or boundary error.

### Anti-Template By Construction

Problems should not be standard tasks with new numbers or stories. They should break common shortcuts, public benchmark memory, and obvious formula application.

### Ambiguity Is A Quality Defect

Problems must be unambiguous. This is not an engineering preference; it is part of problem quality.

### Engineering Is A Guardrail

The workflow still requires structured artifacts, stable IDs, valid JSON/JSONL, and runnable code. But those constraints exist to preserve and evaluate benchmark signal, not to define what a good task is.

### Review Should Reject, Not Polish Everything

Fatal candidate flaws should send work back to writing or blueprinting. Revision should not turn shallow questions into heavily annotated shallow questions.

## Installation

Clone this repository and copy the skill directories into your local skill directory.

For Codex:

```bash
git clone git@github.com:milsonson/benchkills.git /tmp/benchkills
cp -r /tmp/benchkills/* ~/.codex/skills/
```

For Claude Code:

```bash
git clone git@github.com:milsonson/benchkills.git /tmp/benchkills
cp -r /tmp/benchkills/* ~/.claude/skills/
```

If you already have existing versions of these skills, inspect changes before overwriting.

## Updating An Existing Install

From a clone:

```bash
git pull
cp -r ./* ~/.codex/skills/
```

Or sync only selected skills:

```bash
cp -r benchmark-question-writer ~/.codex/skills/
cp -r benchmark-adversarial-reviewer ~/.codex/skills/
```

## Usage Examples

### Build A Benchmark From Scratch

Invoke the `benchskill` skill and provide:

- target directory
- benchmark topic
- target number of final problems
- optional model list

The meta-agent will dispatch each stage and validate outputs.

### Write Candidate Problems Only

Use `benchmark-question-writer` when you already have:

- `data/capability_blueprints.jsonl`
- `benchmark_design_philosophy.md`
- `data/design_principles.json`

### Review Candidate Problems

Use `benchmark-adversarial-reviewer` when you already have:

- `data/capability_blueprints.jsonl`
- `data/problem_candidates.jsonl`
- `benchmark_design_philosophy.md`
- `data/design_principles.json`

### Audit A Completed Benchmark

Use `benchmark-quality-auditor` when you have:

- `data/problems.jsonl`
- `prompts/cot.txt`
- `scorer.py`
- completed run outputs under `outputs/`

## Expected Benchmark Project Shape

A completed benchmark project normally looks like:

```text
<benchmark_dir>/
├── discovery_report.md
├── benchmark_design_philosophy.md
├── data/
│   ├── discovery_plan.json
│   ├── discovery_sources.jsonl
│   ├── discovery_findings.jsonl
│   ├── discovery_open_questions.jsonl
│   ├── capability_clusters.jsonl
│   ├── discovery_red_team.jsonl
│   ├── discovery_revision_notes.jsonl
│   ├── design_principles.json
│   ├── philosophy_red_team.jsonl
│   ├── philosophy_revision_notes.jsonl
│   ├── capability_blueprints.jsonl
│   ├── problem_candidates.jsonl
│   ├── candidate_reviews.jsonl
│   ├── revision_notes.jsonl
│   ├── problems.jsonl
│   ├── scoring_cases.jsonl
│   └── scoring_red_team.jsonl
├── prompts/
│   └── cot.txt
├── outputs/
│   ├── run_manifest.json
│   └── runs/
├── eval_core.py
├── run_eval.py
├── web_runner.py
├── scorer.py
├── config.yaml
├── requirements.txt
├── score.md
└── README.md
```

## Maintenance Notes

- Keep each skill focused on one stage.
- Prefer richer task-quality guidance over more format rules.
- Add engineering constraints only when they prevent real workflow failures.
- Keep scoring and engineering strict, but do not let their concerns leak into discovery and problem design.
- Do not commit generated caches; `.gitignore` excludes `__pycache__/` and `*.py[cod]`.

## License

No license has been declared yet.
