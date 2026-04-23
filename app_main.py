import json
import hashlib
import mimetypes
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import streamlit as st

from router import ExecutionService, TaskInput, ModelCatalog
from router.decision_engine import DecisionEngine
from router.providers import build_execution_prompt
from state_contract import (
    HOME_ACTIVITY_STATES,
    HOME_RETAKE_STATES,
    REENTRY_CONTEXT_STATES,
    TASK_EXECUTION_STATES,
    normalize_execution_state,
    resolve_runtime_execution_state,
    task_primary_action_hint,
    task_primary_action_label,
    task_state_caption,
)

APP_TITLE = "Portable Work Router"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "pwr_data"
UPLOADS_DIR = DATA_DIR / "uploads"
PORTABLE_RUNS_DIR = DATA_DIR / "portable_runs"
REUSABLE_ASSETS_DIR = DATA_DIR / "reusable_assets"
DB_PATH = DATA_DIR / "pwr.db"

TIPOS_TAREA = ["Pensar", "Escribir", "Programar", "Revisar", "Decidir"]
ASSET_TYPE_LABELS = {
    "output": "Resultado",
    "preview": "Preview",
    "briefing": "Briefing",
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
    PORTABLE_RUNS_DIR.mkdir(exist_ok=True)
    REUSABLE_ASSETS_DIR.mkdir(exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_json_loads(value: str, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def repo_relative_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def portable_artifact_path(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    path = Path(text)
    if path.is_absolute():
        try:
            return path.resolve(strict=False).relative_to(BASE_DIR).as_posix()
        except ValueError:
            return text
    return text.replace("\\", "/")


def migrate_portable_artifact_paths(conn: sqlite3.Connection) -> None:
    try:
        rows = conn.execute(
            "SELECT id, artifact_md_path, artifact_json_path FROM executions_history"
        ).fetchall()
    except sqlite3.OperationalError:
        return

    for row in rows:
        md_path = portable_artifact_path(row["artifact_md_path"])
        json_path = portable_artifact_path(row["artifact_json_path"])
        if md_path != row["artifact_md_path"] or json_path != row["artifact_json_path"]:
            conn.execute(
                """
                UPDATE executions_history
                SET artifact_md_path = ?, artifact_json_path = ?
                WHERE id = ?
                """,
                (md_path, json_path, row["id"]),
            )


def build_run_fingerprint(
    task_id: int,
    execution_status: str,
    model: str,
    provider: str,
    prompt_text: str,
    output_text: str,
    error_code: str,
    error_message: str,
) -> str:
    payload = {
        "task_id": task_id,
        "execution_status": execution_status or "",
        "model": model or "",
        "provider": provider or "",
        "prompt_text": prompt_text or "",
        "output_text": output_text or "",
        "error_code": error_code or "",
        "error_message": error_message or "",
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def row_value(row, key: str, default=""):
    try:
        if hasattr(row, "keys") and key in row.keys():
            value = row[key]
            return default if value is None else value
        if isinstance(row, dict):
            value = row.get(key, default)
            return default if value is None else value
    except Exception:
        return default
    return default


def task_execution_state(task) -> str:
    execution_state = normalize_execution_state(row_value(task, "execution_status"))
    status_state = normalize_execution_state(row_value(task, "status"))
    output = str(row_value(task, "llm_output") or "").strip()

    if execution_state in {"executed", "preview", "failed", "draft"}:
        return execution_state
    if status_state in {"executed", "preview", "failed", "draft"}:
        return status_state
    if output and not execution_state:
        return "executed"
    return execution_state or status_state or "pending"


def compact_text(value: str, max_len: int = 220) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        return ""
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def task_execution_progress_messages(state: str) -> list[str]:
    return {
        "failed": [
            "Revisando el ultimo fallo...",
            "Preparando un nuevo intento...",
            "Reintentando con el contexto guardado...",
        ],
        "preview": [
            "Recuperando la propuesta previa...",
            "Preparando la continuacion...",
            "Continuando la tarea...",
        ],
        "pending": [
            "Preparando la tarea pendiente...",
            "Seleccionando el mejor modo...",
            "Iniciando la ejecucion...",
        ],
        "draft": [
            "Revisando el borrador actual...",
            "Preparando la primera ejecucion...",
            "Iniciando la tarea...",
        ],
        "executed": [
            "Recuperando el contexto anterior...",
            "Preparando una nueva ejecucion...",
            "Ejecutando de nuevo...",
        ],
    }.get(state, [
        "Analizando tu tarea...",
        "Seleccionando el mejor modo...",
        "Ejecutando...",
    ])


def build_followthrough_feedback(from_state: str, to_state: str) -> tuple[str, str]:
    from_state = normalize_execution_state(from_state) or "pending"
    to_state = normalize_execution_state(to_state) or "pending"

    if from_state == "failed":
        if to_state == "executed":
            return ("success", "Reintento completado. Revisa abajo el resultado actualizado.")
        if to_state == "preview":
            return ("info", "El reintento dejo una nueva propuesta previa. Revisa abajo desde que punto continuar.")
        return ("warning", "El reintento se guardo, pero sigue habiendo un fallo. Revisa abajo el error actualizado.")

    if from_state == "preview":
        if to_state == "executed":
            return ("success", "La propuesta previa ya se convirtio en un resultado real. Revisa abajo la salida.")
        if to_state == "failed":
            return ("warning", "La continuacion termino en fallo. Revisa abajo el error actualizado.")
        return ("info", "La propuesta previa se actualizo. Revisa abajo la version actual antes de seguir.")

    if from_state in {"pending", "draft"}:
        if to_state == "executed":
            return ("success", "La tarea ya tiene un primer resultado. Revisa abajo la salida generada.")
        if to_state == "preview":
            return ("info", "La tarea dejo de estar pendiente y ahora tiene una propuesta previa lista para continuar.")
        if to_state == "failed":
            return ("warning", "La tarea se intento ejecutar pero termino en fallo. Revisa abajo el error.")
        return ("info", "La tarea sigue preparada para ejecutarse.")

    if from_state == "executed":
        if to_state == "executed":
            return ("success", "Se genero una nueva ejecucion. Revisa abajo el resultado mas reciente.")
        if to_state == "failed":
            return ("warning", "La re-ejecucion termino en fallo. Revisa abajo el error.")
        return ("info", "La tarea se actualizo. Revisa abajo el nuevo estado.")

    return ("info", "La tarea se actualizo. Revisa abajo el estado y el bloque principal.")


def build_reentry_context(task, state: str, latest_run, trace: Optional[dict], visible_output: str) -> dict:
    reference_iso = row_value(latest_run, "executed_at") or row_value(task, "updated_at")
    reference_label = format_time_ago(reference_iso) if reference_iso else ""
    provider = row_value(latest_run, "provider")
    model = row_value(latest_run, "model")
    motor_line = ""
    if provider or model:
        motor_line = f"Ultimo motor: {provider or 'provider?'} / {model or 'modelo?'}"

    if state == "failed":
        snippet_label = "Ultimo error visible"
        snippet_text = compact_text(
            row_value(latest_run, "error_message")
            or row_value(trace or {}, "error_message")
            or row_value(task, "router_summary")
            or "El ultimo intento no se completo."
        )
        last_step = "El ultimo intento fallo y quedo guardado para revisarlo."
    elif state == "preview":
        snippet_label = "Ultima propuesta visible"
        snippet_text = compact_text(
            visible_output
            or row_value(latest_run, "output_text")
            or row_value(task, "router_summary")
            or "Hay una propuesta previa guardada esperando continuacion."
        )
        last_step = "PWR dejo una propuesta previa guardada a la espera de que la continues."
    elif state in {"pending", "draft"}:
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


def open_task_workspace(project_id: int, task_id: int) -> None:
    st.session_state["active_project_id"] = project_id
    st.session_state["selected_task_id"] = task_id
    st.session_state["selected_asset_id"] = None
    st.session_state["view"] = "project_view"


def open_project_workspace(project_id: int) -> None:
    st.session_state["active_project_id"] = project_id
    st.session_state["selected_task_id"] = None
    st.session_state["selected_asset_id"] = None
    st.session_state["view"] = "project_view"


def open_asset_workspace(project_id: int, asset_id: int) -> None:
    st.session_state["active_project_id"] = project_id
    st.session_state["selected_task_id"] = None
    st.session_state["selected_asset_id"] = asset_id
    st.session_state["view"] = "project_view"


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


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition_sql: str) -> None:
    cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition_sql}")


def normalize_existing_task_states(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE tasks
        SET execution_status = CASE
            WHEN LOWER(COALESCE(status, '')) = 'failed' THEN 'failed'
            WHEN LOWER(COALESCE(status, '')) = 'preview' THEN 'preview'
            WHEN LOWER(COALESCE(router_summary, '')) LIKE 'propuesta previa%' THEN 'preview'
            WHEN LOWER(COALESCE(llm_output, '')) LIKE '[propuesta previa%' THEN 'preview'
            WHEN LOWER(COALESCE(llm_output, '')) LIKE 'propuesta previa%' THEN 'preview'
            WHEN LOWER(COALESCE(status, '')) IN ('executed', 'ejecutado') THEN 'executed'
            WHEN TRIM(COALESCE(llm_output, '')) != '' THEN 'executed'
            WHEN LOWER(COALESCE(status, '')) = 'borrador' THEN 'draft'
            ELSE 'pending'
        END
        WHERE execution_status IS NULL
           OR TRIM(execution_status) = ''
           OR LOWER(execution_status) NOT IN ('draft', 'preview', 'pending', 'executed', 'failed')
           OR (LOWER(COALESCE(status, '')) = 'failed' AND LOWER(COALESCE(execution_status, '')) != 'failed')
           OR (LOWER(COALESCE(status, '')) = 'preview' AND LOWER(COALESCE(execution_status, '')) != 'preview')
           OR (LOWER(COALESCE(router_summary, '')) LIKE 'propuesta previa%' AND LOWER(COALESCE(execution_status, '')) != 'preview')
           OR (LOWER(COALESCE(llm_output, '')) LIKE '[propuesta previa%' AND LOWER(COALESCE(execution_status, '')) != 'preview')
           OR (LOWER(COALESCE(llm_output, '')) LIKE 'propuesta previa%' AND LOWER(COALESCE(execution_status, '')) != 'preview')
           OR (LOWER(COALESCE(status, '')) IN ('executed', 'ejecutado') AND LOWER(COALESCE(execution_status, '')) != 'executed')
           OR (LOWER(execution_status) = 'pending' AND TRIM(COALESCE(llm_output, '')) != '')
        """
    )
    conn.execute(
        """
        UPDATE tasks
        SET status = execution_status
        WHERE status IS NULL
           OR TRIM(status) = ''
           OR LOWER(status) IN ('borrador', 'router_listo', 'ejecutado')
           OR LOWER(status) NOT IN ('draft', 'preview', 'pending', 'executed', 'failed')
           OR (
                LOWER(COALESCE(execution_status, '')) IN ('draft', 'preview', 'pending', 'executed', 'failed')
                AND LOWER(COALESCE(status, '')) != LOWER(COALESCE(execution_status, ''))
           )
        """
    )


def init_db() -> None:
    # Defensive: ensure directories exist with recursive creation
    try:
        ensure_dirs()
    except Exception as e:
        # Fallback: force creation even if ensure_dirs fails
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        if str(e).strip():  # Only log if there's actual error info
            print(f"[WARN] ensure_dirs raised: {e}, but mkdir fallback succeeded")

    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT,
                description TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                base_context TEXT DEFAULT '',
                base_instructions TEXT DEFAULT '',
                tags_json TEXT DEFAULT '[]',
                is_favorite INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                task_type TEXT DEFAULT 'Pensar',
                context TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                execution_status TEXT DEFAULT 'pending',
                suggested_model TEXT DEFAULT '',
                router_summary TEXT DEFAULT '',
                llm_output TEXT DEFAULT '',
                useful_extract TEXT DEFAULT '',
                uploads_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                task_id INTEGER,
                source_execution_id INTEGER,
                asset_type TEXT DEFAULT 'output',
                source_execution_status TEXT DEFAULT '',
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT DEFAULT '',
                artifact_md_path TEXT DEFAULT '',
                artifact_json_path TEXT DEFAULT '',
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id),
                FOREIGN KEY(source_execution_id) REFERENCES executions_history(id)
            )
            """
        )

        ensure_column(conn, "projects", "slug", "TEXT")
        ensure_column(conn, "projects", "description", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "objective", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "base_context", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "base_instructions", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "tags_json", "TEXT DEFAULT '[]'")
        ensure_column(conn, "projects", "is_favorite", "INTEGER DEFAULT 0")
        ensure_column(conn, "projects", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "projects", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "project_documents", "mime_type", "TEXT DEFAULT ''")
        ensure_column(conn, "project_documents", "size_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "project_documents", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "project_documents", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "tasks", "project_id", "INTEGER")
        ensure_column(conn, "tasks", "description", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "task_type", "TEXT DEFAULT 'Pensar'")
        ensure_column(conn, "tasks", "context", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "status", "TEXT DEFAULT 'pending'")
        ensure_column(conn, "tasks", "execution_status", "TEXT DEFAULT 'pending'")
        ensure_column(conn, "tasks", "suggested_model", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "router_summary", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "router_metrics_json", "TEXT DEFAULT '{}'")  # Bloque E0: metrics estructuradas
        ensure_column(conn, "tasks", "llm_output", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "useful_extract", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "uploads_json", "TEXT DEFAULT '[]'")
        ensure_column(conn, "tasks", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "tasks", "updated_at", "TEXT DEFAULT ''")

        ensure_column(conn, "assets", "project_id", "INTEGER")
        ensure_column(conn, "assets", "task_id", "INTEGER")
        ensure_column(conn, "assets", "source_execution_id", "INTEGER")
        ensure_column(conn, "assets", "asset_type", "TEXT DEFAULT 'output'")
        ensure_column(conn, "assets", "source_execution_status", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "summary", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "created_at", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "updated_at", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "artifact_md_path", "TEXT DEFAULT ''")
        ensure_column(conn, "assets", "artifact_json_path", "TEXT DEFAULT ''")

        normalize_existing_task_states(conn)

        # ==================== Model Catalog (Bloque D - ACTIVO) ====================
        # Tabla viva para catálogo de modelos y configuración de modos del Router
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,                  -- "gemini", "mock", "claude" (futuro)
                model_name TEXT UNIQUE NOT NULL,         -- "gemini-2.5-flash-lite", etc
                pricing_input_per_mtok REAL DEFAULT 0.0, -- $0.000075 (futuro, granular)
                pricing_output_per_mtok REAL DEFAULT 0.0,-- $0.0003 (futuro, granular)
                context_window INTEGER,                  -- max tokens: 1000000
                capabilities_json TEXT DEFAULT '{}',     -- {"vision": true, "reasoning": false}
                estimated_cost_per_run REAL NOT NULL,    -- 0.05 (eco) o 0.30 (racing) [ACTUAL]
                status TEXT DEFAULT 'active',            -- "active", "deprecated", "limited"
                mode TEXT,                               -- "eco" o "racing" [BRIDGE TEMPORAL]
                is_internal INTEGER DEFAULT 0,           -- 1=mock/test, 0=real/public
                deprecated_at TEXT,                      -- ISO timestamp si deprecated
                updated_at TEXT NOT NULL                 -- Cuándo fue actualizado
            )
            """
        )

        # NOTA: 'mode' es BRIDGE TEMPORAL para esta iteración (Bloque D)
        # FUTURO (Bloque E+): 'mode' migrará a tabla separada 'router_policy'
        # que tendrá reglas de decisión (scoring, umbrales, etc.)
        # No abstraer policy ahora. Mantener 'mode' aquí temporalmente.

        # ===== Seeds iniciales model_catalog (garantizan equivalencia) =====
        catalog_count = conn.execute("SELECT COUNT(*) FROM model_catalog").fetchone()[0]
        if catalog_count == 0:
            # Eco: rápido, barato
            conn.execute("""
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('gemini', 'gemini-2.5-flash-lite', 0.0, 0.0, 1000000,
                  '{"vision":false,"reasoning":false}', 0.05, 'active', 'eco', 0, now_iso()))

            # Racing: potente, caro
            conn.execute("""
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('gemini', 'gemini-2.5-pro', 0.0, 0.0, 1000000,
                  '{"vision":true,"reasoning":true}', 0.30, 'active', 'racing', 0, now_iso()))

            # Mock eco (interno)
            conn.execute("""
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('mock', 'mock-eco', 0.0, 0.0, 1000000,
                  '{"vision":false,"reasoning":false}', 0.05, 'active', 'eco', 1, now_iso()))

            # Mock racing (interno)
            conn.execute("""
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('mock', 'mock-racing', 0.0, 0.0, 1000000,
                  '{"vision":false,"reasoning":false}', 0.30, 'active', 'racing', 1, now_iso()))

        # ===== Executions History (Bloque E0: schema preparado, sin persistencia aún) =====
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS executions_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                execution_status TEXT NOT NULL,  -- "executed", "preview", "failed"
                mode TEXT,                        -- "eco", "racing"
                model TEXT,                       -- "gemini-2.5-flash-lite"
                provider TEXT,                    -- "gemini", "mock"
                latency_ms INTEGER,               -- milliseconds
                estimated_cost REAL,              -- $0.05, $0.30, etc
                prompt_text TEXT DEFAULT '',
                output_text TEXT DEFAULT '',
                error_code TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                router_trace_json TEXT DEFAULT '{}',
                run_fingerprint TEXT DEFAULT '',
                artifact_md_path TEXT DEFAULT '',
                artifact_json_path TEXT DEFAULT '',
                executed_at TEXT NOT NULL,        -- timestamp de ejecución
                created_at TEXT NOT NULL,         -- timestamp de registro (ahora)
                FOREIGN KEY(task_id) REFERENCES tasks(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        ensure_column(conn, "executions_history", "prompt_text", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "output_text", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "error_code", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "error_message", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "router_trace_json", "TEXT DEFAULT '{}'")
        ensure_column(conn, "executions_history", "run_fingerprint", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "artifact_md_path", "TEXT DEFAULT ''")
        ensure_column(conn, "executions_history", "artifact_json_path", "TEXT DEFAULT ''")
        migrate_portable_artifact_paths(conn)

        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            import re
            created = now_iso()

            def make_slug(name):
                slug = re.sub(r'[^\w\s-]', '', name.lower()).strip()
                slug = re.sub(r'[-\s]+', '-', slug)
                return slug

            conn.executemany(
                """
                INSERT INTO projects (
                    name, slug, description, objective, base_context, base_instructions,
                    tags_json, is_favorite, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Portable Work Router",
                        make_slug("Portable Work Router"),
                        "Router de trabajo con múltiples LLM.",
                        "Organizar tareas, contexto y activos portables.",
                        "Proyecto centrado en ordenar trabajo con LLMs para heavy users fuera del IDE.",
                        "Todo en castellano. Sin emojis. Estética sobria B2B.",
                        json.dumps(["pwr", "producto", "ia"], ensure_ascii=False),
                        1,
                        created,
                        created,
                    ),
                    (
                        "RosmarOps",
                        make_slug("RosmarOps"),
                        "SEO adversarial y ciberseguridad.",
                        "Explorar contenidos, herramientas y posicionamiento.",
                        "Proyecto centrado en SEO adversarial, seguridad y contenidos técnicos.",
                        "Priorizar claridad técnica y tono sobrio.",
                        json.dumps(["rosmarops", "seo", "seguridad"], ensure_ascii=False),
                        1,
                        created,
                        created,
                    ),
                ],
            )


def project_upload_dir(project_id: int) -> Path:
    path = UPLOADS_DIR / f"project_{project_id:04d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_project_files(project_id: int, files) -> List[Dict]:
    saved = []
    dest = project_upload_dir(project_id)
    for f in files or []:
        name = Path(f.name).name
        target = dest / name
        target.write_bytes(f.getbuffer())
        saved.append({
            "name": name,
            "path": str(target),
            "size": len(f.getbuffer()),
            "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
        })
    return saved


def save_task_files(project_id: int, task_id: int, files) -> List[Dict]:
    dest = project_upload_dir(project_id) / f"task_{task_id:04d}"
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files or []:
        name = Path(f.name).name
        target = dest / name
        target.write_bytes(f.getbuffer())
        saved.append({
            "name": name,
            "path": str(target),
            "size": len(f.getbuffer()),
            "mime_type": f.type or mimetypes.guess_type(name)[0] or "application/octet-stream",
        })
    return saved


def get_projects() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS task_count,
                   (SELECT COUNT(*) FROM assets a WHERE a.project_id = p.id) AS asset_count
            FROM projects p
            ORDER BY p.is_favorite DESC, p.updated_at DESC, p.id DESC
            """
        ).fetchall()


def get_project(project_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def update_project(project_id: int, name: str, description: str, objective: str, base_context: str, base_instructions: str, tags: str) -> None:
    import re

    # Regenerar slug si el nombre cambió
    slug = re.sub(r'[^\w\s-]', '', name.lower()).strip()
    slug = re.sub(r'[-\s]+', '-', slug)
    if not slug:
        slug = f"project-{project_id}"

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE projects
            SET name = ?, slug = ?, description = ?, objective = ?, base_context = ?, base_instructions = ?,
                tags_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                slug,
                description.strip(),
                objective.strip(),
                base_context.strip(),
                base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                now_iso(),
                project_id,
            ),
        )


def set_favorite(project_id: int, is_favorite: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE projects SET is_favorite = ?, updated_at = ? WHERE id = ?",
            (1 if is_favorite else 0, now_iso(), project_id),
        )


def create_project(name: str, description: str, objective: str, base_context: str, base_instructions: str, tags: str, uploaded_files) -> int:
    import re
    created = now_iso()

    # Generar slug a partir del nombre
    slug = re.sub(r'[^\w\s-]', '', name.lower()).strip()
    slug = re.sub(r'[-\s]+', '-', slug)
    if not slug:
        slug = f"project-{int(created.split('T')[0].replace('-', ''))}"

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
                name, slug, description, objective, base_context, base_instructions,
                tags_json, is_favorite, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                name.strip(),
                slug,
                description.strip(),
                objective.strip(),
                base_context.strip(),
                base_instructions.strip(),
                json.dumps([t.strip() for t in tags.split(",") if t.strip()], ensure_ascii=False),
                created,
                created,
            ),
        )
        pid = int(cur.lastrowid)
        saved = save_project_files(pid, uploaded_files)
        for item in saved:
            conn.execute(
                """
                INSERT INTO project_documents (
                    project_id, title, file_name, file_path, mime_type, size_bytes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid, item["name"], item["name"], item["path"], item["mime_type"],
                    item["size"], created, created,
                ),
            )
        return pid


