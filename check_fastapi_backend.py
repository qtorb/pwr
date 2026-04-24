#!/usr/bin/env python3
"""Minimal HTTP-level check for the PWR FastAPI backend."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from db import BASE_DIR
from db import get_conn
from services.model_observatory import find_task_execution_model_runs


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def cleanup(asset_id: int | None, task_id: int | None) -> None:
    with get_conn() as conn:
        artifact_rows = []
        if task_id:
            artifact_rows = conn.execute(
                "SELECT artifact_md_path, artifact_json_path FROM executions_history WHERE task_id = ?",
                (task_id,),
            ).fetchall()
        if asset_id:
            conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        if task_id:
            conn.execute("DELETE FROM model_runs WHERE task_id = ?", (task_id,))
        if task_id:
            conn.execute("DELETE FROM executions_history WHERE task_id = ?", (task_id,))
        if task_id:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    for row in artifact_rows:
        for key in ("artifact_md_path", "artifact_json_path"):
            rel_path = row[key]
            if not rel_path:
                continue
            path = (BASE_DIR / rel_path).resolve()
            if path.exists():
                path.unlink()


def main() -> int:
    print("PWR FastAPI backend check")
    print("=" * 28)

    failures = 0
    created_task_id: int | None = None
    created_asset_id: int | None = None

    try:
        with TestClient(app) as client:
            response = client.get("/health")
            if response.status_code == 200 and response.json().get("status") == "ok":
                ok("health endpoint responds")
            else:
                fail("health endpoint failed")
                failures += 1

            projects_response = client.get("/api/projects")
            if projects_response.status_code != 200:
                fail("project listing failed")
                return 1

            projects = projects_response.json()["items"]
            if not projects:
                fail("no projects available through the API")
                return 1
            ok(f"listed {len(projects)} project(s) through HTTP")

            project_id = int(projects[0]["id"])
            detail_response = client.get(f"/api/projects/{project_id}")
            if detail_response.status_code == 200:
                ok(f"read project detail id={project_id}")
            else:
                fail("project detail failed")
                failures += 1

            tasks_response = client.get(f"/api/projects/{project_id}/tasks")
            if tasks_response.status_code == 200:
                ok("listed project tasks through HTTP")
            else:
                fail("project task listing failed")
                failures += 1

            home_activity = client.get("/api/home/activity", params={"limit": 3})
            home_reentry = client.get("/api/home/reentry", params={"limit": 3})
            best_model_hint = client.get("/api/model-runs/best", params={"task_type": "Pensar"})
            if home_activity.status_code == 200 and home_reentry.status_code == 200 and best_model_hint.status_code == 200:
                ok("home activity and reentry endpoints respond")
            else:
                fail("home endpoints failed")
                failures += 1

            create_task_response = client.post(
                f"/api/projects/{project_id}/tasks",
                json={
                    "title": "[FASTAPI CHECK] Controlled task",
                    "description": "",
                    "task_type": "Pensar",
                    "context": "Controlled task created by check_fastapi_backend.py",
                },
            )
            if create_task_response.status_code != 200:
                fail("HTTP task creation failed")
                return 1
            created_task = create_task_response.json()
            created_task_id = int(created_task["id"])
            ok(f"created controlled task through HTTP id={created_task_id}")

            read_task_response = client.get(f"/api/tasks/{created_task_id}")
            execution_history_response = client.get(f"/api/tasks/{created_task_id}/executions")
            latest_execution_response = client.get(f"/api/tasks/{created_task_id}/executions/latest")
            if (
                read_task_response.status_code == 200
                and execution_history_response.status_code == 200
                and latest_execution_response.status_code == 200
            ):
                ok("task detail and execution endpoints respond")
            else:
                fail("task detail/execution endpoints failed")
                failures += 1

            execute_task_response = client.post(f"/api/tasks/{created_task_id}/execute")
            if execute_task_response.status_code == 200:
                execute_payload = execute_task_response.json()
                if execute_payload.get("status") in {"preview", "failed", "executed"}:
                    ok(f"task execution endpoint responds with status={execute_payload['status']}")
                else:
                    fail("task execution endpoint returned an invalid status")
                    failures += 1
            else:
                fail("task execution endpoint failed")
                failures += 1

            latest_after_execute = client.get(f"/api/tasks/{created_task_id}/executions/latest")
            task_after_execute = client.get(f"/api/tasks/{created_task_id}")
            if (
                latest_after_execute.status_code == 200
                and latest_after_execute.json().get("item")
                and task_after_execute.status_code == 200
                and task_after_execute.json().get("execution_status") in {"preview", "failed", "executed"}
            ):
                ok("task execution persisted latest execution and updated task state")
            else:
                fail("task execution did not persist the expected state")
                failures += 1

            latest_execution_item = latest_after_execute.json().get("item") or {}
            task_after_execute_payload = task_after_execute.json()
            related_runs = find_task_execution_model_runs(
                created_task_id,
                execution_id=latest_execution_item.get("id"),
            )
            if (
                related_runs
                and related_runs[0]["source_app"] == "PWR-Core"
                and related_runs[0]["status"] == task_after_execute_payload["execution_status"]
            ):
                ok("task execution creates a related model_run in PWR-Core")
            else:
                fail("task execution did not create the expected model_run")
                failures += 1

            create_asset_response = client.post(
                f"/api/projects/{project_id}/assets",
                json={
                    "task_id": created_task_id,
                    "asset_type": "preview" if task_after_execute_payload["execution_status"] == "preview" else "output",
                    "title": "FastAPI controlled asset",
                    "summary": "Representative asset created by HTTP backend check.",
                    "content": (
                        latest_execution_item.get("output_text")
                        or task_after_execute_payload.get("llm_output")
                        or task_after_execute_payload.get("router_summary")
                        or created_task["context"]
                        or "Reusable content"
                    ),
                    "source_execution_status": task_after_execute_payload["execution_status"],
                    "source_execution_id": latest_execution_item.get("id"),
                },
            )
            if create_asset_response.status_code != 200:
                fail("HTTP asset creation failed")
                return 1
            created_asset = create_asset_response.json()
            created_asset_id = int(created_asset["id"])
            if (
                created_asset.get("task_id") == created_task_id
                and created_asset.get("source_execution_id") == latest_execution_item.get("id")
            ):
                ok(f"created representative asset through HTTP id={created_asset_id}")
            else:
                fail("created asset is not linked to the expected task/execution")
                failures += 1

            asset_detail_response = client.get(f"/api/assets/{created_asset_id}")
            project_assets_response = client.get(f"/api/projects/{project_id}/assets")
            asset_reuse_response = client.post(f"/api/assets/{created_asset_id}/reuse")
            related_runs_after_asset = find_task_execution_model_runs(
                created_task_id,
                execution_id=latest_execution_item.get("id"),
            )
            if related_runs_after_asset and int(related_runs_after_asset[0]["converted_to_asset"] or 0) == 1:
                ok("asset creation marks the related model_run as converted_to_asset")
            else:
                fail("asset creation did not mark converted_to_asset on the related model_run")
                failures += 1
            if (
                asset_detail_response.status_code == 200
                and project_assets_response.status_code == 200
                and asset_reuse_response.status_code == 200
            ):
                ok("asset detail, listing and reuse endpoints respond")
            else:
                fail("asset endpoints failed")
                failures += 1

            reuse_payload = asset_reuse_response.json()
            if reuse_payload.get("title") and reuse_payload.get("context") and reuse_payload.get("notice"):
                ok("asset reuse payload is complete over HTTP")
            else:
                fail("asset reuse payload is incomplete over HTTP")
                failures += 1

            related_runs_after_reuse = find_task_execution_model_runs(
                created_task_id,
                execution_id=latest_execution_item.get("id"),
            )
            if related_runs_after_reuse and int(related_runs_after_reuse[0]["reused_later"] or 0) == 1:
                ok("asset reuse marks the related model_run as reused_later")
            else:
                fail("asset reuse did not mark reused_later on the related model_run")
                failures += 1

            best_payload = client.get("/api/model-runs/best", params={"task_type": "Pensar"}).json()
            recommended = best_payload.get("recommended")
            if (
                recommended
                and recommended.get("model")
                and isinstance(recommended.get("total_runs"), int)
                and recommended.get("confidence") in {"low", "medium", "high"}
                and "conversion=" in str(recommended.get("reason") or "")
                and "recent_weighting=" in str(recommended.get("reason") or "")
            ):
                ok("best model hint endpoint returns a recommendation")
            else:
                fail("best model hint endpoint did not return a recommendation")
                failures += 1

    except Exception as exc:
        fail(f"unexpected error: {type(exc).__name__}: {exc}")
        failures += 1
    finally:
        cleanup(created_asset_id, created_task_id)
        if created_task_id or created_asset_id:
            ok(
                "cleaned controlled HTTP test data"
                f"{f' task={created_task_id}' if created_task_id else ''}"
                f"{f' asset={created_asset_id}' if created_asset_id else ''}"
            )

    print("=" * 28)
    if failures:
        fail(f"{failures} backend validation issue(s)")
        return 1

    ok("FastAPI backend is serving the extracted services over HTTP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
