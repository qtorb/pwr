from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from db import (
    PORTABLE_RUNS_DIR,
    build_run_fingerprint,
    compact_text,
    get_conn,
    now_iso,
    repo_relative_path,
    row_value,
    safe_json_loads,
    slugify_for_path,
)
from router.providers import build_execution_prompt
from router.execution_service import ExecutionService
from services.tasks import build_task_input_from_rows
from state_contract import normalize_execution_state, resolve_runtime_execution_state


def normalize_trace(trace: dict) -> dict:
    if not trace:
        return {}
    return {
        "mode": trace.get("mode", ""),
        "model_used": trace.get("model_used") or trace.get("model", ""),
        "provider_used": trace.get("provider_used") or trace.get("provider", ""),
        "reasoning_path": trace.get("reasoning_path", ""),
        "latency_ms": trace.get("latency_ms", 0),
        "estimated_cost": trace.get("estimated_cost", 0),
        "status": trace.get("status", ""),
        "error_code": trace.get("error_code"),
        "error_message": trace.get("error_message"),
        "execution_prompt": trace.get("execution_prompt", ""),
        "is_first_execution": trace.get("is_first_execution", False),
    }


def portable_run_dir(project_id: int, task_id: int) -> Path:
    path = PORTABLE_RUNS_DIR / f"project_{project_id:04d}" / f"task_{task_id:04d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_portable_run_artifacts(run_id: int, project, task, run_data: dict) -> dict:
    project_id = int(row_value(task, "project_id", 0) or 0)
    task_id = int(row_value(task, "id", 0) or 0)
    created = run_data.get("executed_at") or now_iso()
    safe_title = slugify_for_path(row_value(task, "title"), f"task-{task_id}")
    base_name = f"run_{run_id:04d}_{safe_title}"
    target_dir = portable_run_dir(project_id, task_id)
    md_path = target_dir / f"{base_name}.md"
    json_path = target_dir / f"{base_name}.json"

    artifact = {
        "run_id": run_id,
        "timestamp": created,
        "execution_status": run_data.get("execution_status", ""),
        "project": {
            "id": project_id,
            "name": row_value(project, "name"),
            "objective": row_value(project, "objective"),
            "base_context_summary": compact_text(row_value(project, "base_context")),
            "base_instructions_summary": compact_text(row_value(project, "base_instructions")),
        },
        "task": {
            "id": task_id,
            "title": row_value(task, "title"),
            "description": row_value(task, "description"),
            "task_type": row_value(task, "task_type"),
            "temporary_context": row_value(task, "context"),
        },
        "routing": {
            "mode": run_data.get("mode", ""),
            "provider": run_data.get("provider", ""),
            "model": run_data.get("model", ""),
            "latency_ms": run_data.get("latency_ms", 0),
            "estimated_cost": run_data.get("estimated_cost", 0),
        },
        "prompt": run_data.get("prompt_text", ""),
        "output": run_data.get("output_text", ""),
        "error": {
            "code": run_data.get("error_code", ""),
            "message": run_data.get("error_message", ""),
        },
        "router_trace": run_data.get("router_trace", {}),
    }

    md = f"""# PWR Run Artifact

Project: {artifact['project']['name']}
Task: {artifact['task']['title']}
Status: {artifact['execution_status']}
Timestamp: {artifact['timestamp']}

## Work

- Type: {artifact['task']['task_type']}
- Mode: {artifact['routing']['mode']}
- Provider: {artifact['routing']['provider']}
- Model: {artifact['routing']['model']}

## Stable Project Context

{artifact['project']['base_context_summary'] or '(none)'}

## Project Base Instructions

{artifact['project']['base_instructions_summary'] or '(none)'}

## Temporary Task Context

{artifact['task']['temporary_context'] or '(none)'}

## Execution Prompt

```text
{artifact['prompt']}
```

## Output

{artifact['output'] or '(no output)'}

## Error

{artifact['error']['code'] or '(none)'}
{artifact['error']['message'] or ''}
"""
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"md": repo_relative_path(md_path), "json": repo_relative_path(json_path)}


