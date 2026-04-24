from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from db import REUSABLE_ASSETS_DIR, compact_text, get_conn, now_iso, repo_relative_path, row_value


ASSET_TYPE_LABELS = {
    "output": "Resultado",
    "preview": "Preview",
    "briefing": "Briefing",
}


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


def build_asset_reuse_payload(asset) -> dict:
    title = row_value(asset, "title") or "Nueva tarea"
    return {
        "title": title,
        "context": build_asset_reuse_context(asset),
        "notice": f"Activo cargado como base: {title}. Ajusta título o contexto y genera una nueva propuesta.",
    }


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
    normalized_type = str(asset_type or "output").strip().lower()
    if normalized_type not in ASSET_TYPE_LABELS:
        normalized_type = "output"

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
                normalized_type,
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


def get_project_assets(project_id: int) -> list[sqlite3.Row]:
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
