#!/usr/bin/env python3
"""Minimal HTTP-level check for the model observatory MVP."""

from __future__ import annotations

from datetime import datetime, timedelta

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
                    "status": "preview",
                    "latency_ms": 900,
                    "input_tokens": 600,
                    "output_tokens": 140,
                    "cost_usd": 0.009,
                    "quality_rating": 4.0,
                    "converted_to_asset": True,
                    "reused_later": True,
                    "metadata_json": {"phase": "check", "case": "preview"},
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

            with get_conn() as conn:
                conn.execute(
                    "UPDATE model_runs SET created_at = ? WHERE id = ?",
                    ((datetime.now() - timedelta(days=7)).isoformat(timespec="seconds"), created_run_ids[0]),
                )
                conn.execute(
                    "UPDATE model_runs SET created_at = ? WHERE id = ?",
                    ((datetime.now() - timedelta(days=1)).isoformat(timespec="seconds"), created_run_ids[1]),
                )
                conn.execute(
                    "UPDATE model_runs SET created_at = ? WHERE id = ?",
                    ((datetime.now() - timedelta(days=30)).isoformat(timespec="seconds"), created_run_ids[2]),
                )
                conn.execute(
                    "UPDATE model_runs SET created_at = ? WHERE id = ?",
                    ("invalid-timestamp", created_run_ids[3]),
                )

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

            summary_payload = summary_response.json()
            summary_items = summary_payload["summary"]
            matching = [
                row
                for row in summary_items
                if row["provider"] == "gemini"
                and row["model"] == "gemini-2.5-pro"
                and row["task_type"] == "briefing"
            ]
            if matching and int(matching[0]["total_runs"]) == 3:
                ok("model run summary groups by provider/model/task_type")
            else:
                fail("model run summary did not include the expected grouped row")
                failures += 1

            if matching:
                row = matching[0]
                expected = {
                    "success_rate": 0.3333,
                    "preview_rate": 0.3333,
                    "failed_rate": 0.3333,
                    "avg_latency_ms": 1300.0,
                    "avg_cost_usd": 0.016,
                    "avg_input_tokens": 790.0,
                    "avg_output_tokens": 153.33,
                    "conversion_rate": 0.6667,
                    "reuse_rate": 0.3333,
                }
                numeric_failures = [
                    key
                    for key, value in expected.items()
                    if abs(float(row.get(key) or 0.0) - value) > 0.0002
                ]
                if not numeric_failures and int(summary_payload.get("total_runs") or 0) >= 3:
                    ok("model run summary returns the expected rates and averages")
                else:
                    fail(
                        "model run summary metrics differ from the expected values"
                        + (f": {', '.join(numeric_failures)}" if numeric_failures else "")
                    )
                    failures += 1

            best_response = client.get("/api/model-runs/best", params={"task_type": "briefing"})
            if best_response.status_code != 200:
                fail("best model hint endpoint failed")
                return 1

            recommended = best_response.json().get("recommended")
            if (
                recommended
                and recommended.get("provider") == "gemini"
                and recommended.get("model") == "gemini-2.5-pro"
                and recommended.get("task_type") == "briefing"
                and abs(float(recommended.get("score") or 0.0) - 0.6762) <= 0.0002
                and int(recommended.get("total_runs") or 0) == 3
                and recommended.get("confidence") == "low"
                and "conversion=" in str(recommended.get("reason") or "")
                and "reuse=" in str(recommended.get("reason") or "")
                and "runs=3" in str(recommended.get("reason") or "")
                and "confidence=low" in str(recommended.get("reason") or "")
                and "recent_weighting=enabled" in str(recommended.get("reason") or "")
            ):
                ok("best model hint returns the expected recommendation")
            else:
                fail("best model hint did not return the expected recommendation")
                failures += 1

            fallback_best_response = client.get("/api/model-runs/best", params={"task_type": "summary"})
            if fallback_best_response.status_code != 200:
                fail("best model hint fallback endpoint failed")
                return 1

            fallback_recommended = fallback_best_response.json().get("recommended")
            if (
                fallback_recommended
                and fallback_recommended.get("provider") == "openai"
                and fallback_recommended.get("model") == "gpt-5.4-mini"
                and abs(float(fallback_recommended.get("score") or 0.0) - 0.4) <= 0.0002
                and "recent_weighting=fallback" in str(fallback_recommended.get("reason") or "")
            ):
                ok("best model hint falls back cleanly when timestamps are invalid")
            else:
                fail("best model hint did not fall back as expected for invalid timestamps")
                failures += 1

            empty_best_response = client.get("/api/model-runs/best", params={"task_type": "nonexistent"})
            if empty_best_response.status_code != 200:
                fail("best model hint null-case endpoint failed")
                return 1

            if empty_best_response.json().get("recommended") is None:
                ok("best model hint returns null when no data exists for the task_type")
            else:
                fail("best model hint should return null when there is no data for the task_type")
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
