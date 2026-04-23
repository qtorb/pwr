#!/usr/bin/env python3
"""Smoke checks for the live local PWR runtime."""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from router import ExecutionService, TaskInput
from router.providers import build_execution_prompt
from state_contract import (
    HOME_ACTIVITY_STATES,
    HOME_RETAKE_STATES,
    STATE_CONTRACT,
    TASK_EXECUTION_STATES,
    classify_runtime_transition,
    resolve_runtime_execution_state,
)


ROOT = Path(__file__).resolve().parent
APP_PATH = ROOT / "app_main.py"
DB_PATH = ROOT / "pwr_data" / "pwr.db"
PORTABLE_RUNS_DIR = ROOT / "pwr_data" / "portable_runs"


def check(condition: bool, message: str) -> bool:
    status = "OK" if condition else "FAIL"
    print(f"[{status}] {message}")
    return condition


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def repo_relative_path(path: Path) -> str:
    return path.resolve(strict=False).relative_to(ROOT).as_posix()


def run_app(session_state=None) -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    for key, value in (session_state or {}).items():
        at.session_state[key] = value
    at.run()
    return at


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def first_project_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT id FROM projects ORDER BY id LIMIT 1").fetchone()
    return int(row[0]) if row else None


def ensure_live_smoke_project(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM projects WHERE slug = ?", ("pwr-live-gemini-smoke",)).fetchone()
    if row:
        return int(row["id"])

    created = now_iso()
    cur = conn.execute(
        """
        INSERT INTO projects (
            name, slug, description, objective, base_context, base_instructions,
            tags_json, is_favorite, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
            "PWR Live Gemini Smoke",
            "pwr-live-gemini-smoke",
            "Proyecto local para validar ejecucion real con Gemini.",
            "Validar que PWR ejecuta, persiste y renderiza un run real.",
            "Contexto estable smoke: PWR transforma trabajo difuso en tareas ejecutables y portables.",
            "Instrucciones base smoke: responder de forma breve, concreta y verificable.",
            json.dumps(["smoke", "gemini"], ensure_ascii=False),
            created,
            created,
        ),
    )
    return int(cur.lastrowid)


def create_live_smoke_task(conn: sqlite3.Connection, project_id: int) -> int:
    created = now_iso()
    cur = conn.execute(
        """
        INSERT INTO tasks (
            project_id, title, description, task_type, context, status, execution_status,
            suggested_model, router_summary, llm_output, useful_extract, uploads_json,
            router_metrics_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, 'pending', 'pending', '', '', '', '', '[]', '{}', ?, ?)
        """,
        (
            project_id,
            f"LIVE_GEMINI_SMOKE {created}",
            "Validar un run real minimo con Gemini desde el runtime local.",
            "Analizar",
            "Contexto temporal smoke: confirma en una frase que recibiste contexto estable, instrucciones base y contexto temporal.",
            created,
            created,
        ),
    )
    return int(cur.lastrowid)


def run_fingerprint(task_id: int, status: str, model: str, provider: str, prompt: str, output: str, error_code: str, error_message: str) -> str:
    payload = {
        "task_id": task_id,
        "execution_status": status,
        "model": model,
        "provider": provider,
        "prompt_text": prompt,
        "output_text": output,
        "error_code": error_code,
        "error_message": error_message,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write_smoke_artifacts(run_id: int, project_id: int, task_id: int, payload: dict) -> tuple[str, str]:
    target = PORTABLE_RUNS_DIR / f"project_{project_id:04d}" / f"task_{task_id:04d}"
    target.mkdir(parents=True, exist_ok=True)
    md_path = target / f"run_{run_id:04d}_live-gemini-smoke.md"
    json_path = target / f"run_{run_id:04d}_live-gemini-smoke.json"

    md = f"""# PWR Run Artifact

Project: {payload['project_name']}
Task: {payload['task_title']}
Status: {payload['execution_status']}
Timestamp: {payload['executed_at']}

## Work

- Type: {payload['task_type']}
- Mode: {payload['mode']}
- Provider: {payload['provider']}
- Model: {payload['model']}

## Execution Prompt

```text
{payload['prompt_text']}
```

## Output

{payload['output_text'] or '(no output)'}

## Error

{payload['error_code'] or '(none)'}
{payload['error_message'] or ''}
"""
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return repo_relative_path(md_path), repo_relative_path(json_path)


def persist_live_smoke_run(conn: sqlite3.Connection, task_id: int, result, task_input: TaskInput, prompt_text: str) -> int:
    status = resolve_runtime_execution_state(
        result.status,
        result.error.code if result.error else "",
    )
    output = result.output_text or ""
    error_code = result.error.code if result.error else ""
    error_message = result.error.message if result.error else ""
    executed_at = now_iso()
    metrics = {
        "mode": result.routing.mode,
        "model": result.metrics.model_used,
        "provider": result.metrics.provider_used,
        "latency_ms": result.metrics.latency_ms,
        "estimated_cost": result.metrics.estimated_cost,
        "status": status,
        "reasoning_path": result.routing.reasoning_path,
        "execution_prompt": prompt_text,
        "error_code": error_code,
        "error_message": error_message,
        "executed_at": executed_at,
        "smoke": "live_gemini",
    }
    fingerprint = run_fingerprint(
        task_id,
        status,
        result.metrics.model_used,
        result.metrics.provider_used,
        prompt_text,
        output,
        error_code,
        error_message,
    )

    conn.execute(
        """
        UPDATE tasks
        SET status = ?, execution_status = ?, suggested_model = ?, router_summary = ?,
            llm_output = ?, useful_extract = ?, router_metrics_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            status,
            result.metrics.model_used,
            f"Smoke Gemini real\nModo: {result.routing.mode}\nProveedor: {result.metrics.provider_used}\nModelo: {result.metrics.model_used}",
            output,
            output[:700],
            json.dumps(metrics, ensure_ascii=False),
            executed_at,
            task_id,
        ),
    )

    cur = conn.execute(
        """
        INSERT INTO executions_history (
            task_id, project_id, execution_status, mode, model, provider,
            latency_ms, estimated_cost, prompt_text, output_text,
            error_code, error_message, router_trace_json, run_fingerprint,
            executed_at, created_at
        )
        SELECT id, project_id, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        FROM tasks
        WHERE id = ?
        """,
        (
            status,
            result.routing.mode,
            result.metrics.model_used,
            result.metrics.provider_used,
            result.metrics.latency_ms,
            result.metrics.estimated_cost,
            prompt_text,
            output,
            error_code,
            error_message,
            json.dumps(metrics, ensure_ascii=False),
            fingerprint,
            executed_at,
            executed_at,
            task_id,
        ),
    )
    run_id = int(cur.lastrowid)

    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (task["project_id"],)).fetchone()
    artifact_payload = {
        "run_id": run_id,
        "project_id": task["project_id"],
        "project_name": project["name"],
        "task_id": task_id,
        "task_title": task["title"],
        "task_type": task["task_type"],
        "execution_status": status,
        "mode": result.routing.mode,
        "provider": result.metrics.provider_used,
        "model": result.metrics.model_used,
        "prompt_text": prompt_text,
        "output_text": output,
        "error_code": error_code,
        "error_message": error_message,
        "executed_at": executed_at,
        "router_trace": metrics,
    }
    md_path, json_path = write_smoke_artifacts(run_id, task["project_id"], task_id, artifact_payload)
    conn.execute(
        """
        UPDATE executions_history
        SET artifact_md_path = ?, artifact_json_path = ?
        WHERE id = ?
        """,
        (md_path, json_path, run_id),
    )
    return run_id