def get_project_documents(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM project_documents WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def score_model(task_type: str, text: str, inherited_context: str, project_docs: List[sqlite3.Row], task_files: List[Dict]) -> Dict:
    # Legacy compatibility wrapper: live routing now comes from DecisionEngine.
    task_input = TaskInput(
        task_id=0,
        title=text,
        description="",
        task_type=task_type,
        context="",
        project_base_context=inherited_context or "",
    )
    decision = DecisionEngine().decide(task_input)
    return {
        "recommended_model": decision.model,
        "fit": decision.mode,
        "scores": {"mode": decision.mode, "complexity": decision.complexity_score},
        "reasons": [decision.reasoning_path],
    }



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
        tid = int(cur.lastrowid)

        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        task_files = save_task_files(project_id, tid, uploaded_files)
        task_input = build_task_input(
            task_id=tid,
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
                tid,
            ),
        )
        return tid


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


def slugify_for_path(value: str, fallback: str) -> str:
    import re
    slug = re.sub(r"[^\w\s-]", "", (value or "").lower(), flags=re.UNICODE).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug[:60] or fallback


def compact_text(value: str, max_chars: int = 1200) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated]"


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


def get_latest_execution_run(task_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT *
            FROM executions_history
            WHERE task_id = ?
            ORDER BY executed_at DESC, id DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()


def trace_from_history_run(run) -> dict:
    if not run:
        return {}
    trace = safe_json_loads(row_value(run, "router_trace_json"), {})
    trace.update({
        "mode": row_value(run, "mode"),
        "model": row_value(run, "model"),
        "provider": row_value(run, "provider"),
        "latency_ms": row_value(run, "latency_ms", 0),
        "estimated_cost": row_value(run, "estimated_cost", 0),
        "status": row_value(run, "execution_status"),
        "error_code": row_value(run, "error_code"),
        "error_message": row_value(run, "error_message"),
        "execution_prompt": row_value(run, "prompt_text"),
    })
    return normalize_trace(trace)


def save_execution_result(
    task_id: int,
    model_used: str,
    router_summary: str,
    llm_output: str,
    useful_extract: str,
    execution_status: str = "executed",  # "executed" (real), "preview" (demo), "failed" (error)
    router_metrics: Optional[dict] = None  # Bloque E0: métricas estructuradas JSON
) -> None:
    """
    Guarda resultado de ejecución o propuesta previa con métricas estructuradas.

    Args:
        task_id: ID de la tarea
        model_used: Modelo usado
        router_summary: Resumen de decisión del Router
        llm_output: Output (real o demo)
        useful_extract: Extracto para referencia rápida
        execution_status: "executed" (ejecución real) | "preview" (propuesta previa sin Gemini) | "failed" (error)
        router_metrics: Dict con mode, model, provider, latency_ms, estimated_cost, complexity_score, status, reasoning_path, executed_at
    """
    # Serializar router_metrics a JSON (Bloque E0)
    metrics_json = json.dumps(router_metrics or {})

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET suggested_model = ?, router_summary = ?, llm_output = ?, useful_extract = ?,
                status = ?, execution_status = ?, router_metrics_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (model_used, router_summary, llm_output, useful_extract, execution_status, execution_status, metrics_json, now_iso(), task_id),
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
        except Exception as e:
            print(f"[WARN] No se pudo persistir executions_history para task {task_id}: {e}")


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


def asset_type_label(asset_type: str) -> str:
    return ASSET_TYPE_LABELS.get(str(asset_type or "").strip().lower(), "Activo")


def asset_preview_text(asset) -> str:
    summary = compact_text(row_value(asset, "summary"), 140)
    if summary:
        return summary
    return compact_text(row_value(asset, "content"), 140)


def build_asset_reuse_context(asset) -> str:
    parts = [f"[ACTIVO REUTILIZADO · {asset_type_label(row_value(asset, 'asset_type'))}]"]
    if row_value(asset, "title"):
        parts.append(f"Título: {row_value(asset, 'title')}")
    if row_value(asset, "summary"):
        parts.append(f"Resumen: {row_value(asset, 'summary')}")
    if row_value(asset, "task_title"):
        parts.append(f"Tarea origen: {row_value(asset, 'task_title')}")
    parts.append("")
    parts.append(row_value(asset, "content"))
    return "\n".join(part for part in parts if part is not None).strip()


def write_asset_files(asset_id: int, asset, project, task_title: str) -> tuple[str, str]:
    target = REUSABLE_ASSETS_DIR / f"project_{int(row_value(asset, 'project_id', 0) or 0):04d}" / f"asset_{asset_id:04d}"
    target.mkdir(parents=True, exist_ok=True)
    md_path = target / f"asset_{asset_id:04d}.md"
    json_path = target / f"asset_{asset_id:04d}.json"

    payload = {
        "asset_id": asset_id,
        "project_id": row_value(asset, "project_id"),
        "project_name": row_value(project, "name"),
        "task_id": row_value(asset, "task_id"),
        "task_title": task_title,
        "source_execution_id": row_value(asset, "source_execution_id"),
        "source_execution_status": row_value(asset, "source_execution_status"),
        "asset_type": row_value(asset, "asset_type"),
        "title": row_value(asset, "title"),
        "summary": row_value(asset, "summary"),
        "content": row_value(asset, "content"),
        "created_at": row_value(asset, "created_at"),
        "updated_at": row_value(asset, "updated_at"),
    }

    md = f"""# PWR Reusable Asset

Project: {payload['project_name']}
Asset: {payload['title']}
Type: {payload['asset_type']}
Created: {payload['created_at']}

## Origin

- Task: {payload['task_title'] or '(none)'}
- Source run: {payload['source_execution_id'] or '(none)'}
- Source state: {payload['source_execution_status'] or '(none)'}

## Summary

{payload['summary'] or '(none)'}

## Content

```text
{payload['content']}
```
"""
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return repo_relative_path(md_path), repo_relative_path(json_path)


def create_asset(
    project_id: int,
    task_id: int,
    title: str,
    summary: str,
    content: str,
    asset_type: str = "output",
    source_execution_id: Optional[int] = None,
    source_execution_status: str = "",
) -> int:
    created = now_iso()
    asset_type = str(asset_type or "output").strip().lower()
    if asset_type not in ASSET_TYPE_LABELS:
        asset_type = "output"

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO assets (
                project_id, task_id, source_execution_id, asset_type, source_execution_status,
                title, summary, content, created_at, updated_at, artifact_md_path, artifact_json_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '')
            """,
            (
                project_id,
                task_id,
                source_execution_id,
                asset_type,
                source_execution_status.strip(),
                title.strip(),
                summary.strip(),
                content.strip(),
                created,
                created,
            ),
        )
        asset_id = int(cur.lastrowid)
        asset = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        task = conn.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone() if task_id else None
        task_title = row_value(task, "title")
        md_path, json_path = write_asset_files(asset_id, asset, project, task_title)
        conn.execute(
            """
            UPDATE assets
            SET artifact_md_path = ?, artifact_json_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (md_path, json_path, created, asset_id),
        )
        return asset_id


