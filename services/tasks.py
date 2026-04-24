from __future__ import annotations

import json
import mimetypes
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from db import compact_text, format_time_ago, get_conn, now_iso, project_upload_dir, row_value
from router import ModelCatalog, TaskInput
from router.decision_engine import DecisionEngine
from router.providers import build_execution_prompt
from state_contract import HOME_ACTIVITY_STATES, HOME_RETAKE_STATES, normalize_execution_state


def build_task_input(
    task_id: int,
    title: str,
    description: str,
    task_type: str,
    context: str,
    project,
    preferred_mode: Optional[str] = None,
) -> TaskInput:
    return TaskInput(
        task_id=task_id,
        title=title or "",
        description=description or "",
        task_type=task_type or "Pensar",
        context=context or "",
        project_name=row_value(project, "name"),
        project_objective=row_value(project, "objective"),
        project_base_context=row_value(project, "base_context"),
        project_base_instructions=row_value(project, "base_instructions"),
        preferred_mode=preferred_mode,
    )


def build_task_input_from_rows(task, project, context_override: Optional[str] = None, preferred_mode: Optional[str] = None) -> TaskInput:
    return build_task_input(
        task_id=int(row_value(task, "id", 0) or 0),
        title=row_value(task, "title"),
        description=row_value(task, "description"),
        task_type=row_value(task, "task_type", "Pensar"),
        context=context_override if context_override is not None else row_value(task, "context"),
        project=project,
        preferred_mode=preferred_mode,
    )


def summarize_router_decision(decision) -> str:
    return (
        f"Preparado para ejecucion\n"
        f"Modo: {decision.mode}\n"
        f"Proveedor: {decision.provider}\n"
        f"Modelo: {decision.model}\n\n"
        f"Motivo:\n- {decision.reasoning_path}"
    )


def save_task_files(project_id: int, task_id: int, files) -> List[Dict]:
    dest = project_upload_dir(project_id) / f"task_{task_id:04d}"
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for file_obj in files or []:
        name = Path(file_obj.name).name
        target = dest / name
        target.write_bytes(file_obj.getbuffer())
        saved.append(
            {
                "name": name,
                "path": str(target),
                "size": len(file_obj.getbuffer()),
                "mime_type": file_obj.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
            }
        )
    return saved


def create_task(project_id: int, title: str, description: str, task_type: str, context: str, uploaded_files) -> int:
    created = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (
                project_id, title, description, task_type, context, status, execution_status,
                suggested_model, router_summary, llm_output, useful_extract, uploads_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'pending', 'pending', '', '', '', '', '[]', ?, ?)
            """,
            (project_id, title.strip(), description.strip(), task_type, context.strip(), created, created),
        )
        task_id = int(cur.lastrowid)

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        task_files = save_task_files(project_id, task_id, uploaded_files)
        task_input = build_task_input(
            task_id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            context=context,
            project=project,
        )
        decision = DecisionEngine(ModelCatalog(conn)).decide(task_input)
        summary = summarize_router_decision(decision)
        router_metrics = {
            "mode": decision.mode,
            "model": decision.model,
            "provider": decision.provider,
            "complexity_score": decision.complexity_score,
            "status": "pending",
            "reasoning_path": decision.reasoning_path,
            "execution_prompt": build_execution_prompt(task_input),
        }

        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, uploads_json = ?, router_metrics_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                decision.model,
                summary,
                json.dumps(task_files, ensure_ascii=False),
                json.dumps(router_metrics, ensure_ascii=False),
                now_iso(),
                task_id,
            ),
        )
        return task_id


def get_project_tasks(project_id: int, search: str = "") -> List[sqlite3.Row]:
    with get_conn() as conn:
        if search.strip():
            pattern = f"%{search.strip()}%"
            return conn.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND (title LIKE ? OR description LIKE ? OR context LIKE ?)
                ORDER BY updated_at DESC, id DESC
                """,
                (project_id, pattern, pattern, pattern),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def update_task_execution(
    task_id: int,
    *,
    suggested_model: str,
    router_summary: str,
    llm_output: str,
    useful_extract: str,
    execution_status: str,
    router_metrics: Optional[dict] = None,
) -> None:
    metrics_json = json.dumps(router_metrics or {}, ensure_ascii=False)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, llm_output = ?, useful_extract = ?,
                status = ?, execution_status = ?, router_metrics_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                suggested_model,
                router_summary,
                llm_output,
                useful_extract,
                execution_status,
                execution_status,
                metrics_json,
                now_iso(),
                task_id,
            ),
        )


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


