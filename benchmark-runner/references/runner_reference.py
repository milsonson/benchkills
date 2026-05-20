"""Single-file local web runner for benchmark projects."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import eval_core


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://api.deepinfra.com/v1/openai"
DEFAULT_API_KEY_ENV = "DEEPINFRA_API_KEY"


class RunRequest(BaseModel):
    base_url: str = DEFAULT_BASE_URL
    credential_mode: str = "env"
    api_key_env: str = DEFAULT_API_KEY_ENV
    api_key: str = ""
    models: str = ""
    max_tokens: int = Field(default=12000, ge=1)
    concurrency: int = Field(default=64, ge=1)
    temperature: float = 0.0
    seeds: str = ""
    output_dir: str = "outputs"


class ModelFetchRequest(BaseModel):
    base_url: str = DEFAULT_BASE_URL
    credential_mode: str = "env"
    api_key_env: str = DEFAULT_API_KEY_ENV
    api_key: str = ""


class RunnerState:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.task: asyncio.Task[dict[str, Any]] | None = None
        self.cancel_event: asyncio.Event | None = None
        self.started_at: float | None = None
        self.status: dict[str, Any] = {
            "state": "idle",
            "message": "Idle",
            "total": 0,
            "completed": 0,
            "completed_runs": 0,
            "errors": 0,
            "truncated": 0,
            "tokens": 0,
            "elapsed_s": 0,
            "eta_s": None,
            "current_model": None,
            "current_seed": None,
            "run_id": None,
            "active_runs": [],
            "manifest": None,
            "recent_errors": [],
        }
        self._active_runs: set[str] = set()

    def public_status(self) -> dict[str, Any]:
        status = dict(self.status)
        if self.started_at and status.get("state") in {"running", "cancelling", "completed", "cancelled", "error"}:
            status["elapsed_s"] = round(time.perf_counter() - self.started_at, 1)
            completed = int(status.get("completed") or 0)
            total = int(status.get("total") or 0)
            if completed and total > completed and status.get("state") in {"running", "cancelling"}:
                status["eta_s"] = round((status["elapsed_s"] / completed) * (total - completed), 1)
        return status

    async def on_progress(self, event: dict[str, Any]) -> None:
        for key in ("total", "completed", "completed_runs", "errors", "truncated", "tokens"):
            if key in event:
                self.status[key] = event[key]
        if event.get("model"):
            self.status["current_model"] = event["model"]
        if event.get("seed") is not None:
            self.status["current_seed"] = event["seed"]
        if event.get("run_id"):
            self.status["run_id"] = event["run_id"]
        name = event.get("event")
        if name == "started":
            self._active_runs.clear()
            self.status.update({"state": "running", "message": "Running"})
        elif name == "model_started":
            self._active_runs.add(_run_label(event.get("model"), event.get("seed")))
            self.status.update({"state": "running", "message": "Running", "active_runs": sorted(self._active_runs)})
        elif name == "model_completed":
            self._active_runs.discard(_run_label(event.get("model"), event.get("seed")))
            self.status.update({"state": "running", "message": "Running", "active_runs": sorted(self._active_runs)})
        elif name == "cancelled":
            self._active_runs.clear()
            self.status.update({"state": "cancelled", "message": "Cancelled", "active_runs": []})
        elif name == "completed":
            self._active_runs.clear()
            self.status.update({"state": "completed", "message": "Completed", "active_runs": []})

    async def start(self, payload: RunRequest) -> dict[str, Any]:
        if self.task and not self.task.done():
            raise HTTPException(status_code=409, detail="A run is already active")
        validate_request(self.config_path, payload)
        self.cancel_event = asyncio.Event()
        self.started_at = time.perf_counter()
        self.status.update(
            {
                "state": "running",
                "message": "Starting",
                "completed": 0,
                "completed_runs": 0,
                "errors": 0,
                "truncated": 0,
                "tokens": 0,
                "manifest": None,
                "recent_errors": [],
            }
        )
        self.task = asyncio.create_task(self._run(payload.model_dump()))
        return self.public_status()

    async def _run(self, overrides: dict[str, Any]) -> dict[str, Any]:
        try:
            manifest = await eval_core.run_evaluation(self.config_path, overrides, self.on_progress, self.cancel_event)
            self.status["manifest"] = manifest
            self.status["state"] = manifest.get("status", "completed")
            self.status["message"] = self.status["state"].capitalize()
            return manifest
        except asyncio.CancelledError:
            self.status.update({"state": "cancelled", "message": "Cancelled"})
            raise
        except Exception as exc:  # noqa: BLE001 - surface runner-level errors to the UI.
            self.status.update({"state": "error", "message": str(exc), "recent_errors": [str(exc)]})
            raise

    async def stop(self) -> dict[str, Any]:
        if self.cancel_event:
            self.cancel_event.set()
        if self.task and not self.task.done():
            self.status.update({"state": "cancelling", "message": "Cancelling after active requests finish"})
        return self.public_status()


def _run_label(model: Any, seed: Any) -> str:
    return f"{model} / seed {seed}"


def load_defaults(config_path: Path) -> dict[str, Any]:
    config = eval_core.load_config(config_path)
    runtime = config.get("runtime") or {}
    execution = config.get("execution") or {}
    models = [model for model in config.get("models") or [] if isinstance(model, dict)]
    first = models[0] if models else {}
    api_key = str(first.get("api_key") or "")
    api_key_env = DEFAULT_API_KEY_ENV
    if api_key.startswith("${") and api_key.endswith("}"):
        api_key_env = api_key[2:-1]
    return {
        "base_url": first.get("base_url") or DEFAULT_BASE_URL,
        "credential_mode": "env",
        "api_key_env": api_key_env,
        "api_key": "",
        "models": "\n".join(str(model.get("name")) for model in models if model.get("name")),
        "max_tokens": int(first.get("max_tokens") or runtime.get("max_tokens") or 12000),
        "concurrency": int(execution.get("concurrency") or runtime.get("concurrency") or 64),
        "temperature": float(first.get("temperature") or runtime.get("temperature") or 0),
        "seeds": str(config.get("seed") if config.get("seed") is not None else 1),
        "output_dir": str(runtime.get("output_dir") or (config.get("data") or {}).get("output_dir") or "outputs"),
    }


def credential_value(payload: RunRequest | ModelFetchRequest) -> str:
    if payload.credential_mode == "paste":
        return payload.api_key.strip()
    env_name = payload.api_key_env.strip()
    return os.environ.get(env_name, "") if env_name else ""


def validate_request(config_path: Path, payload: RunRequest) -> None:
    errors: list[str] = []
    if not payload.base_url.strip():
        errors.append("Base URL is required.")
    if not eval_core.parse_models(payload.models):
        errors.append("Add at least one model.")
    try:
        seeds = eval_core.parse_seeds(payload.seeds)
        if not seeds:
            errors.append("Add at least one seed.")
    except ValueError:
        errors.append("Seeds must be comma-separated integers.")
    if payload.credential_mode not in {"env", "paste"}:
        errors.append("Credential mode must be env or paste.")
    elif payload.credential_mode == "env":
        env_name = payload.api_key_env.strip()
        if not env_name:
            errors.append("API key environment variable name is required.")
        elif not os.environ.get(env_name):
            errors.append(f"Environment variable {env_name} is not set for this server process.")
    elif not payload.api_key.strip():
        errors.append("Paste an API key or use environment variable mode.")
    if payload.max_tokens < 1:
        errors.append("Max tokens must be at least 1.")
    if payload.concurrency < 1:
        errors.append("Concurrency must be at least 1.")
    try:
        preview = eval_core.preview_outputs(config_path, payload.model_dump())
        if preview["planned_run_count"] < 1:
            errors.append("No planned runs.")
        output_root = Path(preview["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        probe = output_root / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except Exception as exc:  # noqa: BLE001 - validation endpoint should return direct reasons.
        errors.append(f"Output Dir or preview check failed: {exc}")
    if errors:
        raise HTTPException(status_code=400, detail=errors)


def fetch_openai_models(payload: ModelFetchRequest) -> dict[str, Any]:
    base_url = payload.base_url.rstrip("/")
    if not base_url:
        raise HTTPException(status_code=400, detail="Base URL is required.")
    api_key = credential_value(payload)
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    request = urllib.request.Request(f"{base_url}/models", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail=f"Model list request failed: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Model list request failed: {exc}") from exc
    model_ids = sorted(str(item["id"]) for item in data.get("data", []) if isinstance(item, dict) and item.get("id"))
    return {"source": f"{base_url}/models", "count": len(model_ids), "models": model_ids}


def create_app(config_path: Path) -> FastAPI:
    state = RunnerState(config_path)
    app = FastAPI(title="Benchmark Runs")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return HTML

    @app.get("/api/defaults")
    async def defaults() -> dict[str, Any]:
        return load_defaults(config_path)

    @app.post("/api/preview")
    async def preview(payload: RunRequest) -> dict[str, Any]:
        return eval_core.preview_outputs(config_path, payload.model_dump())

    @app.post("/api/recent")
    async def recent(payload: RunRequest) -> dict[str, Any]:
        return {"samples": eval_core.recent_samples(config_path, payload.model_dump(), limit=5)}

    @app.post("/api/models")
    async def models(payload: ModelFetchRequest) -> dict[str, Any]:
        return fetch_openai_models(payload)

    @app.post("/api/start")
    async def start(payload: RunRequest) -> dict[str, Any]:
        return await state.start(payload)

    @app.post("/api/stop")
    async def stop() -> dict[str, Any]:
        return await state.stop()

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        return state.public_status()

    return app


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Benchmark Runs</title>
  <style>
    :root { color-scheme: light; --bg: #f7f8fa; --panel: #ffffff; --text: #17202a; --muted: #667085; --line: #d0d5dd; --accent: #0f766e; --bad: #b42318; --warn: #b54708; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }
    header { padding: 20px 28px 10px; }
    h1 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0; }
    main { display: grid; grid-template-columns: minmax(320px, 420px) 1fr; gap: 16px; padding: 10px 28px 28px; }
    section, aside { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
    h2 { margin: 0 0 12px; font-size: 15px; }
    label { display: block; margin: 10px 0 4px; color: var(--muted); font-size: 12px; font-weight: 650; }
    input, textarea, select { width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 8px 9px; font: inherit; font-size: 13px; background: #fff; }
    textarea { min-height: 118px; resize: vertical; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    button { border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 8px 11px; font-weight: 650; cursor: pointer; }
    button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
    button.danger { color: var(--bad); }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .stack { display: grid; gap: 16px; }
    .metrics { display: grid; grid-template-columns: repeat(5, minmax(110px, 1fr)); gap: 8px; }
    .metric { border: 1px solid var(--line); border-radius: 6px; padding: 10px; min-height: 62px; }
    .metric b { display: block; font-size: 20px; }
    .metric span { color: var(--muted); font-size: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { border-bottom: 1px solid var(--line); padding: 7px 6px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-weight: 700; }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; word-break: break-all; }
    .msg { margin-top: 10px; color: var(--muted); font-size: 13px; white-space: pre-wrap; }
    .error { color: var(--bad); }
    .warn { color: var(--warn); }
    .ok { color: var(--accent); }
    @media (max-width: 920px) { main { grid-template-columns: 1fr; padding: 10px 14px 20px; } header { padding-inline: 14px; } .metrics { grid-template-columns: repeat(2, 1fr); } }
  </style>
</head>
<body>
  <header><h1>Benchmark Runs</h1></header>
  <main>
    <aside>
      <h2>Configuration</h2>
      <label>Base URL</label><input id="base_url">
      <div class="grid2">
        <div><label>Credential</label><select id="credential_mode"><option value="env">Environment</option><option value="paste">Paste key</option></select></div>
        <div><label>API key env</label><input id="api_key_env"></div>
      </div>
      <label>API key</label><input id="api_key" type="password" autocomplete="off">
      <label>Models</label><textarea id="models"></textarea>
      <div class="grid2">
        <div><label>Max tokens</label><input id="max_tokens" type="number" min="1"></div>
        <div><label>Concurrency</label><input id="concurrency" type="number" min="1"></div>
      </div>
      <div class="grid2">
        <div><label>Temperature</label><input id="temperature" type="number" step="0.01"></div>
        <div><label>Seeds</label><input id="seeds"></div>
      </div>
      <label>Output Dir</label><input id="output_dir">
      <div class="actions">
        <button class="primary" id="start">Start</button>
        <button class="danger" id="stop">Stop</button>
        <button id="refresh">Refresh</button>
        <button id="fetch_models">Models</button>
      </div>
      <div id="message" class="msg"></div>
    </aside>
    <div class="stack">
      <section>
        <h2>Status</h2>
        <div class="metrics">
          <div class="metric"><b id="state">idle</b><span>state</span></div>
          <div class="metric"><b id="completed">0 / 0</b><span>items</span></div>
          <div class="metric"><b id="errors">0</b><span>errors</span></div>
          <div class="metric"><b id="truncated">0</b><span>truncated</span></div>
          <div class="metric"><b id="tokens">0</b><span>tokens</span></div>
        </div>
        <div id="run_detail" class="msg"></div>
      </section>
      <section>
        <h2>Run Preview</h2>
        <div id="preview_meta" class="msg"></div>
        <table><thead><tr><th>Run</th><th>Mode</th><th>Done</th><th>Left</th><th>Files</th></tr></thead><tbody id="preview_rows"></tbody></table>
      </section>
      <section>
        <h2>Recent Outputs</h2>
        <table><thead><tr><th>Problem</th><th>Run</th><th>Status</th><th>Score</th><th>Latency</th><th>Tokens</th><th>Flags</th></tr></thead><tbody id="recent_rows"></tbody></table>
      </section>
      <section>
        <h2>Model Discovery</h2>
        <div id="models_result" class="msg"></div>
      </section>
    </div>
  </main>
  <script>
    const ids = ["base_url","credential_mode","api_key_env","api_key","models","max_tokens","concurrency","temperature","seeds","output_dir"];
    const el = id => document.getElementById(id);
    function payload() {
      return {
        base_url: el("base_url").value,
        credential_mode: el("credential_mode").value,
        api_key_env: el("api_key_env").value,
        api_key: el("api_key").value,
        models: el("models").value,
        max_tokens: Number(el("max_tokens").value),
        concurrency: Number(el("concurrency").value),
        temperature: Number(el("temperature").value),
        seeds: el("seeds").value,
        output_dir: el("output_dir").value
      };
    }
    async function post(url, body) {
      const res = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
      const data = await res.json();
      if (!res.ok) throw new Error(Array.isArray(data.detail) ? data.detail.join("\\n") : data.detail || res.statusText);
      return data;
    }
    function setMsg(text, cls="") { el("message").className = "msg " + cls; el("message").textContent = text || ""; }
    async function loadDefaults() {
      const defaults = await fetch("/api/defaults").then(r => r.json());
      ids.forEach(id => { if (defaults[id] !== undefined) el(id).value = defaults[id]; });
      await refreshAll();
    }
    function renderStatus(s) {
      el("state").textContent = s.state || "idle";
      el("completed").textContent = `${s.completed || 0} / ${s.total || 0}`;
      el("errors").textContent = s.errors || 0;
      el("truncated").textContent = s.truncated || 0;
      el("tokens").textContent = s.tokens || 0;
      const eta = s.eta_s == null ? "" : `, eta ${s.eta_s}s`;
      el("run_detail").textContent = `${s.message || ""}\\nActive: ${(s.active_runs || []).join(", ") || "none"}\\nCurrent: ${s.current_model || "-"} seed ${s.current_seed ?? "-"}${eta}`;
    }
    function renderPreview(p) {
      el("preview_meta").textContent = `Output: ${p.output_root}\\nManifest: ${p.manifest.path} (${p.manifest.run_count} runs, ${p.manifest.mtime || "no timestamp"})\\nPlanned: ${p.planned_run_count} runs, ${p.completed_item_count} done, ${p.pending_item_count} left`;
      el("preview_rows").innerHTML = (p.runs || []).map(r => `<tr><td><code>${r.run_id}</code><br>${r.model} / seed ${r.seed}</td><td>${r.mode}</td><td>${r.completed}</td><td>${r.pending}</td><td><code>${r.predictions_path}</code><br><code>${r.scores_path}</code><br><code>${r.usage_path}</code></td></tr>`).join("");
    }
    function renderRecent(samples) {
      el("recent_rows").innerHTML = (samples || []).map(s => {
        const flags = `${s.truncation_type || ""} ${s.has_scoreable_text ? "scoreable" : "no scoreable"} ${s.has_final_answer_marker ? "final marker" : "no final marker"} ${s.error ? "error: " + s.error : ""}`;
        return `<tr><td>${s.problem_id || ""}</td><td>${s.model || ""}<br>seed ${s.seed ?? ""}</td><td>${s.status || ""}</td><td>${s.score ?? ""}</td><td>${s.latency_s ?? ""}</td><td>${s.tokens || 0}</td><td>${flags}</td></tr>`;
      }).join("");
    }
    async function refreshAll() {
      try {
        const [status, preview, recent] = await Promise.all([
          fetch("/api/status").then(r => r.json()),
          post("/api/preview", payload()),
          post("/api/recent", payload())
        ]);
        renderStatus(status); renderPreview(preview); renderRecent(recent.samples); setMsg("");
      } catch (err) { setMsg(err.message, "error"); }
    }
    el("start").onclick = async () => { try { renderStatus(await post("/api/start", payload())); setMsg("Started", "ok"); } catch (err) { setMsg(err.message, "error"); } };
    el("stop").onclick = async () => { try { renderStatus(await post("/api/stop", {})); setMsg("Stop requested", "warn"); } catch (err) { setMsg(err.message, "error"); } };
    el("refresh").onclick = refreshAll;
    el("fetch_models").onclick = async () => {
      try {
        const data = await post("/api/models", payload());
        el("models_result").textContent = `${data.count} models from ${data.source}\\n` + data.models.join("\\n");
      } catch (err) { el("models_result").textContent = err.message; }
    };
    ids.forEach(id => el(id).addEventListener("change", refreshAll));
    loadDefaults();
    setInterval(refreshAll, 3000);
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local benchmark web runner.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Bind port.")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    print(f"Open http://{args.host}:{args.port}")
    uvicorn.run(create_app(config_path.resolve()), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