def run_basic_smoke() -> int:
    failures = 0

    home = run_app()
    failures += 0 if check(len(home.exception) == 0, "Inicio renders without exception") else 1
    failures += 0 if check(set(STATE_CONTRACT.keys()) == TASK_EXECUTION_STATES, "state contract covers live execution states") else 1
    failures += 0 if check(set(HOME_RETAKE_STATES).issubset(set(HOME_ACTIVITY_STATES)), "Home re-entry states are subset of Home activity states") else 1
    failures += 0 if check(resolve_runtime_execution_state("error", "provider_not_available") == "preview", "provider_not_available resolves to preview") else 1
    failures += 0 if check(resolve_runtime_execution_state("error", "invalid_key") == "failed", "provider auth errors resolve to failed") else 1
    failures += 0 if check(classify_runtime_transition("pending", "preview")[0] == "valid", "pending -> preview is valid in runtime contract") else 1
    failures += 0 if check(classify_runtime_transition("failed", "executed")[0] == "valid", "failed -> executed is valid in runtime contract") else 1
    failures += 0 if check(classify_runtime_transition("draft", "pending")[0] == "ambiguous", "draft -> pending stays marked ambiguous for compatibility") else 1

    if not DB_PATH.exists():
        print("[FAIL] pwr_data/pwr.db was not created")
        return 1

    with get_conn() as conn:
        project_id = first_project_id(conn)

        required_task_columns = {"execution_status", "router_metrics_json", "llm_output", "useful_extract"}
        required_history_columns = {
            "execution_status",
            "mode",
            "model",
            "provider",
            "prompt_text",
            "output_text",
            "error_code",
            "error_message",
            "router_trace_json",
            "run_fingerprint",
            "artifact_md_path",
            "artifact_json_path",
        }
        required_asset_columns = {
            "project_id",
            "task_id",
            "source_execution_id",
            "asset_type",
            "source_execution_status",
            "summary",
            "content",
            "artifact_md_path",
            "artifact_json_path",
        }

        failures += 0 if check(required_task_columns <= table_columns(conn, "tasks"), "tasks schema matches live runtime") else 1
        failures += 0 if check(required_history_columns <= table_columns(conn, "executions_history"), "executions_history schema matches live runtime") else 1
        failures += 0 if check(required_asset_columns <= table_columns(conn, "assets"), "assets schema matches reusable-assets runtime") else 1
        failures += 0 if check(project_id is not None, "at least one project is available") else 1

    new_task = run_app({"view": "new_task"})
    failures += 0 if check(len(new_task.exception) == 0, "Nueva tarea renders without exception") else 1

    radar = run_app({"view": "radar"})
    failures += 0 if check(len(radar.exception) == 0, "Radar renders without exception") else 1

    if project_id is not None:
        project = run_app({"active_project_id": project_id, "view": "project_view"})
        failures += 0 if check(len(project.exception) == 0, "Project workspace renders without exception") else 1

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT artifact_md_path, artifact_json_path
            FROM executions_history
            WHERE artifact_md_path != '' OR artifact_json_path != ''
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row:
            failures += 0 if check(not Path(row["artifact_md_path"]).is_absolute(), "latest artifact md path is relative") else 1
            failures += 0 if check(not Path(row["artifact_json_path"]).is_absolute(), "latest artifact json path is relative") else 1
        else:
            warn("no executions_history artifacts yet; run a task to create portable artifacts")

    return failures


