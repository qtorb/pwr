from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from state_contract import normalize_execution_state


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "pwr_data"
UPLOADS_DIR = DATA_DIR / "uploads"
PORTABLE_RUNS_DIR = DATA_DIR / "portable_runs"
REUSABLE_ASSETS_DIR = DATA_DIR / "reusable_assets"
DB_PATH = DATA_DIR / "pwr.db"


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


def safe_json_loads(value: str, default: Any):
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


def compact_text(value: str, max_len: int = 220) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        return ""
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def format_time_ago(iso_string: str) -> str:
    if not iso_string:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_string)
        now = datetime.now()
        diff = now - dt

        if diff.days > 7:
            return "Hace 1+ semanas"
        if diff.days > 0:
            return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
        if diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        if diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Hace {minutes} minuto{'s' if minutes > 1 else ''}"
        return "Hace unos segundos"
    except Exception:
        return iso_string


def slugify_for_path(value: str, fallback: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", str(value or "").lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or fallback


def project_upload_dir(project_id: int) -> Path:
    path = UPLOADS_DIR / f"project_{project_id:04d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    try:
        ensure_dirs()
    except Exception as exc:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        if str(exc).strip():
            print(f"[WARN] ensure_dirs raised: {exc}, but mkdir fallback succeeded")

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
        ensure_column(conn, "tasks", "router_metrics_json", "TEXT DEFAULT '{}'")
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model_name TEXT UNIQUE NOT NULL,
                pricing_input_per_mtok REAL DEFAULT 0.0,
                pricing_output_per_mtok REAL DEFAULT 0.0,
                context_window INTEGER,
                capabilities_json TEXT DEFAULT '{}',
                estimated_cost_per_run REAL NOT NULL,
                status TEXT DEFAULT 'active',
                mode TEXT,
                is_internal INTEGER DEFAULT 0,
                deprecated_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )

        catalog_count = conn.execute("SELECT COUNT(*) FROM model_catalog").fetchone()[0]
        if catalog_count == 0:
            conn.execute(
                """
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "gemini",
                    "gemini-2.5-flash-lite",
                    0.0,
                    0.0,
                    1000000,
                    '{"vision":false,"reasoning":false}',
                    0.05,
                    "active",
                    "eco",
                    0,
                    now_iso(),
                ),
            )
            conn.execute(
                """
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "gemini",
                    "gemini-2.5-pro",
                    0.0,
                    0.0,
                    1000000,
                    '{"vision":true,"reasoning":true}',
                    0.30,
                    "active",
                    "racing",
                    0,
                    now_iso(),
                ),
            )
            conn.execute(
                """
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "mock",
                    "mock-eco",
                    0.0,
                    0.0,
                    1000000,
                    '{"vision":false,"reasoning":false}',
                    0.05,
                    "active",
                    "eco",
                    1,
                    now_iso(),
                ),
            )
            conn.execute(
                """
                INSERT INTO model_catalog
                (provider, model_name, pricing_input_per_mtok, pricing_output_per_mtok,
                 context_window, capabilities_json, estimated_cost_per_run, status, mode, is_internal, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "mock",
                    "mock-racing",
                    0.0,
                    0.0,
                    1000000,
                    '{"vision":false,"reasoning":false}',
                    0.30,
                    "active",
                    "racing",
                    1,
                    now_iso(),
                ),
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS executions_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                execution_status TEXT NOT NULL,
                mode TEXT,
                model TEXT,
                provider TEXT,
                latency_ms INTEGER,
                estimated_cost REAL,
                prompt_text TEXT DEFAULT '',
                output_text TEXT DEFAULT '',
                error_code TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                router_trace_json TEXT DEFAULT '{}',
                run_fingerprint TEXT DEFAULT '',
                artifact_md_path TEXT DEFAULT '',
                artifact_json_path TEXT DEFAULT '',
                executed_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_app TEXT NOT NULL,
                project_id INTEGER,
                task_id INTEGER,
                workflow TEXT DEFAULT '',
                task_type TEXT DEFAULT '',
                agent_role TEXT DEFAULT '',
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms INTEGER DEFAULT 0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                quality_rating REAL,
                converted_to_asset INTEGER DEFAULT 0,
                reused_later INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
            """
        )
        ensure_column(conn, "model_runs", "source_app", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "project_id", "INTEGER")
        ensure_column(conn, "model_runs", "task_id", "INTEGER")
        ensure_column(conn, "model_runs", "workflow", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "task_type", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "agent_role", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "provider", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "model", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "status", "TEXT DEFAULT ''")
        ensure_column(conn, "model_runs", "latency_ms", "INTEGER DEFAULT 0")
        ensure_column(conn, "model_runs", "input_tokens", "INTEGER DEFAULT 0")
        ensure_column(conn, "model_runs", "output_tokens", "INTEGER DEFAULT 0")
        ensure_column(conn, "model_runs", "cost_usd", "REAL DEFAULT 0")
        ensure_column(conn, "model_runs", "quality_rating", "REAL")
        ensure_column(conn, "model_runs", "converted_to_asset", "INTEGER DEFAULT 0")
        ensure_column(conn, "model_runs", "reused_later", "INTEGER DEFAULT 0")
        ensure_column(conn, "model_runs", "metadata_json", "TEXT DEFAULT '{}'")
        ensure_column(conn, "model_runs", "created_at", "TEXT DEFAULT ''")

        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            created = now_iso()

            def make_slug(name: str) -> str:
                slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
                slug = re.sub(r"[-\s]+", "-", slug)
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