def get_recent_home_tasks(
    limit: int = 5,
    states: tuple[str, ...] = HOME_ACTIVITY_STATES,
    today_only: bool = False,
    prioritize_reentry: bool = False,
) -> List[Dict]:
    state_expr = "COALESCE(NULLIF(t.execution_status, ''), NULLIF(t.status, ''), 'pending')"
    placeholders = ", ".join(["?"] * len(states))
    where_clauses = [f"{state_expr} IN ({placeholders})"]
    params: list = list(states)

    if today_only:
        where_clauses.append("date(t.updated_at) = date('now', 'localtime')")

    order_by = "t.updated_at DESC"
    if prioritize_reentry:
        order_by = (
            "CASE "
            f"WHEN {state_expr} = 'failed' THEN 0 "
            f"WHEN {state_expr} = 'preview' THEN 1 "
            f"WHEN {state_expr} = 'pending' THEN 2 "
            f"WHEN {state_expr} = 'executed' THEN 3 "
            "ELSE 4 END, t.updated_at DESC"
        )

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                t.id, t.project_id, t.title, t.task_type, t.suggested_model,
                t.updated_at, p.name AS project_name,
                {state_expr} AS execution_status
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY {order_by}
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_reentry_tasks(limit: int = 5) -> List[Dict]:
    return get_recent_home_tasks(limit=limit, states=HOME_RETAKE_STATES, prioritize_reentry=True)


def get_recent_executed_tasks(limit: int = 6) -> List[Dict]:
    return get_recent_home_tasks(limit=limit, states=("executed",), prioritize_reentry=False)


def build_reentry_context(task, state: str, latest_run, trace: Optional[dict], visible_output: str) -> dict:
    reference_iso = row_value(latest_run, "executed_at") or row_value(task, "updated_at")
    reference_label = format_time_ago(reference_iso) if reference_iso else ""
    provider = row_value(latest_run, "provider")
    model = row_value(latest_run, "model")
    motor_line = ""
    if provider or model:
        motor_line = f"Ultimo motor: {provider or 'provider?'} / {model or 'modelo?'}"

    normalized_state = normalize_execution_state(state) or "pending"
    if normalized_state == "failed":
        snippet_label = "Ultimo error visible"
        snippet_text = compact_text(
            row_value(latest_run, "error_message")
            or row_value(trace or {}, "error_message")
            or row_value(task, "router_summary")
            or "El ultimo intento no se completo."
        )
        last_step = "El ultimo intento fallo y quedo guardado para revisarlo."
    elif normalized_state == "preview":
        snippet_label = "Ultima propuesta visible"
        snippet_text = compact_text(
            visible_output
            or row_value(latest_run, "output_text")
            or row_value(task, "router_summary")
            or "Hay una propuesta previa guardada esperando continuacion."
        )
        last_step = "PWR dejo una propuesta previa guardada a la espera de que la continues."
    elif normalized_state in {"pending", "draft"}:
        snippet_label = "Pendiente actual"
        snippet_text = compact_text(
            row_value(task, "context")
            or row_value(task, "router_summary")
            or "La tarea sigue pendiente de ejecucion."
        )
        last_step = "La tarea quedo creada y lista para su primera ejecucion."
    else:
        snippet_label = "Ultimo resultado visible"
        snippet_text = compact_text(
            visible_output
            or row_value(latest_run, "output_text")
            or row_value(task, "router_summary")
        )
        last_step = "Hay un resultado disponible."

    return {
        "reference_label": reference_label,
        "motor_line": motor_line,
        "last_step": last_step,
        "snippet_label": snippet_label,
        "snippet_text": snippet_text,
    }
