#!/usr/bin/env python3
"""Minimal HTTP-level check for the model observatory MVP."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from db import get_conn


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def cleanup(run_ids: list[int], task_id: int | None) -> None:
    with get_conn() as conn:
        if run_ids:
            placeholders = ", ".join(["?"] * len(run_ids))
            conn.execute(f"DELETE FROM model_runs WHERE id IN ({placeholders})", tuple(run_ids))
        if task_id:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def main() -> int:
    print("PWR model observatory check")
    print("=" * 30)

    failures = 0
    created_run_ids: list[int] = []
    created_task_id: int | None = None

    try:
        with TestClient(app) as client:
            projects_response = client.get("/api/projects")
            if projects_response.status_code != 200:
                fail("project listing failed; cannot prepare observatory check")
                return 1

            projects = projects_response.json()["items"]
            if not projects:
                fail("no projects available through the API")
                return 1

            project_id = int(projects[0]["id"])
            task_response = client.post(
                f"/api/projects/{project_id}/tasks",
                json={
                    "title": "[MODEL OBS CHECK] Controlled task",
                    "description": "",
                    "task_type": "Pensar",
                    "context": "Controlled task created for model observatory validation.",
                },
            )
            if task_response.status_code != 200:
                fail("controlled task creation failed")
                return 1

            created_task_id = int(task_response.json()["id"])
            ok(f"created controlled task id={created_task_id}")

            payloads = [
                {
                    "source_app": "pwr-check",
                    "project_id": project_id,
                    "task_id": created_task_id,
                    "workflow": "retake",
                    "task_type": "briefing",
                    "agent_role": "router",
                    "provider": "gemini",
                    "model": "gemini-2.5-pro",
                    "status": "executed",
                    "latency_ms": 1200,
                    "input_tokens": 900,
                    "output_tokens": 320,
                    "cost_usd": 0.021,
                    "quality_rating": 4.5,
                    "converted_to_asset": True,
                    "reused_later": False,
                    "metadata_json": {"phase": "check", "case": "successful"},
                },
                {
                    "source_app": "pwr-check",
                    "project_id": project_id,
                    "task_id": created_task_id,
                    "workflow": "retake",
                    "task_type": "briefing",
                    "agent_role": "router",
                    "provider": "gemini",
                    "model": "gemini-2.5-pro",
                    "status": "failed",
                    "latency_ms": 1800,
                    "input_tokens": 870,
                    "output_tokens": 0,
                    "cost_usd": 0.018,
                    "quality_rating": None,
                    "converted_to_asset": False,
                    "reused_later": False,
                    "metadata_json": {"phase": "check", "case": "failed"},
                },
                {
                    "source_app": "uxmachine-check",
                    "project_id": None,
                    "task_id": None,
                    "workflow": "synthesis",
                    "task_type": "summary",
                    "agent_role": "analyst",
                    "provider": "openai",
                    "model": "gpt-5.4-mini",
                    "status": "executed",
                    "latency_ms": 950,
                    "input_tokens": 500,
                    "output_tokens": 220,
                    "cost_usd": 0.011,
                    "quality_rating": 4.0,
                    "converted_to_asset": False,
                    "reused_later": True,
                    "metadata_json": {"phase": "check", "case": "secondary"},
                },
            ]

            for payload in payloads:
                response = client.post("/api/model-runs", json=payload)
                if response.status_code != 200:
                    fail("model run creation failed")
                    return 1
                created = response.json()
                created_run_ids.append(int(created["id"]))
            ok(f"registered {len(created_run_ids)} model run(s)")

            list_response = client.get("/api/model-runs", params={"source_app": "pwr-check", "limit": 10})
            if list_response.status_code != 200:
                fail("model run listing failed")
                return 1

            items = list_response.json()["items"]
            if len(items) >= 2 and all(item["source_app"] == "pwr-check" for item in items[:2]):
                ok("listed model runs through HTTP")
            else:
                fail("model run listing did not return the expected filtered data")
                failures += 1

            summary_response = client.get("/api/model-runs/summary", params={"source_app": "pwr-check", "limit": 10})
            if summary_response.status_code != 200:
                fail("model run summary failed")
                return 1

            summary_items = summary_response.json()["items"]
            matching = [
                row
                for row in summary_items
                if row["provider"] == "gemini"
                and row["model"] == "gemini-2.5-pro"
                and row["task_type"] == "briefing"
            ]
            if matching and int(matching[0]["run_count"]) >= 2:
                ok("model run summary groups by provider/model/task_type")
            else:
                fail("model run summary did not include the expected grouped row")
                failures += 1

    except Exception as exc:
        fail(f"unexpected error: {type(exc).__name__}: {exc}")
        failures += 1
    finally:
        cleanup(created_run_ids, created_task_id)
        if created_run_ids or created_task_id:
            ok(
                "cleaned controlled observatory test data"
                f"{f' task={created_task_id}' if created_task_id else ''}"
                f"{f' runs={len(created_run_ids)}' if created_run_ids else ''}"
            )

    print("=" * 30)
    if failures:
        fail(f"{failures} model observatory issue(s)")
        return 1

    ok("model observatory MVP responds correctly over HTTP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