def generate_demo_proposal(decision, task_input) -> dict:
    """Build the same preview payload used by the live runtime fallback."""
    title = str(task_input.title or "").strip()
    description = str(task_input.description or "").strip()
    context = str(task_input.context or "").strip()
    mode = str(decision.mode or "")

    if mode == "eco":
        time_estimate = "~2-4s"
        cost_estimate = "bajo"
    else:
        time_estimate = "~10-30s"
        cost_estimate = "medio-alto"

    understood_parts = []
    if title:
        understood_parts.append(f"Quieres {title.lower()}")
    if description:
        understood_parts.append(description)
    if context:
        understood_parts.append(f"Con contexto: {context}")

    understood = ", ".join(understood_parts) if understood_parts else "Analizar una tarea"
    understood = understood[0].upper() + understood[1:] + "."

    if mode == "eco":
        strategy = (
            "Lo abordaria de forma rapida, enfocandome en lo esencial y devolviendo "
            "una respuesta clara y directa."
        )
    else:
        strategy = (
            "Lo abordaria con analisis profundo, considerando alternativas y "
            "devolviendo una recomendacion fundamentada."
        )

    priority = "velocidad y claridad" if mode == "eco" else "precision y profundidad"
    task_type = str(task_input.task_type or "Pensar")
    expected_output_map = {
        "Pensar": "analisis estructurado con recomendaciones",
        "Escribir": "contenido claro y listo para usar",
        "Programar": "codigo funcional y documentado",
        "Revisar": "evaluacion con puntos de mejora",
        "Decidir": "comparacion de opciones con recomendacion",
    }
    execution_prompt = build_execution_prompt(task_input)

    return {
        "understood": understood,
        "strategy": strategy,
        "priority": priority,
        "expected_output": expected_output_map.get(task_type, "respuesta clara y estructurada"),
        "execution_prompt": execution_prompt,
        "suggested_prompt": execution_prompt,
        "mode": mode,
        "model": str(decision.model or ""),
        "time_estimate": time_estimate,
        "cost_estimate": cost_estimate,
    }


def execute_task_now(task_id: int) -> dict:
    """Execute a task through the live PWR runtime and persist the result."""
    with get_conn() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (task["project_id"],)).fetchone()
        if not project:
            raise ValueError(f"Project {task['project_id']} not found for task {task_id}")

        task_input = build_task_input_from_rows(task, project)
        execution_prompt = build_execution_prompt(task_input)
        result = ExecutionService(conn).execute(task_input)
        execution_status = resolve_runtime_execution_state(
            result.status,
            result.error.code if result.error else "",
        )

        if result.status == "error":
            if execution_status == "preview":
                demo_proposal = generate_demo_proposal(result.routing, task_input)
                output = f"""[PROPUESTA PREVIA - Modo Demo]

Que he entendido:
{demo_proposal['understood']}

Como lo resolveria:
{demo_proposal['strategy']}

Prioridad: {demo_proposal['priority']}
Salida esperada: {demo_proposal['expected_output']}

Contenido de ejecucion:
{demo_proposal['execution_prompt']}

---
Nota: Esta es una propuesta previa basada en el analisis del Router.
Para obtener el resultado real, conecta un motor en Configuracion.
"""
                extract = demo_proposal["understood"]
                router_summary = (
                    f"Propuesta previa (demo)\n"
                    f"Modo: {result.routing.mode}\n"
                    f"Modelo: {result.routing.model}\n"
                    f"Motivo:\n- {result.routing.reasoning_path}\n\n"
                    f"Para resultado real: Conecta {result.routing.provider}"
                )
                message = "Tarea actualizada con una propuesta previa."
            else:
                output = ""
                extract = ""
                router_summary = (
                    f"Intento fallido\n"
                    f"Modo: {result.routing.mode}\n"
                    f"Modelo: {result.metrics.model_used}\n"
                    f"Error: {result.error.code}\n"
                    f"Mensaje: {result.error.message}\n\n"
                    f"Motivo:\n- {result.routing.reasoning_path}"
                )
                message = "La ejecucion termino en fallo."
        else:
            output = result.output_text
            extract = output[:700]
            router_summary = (
                f"Ejecucion completada\n"
                f"Modo: {result.routing.mode}\n"
                f"Modelo: {result.metrics.model_used}\n"
                f"Proveedor: {result.metrics.provider_used}\n"
                f"Complejidad: {result.routing.complexity_score:.2f}\n"
                f"Latencia: {result.metrics.latency_ms} ms\n"
                f"Coste estimado: ${result.metrics.estimated_cost:.3f}\n\n"
                f"Motivo:\n- {result.routing.reasoning_path}"
            )
            message = "La tarea se ejecuto y quedo actualizada."

        router_metrics = {
            "mode": result.routing.mode,
            "model": result.metrics.model_used,
            "provider": result.metrics.provider_used,
            "latency_ms": result.metrics.latency_ms,
            "estimated_cost": result.metrics.estimated_cost,
            "complexity_score": result.routing.complexity_score,
            "status": execution_status,
            "reasoning_path": result.routing.reasoning_path,
            "execution_prompt": execution_prompt,
            "error_code": result.error.code if result.error else "",
            "error_message": result.error.message if result.error else "",
            "executed_at": now_iso(),
        }
        save_execution_result(
            task_id=task_id,
            model_used=result.metrics.model_used,
            router_summary=router_summary,
            llm_output=output,
            useful_extract=extract,
            execution_status=execution_status,
            router_metrics=router_metrics,
        )

    latest_run = get_latest_execution_run(task_id)
    return {
        "task_id": task_id,
        "status": execution_status,
        "execution_id": int(row_value(latest_run, "id", 0) or 0) or None,
        "message": message,
    }


