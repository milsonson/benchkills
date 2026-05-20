# Architecture checkpoint

1. 存在：`data/problems.jsonl`（空占位可）、`prompts/cot.txt`、`outputs/`、`outputs/runs/`、`eval_core.py`、`run_eval.py`、`web_runner.py`、`scorer.py`、`config.yaml`、`requirements.txt`、`README.md`；不得生成 `web/index.html`、`web/app.html` 或其它 HTML runner 文件。
2. `python -m py_compile eval_core.py run_eval.py web_runner.py scorer.py` 通过。
3. `config.yaml` 可 YAML 解析；`models` 是非空列表，每项含 `name` / `provider` / `tier` / `family` / `rank_order`；`name` 非占位符（排除 `model-name-here`、`TODO`、`example-model`）；api key 以 `${ENV_VAR}` 引用；包含 `runtime.output_dir` / `runtime.runs_dir` / `runtime.run_manifest_path` / `runtime.concurrency`。
4. `prompts/cot.txt` 是可用 prompt，非占位符，并要求稳定的最终答案标记（如 `Final answer:`）。
