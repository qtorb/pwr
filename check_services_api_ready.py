#!/usr/bin/env python3
"""Minimal API-readiness check for PWR services without Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path

from db import get_conn, init_db, now_iso
from services.assets import build_asset_reuse_payload, create_asset, get_asset, get_project_assets
from services.executions import get_execution_history, get_latest_execution_run
from services.projects import get_project, get_projects
from services.tasks import create_task, get_project_tasks, get_task


ROOT = Path(__file__).resolve().parent


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def cleanup(created_asset_id: int | None, created_task_id: int | None) -> None:
    with get_conn() as conn:
        if created_asset_id:
            conn.execute("DELETE FROM assets WHERE id = ?", (created_asset_id,))
        if created_task_id:
            conn.execute("DELETE FROM tasks WHERE id = ?", (created_task_id,))


def main() -> int:
    print("PWR services API-ready check")
    print("=" * 32)

    failures = 0
    created_task_id: int | None = None
    created_asset_id: int | None = None

    try:
        init_db()

        if "streamlit" in sys.modules:
            fail("streamlit was imported before service validation started")
            failures += 1
        else:
            ok("services imported without streamlit")

        projects = get_projects()
        if not projects:
            fail("no projects available")
            return 1
        ok(f"listed {len(projects)} project(s)")

        project = projects[0]
        project_row = get_project(int(project["id"]))
        if not project_row:
            fail("could not read a concrete project row")
            return 1
        ok(f"read project id={project_row['id']} name={project_row['name']}")

        tasks = get_project_tasks(int(project_row["id"]))
        ok(f"listed {len(tasks)} task(s) for project id={project_row['id']}")

        existing_task = None
        for candidate_project in projects:
            candidate_tasks = get_project_tasks(int(candidate_project["id"]))
            if candidate_tasks:
                existing_task = candidate_tasks[0]
                break

        if existing_task:
            history = get_execution_history(int(existing_task["id"]))
            latest_run = get_latest_execution_run(int(existing_task["id"]))
            ok(
                "read execution history for existing task "
                f"id={existing_task['id']} rows={len(history)} latest_run={'yes' if latest_run else 'no'}"
            )
        else:
            warn("no existing tasks with execution history available; continuing with controlled create flow")

        test_stamp = now_iso().replace(":", "-")
        test_title = f"[API READY CHECK] {test_stamp}"
        test_context = "Controlled task created by check_services_api_ready.py for service-only validation."
        created_task_id = create_task(
            int(project_row["id"]),
            test_title,
            "",
            "Pensar",
            test_context,
            None,
        )
        ok(f"created controlled task id={created_task_id}")

        created_task = get_task(created_task_id)
        if not created_task:
            fail("created task cannot be read back")
            failures += 1
        else:
            ok(f"read created task id={created_task['id']} status={created_task['execution_status']}")

        created_history = get_execution_history(created_task_id)
        ok(f"read execution history for created task rows={len(created_history)}")

        created_asset_id = create_asset(
            int(project_row["id"]),
            created_task_id,
            f"API Ready Asset {test_stamp}",
            "Controlled reusable asset created by the API-ready check.",
            created_task["router_summary"] or created_task["context"] or "Controlled reusable content",
            asset_type="briefing",
            source_execution_id=None,
            source_execution_status=created_task["execution_status"],
        )
        ok(f"created representative asset id={created_asset_id}")

        asset = get_asset(created_asset_id)
        if not asset:
            fail("created asset cannot be read back")
            failures += 1
        else:
            ok(f"read created asset id={asset['id']} type={asset['asset_type']}")

        project_assets = get_project_assets(int(project_row["id"]))
        found_asset = any(int(row["id"]) == created_asset_id for row in project_assets)
        if found_asset:
            ok(f"project asset listing includes asset id={created_asset_id}")
        else:
            fail("project asset listing does not include the created asset")
            failures += 1

        reuse_payload = build_asset_reuse_payload(asset)
        if reuse_payload.get("title") and reuse_payload.get("context") and reuse_payload.get("notice"):
            ok("prepared reusable-asset payload for a future new task base")
        else:
            fail("asset reuse payload is incomplete")
            failures += 1

    except Exception as exc:
        fail(f"unexpected error: {type(exc).__name__}: {exc}")
        failures += 1
    finally:
        cleanup(created_asset_id, created_task_id)
        if created_task_id or created_asset_id:
            ok(
                "cleaned controlled test data"
                f"{f' task={created_task_id}' if created_task_id else ''}"
                f"{f' asset={created_asset_id}' if created_asset_id else ''}"
            )

    print("=" * 32)
    if failures:
        fail(f"{failures} API-ready validation issue(s)")
        return 1

    ok("services are usable outside Streamlit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