def run_live_gemini_smoke() -> int:
    if not os.getenv("GEMINI_API_KEY"):
        warn("GEMINI_API_KEY is not available; live Gemini smoke skipped")
        warn("Set it in PowerShell, then run: .\\.venv\\Scripts\\python.exe run_smoke_test.py --live-gemini")
        return 0

    print("[INFO] Running live Gemini smoke")
    failures = 0

    with get_conn() as conn:
        project_id = ensure_live_smoke_project(conn)
        task_id = create_live_smoke_task(conn, project_id)
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        task_input = TaskInput(
            task_id=task_id,
            title=task["title"],
            description=task["description"],
            task_type=task["task_type"],
            context=task["context"],
            project_name=project["name"],
            project_objective=project["objective"],
            project_base_context=project["base_context"],
            project_base_instructions=project["base_instructions"],
        )

        visible_prompt = build_execution_prompt(task_input)
        service = ExecutionService(conn)

        if "gemini" not in service.providers:
            print(f"[FAIL] Gemini provider unavailable: {service.provider_errors.get('gemini', 'unknown error')}")
            return 1

        provider_prompt = service.providers["gemini"]._build_prompt(task_input)
        failures += 0 if check(visible_prompt == provider_prompt, "visible execution prompt matches provider payload") else 1

        result = service.execute(task_input)
        run_id = persist_live_smoke_run(conn, task_id, result, task_input, visible_prompt)
        conn.commit()

        row = conn.execute(
            """
            SELECT execution_status, output_text, artifact_md_path, artifact_json_path
            FROM executions_history
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()

    failures += 0 if check(row is not None, "live smoke persisted executions_history row") else 1
    if row:
        failures += 0 if check(row["execution_status"] == "executed", "live smoke execution_status is executed") else 1
        failures += 0 if check(bool(row["output_text"].strip()), "live smoke output persisted") else 1
        failures += 0 if check(Path(ROOT / row["artifact_md_path"]).exists(), "live smoke markdown artifact exists") else 1
        failures += 0 if check(Path(ROOT / row["artifact_json_path"]).exists(), "live smoke json artifact exists") else 1

    rendered = run_app({"active_project_id": project_id, "selected_task_id": task_id, "view": "project_view"})
    captions = "\n".join(str(c.value) for c in rendered.caption)
    failures += 0 if check(len(rendered.exception) == 0, "live smoke task renders without exception") else 1
    failures += 0 if check("Ultimo run persistido" in captions, "live smoke latest run is visible in task") else 1

    if failures:
        print(f"[FAIL] live Gemini smoke failed for task_id={task_id}")
    else:
        print(f"[OK] live Gemini smoke passed for task_id={task_id}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="PWR local runtime smoke test")
    parser.add_argument("--live-gemini", action="store_true", help="Run the real Gemini smoke if GEMINI_API_KEY is available")
    parser.add_argument("--skip-live-gemini", action="store_true", help="Skip the real Gemini smoke even if GEMINI_API_KEY is available")
    args = parser.parse_args()

    print("PWR local smoke test")
    print("=" * 28)

    failures = run_basic_smoke()

    if args.skip_live_gemini:
        warn("live Gemini smoke skipped by flag")
    elif args.live_gemini or os.getenv("GEMINI_API_KEY"):
        failures += run_live_gemini_smoke()
    else:
        warn("GEMINI_API_KEY is not available; live Gemini smoke not attempted")
        warn("Run with --live-gemini after exporting GEMINI_API_KEY to validate a real call")

    print("=" * 28)
    if failures:
        print(f"[FAIL] {failures} smoke check(s) failed")
        return 1

    print("[OK] local runtime smoke passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
