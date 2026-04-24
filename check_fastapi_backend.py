#!/usr/bin/env python3
"""Minimal HTTP-level check for the PWR FastAPI backend."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from db import BASE_DIR
from db import get_conn
from services.model_observatory import find_task_execution_model_runs, list_model_feedback


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def cleanup(asset_id: int | None, task_id: int | None, project_id: int | None) -> None:
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
            conn.execute("DELETE FROM model_feedback WHERE task_id = ?", (task_id,))
        if task_id:
            conn.execute("DELETE FROM model_runs WHERE task_id = ?", (task_id,))
        if task_id:
            conn.execute("DELETE FROM executions_history WHERE task_id = ?", (task_id,))
        if task_id:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if project_id:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

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
    manual_task_id: int | None = None
    created_asset_id: int | None = None
    created_project_id: int | None = None

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

            create_project_response = client.post(
                "/api/projects",
                json={
                    "name": "[FASTAPI CHECK] Controlled project",
                    "description": "Proyecto controlado para validar integridad Project -> Tasks.",
                },
            )
            if create_project_response.status_code != 200:
                fail("project creation endpoint failed")
                return 1
            created_project = create_project_response.json()
            created_project_id = int(created_project["id"])
            ok(f"created controlled project through HTTP id={created_project_id}")

            detail_response = client.get(f"/api/projects/{created_project_id}")
            if detail_response.status_code == 200:
                ok(f"read project detail id={created_project_id}")
            else:
                fail("project detail failed")
                failures += 1

            tasks_response = client.get(f"/api/projects/{created_project_id}/tasks")
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

            missing_project_response = client.post(
                "/api/tasks",
                json={
                    "title": "[FASTAPI CHECK] Missing project",
                    "description": "",
                    "task_type": "Pensar",
                    "context": "This request should fail because project_id is required.",
                },
            )
            if missing_project_response.status_code == 422:
                ok("global task creation requires project_id")
            else:
                fail("global task creation should reject missing project_id")
                failures += 1

            create_task_response = client.post(
                "/api/tasks",
                json={
                    "project_id": created_project_id,
                    "title": "[FASTAPI CHECK] Controlled task",
                    "description": "",
                    "task_type": "Pensar",
                    "context": "Controlled task created by check_fastapi_backend.py",
                    "preferred_model": "gemini-2.5-pro",
                },
            )
            if create_task_response.status_code != 200:
                fail("HTTP task creation failed")
                return 1
            created_task = create_task_response.json()
            created_task_id = int(created_task["id"])
            ok(f"created controlled task through HTTP id={created_task_id}")
            if created_task.get("suggested_model") == "gemini-2.5-pro":
                ok("task creation accepts preferred_model for low-friction workspace flows")
            else:
                fail("task creation did not keep the requested preferred_model")
                failures += 1

            manual_task_response = client.post(
                "/api/tasks",
                json={
                    "project_id": created_project_id,
                    "title": "[FASTAPI CHECK] Manual capture task",
                    "description": "",
                    "task_type": "Pensar",
                    "context": "Prompt inicial para validar guardado manual.",
                    "preferred_model": "mock-racing",
                },
            )
            if manual_task_response.status_code != 200:
                fail("manual capture task creation failed")
                return 1
            manual_task_id = int(manual_task_response.json()["id"])
            ok(f"created manual capture task id={manual_task_id}")

            manual_save_response = client.post(
                f"/api/tasks/{manual_task_id}/manual-result",
                json={
                    "model": "mock-racing",
                    "prompt": "Prompt manual actualizado desde Task Workspace.",
                    "result_text": "Resultado manual controlado para validar el flujo unificado.",
                },
            )
            manual_task_after_save = client.get(f"/api/tasks/{manual_task_id}")
            manual_latest_execution = client.get(f"/api/tasks/{manual_task_id}/executions/latest")
            if (
                manual_save_response.status_code == 200
                and manual_save_response.json().get("status") == "executed"
                and manual_task_after_save.status_code == 200
                and manual_task_after_save.json().get("execution_status") == "executed"
                and manual_task_after_save.json().get("context") == "Prompt manual actualizado desde Task Workspace."
                and manual_latest_execution.status_code == 200
                and manual_latest_execution.json().get("item")
                and manual_latest_execution.json()["item"].get("output_text") == "Resultado manual controlado para validar el flujo unificado."
            ):
                ok("manual result endpoint saves prompt/result and updates task state")
            else:
                fail("manual result endpoint did not persist the expected manual execution")
                failures += 1

            filtered_tasks_response = client.get("/api/tasks", params={"project_id": created_project_id})
            global_tasks_response = client.get("/api/tasks", params={"limit": 20})
            read_task_response = client.get(f"/api/tasks/{created_task_id}")
            execution_history_response = client.get(f"/api/tasks/{created_task_id}/executions")
            latest_execution_response = client.get(f"/api/tasks/{created_task_id}/executions/latest")
            if (
                filtered_tasks_response.status_code == 200
                and global_tasks_response.status_code == 200
                and read_task_response.status_code == 200
                and execution_history_response.status_code == 200
                and latest_execution_response.status_code == 200
            ):
                ok("task detail and execution endpoints respond")
            else:
                fail("task detail/execution endpoints failed")
                failures += 1

            filtered_items = filtered_tasks_response.json().get("items", [])
            global_items = global_tasks_response.json().get("items", [])
            read_task_payload = read_task_response.json()
            if (
                any(int(item["id"]) == created_task_id for item in filtered_items)
                and any(int(item["id"]) == created_task_id for item in global_items)
                and int(read_task_payload.get("project_id") or 0) == created_project_id
                and read_task_payload.get("project_name") == created_project.get("name")
            ):
                ok("global task listing and task detail include project context")
            else:
                fail("task endpoints did not expose the expected project context")
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

            summary_before_feedback = client.get("/api/model-runs/summary").json().get("summary", [])
            matching_before_feedback = next(
                (
                    row
                    for row in summary_before_feedback
                    if row.get("provider") == (related_runs[0]["provider"] if related_runs else "gemini")
                    and row.get("model") == (related_runs[0]["model"] if related_runs else "gemini-2.5-flash-lite")
                    and row.get("task_type") == (created_task.get("task_type") or "generic")
                ),
                None,
            )
            useful_before = int((matching_before_feedback or {}).get("feedback_useful_count") or 0)
            total_before = int((matching_before_feedback or {}).get("feedback_total") or 0)

            feedback_response = client.post(
                "/api/model-feedback",
                json={
                    "task_id": created_task_id,
                    "task_type": created_task.get("task_type") or "generic",
                    "provider": related_runs[0]["provider"] if related_runs else "gemini",
                    "model": related_runs[0]["model"] if related_runs else "gemini-2.5-flash-lite",
                    "score": 0.75,
                    "confidence": "medium",
                    "feedback": "useful",
                },
            )
            feedback_rows = list_model_feedback(task_id=created_task_id, limit=10)
            summary_after_feedback = client.get("/api/model-runs/summary").json().get("summary", [])
            matching_after_feedback = next(
                (
                    row
                    for row in summary_after_feedback
                    if row.get("provider") == (related_runs[0]["provider"] if related_runs else "gemini")
                    and row.get("model") == (related_runs[0]["model"] if related_runs else "gemini-2.5-flash-lite")
                    and row.get("task_type") == (created_task.get("task_type") or "generic")
                ),
                None,
            )
            if (
                feedback_response.status_code == 200
                and feedback_response.json().get("feedback") == "useful"
                and feedback_rows
                and feedback_rows[0]["feedback"] == "useful"
                and matching_after_feedback
                and int(matching_after_feedback.get("feedback_useful_count") or 0) == useful_before + 1
                and int(matching_after_feedback.get("feedback_total") or 0) == total_before + 1
            ):
                ok("model feedback endpoint persists hint feedback and summary reflects it")
            else:
                fail("model feedback endpoint did not persist the expected feedback in summary")
                failures += 1

            create_asset_response = client.post(
                f"/api/projects/{created_project_id}/assets",
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
            project_assets_response = client.get(f"/api/projects/{created_project_id}/assets")
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
                and isinstance(recommended.get("quality_score"), (int, float))
                and isinstance(recommended.get("cost_efficiency"), (int, float))
                and isinstance(recommended.get("latency_efficiency"), (int, float))
                and isinstance(recommended.get("reliability_score"), (int, float))
                and "quality=" in str(recommended.get("reason") or "")
                and "reliability=" in str(recommended.get("reason") or "")
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
        cleanup(None, manual_task_id, None)
        cleanup(created_asset_id, created_task_id, created_project_id)
        if manual_task_id or created_task_id or created_asset_id or created_project_id:
            ok(
                "cleaned controlled HTTP test data"
                f"{f' manual_task={manual_task_id}' if manual_task_id else ''}"
                f"{f' task={created_task_id}' if created_task_id else ''}"
                f"{f' asset={created_asset_id}' if created_asset_id else ''}"
                f"{f' project={created_project_id}' if created_project_id else ''}"
            )

    print("=" * 28)
    if failures:
        fail(f"{failures} backend validation issue(s)")
        return 1

    ok("FastAPI backend is serving the extracted services over HTTP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