def infer_manual_provider(model_name: str) -> str:
    normalized = str(model_name or "").strip().lower()
    if not normalized:
        return "manual"
    if normalized.startswith("gemini"):
        return "gemini"
    if normalized.startswith("mock"):
        return "mock"
    if "/" in normalized:
        return normalized.split("/", 1)[0]
    return "manual"


def save_manual_task_result(task_id: int, model_name: str, prompt_text: str, result_text: str) -> dict:
    normalized_model = str(model_name or "").strip() or "manual-external"
    normalized_prompt = str(prompt_text or "").strip()
    normalized_result = str(result_text or "").strip()
    if not normalized_result:
        raise ValueError("Result text is required")

    with get_conn() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (task["project_id"],)).fetchone()
        if not project:
            raise ValueError(f"Project {task['project_id']} not found for task {task_id}")

        if normalized_prompt != str(row_value(task, "context") or "").strip():
            conn.execute(
                """
                UPDATE tasks
                SET context = ?, updated_at = ?
                WHERE id = ?
                """,
                (normalized_prompt, now_iso(), task_id),
            )

    provider = infer_manual_provider(normalized_model)
    router_summary = (
        "Resultado manual guardado\n"
        "Modo: manual\n"
        f"Proveedor: {provider}\n"
        f"Modelo: {normalized_model}\n\n"
        "Motivo:\n- Resultado pegado manualmente desde Task Workspace."
    )
    router_metrics = {
        "mode": "manual",
        "model": normalized_model,
        "provider": provider,
        "latency_ms": 0,
        "estimated_cost": 0.0,
        "status": "executed",
        "reasoning_path": "Resultado pegado manualmente desde Task Workspace.",
        "execution_prompt": normalized_prompt,
        "error_code": "",
        "error_message": "",
        "executed_at": now_iso(),
        "manual_capture": True,
        "source": "task-workspace",
    }
    save_execution_result(
        task_id=task_id,
        model_used=normalized_model,
        router_summary=router_summary,
        llm_output=normalized_result,
        useful_extract=normalized_result[:700],
        execution_status="executed",
        router_metrics=router_metrics,
    )

    latest_run = get_latest_execution_run(task_id)
    return {
        "task_id": task_id,
        "status": "executed",
        "execution_id": int(row_value(latest_run, "id", 0) or 0) or None,
        "message": "Resultado manual guardado correctamente.",
    }


def persist_execution_history(
    conn: sqlite3.Connection,
    task_id: int,
    model_used: str,
    llm_output: str,
    execution_status: str,
    router_metrics: Optional[dict],
) -> Optional[int]:
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        return None

    project = conn.execute("SELECT * FROM projects WHERE id = ?", (task["project_id"],)).fetchone()
    metrics = router_metrics or {}
    prompt_text = metrics.get("execution_prompt") or build_execution_prompt(build_task_input_from_rows(task, project or {}))
    executed_at = metrics.get("executed_at") or now_iso()
    mode = metrics.get("mode", "")
    model = metrics.get("model") or metrics.get("model_used") or model_used
    provider = metrics.get("provider") or metrics.get("provider_used") or ""
    latency_ms = int(metrics.get("latency_ms") or 0)
    estimated_cost = float(metrics.get("estimated_cost") or 0)
    error_code = metrics.get("error_code") or ""
    error_message = metrics.get("error_message") or ""
    trace_json = json.dumps(metrics, ensure_ascii=False)
    output_text = llm_output or ""
    run_fingerprint = build_run_fingerprint(
        task_id=task_id,
        execution_status=execution_status,
        model=model,
        provider=provider,
        prompt_text=prompt_text,
        output_text=output_text,
        error_code=error_code,
        error_message=error_message,
    )

    existing = conn.execute(
        """
        SELECT id
        FROM executions_history
        WHERE task_id = ? AND run_fingerprint = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (task_id, run_fingerprint),
    ).fetchone()
    if existing:
        return int(existing["id"])

    cur = conn.execute(
        """
        INSERT INTO executions_history (
            task_id, project_id, execution_status, mode, model, provider,
            latency_ms, estimated_cost, prompt_text, output_text,
            error_code, error_message, router_trace_json, run_fingerprint, executed_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            task["project_id"],
            execution_status,
            mode,
            model,
            provider,
            latency_ms,
            estimated_cost,
            prompt_text,
            output_text,
            error_code,
            error_message,
            trace_json,
            run_fingerprint,
            executed_at,
            now_iso(),
        ),
    )
    run_id = int(cur.lastrowid)

    run_data = {
        "execution_status": execution_status,
        "mode": mode,
        "model": model,
        "provider": provider,
        "latency_ms": latency_ms,
        "estimated_cost": estimated_cost,
        "prompt_text": prompt_text,
        "output_text": output_text,
        "error_code": error_code,
        "error_message": error_message,
        "router_trace": metrics,
        "executed_at": executed_at,
    }
    paths = write_portable_run_artifacts(run_id, project or {}, task, run_data)
    conn.execute(
        """
        UPDATE executions_history
        SET artifact_md_path = ?, artifact_json_path = ?
        WHERE id = ?
        """,
        (paths["md"], paths["json"], run_id),
    )
    return run_id