def get_project_assets(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT
                a.*,
                t.title AS task_title,
                eh.executed_at AS source_executed_at,
                eh.provider AS source_provider,
                eh.model AS source_model
            FROM assets a
            LEFT JOIN tasks t ON a.task_id = t.id
            LEFT JOIN executions_history eh ON a.source_execution_id = eh.id
            WHERE a.project_id = ?
            ORDER BY COALESCE(a.updated_at, a.created_at) DESC, a.id DESC
            """,
            (project_id,),
        ).fetchall()


def get_asset(asset_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT
                a.*,
                p.name AS project_name,
                t.title AS task_title,
                eh.executed_at AS source_executed_at,
                eh.provider AS source_provider,
                eh.model AS source_model
            FROM assets a
            LEFT JOIN projects p ON a.project_id = p.id
            LEFT JOIN tasks t ON a.task_id = t.id
            LEFT JOIN executions_history eh ON a.source_execution_id = eh.id
            WHERE a.id = ?
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()


# ==================== BLOQUE E1: RADAR SNAPSHOT LAYER ====================
def build_radar_snapshot(internal: bool = False) -> dict:
    """
    Construye snapshot del catálogo vivo (E1a: Snapshot Layer).

    Esta es la FUENTE ÚNICA para Radar v1. Está diseñada para ser reutilizable:
    - Hoy: renderizada en vista Streamlit
    - Mañana: exportable a JSON, API REST, dashboards externos

    Responsabilidades:
    - Conectar a BD
    - Instanciar ModelCatalog desde datos vivos
    - Llamar export_public_catalog(include_internal)
    - Envolver con metadata clara

    Args:
        internal: bool
          - False (default): Filtra modelos con is_internal=1 (mock, test)
          - True: Incluye modelos internos (solo para debugging)

    Returns:
        dict con estructura:
        {
          "status": "ok|error",
          "radar": {
            "providers": {...},
            "modes": {...},
            "summary": {...}
          },
          "metadata": {
            "generated_at": ISO8601,
            "radar_version": "1.0",
            ...
          }
        }

    NOTA IMPORTANTE: "Radar v1 = Live Catalog Snapshot"
    - ✅ QUÉ está disponible hoy (providers, modelos, modos)
    - ❌ NO es observatorio histórico
    - ❌ NO es benchmarking
    - ❌ NO es health monitor
    - ❌ NO es scoring adaptativo
    """
    try:
        with get_conn() as conn:
            catalog = ModelCatalog(conn)
            radar_data = catalog.export_public_catalog(include_internal=internal)

        return {
            "status": "ok",
            "radar": radar_data,
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0",
                "catalog_source": "model_catalog BD",
                "framing": "live catalog snapshot (NOT historical observatory)",
                "note": "Mode = temporal bridge to router_policy table (future phase)",
                "include_internal": internal
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0"
            }
        }


def inject_css():
    st.markdown(
        """
        <style>
        /* GLOBAL */
        .stApp { background: #FAFBFC; color: #0F172A; }
        .block-container { max-width: 1480px; padding-top: 0.75rem; padding-bottom: 1.4rem; padding-left: 1.2rem; padding-right: 1.2rem; }

        /* SIDEBAR */
        [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stSidebar"] * { color: #0F172A !important; }

        /* PANELS */
        .panel {
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            border-radius:10px;
            padding:1.25rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.08);
        }

        .router-panel {
            border-left: 4px solid #10B981;
            box-shadow: 0 2px 8px rgba(15,23,42,0.1);
            border-top: 1px solid #F1F5F9;
            padding: 1.75rem !important;
        }

        /* CONTEXT BAR */
        .context-bar {
            padding: 1rem;
            border-bottom: 1px solid #F1F5F9;
            font-size: 12px;
        }

        .context-label {
            font-size: 10px;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .context-item {
            padding: 0.4rem 0;
            display: flex;
            gap: 0.75rem;
            align-items: center;
            font-size: 12px;
            color: #475569;
        }

        .context-value {
            margin-left: auto;
            color: #94A3B8;
            font-size: 12px;
        }

        /* COMMAND BAR */
        .command-bar {
            padding: 1rem;
            border-bottom: 1px solid #E2E8F0;
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        }

        .command-label {
            font-size: 10px;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        /* TASK LIST */
        .task-list-header {
            padding: 0.75rem 1rem;
            font-size: 11px;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: #F8FAFC;
            border-bottom: 1px solid #F1F5F9;
        }

        .task-item {
            padding: 0.75rem;
            border-bottom: 1px solid #F1F5F9;
            border-left: 3px solid transparent;
            margin: 0 0.5rem;
            border-radius: 0 6px 6px 0;
            cursor: pointer;
            transition: all 0.2s;
        }

        .task-item:hover {
            background: #F8FAFC;
        }

        .task-item.active {
            background: #EFF6FF;
            border-left-color: #2563EB;
        }

        .task-title {
            font-size: 13px;
            font-weight: 500;
            color: #0F172A;
            margin-bottom: 0.3rem;
        }

        .task-meta {
            display: flex;
            gap: 0.5rem;
            font-size: 11px;
            color: #94A3B8;
        }

        .task-meta-item {
            background: #F1F5F9;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 500;
        }

        /* FORMS */
        div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea {
            border-radius: 8px !important;
            border: 1px solid #E2E8F0 !important;
            background: #FFF !important;
            color: #0F172A !important;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        }

        /* BUTTONS */
        div.stButton > button, .stDownloadButton > button {
            border-radius: 6px !important;
            border: 1px solid #CBD5E1 !important;
            background: #FFF !important;
            color: #0F172A !important;
            padding: 0.6rem 1rem !important;
            font-weight: 600 !important;
            font-size: 13px !important;
        }

        div.stButton > button:hover, .stDownloadButton > button:hover {
            border-color: #94A3B8 !important;
            background: #F8FAFC !important;
        }

        /* PRIMARY BUTTON OVERRIDE */
        [data-testid="stVerticalBlock"] > :nth-child(1) div.stButton > button {
            background: #2563EB !important;
            color: #FFFFFF !important;
            border-color: #2563EB !important;
        }

        [data-testid="stVerticalBlock"] > :nth-child(1) div.stButton > button:hover {
            background: #1D4ED8 !important;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
        }

        /* EMPTY STATE */
        .empty-state {
            text-align: center;
            padding: 3rem 2rem;
            color: #64748B;
        }

        .empty-icon { font-size: 48px; margin-bottom: 1rem; opacity: 0.6; }
        .empty-title { font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 0.5rem; }
        .empty-description { font-size: 13px; margin-bottom: 1.5rem; line-height: 1.6; }

        .empty-steps { font-size: 12px; text-align: left; display: inline-block; }
        .empty-step { margin: 0.4rem 0; display: flex; gap: 0.75rem; align-items: flex-start; }
        .step-number {
            background: #F1F5F9; color: #64748B; width: 24px; height: 24px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            font-weight: 600; flex-shrink: 0; font-size: 11px;
        }

        /* HOME PAGE STYLES */
        .home-header {
            background: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
            padding: 1rem 1.5rem;
            margin-bottom: 0;
        }

        .home-header-title {
            font-size: 18px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.25rem;
        }

        .home-header-subtitle {
            font-size: 13px;
            color: #64748B;
        }

        .home-main {
            padding: 1.5rem;
            max-width: 1000px;
            margin: 0 auto;
            width: 100%;
        }

        .home-block-title {
            font-size: 12px;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 1rem;
            margin-top: 1.5rem;
        }

        .home-block-title:first-of-type {
            margin-top: 0;
        }

        .home-recent-work {
            display: flex;
            flex-direction: column;
            gap: 0;
            margin-bottom: 2rem;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            overflow: hidden;
        }

        .home-task-item {
            background: #FFFFFF;
            border-bottom: 1px solid #F1F5F9;
            padding: 1.25rem;
            display: flex;
            gap: 1rem;
            align-items: flex-start;
        }

        .home-task-item:last-child {
            border-bottom: none;
        }

        .home-task-item.active {
            background: #EFF6FF;
        }

        .home-task-content {
            flex: 1;
        }

        .home-task-title {
            font-size: 14px;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.5rem;
        }

        .home-task-item.active .home-task-title {
            font-size: 15px;
            font-weight: 700;
        }

        .home-task-meta {
            font-size: 11px;
            color: #94A3B8;
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .home-task-meta-badge {
            background: #F1F5F9;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 500;
        }

        .home-task-button {
            padding: 0.5rem 1rem;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .home-task-item.active .home-task-button {
            background: #2563EB;
            color: #FFFFFF;
        }

        .home-task-item:not(.active) .home-task-button {
            background: transparent;
            color: #2563EB;
            border: 1.5px solid #DBEAFE;
        }

        .home-task-item:not(.active) .home-task-button:hover {
            background: #EFF6FF;
            border-color: #BFDBFE;
        }

        .home-capture-block {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 2rem;
        }

        .home-capture-input-wrapper {
            position: relative;
            margin-bottom: 0.75rem;
        }

        .home-capture-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #2563EB;
            font-weight: 600;
            font-size: 14px;
        }

        .home-capture-input {
            width: 100%;
            background: #FFFFFF;
            border: 2px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.75rem 0.75rem 0.75rem 2.5rem;
            font-size: 13px;
            color: #0F172A;
            font-weight: 500;
            transition: all 0.2s;
        }

        .home-capture-input:focus {
            outline: none;
            border-color: #2563EB;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .home-capture-input::placeholder {
            color: #94A3B8;
        }

        .home-capture-options {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
            font-size: 11px;
        }

        .home-capture-option {
            color: #2563EB;
            text-decoration: none;
            font-weight: 600;
            cursor: pointer;
            transition: color 0.2s;
        }

        .home-capture-option:hover {
            color: #1D4ED8;
            text-decoration: underline;
        }

        .home-capture-button {
            background: #2563EB;
            color: #FFFFFF;
            border: none;
            padding: 0.65rem 1rem;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s;
        }

        .home-capture-button:hover:not(:disabled) {
            background: #1D4ED8;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2);
        }

        .home-capture-button:disabled {
            background: #CBD5E1;
            cursor: not-allowed;
        }

        .home-projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .home-project-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .home-project-header {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .home-project-icon {
            font-size: 18px;
        }

        .home-project-name {
            font-size: 14px;
            font-weight: 600;
            color: #0F172A;
        }

        .home-project-tasks {
            font-size: 12px;
            color: #64748B;
        }

        .home-project-lastupdate {
            font-size: 11px;
            color: #94A3B8;
        }

        .home-project-actions {
            display: flex;
            gap: 0.75rem;
            align-items: center;
            margin-top: 0.5rem;
        }

        .home-project-button-open {
            flex: 1;
            background: #2563EB;
            color: #FFFFFF;
            border: none;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .home-project-button-open:hover {
            background: #1D4ED8;
        }

        .home-project-favorite {
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.2s;
            padding: 0.4rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .home-project-favorite:hover {
            background: #F1F5F9;
            border-radius: 6px;
        }

        .home-projects-link {
            color: #2563EB;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: color 0.2s;
        }

        .home-projects-link:hover {
            text-decoration: underline;
        }

        .home-create-project-container {
            display: flex;
            justify-content: center;
            margin-top: 1rem;
        }

        .home-create-project-button {
            background: transparent;
            color: #2563EB;
            border: 1.5px solid #DBEAFE;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .home-create-project-button:hover {
            background: #EFF6FF;
            border-color: #BFDBFE;
        }

        .home-empty-state {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
        }

        .home-empty-icon {
            font-size: 40px;
            margin-bottom: 1rem;
            opacity: 0.6;
        }

        .home-empty-title {
            font-size: 14px;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.5rem;
        }

        .home-empty-description {
            font-size: 12px;
            color: #64748B;
            margin-bottom: 1rem;
            line-height: 1.6;
        }

        .home-empty-link {
            color: #2563EB;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            border-bottom: 1px solid #2563EB;
            cursor: pointer;
            transition: color 0.2s;
        }

        .home-empty-link:hover {
            color: #1D4ED8;
        }

        @media (max-width: 768px) {
            .home-main {
                padding: 1rem;
            }

            .home-projects-grid {
                grid-template-columns: 1fr;
            }
        }


        /* ========== PWR GLOBAL SHELL (FASE 1) ========== */
        :root {
            --pwr-bg: #ffffff;
            --pwr-bg-subtle: #f9fafb;
            --pwr-text: #1f2937;
            --pwr-text-secondary: #6b7280;
            --pwr-border: #e5e7eb;
            --pwr-accent: #2563eb;
            --pwr-radius: 4px;
            --pwr-spacing-xs: 8px;
            --pwr-spacing-sm: 12px;
            --pwr-spacing-md: 16px;
            --pwr-spacing-lg: 24px;
            --pwr-header-height: 60px;
            --pwr-max-width: 1200px;
        }

        /* Global app styling */
        .stApp {
            background: var(--pwr-bg);
        }

        /* Hide Streamlit default sidebar */
        [data-testid="stSidebar"] {
            display: none !important;
        }

        /* Main content area - control width and padding */
        .block-container {
            max-width: var(--pwr-max-width) !important;
            margin: 0 auto !important;
            padding: var(--pwr-spacing-lg) !important;
        }

        /* PWR Header wrapper */
        .pwr-header-container {
            height: var(--pwr-header-height);
            background: var(--pwr-bg);
            border-bottom: 1px solid var(--pwr-border);
            display: flex;
            align-items: center;
            padding: 0 var(--pwr-spacing-lg);
            position: sticky;
            top: 0;
            z-index: 999;
            margin: calc(var(--pwr-spacing-lg) * -1);
            margin-bottom: var(--pwr-spacing-lg);
        }

        .pwr-header-brand {
            font-size: 18px;
            font-weight: 700;
            color: var(--pwr-text);
            letter-spacing: -0.5px;
        }

        .pwr-header-nav {
            display: flex;
            gap: var(--pwr-spacing-lg);
            margin-left: var(--pwr-spacing-xl);
            flex: 1;
        }

        .pwr-header-nav-item {
            font-size: 14px;
            color: var(--pwr-text-secondary);
            cursor: pointer;
            padding: 8px 0;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .pwr-header-nav-item:hover {
            color: var(--pwr-text);
        }

        .pwr-header-nav-item.active {
            color: var(--pwr-accent);
            border-bottom-color: var(--pwr-accent);
        }

        .pwr-header-actions {
            display: flex;
            gap: var(--pwr-spacing-md);
            margin-left: auto;
        }

        /* Typography improvements */
        html, body, * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--pwr-text);
            line-height: 1.2;
            letter-spacing: -0.3px;
        }

        p, span, div {
            color: var(--pwr-text);
        }

        /* Button normalization */
        .stButton button {
            border: 1px solid var(--pwr-border) !important;
            background: var(--pwr-bg) !important;
            color: var(--pwr-text) !important;
            border-radius: var(--pwr-radius) !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            transition: all 0.2s ease !important;
        }

        .stButton button:hover {
            background: var(--pwr-bg-subtle) !important;
            border-color: var(--pwr-text-secondary) !important;
        }

        /* Primary button */
        .stButton button[kind="primary"] {
            background: var(--pwr-accent) !important;
            color: #ffffff !important;
            border-color: var(--pwr-accent) !important;
        }

        .stButton button[kind="primary"]:hover {
            background: #1d4ed8 !important;
            border-color: #1d4ed8 !important;
        }

        /* Card normalization */
        .pwr-card {
            background: var(--pwr-bg);
            border: 1px solid var(--pwr-border);
            border-radius: var(--pwr-radius);
            padding: var(--pwr-spacing-lg);
        }

        /* Spacing utilities */
        .pwr-spacing-md {
            margin-bottom: var(--pwr-spacing-md);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )




def render_pwr_header():
    """Renderiza header superior con navegación principal."""
    current_view = st.session_state.get("view", "home")
    col_brand, col_nav_init, col_nav_tasks, col_nav_projects, col_nav_radar, col_actions = st.columns([1.2, 1.2, 1.2, 1.5, 1.2, 2], gap="small")
    
    with col_brand:
        st.markdown("<div class='pwr-header-brand'>PWR</div>", unsafe_allow_html=True)
    
    with col_nav_init:
        if st.button("Inicio", use_container_width=True, key="nav_home"):
            st.session_state["view"] = "home"
            st.rerun()
    
    with col_nav_tasks:
        if st.button("Tareas", use_container_width=True, key="nav_tasks"):
            st.session_state["view"] = "new_task"
            st.rerun()
    
    with col_nav_projects:
        if st.button("Proyectos", use_container_width=True, key="nav_projects"):
            st.session_state["view"] = "project_view"
            st.rerun()
    
    with col_nav_radar:
        if st.button("Radar", use_container_width=True, key="nav_radar"):
            st.session_state["view"] = "radar"
            st.rerun()
    
    with col_actions:
        if st.button("Nueva Tarea", use_container_width=True, key="nav_new_task_primary", type="primary"):
            st.session_state["view"] = "new_task"
            st.rerun()
    
    st.divider()


def project_selector():
    projects = get_projects()
    names = [p["name"] for p in projects]
    selected_project_id = st.session_state.get("active_project_id")
    default_index = 0
    options = ["Seleccionar proyecto"] + names
    if selected_project_id:
        current = get_project(selected_project_id)
        if current and current["name"] in names:
            default_index = names.index(current["name"]) + 1

    selected_name = st.selectbox("Proyecto activo", options, index=default_index)
    if selected_name != "Seleccionar proyecto":
        for p in projects:
            if p["name"] == selected_name:
                st.session_state["active_project_id"] = p["id"]
                break


def render_header():
    projects = get_projects()
    total_tasks = sum([p["task_count"] for p in projects])
    total_assets = sum([p["asset_count"] for p in projects])

    c1, c2 = st.columns([2.2, 1.4])
    with c1:
        st.markdown(
            """
            <div class="card">
                <h1 style="margin:0;">Portable Work Router</h1>
                <div class="muted">Selecciona un proyecto, captura una tarea y conviértela en trabajo reusable.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric"><div class="meta">Proyectos</div><div style="font-size:1.35rem;font-weight:700;">{len(projects)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric"><div class="meta">Tareas</div><div style="font-size:1.35rem;font-weight:700;">{total_tasks}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric"><div class="meta">Activos</div><div style="font-size:1.35rem;font-weight:700;">{total_assets}</div></div>', unsafe_allow_html=True)


def get_recent_executed_tasks(limit: int = 3) -> List[Dict]:
    """Get recent tasks relevant for Home re-entry, ordered by recency or re-entry priority."""
    return get_recent_home_tasks(limit=limit, states=("executed",), prioritize_reentry=False)


def home_task_icon(state: str) -> str:
    return {
        "executed": "✅",
        "preview": "📝",
        "failed": "⚠️",
        "pending": "⏳",
        "draft": "🗒️",
    }.get(state, "📌")


def home_task_action_label(state: str) -> str:
    return {
        "executed": "Abrir",
        "preview": "Continuar",
        "failed": "Revisar fallo",
        "pending": "Retomar",
        "draft": "Retomar",
    }.get(state, "Abrir")


def get_recent_home_tasks(
    limit: int = 5,
    states: tuple[str, ...] = HOME_ACTIVITY_STATES,
    today_only: bool = False,
    prioritize_reentry: bool = False,
) -> List[Dict]:
    conn = get_conn()
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

    rows = conn.execute(
        f"""
        SELECT
            t.id, t.project_id, t.title, t.task_type, t.suggested_model,
            t.updated_at, p.name as project_name,
            {state_expr} AS execution_status
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY {order_by}
        LIMIT ?
        """,
        (*params, limit)
    ).fetchall()
    return [dict(row) for row in rows]


def get_projects_with_activity() -> List[Dict]:
    """Get all projects with task count and last activity timestamp"""
    projects = get_projects()
    result = []
    for p in projects:
        project_dict = dict(p)
        # Get task count
        conn = get_conn()
        task_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE project_id = ?",
            (p["id"],)
        ).fetchone()["cnt"]

        # Get last activity timestamp
        last_task = conn.execute(
            "SELECT updated_at FROM tasks WHERE project_id = ? ORDER BY updated_at DESC LIMIT 1",
            (p["id"],)
        ).fetchone()

        project_dict["active_task_count"] = task_count
        project_dict["last_activity"] = last_task["updated_at"] if last_task else p["created_at"]
        result.append(project_dict)

    return result


def reuse_asset_as_task_base(project_id: int, asset) -> None:
    st.session_state[f"asset_reuse_payload_{project_id}"] = {
        "title": row_value(asset, "title") or "Nueva tarea",
        "context": build_asset_reuse_context(asset),
        "notice": f"Activo cargado como base: {row_value(asset, 'title')}. Ajusta título o contexto y genera una nueva propuesta.",
    }
    st.session_state["selected_asset_id"] = None
    st.session_state["selected_task_id"] = None
    st.session_state["view"] = "project_view"


def render_asset_detail(project_id: int, asset) -> None:
    st.markdown("#### Activo reutilizable")
    meta_parts = [
        asset_type_label(row_value(asset, "asset_type")),
        format_time_ago(row_value(asset, "updated_at") or row_value(asset, "created_at")),
    ]
    if row_value(asset, "task_title"):
        meta_parts.append(f"Origen: {row_value(asset, 'task_title')}")
    if row_value(asset, "source_execution_status"):
        meta_parts.append(task_state_caption(row_value(asset, "source_execution_status")))
    st.caption(" · ".join(part for part in meta_parts if part))

    if row_value(asset, "source_provider") or row_value(asset, "source_model"):
        st.caption(
            f"Motor origen: {row_value(asset, 'source_provider') or 'provider?'} / "
            f"{row_value(asset, 'source_model') or 'modelo?'}"
        )

    if row_value(asset, "summary"):
        st.info(row_value(asset, "summary"))

    action_col1, action_col2, action_col3 = st.columns([2.2, 1.4, 1.2])
    with action_col1:
        if st.button("Usar como base de nueva tarea", use_container_width=True, key=f"use_asset_primary_{row_value(asset, 'id')}"):
            reuse_asset_as_task_base(project_id, asset)
            st.rerun()
    with action_col2:
        task_id = int(row_value(asset, "task_id", 0) or 0)
        if task_id and st.button("Abrir tarea origen", use_container_width=True, key=f"open_asset_task_{row_value(asset, 'id')}"):
            open_task_workspace(project_id, task_id)
            st.rerun()
    with action_col3:
        if st.button("Cerrar activo", use_container_width=True, key=f"close_asset_{row_value(asset, 'id')}"):
            st.session_state["selected_asset_id"] = None
            st.rerun()

    st.text_area(
        "Contenido del activo",
        value=row_value(asset, "content"),
        height=320,
        key=f"asset_content_{row_value(asset, 'id')}",
        disabled=True,
    )

    if row_value(asset, "artifact_md_path") or row_value(asset, "artifact_json_path"):
        with st.expander("Rastro portable del activo", expanded=False):
            if row_value(asset, "artifact_md_path"):
                st.caption("Markdown")
                st.code(row_value(asset, "artifact_md_path"), language="text")
            if row_value(asset, "artifact_json_path"):
                st.caption("JSON")
                st.code(row_value(asset, "artifact_json_path"), language="text")


def format_time_ago(iso_string: str) -> str:
    """Convert ISO timestamp to human-readable 'time ago' format"""
    if not iso_string:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_string)
        now = datetime.now()
        diff = now - dt

        if diff.days > 7:
            return "Hace 1+ semanas"
        elif diff.days > 0:
            return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "Hace unos segundos"
    except:
        return iso_string


def generate_demo_proposal(decision, task_input: "TaskInput") -> dict:
    """
    Genera propuesta previa útil cuando no hay proveedor real.

    No ejecuta nada. Solo usa el análisis del Router para mostrar:
    - Qué ha entendido el sistema
    - Cómo lo resolvería
    - Prioridades
    - Prompt sugerido
    - Estimaciones

    Args:
        decision: RoutingDecision del Router
        task_input: TaskInput con titulo, descripción, contexto

    Returns:
        dict con:
        {
            "understood": str,
            "strategy": str,
            "priority": str,
            "expected_output": str,
            "suggested_prompt": str,
            "mode": str ("eco" o "racing"),
            "model": str (nombre del modelo),
            "time_estimate": str,
            "cost_estimate": str
        }
    """
    # Extraer información del RouterDecision y TaskInput
    title = task_input.title.strip()
    description = task_input.description.strip()
    context = task_input.context.strip()
    mode = decision.mode

    # Mapeos para estimaciones
    if mode == "eco":
        time_estimate = "~2–4s"
        cost_estimate = "bajo"
        mode_label = "rápido y preciso"
    else:  # racing
        time_estimate = "~10–30s"
        cost_estimate = "medio-alto"
        mode_label = "análisis profundo y detallado"

    # Generar "Qué he entendido" (resumen natural de la tarea)
    understood_parts = []
    if title:
        understood_parts.append(f"Quieres {title.lower()}")
    if description:
        understood_parts.append(description)
    if context:
        understood_parts.append(f"Con contexto: {context}")

    understood = ", ".join(understood_parts) if understood_parts else "Analizar una tarea"
    understood = understood[0].upper() + understood[1:] + "."

    # Generar "Cómo lo resolvería" basado en modo y señales
    if mode == "eco":
        strategy = f"Lo abordaría de forma rápida, enfocándome en lo esencial y devolviendo una respuesta clara y directa."
    else:
        strategy = f"Lo abordaría con análisis profundo, considerando alternativas y devolviendo una recomendación fundamentada."

    # Prioridades claras según modo
    priority = "velocidad y claridad" if mode == "eco" else "precisión y profundidad"

    # Salida esperada (inferida del tipo de tarea)
    task_type = task_input.task_type or "Pensar"
    expected_output_map = {
        "Pensar": "análisis estructurado con recomendaciones",
        "Escribir": "contenido claro y listo para usar",
        "Programar": "código funcional y documentado",
        "Revisar": "evaluación con puntos de mejora",
        "Decidir": "comparación de opciones con recomendación",
    }
    expected_output = expected_output_map.get(task_type, "respuesta clara y estructurada")

    execution_prompt = build_execution_prompt(task_input)

    return {
        "understood": understood,
        "strategy": strategy,
        "priority": priority,
        "expected_output": expected_output,
        "execution_prompt": execution_prompt,
        "suggested_prompt": execution_prompt,
        "mode": mode,
        "model": decision.model,
        "time_estimate": time_estimate,
        "cost_estimate": cost_estimate,
    }


def display_demo_mode_panel(demo_proposal: dict) -> None:
    """
    Muestra panel de propuesta previa cuando no hay proveedor real.

    Estructura:
    - Qué he entendido
    - Cómo lo resolvería
    - Prompt sugerido
    - Para resultado real: configurar motor

    Args:
        demo_proposal: dict retornado por generate_demo_proposal()
    """
    st.write("")  # Espaciado

    # Header: Propuesta previa (no "demo", es preview operativa)
    st.markdown("### ✨ Propuesta previa")
    st.caption("La ejecución real requiere conectar un motor")

    st.write("")

    # Bloque 1: Qué he entendido
    st.markdown("**🧠 Qué he entendido**")
    st.write(demo_proposal["understood"])

    st.write("")

    # Bloque 2: Cómo lo resolvería
    st.markdown("**🎯 Cómo lo resolvería**")
    st.write(demo_proposal["strategy"])
    st.caption(f"**Prioridad:** {demo_proposal['priority']}")
    st.caption(f"**Salida esperada:** {demo_proposal['expected_output']}")

    st.write("")

    # Bloque 3: contenido real que usaria la ejecucion
    st.markdown("**Contenido de ejecucion**")
    st.code(demo_proposal["execution_prompt"], language="text")

    st.write("")

    # Bloque 4: CTA
    st.info(
        f"**Modo:** {demo_proposal['mode'].upper()} | "
        f"**Modelo:** {demo_proposal['model']} | "
        f"⏱️ {demo_proposal['time_estimate']} | "
        f"💰 {demo_proposal['cost_estimate']}"
    )

    st.write("")
    st.caption("Para generar el resultado real, conecta un motor en Configuración")


def display_decision_preview(decision, task_title: str):
    """
    Muestra la decisión del Router de forma clara y atractiva.

    Estructura:
    💡 Cómo lo voy a resolver

    Modo recomendado: ECO (rápido) / RACING (análisis profundo)
    Motivo: [reasoning]

    Tiempo estimado: ~2–4s / ~10–30s
    Coste estimado: bajo / medio-alto
    """
    if not decision or not task_title.strip():
        return

    mode_emoji = "🟢" if decision.mode == "eco" else "🔵"
    mode_label = "ECO (rápido)" if decision.mode == "eco" else "RACING (análisis profundo)"

    # Estimaciones basadas en modo
    if decision.mode == "eco":
        time_est = "~2–4s"
        cost_level = "bajo"
    else:
        time_est = "~10–30s"
        cost_level = "medio-alto"

    st.info("")  # Espaciado visual
    st.markdown("### 💡 Cómo lo voy a resolver")
    st.markdown(f"**Modo recomendado:** {mode_label}")
    st.caption(f"Proveedor/modelo real: {decision.provider} / {decision.model}")

    # Extraer motivo del reasoning_path (primera línea o primera oración)
    reasoning_lines = decision.reasoning_path.split("\n")
    motivo = reasoning_lines[0] if reasoning_lines else "Decisión automática"
    st.markdown(f"**Motivo:** {motivo}")

    st.write("")  # Espaciado

    # Metadata: Tiempo y Coste (formato compacto)
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"⏱️ Tiempo estimado: {time_est}")
    with col2:
        st.caption(f"💰 Coste estimado: {cost_level}")


def display_execution_view(decision, task_input: TaskInput, execution_prompt: str, trace: Optional[dict] = None) -> None:
    """Shows the same execution brief that the provider will receive."""
    if not decision:
        return

    st.markdown("### Vista de ejecucion")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"**Modo**\n{decision.mode}")
    with col2:
        st.caption(f"**Proveedor**\n{decision.provider}")
    with col3:
        st.caption(f"**Modelo**\n{decision.model}")

    included = [
        "contexto estable" if task_input.project_base_context.strip() else "sin contexto estable",
        "instrucciones base" if task_input.project_base_instructions.strip() else "sin instrucciones base",
        "contexto temporal" if task_input.context.strip() else "sin contexto temporal",
    ]
    st.caption("Incluye: " + " · ".join(included))

    if trace and trace.get("status") and trace.get("status") != "pending":
        status = trace.get("status")
        latency = trace.get("latency_ms", 0)
        cost = trace.get("estimated_cost", 0)
        st.caption(f"Ultima ejecucion: {status} · ~{latency}ms · ${cost:.4f}")

    with st.expander("Contenido que se ejecuta", expanded=False):
        st.code(execution_prompt, language="text")


def display_onboarding_result(result, task_input, is_first_execution: bool = True, project_name: str = None, task_name: str = None):
    """
    H: Muestra resultado de ejecución con persistencia visible

    1. Resultado - contenido principal
    2. "Guardado en" - sección clara y sobria (no célébración)
    3. Acciones jerárquicas: Ver proyecto (PRIMARIA) > Reutilizar/Crear (SECUNDARIAS) > Copiar (TERCIARIA)

    Propósito: Cerrar con claridad, tranquilidad, persistencia visible y siguiente paso obvio
    """
    if not result or result.status == "error":
        return

    st.write("")  # Espaciado

    # ==================== RESULTADO PRINCIPAL ====================
    st.markdown("### 📋 Resultado")
    st.markdown(result.output_text)

    st.write("")  # Espaciado

    # ==================== BLOQUE: Guardado en (sobrio y tranquilizador) ====================
    # Sección muy compacta, clara, sin celebración
    col1, col2 = st.columns([0.08, 0.92])
    with col1:
        st.markdown("✅")
    with col2:
        st.markdown("**Guardado**")

    if project_name and task_name:
        st.caption(f"En: **{project_name[:40]}**")
        st.caption(f"Tarea: **{task_name[:50]}**")

    st.write("")  # Espaciado pequeño

    # ==================== ACCIÓN PRIMARIA: Ver en proyecto ====================
    # CTA clara que guía sin aplastar el resultado
    if st.button("📂 Ver en proyecto", use_container_width=True, type="primary", key="result_view_project"):
        # Guarda datos para que home/project_view sepan dónde ir
        if "project_id" in st.session_state.get("onboard_result", {}):
            st.session_state["active_project_id"] = st.session_state["onboard_result"]["project_id"]
        st.session_state["view"] = "home"
        st.rerun()

    st.write("")  # Espaciado

    # ==================== ACCIONES SECUNDARIAS: Más opciones ====================
    st.caption("Más acciones:")

    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button("🔄 Usar como contexto", use_container_width=True, key="result_use_context"):
            # Guarda resultado para pasar como contexto a nueva tarea
            extract = result.output_text[:500]
            st.session_state["context_from_result"] = extract
            st.session_state["view"] = "new_task"
            st.rerun()

    with col2:
        if st.button("🎯 Crear tarea relacionada", use_container_width=True, key="result_create_related"):
            # Abre new_task en el proyecto actual
            if "project_id" in st.session_state.get("onboard_result", {}):
                st.session_state["active_project_id"] = st.session_state["onboard_result"]["project_id"]
            st.session_state["view"] = "new_task"
            st.rerun()

    st.write("")  # Espaciado pequeño

    # ==================== ACCIÓN TERCIARIA: Copiar (expandible, discreta) ====================
    with st.expander("📋 Copiar resultado", expanded=False):
        extract = result.output_text[:700]
        st.text_area("",
                     value=extract,
                     height=120,
                     disabled=True,
                     label_visibility="collapsed")
        st.caption("Selecciona y copia el texto que necesites")


# ════════════════════════════════════════════════════════════════════════════════
# BLOQUE E1: RADAR SNAPSHOT LAYER + VISTA
# ════════════════════════════════════════════════════════════════════════════════
# Snapshot function: Aislada, limpia, reutilizable
# Preparada para extraer a módulo propio si es necesario (E2+)
# ════════════════════════════════════════════════════════════════════════════════

def build_radar_snapshot(internal: bool = False) -> dict:
    """
    Construye snapshot del catálogo vivo (E1a - Snapshot Layer).

    Responsabilidades:
    - Conectar a BD
    - Instanciar ModelCatalog desde datos vivos
    - Exportar catálogo con filtrado de is_internal
    - Envolver con metadata clara

    Args:
        internal: Si False (default), oculta modelos con is_internal=1 (mock, test)
                  Si True, incluye modelos internos (debug/desarrollo)

    Returns:
        Dict con estructura:
        {
            "status": "ok" | "error",
            "radar": {...},        # Catálogo vivo
            "metadata": {...}      # Metadata y framing
        }

    NOTA: Esta función es REUTILIZABLE para:
    - Renderizar en Streamlit (E1b)
    - Exportar a JSON (E2+)
    - Consumir en API REST (E3+)
    Sin cambios de lógica, solo transporte.

    Bloque E1: Live Catalog Snapshot
    ═════════════════════════════════════════════════════════════════════
    """
    try:
        with get_conn() as conn:
            catalog = ModelCatalog(conn)
            radar_data = catalog.export_public_catalog(include_internal=internal)

        return {
            "status": "ok",
            "radar": radar_data,
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0",
                "catalog_source": "model_catalog BD",
                "framing": "live catalog snapshot – NOT observatorio histórico, NOT benchmarking, NOT health monitor, NOT adaptive scoring",
                "note": "Mode = temporal bridge to router_policy table (future)",
                "include_internal": internal
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "generated_at": now_iso(),
                "radar_version": "1.0"
            }
        }


def radar_view() -> None:
    """
    Vista Streamlit: Radar v1 - Catálogo vivo visible (E1b).

    Estructura minimalista con narrativa de producto:
    - Encabezado + explicación clara
    - Resumen: providers, modelos, modos
    - Listado detallado por provider
    - Metadata transparente
    """
    # ==================== ENCABEZADO ====================
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.write("📡")
    with col2:
        st.title("Radar")

    st.markdown("""
    **Catálogo vivo de PWR** — Qué modelos y modos tiene PWR para ayudarte a decidir cómo abordar tareas.

    Aquí ves la configuración en tiempo real que PWR consulta para elegir
    el modelo más adecuado (eco: rápido/barato, racing: potente/caro).

    ⚠️ Esto NO es observatorio histórico. NO ves cuándo se usó cada modelo.
    Solo el catálogo de disponibilidad.
    """)

    st.divider()

    # ==================== SNAPSHOT ====================
    # Controlar si mostrar internos
    show_internal = st.checkbox(
        "🔧 Mostrar modelos internos (debug)",
        value=False,
        help="Modelos mock/test solo para desarrollo"
    )

    # Construir snapshot (función reutilizable)
    snapshot = build_radar_snapshot(internal=show_internal)

    if snapshot["status"] != "ok":
        st.error(f"⚠️ Error: {snapshot.get('error', 'Unknown error')}")
        return

    radar_data = snapshot["radar"]
    metadata = snapshot["metadata"]

    # ==================== RESUMEN ====================
    st.subheader("📊 Resumen")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔌 Providers", radar_data["summary"]["total_providers"])
    with col2:
        st.metric("🤖 Modelos", radar_data["summary"]["total_models"])
    with col3:
        st.metric("⚙️ Modos", len(radar_data["summary"]["modes_list"]))
    with col4:
        st.metric("📌 Por defecto", radar_data["summary"]["default_mode"])

    st.write("")

    # ==================== PROVIDERS ====================
    st.subheader("🔌 Providers y Modelos")

    for provider_name in sorted(radar_data["providers"].keys()):
        provider = radar_data["providers"][provider_name]

        with st.expander(f"**{provider_name.upper()}** · {len(provider['models'])} modelo(s)", expanded=True):
            for idx, model in enumerate(provider["models"]):
                # Header: nombre + status + internal badge
                col1, col2, col3 = st.columns([0.5, 0.25, 0.25])

                with col1:
                    status_emoji = "🟢" if model["status"] == "active" else "🟡"
                    internal_badge = " **[INTERNAL]**" if model["is_internal"] else ""
                    st.markdown(f"{status_emoji} **{model['name']}{internal_badge}**")

                with col2:
                    st.caption(f"📌 {model['mode'].upper()}")

                with col3:
                    st.caption(f"💰 ${model['estimated_cost_per_run']:.3f}")

                # Capabilities badges
                caps = model.get("capabilities", {})
                badges = []
                if caps.get("vision"):
                    badges.append("👁️ Vision")
                if caps.get("reasoning"):
                    badges.append("🧠 Reasoning")
                if caps.get("code_execution"):
                    badges.append("💻 Code")

                if badges:
                    st.caption("Capacidades: " + " · ".join(badges))
                else:
                    st.caption("Capacidades: —")

                # Context window
                st.caption(f"Context window: {model['context_window']:,} tokens")

                # Separator
                if idx < len(provider["models"]) - 1:
                    st.divider()

    st.write("")

    # ==================== MODES ====================
    st.subheader("⚙️ Modos de Ejecución")

    for mode_name in radar_data["summary"]["modes_list"]:
        mode = radar_data["modes"][mode_name]

        with st.expander(f"**{mode['label']}** ({mode_name})", expanded=False):
            st.write(mode['description'])
            st.caption(f"Modelos: {', '.join(mode['models'])}")

    st.write("")

    # ==================== METADATA FOOTER ====================
    st.divider()

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.caption(f"🕐 Generado: {metadata['generated_at']}")
        st.caption(f"📌 Versión: {metadata['radar_version']} · Fuente: {metadata['catalog_source']}")

    with col2:
        if show_internal:
            st.warning("⚠️ Modelos internos incluidos", icon="🔧")

    st.markdown(f"*{metadata['framing']}*")
    st.markdown(f"*Nota: {metadata['note']}*")


def onboarding_view():
    """
    ESTADO A: Onboarding puro (usuario nuevo, sin actividad previa)
    - INPUT es protagonista visual (primer elemento)
    - Microfrase mínima de contexto (no explicación larga)
    - Ejemplos como sugerencias de tarea
    - Preview condicional (solo si input tiene suficiente sentido)
    - Flujo automático: escribir → ver propuesta → ejecutar → resultado
    """
    # Inicializar ExecutionService para decisiones
    with get_conn() as conn:
        execution_service = ExecutionService(conn)

    # ==================== INPUT PROTAGONISTA ====================
    st.markdown("**¿Cuál es tu tarea?**")

    capture_title = st.text_area(
        "",
        placeholder="Resume un documento • Escribe un email • Analiza un gráfico • Propón un plan",
        key="onboard_capture_input",
        height=120,
        label_visibility="collapsed"
    )

    # Microfrase mínima (no protagonista, contexto ligero)
    st.caption("PWR elige el mejor modelo para tu tarea")

    # ==================== EJEMPLOS COMO SUGERENCIAS ====================
    if not capture_title.strip():
        st.caption("💡 Sugerencias: resume este documento, escribe un email, analiza un gráfico")

    st.write("")  # Espaciado pequeño

    # ==================== PREVIEW CONDICIONAL (solo si input tiene sentido) ====================
    # Preview aparece si input tiene al menos ~20 caracteres (suficiente para ser tarea clara)
    if capture_title.strip() and len(capture_title.strip()) >= 15:
        task_input = build_task_input(
            task_id=0,
            title=capture_title.strip(),
            description="",
            task_type="Pensar",
            context="",
            project={},
        )
        try:
            decision = execution_service.decision_engine.decide(task_input)
            display_decision_preview(decision, capture_title)

            st.write("")  # Espaciado pequeño

            # ==================== BOTÓN (solo si preview mostrado) ====================
            if st.button("✨ Empezar", use_container_width=True,
                         key="onboard_capture_btn", type="primary"):
                # Crear proyecto default
                projects = get_projects()
                if not projects:
                    default_project_id = create_project(
                        name="Mi primer proyecto",
                        description="Proyecto de prueba",
                        objective="Explorar PWR",
                        base_context="",
                        base_instructions="",
                        tags="",
                        files=None
                    )
                else:
                    default_project_id = projects[0]["id"]

                # Crear tarea
                task_id = create_task(
                    project_id=default_project_id,
                    title=capture_title.strip(),
                    description="",
                    task_type="Pensar",
                    context="",
                    uploaded_files=None
                )

                # Ejecutar
                task = get_task(task_id)
                execution_project = get_project(default_project_id)
                task_input = build_task_input_from_rows(task, execution_project)

                progress_placeholder = st.empty()
                status_messages = [
                    "Analizando tu tarea...",
                    "Seleccionando el mejor modo...",
                    "Ejecutando..."
                ]

                for idx, msg in enumerate(status_messages):
                    progress_placeholder.info(f"⏳ {msg}")
                    import time
                    time.sleep(0.3)

                try:
                    execution_result = execution_service.execute(task_input)
                    progress_placeholder.empty()

                    execution_status = resolve_runtime_execution_state(
                        execution_result.status,
                        execution_result.error.code if execution_result.error else "",
                    )

                    if execution_status == "executed":
                        output = execution_result.output_text
                        extract = output[:700]
                        router_summary = (
                            f"Ejecución completada\n"
                            f"Modo: {execution_result.routing.mode}\n"
                            f"Modelo: {execution_result.metrics.model_used}\n"
                            f"Motivo:\n- {execution_result.routing.reasoning_path}"
                        )
                    elif execution_status == "preview":
                        demo_proposal = generate_demo_proposal(execution_result.routing, task_input)
                        output = f"""[PROPUESTA PREVIA - Modo Demo]

🧠 Qué he entendido:
{demo_proposal['understood']}

🎯 Cómo lo resolvería:
{demo_proposal['strategy']}

Prioridad: {demo_proposal['priority']}
Salida esperada: {demo_proposal['expected_output']}

Contenido de ejecucion:
{demo_proposal['execution_prompt']}

---
Nota: Esta es una propuesta previa basada en el análisis del Router.
Para obtener el resultado real, conecta un motor en Configuración.
"""
                        extract = demo_proposal["understood"]
                        router_summary = (
                            f"Propuesta previa (demo)\n"
                            f"Modo: {execution_result.routing.mode}\n"
                            f"Modelo: {execution_result.routing.model}\n"
                            f"Motivo:\n- {execution_result.routing.reasoning_path}\n\n"
                            f"Para resultado real: Conecta {execution_result.routing.provider}"
                        )
                    else:
                        output = "[Resultado no disponible]"
                        extract = ""
                        router_summary = f"Intento fallido\nError: {execution_result.error.message if execution_result.error else 'desconocido'}"

                    router_metrics = {
                        "mode": execution_result.routing.mode,
                        "model": execution_result.metrics.model_used,
                        "provider": execution_result.metrics.provider_used,
                        "complexity_score": execution_result.routing.complexity_score,
                        "status": execution_status,
                        "reasoning_path": execution_result.routing.reasoning_path,
                        "execution_prompt": build_execution_prompt(task_input),
                        "error_code": execution_result.error.code if execution_result.error else "",
                        "error_message": execution_result.error.message if execution_result.error else "",
                    }

                    save_execution_result(
                        task_id=task_id,
                        model_used=execution_result.metrics.model_used,
                        router_summary=router_summary,
                        llm_output=output,
                        useful_extract=extract,
                        execution_status=execution_status,
                        router_metrics=router_metrics,
                    )

                    st.session_state["onboard_result_ready"] = True
                    st.session_state["onboard_result"] = {
                        "task_id": task_id,
                        "project_id": default_project_id,
                        "task": task,
                        "result": execution_result,
                    }
                    open_task_workspace(default_project_id, task_id)

                    st.rerun()

                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"Error en ejecución: {str(e)}")

        except Exception as e:
            st.caption(f"⚠️ No se pudo analizar: {str(e)[:50]}...")

    # ==================== RESULTADO (solo si completado) ====================
    if st.session_state.get("onboard_result_ready"):
        st.write("")  # Espaciado pequeño
        onboard_data = st.session_state.get("onboard_result", {})
        if onboard_data:
            result = onboard_data.get("result")
            task = onboard_data.get("task")
            project_id = onboard_data.get("project_id")
            project = get_project(project_id) if project_id else None
            project_name = project["name"] if project else "Mi primer proyecto"
            # task es sqlite3.Row, usar indexación directa en lugar de .get()
            task_name = task["title"] if task else ""
            display_onboarding_result(result, task, is_first_execution=True, project_name=project_name, task_name=task_name)


def new_task_view():
    """
    ESTADO B: Nueva tarea — flujo lineal dedicado
    - Flujo lineal explícito: 1. ¿Qué necesitas? → 2. Propuesta → 3. Detalles → 4. Ejecuta
    - Botón "Volver" discreto
    - Sin "Retoma tu trabajo" ni "Tus proyectos"
    """
    # Inicializar ExecutionService
    with get_conn() as conn:
        execution_service = ExecutionService(conn)

    projects = get_projects()
    default_project = projects[0] if projects else None

    # Header: Título + Volver (discreto)
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.markdown("### ¿Qué necesitas hacer ahora?")
    with col2:
        if st.button("← Volver", key="new_task_back", use_container_width=True):
            st.session_state["view"] = "home"
            st.session_state["home_capture_input"] = ""
            st.session_state["selected_asset_id"] = None
            st.rerun()

    if default_project:
        st.caption(f"En proyecto: **{default_project['name']}**")

    st.write("")  # Espaciado

    # ==================== PASO 1: ¿QUÉ NECESITAS? ====================
    st.markdown("### 1. ¿Qué necesitas?")

    capture_title = st.text_area(
        "",
        placeholder="Ej: resume este documento • escribe un email • analiza un excel • propón un plan",
        key="home_capture_input",
        height=90,
        label_visibility="collapsed"
    )

    st.write("")  # Espaciado

    # ==================== PASO 2: CÓMO LO VAMOS A RESOLVER (automático) ====================
    if capture_title.strip():
        st.markdown("### 2. Cómo lo vamos a resolver")

        task_input = build_task_input(
            task_id=0,
            title=capture_title.strip(),
            description="",
            task_type="Pensar",
            context="",
            project=default_project or {},
        )
        try:
            decision = execution_service.decision_engine.decide(task_input)
            display_decision_preview(decision, capture_title)
        except Exception as e:
            st.warning(f"No se pudo determinar la estrategia: {str(e)}")

        st.write("")  # Espaciado

        # ==================== PASO 3: DETALLES (OPCIONAL) ====================
        st.markdown("### 3. Detalles (opcional)")

        context = ""
        with st.expander("Añadir contexto"):
            context = st.text_area(
                "",
                placeholder="Información relevante para ejecutar la tarea...",
                height=60,
                key="home_task_context",
                label_visibility="collapsed"
            )

        st.write("")  # Espaciado

        # ==================== PASO 4: EJECUTA ====================
        st.markdown("### 4. Ejecuta")

        if st.button("✨ Generar propuesta", use_container_width=True, key="home_capture_btn",
                     disabled=not default_project, type="primary"):
            if default_project and capture_title.strip():
                tid = create_task(default_project["id"], capture_title, "", TIPOS_TAREA[0], context or "", None)
                open_task_workspace(default_project["id"], tid)
                st.rerun()


def home_view():
    """
    ESTADO C: Home de trabajo — navegación limpia
    - Dos opciones claras: retomar trabajo O crear algo nuevo
    - Si no hay actividad: llama onboarding_view()
    - Si hay actividad: muestra tareas recientes y proyectos
    """
    # Detectar si hay actividad
    recent_tasks = get_recent_executed_tasks(limit=1)
    projects = get_projects()
    has_activity = len(recent_tasks) > 0 or len(projects) > 0

    if not has_activity:
        # ESTADO A: Onboarding puro
        onboarding_view()
        return

    # ESTADO C: Navegación de trabajo
    st.markdown("### 🏠 Mis tareas")

    st.write("")  # Espaciado

    # ==================== SECCIÓN: HOY (Historial del día) ====================
    st.markdown("#### Hoy")

    today_tasks = get_recent_home_tasks(limit=6, today_only=True)

    if not today_tasks:
        st.caption("📋 Sin actividad reciente hoy")
    else:
        for task in today_tasks:
            time_ago = format_time_ago(task.get("updated_at", ""))
            state = normalize_execution_state(task.get("execution_status")) or "pending"
            state_label = task_state_caption(state)
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"{home_task_icon(state)} **{task['title'][:45]}**")
                project_name = task.get('project_name') or "Sin proyecto"
                st.caption(f"{project_name} · {state_label} · {time_ago}")
            with col2:
                if st.button("Abrir", key=f"home_today_{task['id']}", help="Abrir", use_container_width=True):
                    open_task_workspace(task["project_id"], task["id"])
                    st.rerun()

    st.divider()

    # ==================== OPCIÓN 1: RETOMAR TRABAJO ====================
    st.markdown("#### Para retomar")

    recent_tasks = get_recent_home_tasks(
        limit=6,
        states=HOME_RETAKE_STATES,
        prioritize_reentry=False,
    )

    if not recent_tasks:
        st.caption("📋 Sin tareas abiertas o con fallo para retomar.")
    else:
        cols_per_row = 3
        for i in range(0, len(recent_tasks), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, task in enumerate(recent_tasks[i:i+cols_per_row]):
                with cols[j]:
                    time_ago = format_time_ago(task.get("updated_at", ""))
                    state = normalize_execution_state(task.get("execution_status")) or "pending"
                    state_label = task_state_caption(state)
                    project_name = task.get("project_name") or "Sin proyecto"
                    st.markdown(f"**{home_task_icon(state)} {task['title'][:40]}**")
                    st.caption(f"{project_name} · {state_label} · {time_ago}")
                    if st.button(home_task_action_label(state), key=f"home_continue_{task['id']}", use_container_width=True):
                        open_task_workspace(task["project_id"], task["id"])
                        st.rerun()

    st.divider()

    # ==================== OPCIÓN 2: CREAR ALGO NUEVO ====================
    st.markdown("#### Mis proyectos")

    projects_with_activity = get_projects_with_activity()

    if not projects_with_activity:
        st.caption("📁 Sin proyectos. Crea uno para comenzar.")
    else:
        cols_per_row = 2
        for i in range(0, len(projects_with_activity), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, project in enumerate(projects_with_activity[i:i+cols_per_row]):
                with cols[j]:
                    st.markdown(f"**📁 {project['name'][:30]}**")
                    st.caption(f"{project['active_task_count']} tareas")
                    if st.button("Abrir", key=f"home_open_project_{project['id']}", use_container_width=True):
                        open_project_workspace(project["id"])
                        st.rerun()

    st.write("")

    st.divider()

    # ==================== CTAs: DOS OPCIONES CLARAS ====================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Nueva tarea", use_container_width=True, key="home_new_task_btn", type="primary"):
            st.session_state["view"] = "new_task"
            st.session_state["selected_asset_id"] = None
            st.rerun()

    with col2:
        if st.button("➕ Crear proyecto", use_container_width=True, key="home_create_new"):
            st.session_state["show_create_project"] = True
            st.rerun()

    st.write("")

    # ==================== MODAL: CREAR PROYECTO (discreto) ====================
    if st.session_state.get("show_create_project"):
        st.divider()
        st.subheader("Crear proyecto")

        with st.form("create_project_form"):
            name = st.text_input("Nombre", placeholder="Mi proyecto")
            description = st.text_area("Descripción", height=60, placeholder="Breve resumen...")
            objective = st.text_area("Objetivo", height=60, placeholder="¿Qué quiero lograr?")
            base_context = st.text_area("Contexto", height=80, placeholder="Referencias útiles...")
            base_instructions = st.text_area("Reglas", height=80, placeholder="Criterios estables...")
            tags = st.text_input("Etiquetas", placeholder="producto, ia, trabajo")
            files = st.file_uploader("Documentos", accept_multiple_files=True)

            submitted = st.form_submit_button("Crear", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    pid = create_project(name, description, objective, base_context, base_instructions, tags, files)
                    open_project_workspace(pid)
                    st.session_state["show_create_project"] = False
                    st.rerun()


def project_view():
    """
    FASE 1-4 REDESIGN: Master-detail layout con sidebar navigation
    - Sidebar (25%): Proyecto resumido + Captura compacta + Tareas
    - Main (75%): Router decision + Resultado + Expandibles
    """
    pid = st.session_state.get("active_project_id")
    if not pid:
        selected_tid = st.session_state.get("selected_task_id")
        if selected_tid:
            selected_task = get_task(selected_tid)
            if selected_task:
                open_task_workspace(selected_task["project_id"], selected_task["id"])
                st.rerun()
        st.info("Selecciona un proyecto.")
        return

    project = get_project(pid)
    if not project:
        st.warning("No se pudo cargar el proyecto.")
        return

    # Inicializar ExecutionService con BD viva via ModelCatalog
    with get_conn() as conn:
        execution_service = ExecutionService(conn)

    all_projects = get_projects()
    tags = ", ".join(safe_json_loads(project["tags_json"], []))
    docs = get_project_documents(pid)
    tasks = get_project_tasks(pid)
    assets = get_project_assets(pid)

    # HEADER COMPACTO
    h1, h2 = st.columns([5.5, 1])
    with h1:
        st.markdown(f"<div style='font-size:11px; color:#475569; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:2px;'>Proyecto</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:15px; font-weight:600; color:#0F172A;'>{project['name']}</div>", unsafe_allow_html=True)
    with h2:
        if st.button("Cerrar", use_container_width=True):
            st.session_state["active_project_id"] = None
            st.session_state["selected_task_id"] = None
            st.session_state["selected_asset_id"] = None
            st.session_state["view"] = "home"
            st.rerun()

    st.markdown("---")

    # MAIN LAYOUT: Sidebar + Main (FASE 1)
    sidebar, main = st.columns([0.25, 0.75], gap="large")

    # ==================== SIDEBAR ====================
    with sidebar:
        # Proyecto como hint (automático, no decisión)
        st.caption(f"Trabajando en: **{project['name']}**")
        asset_reuse_payload = st.session_state.pop(f"asset_reuse_payload_{pid}", None)
        if asset_reuse_payload:
            st.session_state[f"title_{pid}"] = asset_reuse_payload.get("title", "")
            st.session_state[f"ctx_task_{pid}"] = asset_reuse_payload.get("context", "")
            st.session_state[f"asset_prefill_notice_{pid}"] = asset_reuse_payload.get("notice", "")
        prefill_notice = st.session_state.pop(f"asset_prefill_notice_{pid}", "")
        if prefill_notice:
            st.success(prefill_notice)

        st.write("")  # Espaciado

        # MARKDOWN: Titular claro
        st.markdown("## ¿Qué necesitas hacer ahora?")

        # INPUT PROTAGONISTA (text_area, 110px)
        title = st.text_area(
            "",
            placeholder="Ej: resume este documento • escribe un email • analiza un excel • propón un plan estratégico",
            key=f"title_{pid}",
            height=110,
            label_visibility="collapsed"
        )

        st.caption("Voy a elegir la mejor forma de resolverlo por ti")

        st.write("")  # Espaciado

        # ==================== DECISION PREVIA ====================
        if title.strip():
            task_input = build_task_input(
                task_id=0,
                title=title.strip(),
                description="",
                task_type="Pensar",
                context="",
                project=project,
            )
            try:
                decision = execution_service.decision_engine.decide(task_input)
                display_decision_preview(decision, title)
            except Exception as e:
                st.warning(f"No se pudo determinar la estrategia: {str(e)}")

        st.write("")  # Espaciado

        # CONTEXTO PROGRESIVO: Opcional, cerrado por defecto
        context = ""
        with st.expander("Añadir contexto (opcional)", expanded=False):
            context = st.text_area(
                "",
                height=60,
                placeholder="Información relevante para ejecutar la tarea...",
                key=f"ctx_task_{pid}",
                label_visibility="collapsed"
            )

        st.write("")  # Espaciado

        # BOTÓN ÚNICO
        if st.button("Generar propuesta", use_container_width=True, key=f"create_task_{pid}", disabled=not title.strip()):
            if title.strip():
                tid = create_task(pid, title, "", TIPOS_TAREA[0], context or "", None)
                open_task_workspace(pid, tid)
                st.rerun()

        st.write("")  # Espaciado

        # LISTA DE TAREAS — Separadas en Ejecutadas vs Pendientes (H: Persistencia Visible)
        st.markdown(f"### Tareas ({len(tasks)})")

        search = st.text_input("Buscar", placeholder="Título o descripción...", key=f"search_{pid}", label_visibility="collapsed")
        filtered = get_project_tasks(pid, search=search)

        if not filtered:
            st.caption("Sin tareas en este proyecto")
        else:
            task_groups = [
                ("#### Ejecutadas", [t for t in filtered if task_execution_state(t) == "executed"]),
                ("#### Preview", [t for t in filtered if task_execution_state(t) == "preview"]),
                ("#### Fallidas", [t for t in filtered if task_execution_state(t) == "failed"]),
                ("#### Pendientes", [t for t in filtered if task_execution_state(t) in {"pending", "draft"}]),
            ]

            for heading, group in task_groups:
                if not group:
                    continue
                st.markdown(heading)
                for t in group:
                    task_type_display = t["task_type"] or "Tarea"
                    state = task_execution_state(t)
                    col_title, col_btn = st.columns([0.75, 0.25])

                    with col_title:
                        st.markdown(f"**{t['title']}**")
                        st.caption(f"{task_type_display}")
                        st.caption(task_state_caption(state))

                    with col_btn:
                        if st.button("Abrir", key=f"open_task_{t['id']}", use_container_width=False):
                            open_task_workspace(pid, t["id"])
                            st.rerun()

                    st.divider()

    # ==================== MAIN ====================
    with main:
        selected_asset_id = st.session_state.get("selected_asset_id")
        selected_asset = get_asset(selected_asset_id) if selected_asset_id else None
        if selected_asset_id and (not selected_asset or int(row_value(selected_asset, "project_id", 0) or 0) != pid):
            st.session_state["selected_asset_id"] = None
            selected_asset = None

        if selected_asset:
            render_asset_detail(pid, selected_asset)
            return

        tid = st.session_state.get("selected_task_id")
        if not tid:
            st.info("Selecciona o crea una tarea para trabajar.")
            return

        task = get_task(tid)
        if not task or task["project_id"] != pid:
            st.info("Selecciona una tarea válida del proyecto.")
            return

        current_state = task_execution_state(task)
        trace_key = f"trace_{tid}"
        followthrough_key = f"followthrough_{tid}"
        task_input = build_task_input_from_rows(task, project)
        current_decision = execution_service.decision_engine.decide(task_input)
        execution_prompt = build_execution_prompt(task_input)
        latest_run = get_latest_execution_run(tid)
        visible_output = task["llm_output"] or (latest_run["output_text"] if latest_run else "")

        # PREPARAR VARIABLES PARA ROUTER (usado al final, no aquí)
        trace = normalize_trace(
            st.session_state.get(trace_key)
            or trace_from_history_run(latest_run)
            or safe_json_loads(task["router_metrics_json"], {})
        )
        is_first_execution = trace.get("is_first_execution", False) if trace else False
        reentry_states = REENTRY_CONTEXT_STATES
        followthrough = st.session_state.pop(followthrough_key, None)
        if current_state in reentry_states:
            reentry_context = build_reentry_context(task, current_state, latest_run, trace, visible_output)
            st.markdown("#### Contexto para retomar")
            header_parts = [f"Estado actual: {task_state_caption(current_state)}"]
            if reentry_context["reference_label"]:
                header_parts.append(f"Ultima referencia: {reentry_context['reference_label']}")
            st.caption(" · ".join(header_parts))
            if reentry_context["motor_line"]:
                st.caption(reentry_context["motor_line"])
            st.caption(f"Ultimo paso detectado: {reentry_context['last_step']}")
            if reentry_context["snippet_text"]:
                if current_state == "failed":
                    st.warning(f"{reentry_context['snippet_label']}: {reentry_context['snippet_text']}")
                else:
                    st.info(f"{reentry_context['snippet_label']}: {reentry_context['snippet_text']}")

        if followthrough:
            feedback_level, feedback_message = build_followthrough_feedback(
                followthrough.get("from_state", ""),
                followthrough.get("to_state", current_state),
            )
            if feedback_level == "success":
                st.success(feedback_message)
            elif feedback_level == "warning":
                st.warning(feedback_message)
            else:
                st.info(feedback_message)

        display_execution_view(current_decision, task_input, execution_prompt, trace)
        if current_state not in reentry_states:
            st.caption(f"Estado de tarea: {task_state_caption(current_state)}")
        provider_block = execution_service.provider_errors.get(current_decision.provider)
        if provider_block:
            st.warning(f"Proveedor bloqueado: {provider_block}")
        if latest_run:
            st.caption(
                f"Ultimo run persistido: {task_state_caption(latest_run['execution_status'])} | "
                f"{latest_run['provider'] or 'provider?'} / {latest_run['model'] or 'modelo?'} | "
                f"{latest_run['executed_at']}"
            )
            if latest_run["artifact_md_path"] or latest_run["artifact_json_path"]:
                with st.expander("Rastro portable (.md/.json)", expanded=False):
                    if latest_run["artifact_md_path"]:
                        st.caption("Markdown")
                        st.code(latest_run["artifact_md_path"], language="text")
                    if latest_run["artifact_json_path"]:
                        st.caption("JSON")
                        st.code(latest_run["artifact_json_path"], language="text")

        # Botón ejecutar - primario
        col_exec, col_other = st.columns([2, 3])
        with col_exec:
            execute_btn = st.button(
                task_primary_action_label(current_state),
                use_container_width=True,
                key=f"execute_router_{tid}",
                type="primary",
            )
        with col_other:
            st.caption(f"Siguiente accion: {task_primary_action_hint(current_state)}")

        if execute_btn:
            # Detectar si es primera ejecución
            is_first_execution = current_state not in {"executed", "preview"}

            # Mostrar progreso visual (no spinner genérico)
            progress_placeholder = st.empty()
            status_messages = task_execution_progress_messages(current_state)

            for idx, msg in enumerate(status_messages):
                progress_placeholder.info(f"⏳ {msg}")
                import time
                time.sleep(0.3)  # Timing visual para que se vea el progreso

            result = execution_service.execute(task_input)

            # Limpiar mensaje de progreso
            progress_placeholder.empty()

            # Construir router_summary con info completa (éxito o error)
            execution_status = resolve_runtime_execution_state(
                result.status,
                result.error.code if result.error else "",
            )

            if result.status == "error":
                # Detectar si es fallback (provider no disponible)
                is_fallback = execution_status == "preview"

                if is_fallback:
                    # ==================== MODO DEMO: Propuesta Previa ====================
                    # Generar propuesta previa útil basada en análisis del Router
                    demo_proposal = generate_demo_proposal(result.routing, task_input)
                    display_demo_mode_panel(demo_proposal)

                    # Guardar propuesta previa
                    output = f"""[PROPUESTA PREVIA - Modo Demo]

🧠 Qué he entendido:
{demo_proposal['understood']}

🎯 Cómo lo resolvería:
{demo_proposal['strategy']}

Prioridad: {demo_proposal['priority']}
Salida esperada: {demo_proposal['expected_output']}

Contenido de ejecucion:
{demo_proposal['execution_prompt']}

---
Nota: Esta es una propuesta previa basada en el análisis del Router.
Para obtener el resultado real, conecta un motor en Configuración.
"""
                    extract = demo_proposal["understood"]

                    router_summary = (
                        f"Propuesta previa (demo)\n"
                        f"Modo: {result.routing.mode}\n"
                        f"Modelo: {result.routing.model}\n"
                        f"Motivo:\n- {result.routing.reasoning_path}\n\n"
                        f"Para resultado real: Conecta {result.routing.provider}"
                    )

                else:
                    # ==================== ERROR REAL (no fallback) ====================
                    # Mostrar warning estructurado (amarillo, no rojo)
                    st.warning(f"""
**⚠️ No se pudo completar la ejecución**

**Tipo de error:** {result.error.code}
**Detalles:** {result.error.message}

→ Revisa la configuración del proveedor o conecta un motor diferente.
                    """.strip())

                    router_summary = (
                        f"Intento fallido\n"
                        f"Modo: {result.routing.mode}\n"
                        f"Modelo: {result.metrics.model_used}\n"
                        f"Error: {result.error.code}\n"
                        f"Mensaje: {result.error.message}\n\n"
                        f"Motivo:\n- {result.routing.reasoning_path}"
                    )
                    output = ""
                    extract = ""
            else:
                # ==================== EJECUCIÓN EXITOSA ====================
                output = result.output_text
                extract = output[:700]

                router_summary = (
                    f"Ejecución completada\n"
                    f"Modo: {result.routing.mode}\n"
                    f"Modelo: {result.metrics.model_used}\n"
                    f"Proveedor: {result.metrics.provider_used}\n"
                    f"Complejidad: {result.routing.complexity_score:.2f}\n"
                    f"Latencia: {result.metrics.latency_ms} ms\n"
                    f"Coste estimado: ${result.metrics.estimated_cost:.3f}\n\n"
                    f"Motivo:\n- {result.routing.reasoning_path}"
                )

            # Guardar resultado en BD (siempre: executed, preview, o failed)
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
                task_id=task["id"],
                model_used=result.metrics.model_used,
                router_summary=router_summary,
                llm_output=output,
                useful_extract=extract,
                execution_status=execution_status,
                router_metrics=router_metrics,
            )

            # Guardar trazabilidad en session (para mostrar en UI)
            st.session_state[trace_key] = {
                "mode": result.routing.mode,
                "model_used": result.metrics.model_used,
                "provider_used": result.metrics.provider_used,
                "reasoning_path": result.routing.reasoning_path,
                "latency_ms": result.metrics.latency_ms,
                "estimated_cost": result.metrics.estimated_cost,
                "status": execution_status,  # "executed", "preview", o "failed"
                "execution_status": execution_status,  # Explícito: qué tipo de resultado
                "error_code": result.error.code if result.error else None,
                "error_message": result.error.message if result.error else None,
                "execution_prompt": execution_prompt,
                "is_first_execution": is_first_execution,  # Flag para momento WOW
            }
            st.session_state[followthrough_key] = {
                "from_state": current_state,
                "to_state": execution_status,
            }
            st.rerun()

        st.write("")

        # FASE 4: RESULTADO PANEL - PROTAGONIST
        if current_state == "failed":
            st.warning(task["router_summary"] or "Ejecucion fallida. Revisa la configuracion del proveedor.")
        elif current_state in {"pending", "draft"}:
            # Estado vacío: aguardando ejecución
            st.info("📝 Resultado pendiente. Ejecuta el Router arriba para recibir la respuesta.")
        else:
            # Con resultado: estructura simple y clara
            # [1] RESULTADO (PROTAGONISTA)
            output = st.text_area(
                "",
                value=visible_output,
                height=280,
                placeholder="Resultado de la ejecución...",
                key=f"output_{tid}",
                label_visibility="collapsed"
            )

            st.write("")  # Espaciado

            # [2] LÍNEA DE CONTINUIDAD (MICROCOPY)
            st.caption("Puedes editar este resultado o mejorarlo con análisis más profundo.")

            st.write("")  # Espaciado

            # [3] ACCIONES (4 botones máximo, orden exacto)
            col1, col2, col3, col4 = st.columns(4)

            # Definir claves de session_state para todos los flujos
            save_panel_key = f"save_asset_panel_{tid}"
            improve_in_progress_key = f"improve_in_progress_{tid}"
            improved_result_key = f"improved_result_{tid}"
            improved_trace_key = f"improved_trace_{tid}"

            # 1. PRIMARIO: Guardar como activo (abre mini-flujo)
            with col1:
                if st.button("📦 Guardar como activo", use_container_width=True, key=f"save_asset_btn_{tid}"):
                    if not output.strip():
                        st.error("No hay contenido para guardar.")
                    else:
                        st.session_state[save_panel_key] = True
                        st.rerun()

            # 2. SECUNDARIO: Mejorar resultado (con análisis más profundo)
            with col2:
                if st.button("✨ Mejorar con análisis más profundo", use_container_width=True, key=f"improve_{tid}"):
                    st.session_state[improve_in_progress_key] = True
                    st.rerun()

            # FLUJO DE MEJORA: Mostrar spinner y ejecutar
            if st.session_state.get(improve_in_progress_key, False) and not st.session_state.get(improved_result_key):
                st.write("")  # Espaciado

                # Mostrar progreso visual
                progress_placeholder = st.empty()
                status_messages = [
                    "Analizando resultado actual...",
                    "Ejecutando con análisis más profundo...",
                    "Procesando mejoras..."
                ]

                for idx, msg in enumerate(status_messages):
                    progress_placeholder.info(f"⏳ {msg}")
                    import time
                    time.sleep(0.3)

                # Crear TaskInput mejorado con RACING mode forzado
                # El contexto enriquecido incluye el resultado anterior
                enriched_context = f"{task['context'] or ''}\n\n[RESULTADO ANTERIOR]\n{output}"

                improved_task_input = build_task_input_from_rows(
                    task,
                    project,
                    context_override=enriched_context.strip(),
                    preferred_mode="racing",
                )
                improved_execution_prompt = build_execution_prompt(improved_task_input)

                # Ejecutar con RACING mode
                improved_result = execution_service.execute(improved_task_input)

                # Limpiar spinner
                progress_placeholder.empty()

                # Guardar resultado mejorado en session_state
                if improved_result.status == "completed":
                    st.session_state[improved_result_key] = improved_result.output_text
                    st.session_state[improved_trace_key] = {
                        "mode": improved_result.routing.mode,
                        "model_used": improved_result.metrics.model_used,
                        "provider_used": improved_result.metrics.provider_used,
                        "reasoning_path": improved_result.routing.reasoning_path,
                        "latency_ms": improved_result.metrics.latency_ms,
                        "estimated_cost": improved_result.metrics.estimated_cost,
                        "status": improved_result.status,
                        "execution_prompt": improved_execution_prompt,
                    }
                    st.rerun()
                else:
                    st.error(f"Error en mejora: {improved_result.error.message}")
                    st.session_state[improve_in_progress_key] = False
                    st.session_state[improved_result_key] = None
                    st.rerun()

            # 3. SECUNDARIO: Personalizar resultado
            with col3:
                st.button("✏️ Personalizar", use_container_width=True, key=f"edit_result_{tid}", disabled=True, help="El resultado ya es editable arriba. Modifica el texto directamente.")

            # 4. TERCIARIO: Re-ejecutar
            with col4:
                if st.button("🔄 Re-ejecutar", use_container_width=True, key=f"reexec_{tid}"):
                    st.session_state[trace_key] = None
                    st.rerun()

            # MICRO-FLUJO: Panel de guardado inline
            if st.session_state.get(save_panel_key, False):
                st.write("")  # Espaciado

                # Panel de guardado
                with st.container():
                    st.markdown("---")
                    st.markdown("**Guardar como activo reutilizable**")
                    type_options = ["preview", "briefing"] if current_state == "preview" else ["output", "briefing"]
                    default_type = "preview" if current_state == "preview" else "output"
                    asset_type_key = f"asset_type_{tid}"
                    if st.session_state.get(asset_type_key) not in type_options:
                        st.session_state[asset_type_key] = default_type
                    asset_type = st.selectbox(
                        "Tipo de activo",
                        type_options,
                        index=type_options.index(default_type),
                        key=asset_type_key,
                        format_func=asset_type_label,
                    )

                    source_content = execution_prompt if asset_type == "briefing" else output.strip()
                    auto_name_source = execution_prompt if asset_type == "briefing" else output
                    words = auto_name_source.split()[:8]
                    if asset_type == "briefing":
                        auto_name = f"{task['title']} briefing"
                    else:
                        auto_name = " ".join(words) if words else "Activo sin título"
                    st.caption(
                        "Se guardará el briefing de ejecución actual."
                        if asset_type == "briefing"
                        else "Se guardará el contenido visible del resultado o preview."
                    )

                    # Campo 1: Nombre del activo
                    asset_name = st.text_input(
                        "Nombre del activo",
                        value=auto_name,
                        key=f"asset_name_{tid}",
                        placeholder="Título identificable...",
                        help="Las primeras palabras del resultado"
                    )

                    # Campo 2: Proyecto
                    project_options = [p["name"] for p in all_projects] if all_projects else ["Sin proyecto"]
                    selected_project_idx = 0
                    for idx, p in enumerate(all_projects):
                        if p["id"] == pid:
                            selected_project_idx = idx
                            break

                    asset_project = st.selectbox(
                        "Proyecto",
                        project_options,
                        index=selected_project_idx,
                        key=f"asset_project_{tid}",
                        help="Dónde se guardará este activo"
                    )

                    # Campo 3: Descripción (opcional)
                    asset_description = st.text_area(
                        "Descripción (opcional)",
                        value="",
                        height=60,
                        key=f"asset_desc_{tid}",
                        placeholder="Notas sobre cuándo reutilizar esto...",
                        help="Ayuda futura a entender este activo"
                    )

                    # Botones: Guardar y Cancelar
                    btn_col1, btn_col2 = st.columns([0.5, 0.5])

                    with btn_col1:
                        if st.button("✓ Guardar activo", use_container_width=True, key=f"confirm_save_{tid}"):
                            # Guardar el activo
                            selected_proj_id = next((p["id"] for p in all_projects if p["name"] == asset_project), pid)
                            asset_id = create_asset(
                                selected_proj_id,
                                tid,
                                asset_name,
                                asset_description,
                                source_content,
                                asset_type=asset_type,
                                source_execution_id=int(row_value(latest_run, "id", 0) or 0) or None,
                                source_execution_status=current_state,
                            )

                            # Limpiar estado
                            st.session_state[save_panel_key] = False
                            for key_name in (
                                f"asset_type_{tid}",
                                f"asset_name_{tid}",
                                f"asset_project_{tid}",
                                f"asset_desc_{tid}",
                            ):
                                st.session_state.pop(key_name, None)
                            st.session_state["selected_asset_id"] = asset_id if selected_proj_id == pid else None
                            st.success(f"✨ **{asset_name}** guardado en **{asset_project}** como activo reutilizable")
                            st.rerun()

                    with btn_col2:
                        if st.button("✕ Cancelar", use_container_width=True, key=f"cancel_save_{tid}"):
                            st.session_state[save_panel_key] = False
                            for key_name in (
                                f"asset_type_{tid}",
                                f"asset_name_{tid}",
                                f"asset_project_{tid}",
                                f"asset_desc_{tid}",
                            ):
                                st.session_state.pop(key_name, None)
                            st.rerun()

            # BLOQUE DE RESULTADO MEJORADO (después del original)
            if st.session_state.get(improved_result_key):
                st.write("")  # Espaciado
                st.markdown("---")
                st.write("")

                # IMPACTO VISUAL: Mostrar que accedió a poder extra
                st.markdown("### 🚀 Resultado con Análisis Profundo")
                st.caption("El sistema revisó tu trabajo con el modelo más potente. Aquí está lo que descubrió:")

                improved_output = st.session_state.get(improved_result_key, "")

                # Textarea para resultado mejorado (editable)
                improved_output_edited = st.text_area(
                    "",
                    value=improved_output,
                    height=280,
                    placeholder="Resultado mejorado...",
                    key=f"improved_output_{tid}",
                    label_visibility="collapsed"
                )

                st.write("")  # Espaciado

                # Información de la mejora
                improved_trace = st.session_state.get(improved_trace_key, {})
                if improved_trace:
                    st.caption(
                        f"✨ Análisis profundo | {improved_trace['model_used']} | "
                        f"~{improved_trace['latency_ms']}ms | "
                        f"${improved_trace['estimated_cost']:.4f}"
                    )

                st.write("")  # Espaciado

                # Botones de acción para resultado mejorado
                imp_col1, imp_col2, imp_col3 = st.columns([0.5, 0.25, 0.25])

                with imp_col1:
                    if st.button("✓ Usar este resultado", use_container_width=True, key=f"use_improved_{tid}"):
                        # Reemplazar el resultado original con el mejorado
                        improved_metrics = {
                            "mode": improved_trace.get("mode", ""),
                            "model": improved_trace.get("model_used", ""),
                            "provider": improved_trace.get("provider_used", ""),
                            "latency_ms": improved_trace.get("latency_ms", 0),
                            "estimated_cost": improved_trace.get("estimated_cost", 0),
                            "complexity_score": improved_trace.get("complexity_score", 0),
                            "status": "executed",
                            "reasoning_path": improved_trace.get("reasoning_path", ""),
                            "execution_prompt": improved_trace.get("execution_prompt", ""),
                            "executed_at": now_iso(),
                        }
                        save_execution_result(
                            task_id=task["id"],
                            model_used=improved_trace.get("model_used", ""),
                            router_summary=(
                                f"Resultado mejorado con análisis profundo\n"
                                f"Modelo: {improved_trace.get('model_used', '')}\n"
                                f"Modo: {improved_trace.get('mode', '')}\n"
                                f"Proveedor: {improved_trace.get('provider_used', '')}\n"
                                f"Latencia: {improved_trace.get('latency_ms', 0)} ms\n"
                                f"Coste estimado: ${improved_trace.get('estimated_cost', 0):.3f}\n\n"
                                f"Motivo:\n- {improved_trace.get('reasoning_path', '')}"
                            ),
                            llm_output=improved_output_edited.strip(),
                            useful_extract=improved_output_edited.strip()[:700],
                            router_metrics=improved_metrics,
                        )

                        # Actualizar trace
                        st.session_state[trace_key] = {
                            "mode": improved_trace.get("mode"),
                            "model_used": improved_trace.get("model_used"),
                            "provider_used": improved_trace.get("provider_used"),
                            "reasoning_path": improved_trace.get("reasoning_path"),
                            "latency_ms": improved_trace.get("latency_ms"),
                            "estimated_cost": improved_trace.get("estimated_cost"),
                            "status": "completed",
                            "error_code": None,
                            "error_message": None,
                            "execution_prompt": improved_trace.get("execution_prompt", ""),
                            "is_first_execution": False,
                        }

                        # Limpiar estados de mejora
                        st.session_state[improve_in_progress_key] = False
                        st.session_state[improved_result_key] = None
                        st.session_state[improved_trace_key] = None

                        st.success("✨ **Excelente.** Tu resultado ahora es la versión con análisis profundo")
                        st.rerun()

                with imp_col2:
                    if st.button("↔️ Comparar", use_container_width=True, key=f"compare_improved_{tid}"):
                        st.info("Comparación: arriba original, abajo mejorado. Desplázate para ver ambos.")

                with imp_col3:
                    if st.button("✕ Descartar", use_container_width=True, key=f"discard_improved_{tid}"):
                        # Limpiar estado de mejora
                        st.session_state[improve_in_progress_key] = False
                        st.session_state[improved_result_key] = None
                        st.session_state[improved_trace_key] = None
                        st.rerun()

        st.write("")

        # ROUTER DECISION - CONTEXTO EXPLICATIVO
        if trace:
            st.write("")  # Espaciado

            mode_label = "🟢 Modo ECO" if trace["mode"] == "eco" else "🔵 Análisis Profundo"
            mode_desc = "Respuesta rápida y precisa" if trace["mode"] == "eco" else "Análisis detallado y completo"

            # DECISIÓN (contexto explicativo, no protagonista)
            st.markdown(f"**{mode_label}** — _{mode_desc}_")

            # RAZONAMIENTO (por qué eligió este modo)
            if trace.get("reasoning_path"):
                st.caption(f"**Por qué:** {trace['reasoning_path']}")

            # METADATA (discreta, en columnas)
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            with col_meta1:
                st.caption(f"**Modelo**\n{trace['model_used']}")
            with col_meta2:
                st.caption(f"**Tiempo**\n~{trace['latency_ms']}ms")
            with col_meta3:
                st.caption(f"**Coste**\n${trace['estimated_cost']:.4f}")

            st.write("")  # Espaciado

        # EXPANDIBLES - BAJO DEMANDA
        # 1. Ficha del proyecto
        with st.expander("📋 Ficha del proyecto", expanded=False):
            st.markdown("**Objetivo**")
            st.caption(project["objective"] or "Sin objetivo definido")
            st.markdown("**Contexto de referencia**")
            st.caption(project["base_context"] or "Sin contexto base")
            st.markdown("**Reglas estables**")
            st.caption(project["base_instructions"] or "Sin reglas definidas")

        # 2. Contenido de ejecucion
        with st.expander("Contenido de ejecucion", expanded=False):
            st.code(execution_prompt, language="text")

        # 3. Trazabilidad
        if trace:
            with st.expander("🔍 Trazabilidad & Detalles técnicos", expanded=False):
                st.write(f"**Estado:** {trace['status'].upper()}")
                st.write(f"**Modo:** {trace['mode']}")
                st.write(f"**Modelo:** {trace['model_used']}")
                st.write(f"**Proveedor:** {trace['provider_used']}")
                st.write(f"**Latencia:** {trace['latency_ms']} ms")
                st.write(f"**Coste estimado:** ${trace['estimated_cost']:.3f}")
                st.write("**Motivo de la decisión:**")
                st.write(trace["reasoning_path"])
                if trace.get("error_code"):
                    st.warning(f"**Error:** {trace['error_code']}")
                    st.write(trace["error_message"])

        # 4. Activos relacionados
        if assets:
            with st.expander(f"🎯 Activos relacionados ({len(assets)})", expanded=False):
                for a in assets[:10]:
                    st.markdown(f"**{a['title']}** · {asset_type_label(a['asset_type'])}")
                    origin_parts = []
                    if row_value(a, "task_title"):
                        origin_parts.append(row_value(a, "task_title"))
                    if row_value(a, "source_execution_status"):
                        origin_parts.append(task_state_caption(row_value(a, "source_execution_status")))
                    if row_value(a, "created_at"):
                        origin_parts.append(format_time_ago(row_value(a, "created_at")))
                    if origin_parts:
                        st.caption(" · ".join(origin_parts))
                    preview = asset_preview_text(a)
                    if preview:
                        st.caption(preview)
                    asset_col1, asset_col2 = st.columns([1.2, 1.8])
                    with asset_col1:
                        if st.button("Abrir activo", key=f"open_asset_{a['id']}", use_container_width=True):
                            open_asset_workspace(pid, a["id"])
                            st.rerun()
                    with asset_col2:
                        if st.button("Usar como base", key=f"use_asset_{a['id']}", use_container_width=True):
                            reuse_asset_as_task_base(pid, a)
                            st.rerun()
                    st.divider()
        else:
            with st.expander("🎯 Activos relacionados (0)", expanded=False):
                st.info("Todavía no hay activos en este proyecto.")


# ==================== BLOQUE E1b: RADAR VIEW ====================
def radar_view():
    """
    Renderiza catálogo vivo como página Streamlit (E1b: Vista).

    Consume snapshot de build_radar_snapshot() y presenta:
    - Narrativa clara: "Live catalog snapshot"
    - Resumen: providers, modelos, modos disponibles
    - Detalle por provider
    - Metadata honesta

    NO es observatorio histórico, NO promete features que no tiene.
    """
    # ==================== Header + Narrativa ====================
    st.header("📡 Radar")
    st.markdown("""
    **Live Catalog Snapshot**

    Qué ves aquí es el estado actual del catálogo de PWR.
    """)

    # Control toggle para debug
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        show_internal = st.checkbox(
            "🔧 Debug",
            value=False,
            help="Mostrar modelos internos (mock/test)"
        )

    # Construir snapshot
    radar = build_radar_snapshot(internal=show_internal)

    if radar["status"] != "ok":
        st.error(f"⚠️ Error: {radar.get('error', 'Unknown')}")
        return

    radar_data = radar["radar"]
    metadata = radar["metadata"]

    # ==================== Resumen (Arriba) ====================
    st.subheader("📊 Estado del Catálogo")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Providers", radar_data["summary"]["total_providers"])
    with col2:
        st.metric("Modelos", radar_data["summary"]["total_models"])
    with col3:
        st.metric("Modos", len(radar_data["summary"]["modes_list"]))
    with col4:
        st.metric("Default", radar_data["summary"]["default_mode"])

    st.divider()

    # ==================== Providers: Listado Detallado ====================
    st.subheader("🔌 Providers")

    for provider_name in sorted(radar_data["providers"].keys()):
        provider = radar_data["providers"][provider_name]

        st.markdown(f"#### {provider_name.upper()}")

        for model in provider["models"]:
            # Layout: nombre + status | mode + costo | capabilities
            col1, col2, col3 = st.columns([0.4, 0.3, 0.3])

            with col1:
                # Status badge + nombre
                status_emoji = "🟢" if model["status"] == "active" else "🟡"
                internal_badge = " [INTERNAL]" if model["is_internal"] else ""
                st.write(f"{status_emoji} **{model['name']}{internal_badge}**")

            with col2:
                # Mode + cost
                st.caption(f"📌 {model['mode']} | 💰 ${model['estimated_cost_per_run']:.3f}")

            with col3:
                # Capabilities badges
                caps = model.get("capabilities", {})
                badges = []
                if caps.get("vision"):
                    badges.append("👁️")
                if caps.get("reasoning"):
                    badges.append("🧠")
                if caps.get("code_execution"):
                    badges.append("💻")
                st.caption(" ".join(badges) if badges else "—")

            # Expandable full details
            with st.expander(f"Detalles de {model['name']}", expanded=False):
                col_detail1, col_detail2 = st.columns(2)

                with col_detail1:
                    st.write(f"**Provider**: {model['provider']}")
                    st.write(f"**Status**: {model['status']}")
                    st.write(f"**Mode**: {model['mode']}")

                with col_detail2:
                    st.write(f"**Context Window**: {model['context_window']:,} tokens")
                    st.write(f"**Estimated Cost**: ${model['estimated_cost_per_run']:.4f}")
                    st.write(f"**Capabilities**: {json.dumps(model.get('capabilities', {}), indent=2)}")

        st.divider()

    # ==================== Modes: Descripción ====================
    st.subheader("⚙️ Modos")

    for mode_name in radar_data["summary"]["modes_list"]:
        mode = radar_data["modes"][mode_name]

        with st.expander(f"**{mode['label']}** ({mode_name})", expanded=False):
            st.write(mode["description"])
            st.caption(f"Modelos: {', '.join(mode['models'])}")

    st.divider()

    # ==================== Metadata Footer ====================
    st.subheader("ℹ️ Acerca de este Radar")

    col1, col2 = st.columns([0.7, 0.3])

    with col1:
        st.caption(f"📅 Generado: {metadata['generated_at']}")
        st.caption(f"📦 Versión: {metadata['radar_version']} · Fuente: {metadata['catalog_source']}")

    with col2:
        if show_internal:
            st.warning("⚠️ Modelos internos mostrados")

    # Clarificación sobre lo que ES y lo que NO ES
    st.markdown(f"""
    **Qué es Radar v1:**
    - ✅ Snapshot del catálogo vivo (qué tenemos hoy)
    - ✅ Configuración de providers y modelos
    - ✅ Capacidades disponibles

    **Qué NO es Radar v1 (aún):**
    - ❌ Observatorio histórico
    - ❌ Benchmarking
    - ❌ Health monitor
    - ❌ Scoring adaptativo

    *{metadata['note']}*
    """)



# ==================== APP ENTRY POINT ====================
if "view" not in st.session_state:
    st.session_state["view"] = "home"
if "selected_task_id" not in st.session_state:
    st.session_state["selected_task_id"] = None
if "active_project_id" not in st.session_state:
    st.session_state["active_project_id"] = None

st.set_page_config(page_title=APP_TITLE, layout="wide")
init_db()
inject_css()
render_pwr_header()

current_view = st.session_state.get("view", "home")
if current_view == "home":
    home_view()
elif current_view == "new_task":
    new_task_view()
elif current_view == "project_view":
    project_view()
elif current_view == "radar":
    radar_view()
elif current_view == "onboarding":
    onboarding_view()
else:
    home_view()


def main():
    import sys
    print("[MAIN] Starting main()", file=sys.stderr, flush=True)

    print("[MAIN] Calling st.set_page_config()...", file=sys.stderr, flush=True)
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    print("[MAIN] st.set_page_config() OK", file=sys.stderr, flush=True)

    # ===== Railway Persistence Warning =====
    import os
    print("[MAIN] Checking PORT env var...", file=sys.stderr, flush=True)
    # Detect Railway environment by presence of PORT env variable (Railway-specific)
    if os.environ.get("PORT"):  # Railway sets PORT env var
        print(f"[MAIN] PORT={os.environ.get('PORT')}", file=sys.stderr, flush=True)
        st.warning(
            "⚠️ **Entorno de prueba en Railway.** La persistencia local con SQLite puede ser efímera. "
            "Válido para test corto de UX, no para uso productivo.",
            icon="🔧"
        )

    # ===== Initialize Database (with defensive error handling) =====
    print("[MAIN] About to call init_db()...", file=sys.stderr, flush=True)
    try:
        init_db()
        print("[MAIN] init_db() OK", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[MAIN] init_db() FAILED: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        st.error(f"❌ Startup error: Database initialization failed: {str(e)}")
        st.stop()

    print("[MAIN] About to call inject_css()...", file=sys.stderr, flush=True)
    inject_css()
    print("[MAIN] inject_css() OK", file=sys.stderr, flush=True)

    print("[MAIN] About to build sidebar...", file=sys.stderr, flush=True)
    with st.sidebar:
        # ==================== TÍTULO REDUCIDO ====================
        st.markdown("### PWR")

        # ==================== NAVEGACIÓN PRINCIPAL VERTICAL (minimalista) ====================
        current_view = st.session_state.get("view", "home")

        if st.button("🏠 Home", use_container_width=True, key="nav_home",
                     type="primary" if current_view == "home" else "secondary"):
            st.session_state["view"] = "home"
            st.session_state["active_project_id"] = None
            st.rerun()

        if st.button("📡 Radar", use_container_width=True, key="nav_radar",
                     type="primary" if current_view == "radar" else "secondary"):
            st.session_state["view"] = "radar"
            st.rerun()

        st.divider()

        # ==================== CONTEXTO SOLO (mirrors estado, no duplica) ====================
        active_project_id = st.session_state.get("active_project_id")
        active_task_id = st.session_state.get("selected_task_id")

        if active_project_id:
            with get_conn() as conn:
                project = conn.execute("SELECT name FROM projects WHERE id = ?", (active_project_id,)).fetchone()
                if project:
                    st.caption("📁 Proyecto activo")
                    st.markdown(f"**{project['name'][:25]}**")
                    st.divider()

        if active_task_id:
            with get_conn() as conn:
                task = conn.execute("SELECT title FROM tasks WHERE id = ?", (active_task_id,)).fetchone()
                if task:
                    st.caption("📌 Tarea actual")
                    st.markdown(f"**{task['title'][:25]}**")
                    st.divider()

    # ==================== ROUTING ====================
    print("[MAIN] About to do routing...", file=sys.stderr, flush=True)
    current_view = st.session_state.get("view", "home")
    print(f"[MAIN] current_view = {current_view}", file=sys.stderr, flush=True)

    if current_view == "radar":
        radar_view()
    elif current_view == "new_task":
        new_task_view()
    elif st.session_state.get("active_project_id"):
        render_header()
        st.write("")
        project_view()
    else:
        home_view()


if __name__ == "__main__":
    # Streamlit already renders the app through the top-level routing above.
    pass
