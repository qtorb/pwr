from __future__ import annotations

import json
import sqlite3
from typing import Optional

from db import get_conn, now_iso, row_value, safe_json_loads


def create_model_run(
    *,
    source_app: str,
    project_id: int | None,
    task_id: int | None,
    workflow: str,
    task_type: str,
    agent_role: str,
    provider: str,
    model: str,
    status: str,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    quality_rating: float | None = None,
    converted_to_asset: bool = False,
    reused_later: bool = False,
    metadata_json: Optional[dict] = None,
) -> int:
    created_at = now_iso()
    payload = json.dumps(metadata_json or {}, ensure_ascii=False)

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO model_runs (
                source_app, project_id, task_id, workflow, task_type, agent_role,
                provider, model, status, latency_ms, input_tokens, output_tokens,
                cost_usd, quality_rating, converted_to_asset, reused_later,
                metadata_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_app.strip(),
                project_id,
                task_id,
                workflow.strip(),
                task_type.strip(),
                agent_role.strip(),
                provider.strip(),
                model.strip(),
                status.strip(),
                int(latency_ms or 0),
                int(input_tokens or 0),
                int(output_tokens or 0),
                float(cost_usd or 0),
                quality_rating,
                1 if converted_to_asset else 0,
                1 if reused_later else 0,
                payload,
                created_at,
            ),
        )
        return int(cur.lastrowid)