def get_execution_history(task_id: int, limit: Optional[int] = None) -> list[sqlite3.Row]:
    sql = """
        SELECT *
        FROM executions_history
        WHERE task_id = ?
        ORDER BY executed_at DESC, id DESC
    """
    params: list = [task_id]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    with get_conn() as conn:
        return conn.execute(sql, tuple(params)).fetchall()


def get_latest_execution_run(task_id: int) -> Optional[sqlite3.Row]:
    runs = get_execution_history(task_id, limit=1)
    return runs[0] if runs else None


def trace_from_history_run(run) -> dict:
    if not run:
        return {}
    trace = safe_json_loads(row_value(run, "router_trace_json"), {})
    trace.update(
        {
            "mode": row_value(run, "mode"),
            "model": row_value(run, "model"),
            "provider": row_value(run, "provider"),
            "latency_ms": row_value(run, "latency_ms", 0),
            "estimated_cost": row_value(run, "estimated_cost", 0),
            "status": row_value(run, "execution_status"),
            "error_code": row_value(run, "error_code"),
            "error_message": row_value(run, "error_message"),
            "execution_prompt": row_value(run, "prompt_text"),
        }
    )
    return normalize_trace(trace)


def execution_artifact_paths(run) -> dict[str, str]:
    if not run:
        return {"md": "", "json": ""}
    return {
        "md": row_value(run, "artifact_md_path"),
        "json": row_value(run, "artifact_json_path"),
    }


def visible_output(task, latest_run=None) -> str:
    return str(row_value(task, "llm_output") or row_value(latest_run, "output_text") or "").strip()


def visible_error(task, latest_run=None, trace: Optional[dict] = None) -> str:
    return str(
        row_value(latest_run, "error_message")
        or row_value(trace or {}, "error_message")
        or row_value(task, "router_summary")
        or ""
    ).strip()


def save_execution_result(
    task_id: int,
    model_used: str,
    router_summary: str,
    llm_output: str,
    useful_extract: str,
    execution_status: str = "executed",
    router_metrics: Optional[dict] = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, llm_output = ?, useful_extract = ?,
                status = ?, execution_status = ?, router_metrics_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                model_used,
                router_summary,
                llm_output,
                useful_extract,
                execution_status,
                execution_status,
                json.dumps(router_metrics or {}, ensure_ascii=False),
                now_iso(),
                task_id,
            ),
        )
        try:
            persist_execution_history(
                conn=conn,
                task_id=task_id,
                model_used=model_used,
                llm_output=llm_output,
                execution_status=execution_status,
                router_metrics=router_metrics or {},
            )
        except Exception as exc:
            print(f"[WARN] No se pudo persistir executions_history para task {task_id}: {exc}")


def update_task_result(task_id: int, llm_output: str, useful_extract: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET llm_output = ?, useful_extract = ?, status = 'executed', execution_status = 'executed', updated_at = ?
            WHERE id = ?
            """,
            (llm_output, useful_extract, now_iso(), task_id),
        )


def latest_run_state(task, latest_run=None) -> str:
    return normalize_execution_state(row_value(latest_run, "execution_status") or row_value(task, "execution_status")) or "pending"
