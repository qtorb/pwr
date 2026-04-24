from __future__ import annotations

import json
import mimetypes
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from db import get_conn, now_iso, project_upload_dir


PROJECT_SELECT = """
    SELECT
        p.*,
        (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS task_count,
        (SELECT COUNT(*) FROM assets a WHERE a.project_id = p.id) AS asset_count,
        COALESCE(
            (
                SELECT MAX(activity_at)
                FROM (
                    SELECT MAX(updated_at) AS activity_at
                    FROM tasks
                    WHERE project_id = p.id
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS activity_at
                    FROM assets
                    WHERE project_id = p.id
                )
            ),
            p.updated_at,
            p.created_at
        ) AS last_activity_at
    FROM projects p
"""


def save_project_files(project_id: int, files) -> List[Dict]:
    saved = []
    dest = project_upload_dir(project_id)
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


def get_projects() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            PROJECT_SELECT
            + """
            ORDER BY p.is_favorite DESC, last_activity_at DESC, p.updated_at DESC, p.id DESC
            """
        ).fetchall()


def get_project(project_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            PROJECT_SELECT
            + """
            WHERE p.id = ?
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()


def update_project(
    project_id: int,
    name: str,
    description: str,
    objective: str,
    base_context: str,
    base_instructions: str,
    tags: str,
) -> None:
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
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
                json.dumps([tag.strip() for tag in tags.split(",") if tag.strip()], ensure_ascii=False),
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


def create_project(
    name: str,
    description: str,
    objective: str,
    base_context: str,
    base_instructions: str,
    tags: str,
    uploaded_files,
) -> int:
    created = now_iso()
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
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
                json.dumps([tag.strip() for tag in tags.split(",") if tag.strip()], ensure_ascii=False),
                created,
                created,
            ),
        )
        project_id = int(cur.lastrowid)
        saved = save_project_files(project_id, uploaded_files)
        for item in saved:
            conn.execute(
                """
                INSERT INTO project_documents (
                    project_id, title, file_name, file_path, mime_type, size_bytes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    item["name"],
                    item["name"],
                    item["path"],
                    item["mime_type"],
                    item["size"],
                    created,
                    created,
                ),
            )
        return project_id


def get_project_documents(project_id: int) -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM project_documents WHERE project_id = ? ORDER BY updated_at DESC, id DESC",
            (project_id,),
        ).fetchall()


def get_projects_with_activity() -> List[dict]:
    projects = get_projects()
    result = []
    with get_conn() as conn:
        for project in projects:
            project_dict = dict(project)
            task_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM tasks WHERE project_id = ?",
                (project["id"],),
            ).fetchone()["cnt"]
            last_task = conn.execute(
                "SELECT updated_at FROM tasks WHERE project_id = ? ORDER BY updated_at DESC LIMIT 1",
                (project["id"],),
            ).fetchone()
            project_dict["active_task_count"] = task_count
            project_dict["last_activity"] = last_task["updated_at"] if last_task else project["created_at"]
            result.append(project_dict)
    return result