def get_model_run(run_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT *
            FROM model_runs
            WHERE id = ?
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()


def list_model_runs(
    *,
    limit: int = 50,
    source_app: str = "",
    provider: str = "",
    model: str = "",
    workflow: str = "",
    task_type: str = "",
    status: str = "",
) -> list[sqlite3.Row]:
    where_clauses = ["1 = 1"]
    params: list = []

    for column, value in (
        ("source_app", source_app),
        ("provider", provider),
        ("model", model),
        ("workflow", workflow),
        ("task_type", task_type),
        ("status", status),
    ):
        if str(value or "").strip():
            where_clauses.append(f"{column} = ?")
            params.append(str(value).strip())

    params.append(limit)
    with get_conn() as conn:
        return conn.execute(
            f"""
            SELECT *
            FROM model_runs
            WHERE {' AND '.join(where_clauses)}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()


def get_model_run_summary(
    *,
    limit: int = 100,
    source_app: str = "",
    workflow: str = "",
) -> list[dict]:
    where_clauses = ["1 = 1"]
    params: list = []

    if str(source_app or "").strip():
        where_clauses.append("source_app = ?")
        params.append(str(source_app).strip())

    if str(workflow or "").strip():
        where_clauses.append("workflow = ?")
        params.append(str(workflow).strip())

    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                provider,
                model,
                task_type,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN LOWER(COALESCE(status, '')) = 'executed' THEN 1 ELSE 0 END) AS executed_count,
                SUM(CASE WHEN LOWER(COALESCE(status, '')) = 'preview' THEN 1 ELSE 0 END) AS preview_count,
                SUM(CASE WHEN LOWER(COALESCE(status, '')) = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms END) AS avg_latency_ms,
                AVG(CASE WHEN cost_usd IS NOT NULL THEN cost_usd END) AS avg_cost_usd,
                AVG(CASE WHEN input_tokens IS NOT NULL THEN input_tokens END) AS avg_input_tokens,
                AVG(CASE WHEN output_tokens IS NOT NULL THEN output_tokens END) AS avg_output_tokens,
                SUM(CASE WHEN COALESCE(converted_to_asset, 0) != 0 THEN 1 ELSE 0 END) AS converted_to_asset_count,
                SUM(CASE WHEN COALESCE(reused_later, 0) != 0 THEN 1 ELSE 0 END) AS reused_later_count
            FROM model_runs
            WHERE {' AND '.join(where_clauses)}
            GROUP BY provider, model, task_type
            ORDER BY total_runs DESC, provider ASC, model ASC, task_type ASC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

    summary: list[dict] = []
    for row in rows:
        total_runs = int(row_value(row, "total_runs", 0) or 0)
        executed_count = int(row_value(row, "executed_count", 0) or 0)
        preview_count = int(row_value(row, "preview_count", 0) or 0)
        failed_count = int(row_value(row, "failed_count", 0) or 0)
        converted_count = int(row_value(row, "converted_to_asset_count", 0) or 0)
        reused_count = int(row_value(row, "reused_later_count", 0) or 0)
        denominator = float(total_runs or 0)

        def ratio(value: int) -> float:
            if denominator <= 0:
                return 0.0
            return round(float(value) / denominator, 4)

        def metric(value, digits: int):
            if value is None:
                return None
            return round(float(value), digits)

        summary.append(
            {
                "provider": row_value(row, "provider"),
                "model": row_value(row, "model"),
                "task_type": row_value(row, "task_type"),
                "total_runs": total_runs,
                "success_rate": ratio(executed_count),
                "preview_rate": ratio(preview_count),
                "failed_rate": ratio(failed_count),
                "avg_latency_ms": metric(row_value(row, "avg_latency_ms", None), 2),
                "avg_cost_usd": metric(row_value(row, "avg_cost_usd", None), 6),
                "avg_input_tokens": metric(row_value(row, "avg_input_tokens", None), 2),
                "avg_output_tokens": metric(row_value(row, "avg_output_tokens", None), 2),
                "conversion_rate": ratio(converted_count),
                "reuse_rate": ratio(reused_count),
            }
        )

    return summary


def delete_model_runs(run_ids: list[int]) -> None:
    if not run_ids:
        return
    placeholders = ", ".join(["?"] * len(run_ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM model_runs WHERE id IN ({placeholders})", tuple(run_ids))


def model_run_metadata(row) -> dict:
    return safe_json_loads(row_value(row, "metadata_json"), {})


def find_task_execution_model_runs(task_id: int, execution_id: int | None = None) -> list[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM model_runs
            WHERE task_id = ? AND workflow = 'task_execution'
            ORDER BY created_at DESC, id DESC
            """,
            (task_id,),
        ).fetchall()

    if execution_id is None:
        return rows

    expected = int(execution_id or 0)
    return [
        row
        for row in rows
        if int(model_run_metadata(row).get("execution_id") or 0) == expected
    ]


def register_task_execution_model_run(
    *,
    source_app: str,
    project_id: int | None,
    task_id: int,
    execution_id: int,
    task_type: str,
    provider: str,
    model: str,
    status: str,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    metadata_json: Optional[dict] = None,
) -> int | None:
    existing = find_task_execution_model_runs(task_id, execution_id=execution_id)
    if existing:
        return int(row_value(existing[0], "id", 0) or 0) or None

    payload = dict(metadata_json or {})
    payload["execution_id"] = execution_id

    return create_model_run(
        source_app=source_app or "PWR-Core",
        project_id=project_id,
        task_id=task_id,
        workflow="task_execution",
        task_type=(task_type or "generic").strip() or "generic",
        agent_role="executor",
        provider=(provider or "unknown").strip() or "unknown",
        model=(model or "unknown").strip() or "unknown",
        status=(status or "failed").strip() or "failed",
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        quality_rating=None,
        converted_to_asset=False,
        reused_later=False,
        metadata_json=payload,
    )


def mark_task_execution_runs_converted_to_asset(task_id: int, execution_id: int | None = None) -> list[int]:
    rows = find_task_execution_model_runs(task_id, execution_id=execution_id)
    run_ids = [int(row_value(row, "id", 0) or 0) for row in rows if int(row_value(row, "id", 0) or 0) > 0]
    if not run_ids:
        return []

    placeholders = ", ".join(["?"] * len(run_ids))
    with get_conn() as conn:
        conn.execute(
            f"UPDATE model_runs SET converted_to_asset = 1 WHERE id IN ({placeholders})",
            tuple(run_ids),
        )
    return run_ids


def mark_task_execution_runs_reused_later(task_id: int, execution_id: int | None = None) -> list[int]:
    rows = find_task_execution_model_runs(task_id, execution_id=execution_id)
    run_ids = [int(row_value(row, "id", 0) or 0) for row in rows if int(row_value(row, "id", 0) or 0) > 0]
    if not run_ids:
        return []

    placeholders = ", ".join(["?"] * len(run_ids))
    with get_conn() as conn:
        conn.execute(
            f"UPDATE model_runs SET reused_later = 1 WHERE id IN ({placeholders})",
            tuple(run_ids),
        )
    return run_ids
