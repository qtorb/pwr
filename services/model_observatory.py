from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional

from db import get_conn, now_iso, row_value, safe_json_loads


def clamp01(value: float) -> float:
    return round(min(max(float(value), 0.0), 1.0), 4)


def compute_reliability_score(row: dict) -> float:
    try:
        success_rate = row.get("success_rate")
        preview_rate = row.get("preview_rate")
        failed_rate = row.get("failed_rate")
        if success_rate is None or preview_rate is None or failed_rate is None:
            return 1.0

        raw_score = (
            float(success_rate) * 1.0
            + float(preview_rate) * 0.4
            - float(failed_rate) * 0.8
        )
    except (TypeError, ValueError):
        return 1.0

    return clamp01(raw_score)


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


def create_model_feedback(
    *,
    task_id: int,
    task_type: str,
    provider: str,
    model: str,
    score: float,
    confidence: str,
    feedback: str,
) -> int:
    created_at = now_iso()

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO model_feedback (
                task_id, task_type, provider, model, score, confidence, feedback, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(task_id),
                str(task_type or "").strip(),
                str(provider or "").strip(),
                str(model or "").strip(),
                float(score or 0.0),
                str(confidence or "").strip(),
                str(feedback or "").strip(),
                created_at,
            ),
        )
        return int(cur.lastrowid)


def get_model_feedback(feedback_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT *
            FROM model_feedback
            WHERE id = ?
            LIMIT 1
            """,
            (feedback_id,),
        ).fetchone()


def list_model_feedback(*, task_id: int | None = None, limit: int = 50) -> list[sqlite3.Row]:
    where_clauses = ["1 = 1"]
    params: list = []

    if task_id is not None:
        where_clauses.append("task_id = ?")
        params.append(int(task_id))

    params.append(int(limit))
    with get_conn() as conn:
        return conn.execute(
            f"""
            SELECT *
            FROM model_feedback
            WHERE {' AND '.join(where_clauses)}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()


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
                mr.provider,
                mr.model,
                mr.task_type,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN LOWER(COALESCE(mr.status, '')) = 'executed' THEN 1 ELSE 0 END) AS executed_count,
                SUM(CASE WHEN LOWER(COALESCE(mr.status, '')) = 'preview' THEN 1 ELSE 0 END) AS preview_count,
                SUM(CASE WHEN LOWER(COALESCE(mr.status, '')) = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                AVG(CASE WHEN mr.latency_ms IS NOT NULL THEN mr.latency_ms END) AS avg_latency_ms,
                AVG(CASE WHEN mr.cost_usd IS NOT NULL THEN mr.cost_usd END) AS avg_cost_usd,
                AVG(CASE WHEN mr.input_tokens IS NOT NULL THEN mr.input_tokens END) AS avg_input_tokens,
                AVG(CASE WHEN mr.output_tokens IS NOT NULL THEN mr.output_tokens END) AS avg_output_tokens,
                SUM(CASE WHEN COALESCE(mr.converted_to_asset, 0) != 0 THEN 1 ELSE 0 END) AS converted_to_asset_count,
                SUM(CASE WHEN COALESCE(mr.reused_later, 0) != 0 THEN 1 ELSE 0 END) AS reused_later_count,
                COALESCE(MAX(mf.feedback_useful_count), 0) AS feedback_useful_count,
                COALESCE(MAX(mf.feedback_not_useful_count), 0) AS feedback_not_useful_count,
                COALESCE(MAX(mf.feedback_used_other_count), 0) AS feedback_used_other_count,
                COALESCE(MAX(mf.feedback_total), 0) AS feedback_total
            FROM model_runs mr
            LEFT JOIN (
                SELECT
                    provider,
                    model,
                    task_type,
                    SUM(CASE WHEN feedback = 'useful' THEN 1 ELSE 0 END) AS feedback_useful_count,
                    SUM(CASE WHEN feedback = 'not_useful' THEN 1 ELSE 0 END) AS feedback_not_useful_count,
                    SUM(CASE WHEN feedback = 'used_other' THEN 1 ELSE 0 END) AS feedback_used_other_count,
                    COUNT(*) AS feedback_total
                FROM model_feedback
                GROUP BY provider, model, task_type
            ) mf
                ON COALESCE(mf.provider, '') = COALESCE(mr.provider, '')
               AND COALESCE(mf.model, '') = COALESCE(mr.model, '')
               AND COALESCE(mf.task_type, '') = COALESCE(mr.task_type, '')
            WHERE {' AND '.join(f'mr.{clause}' if clause != '1 = 1' else clause for clause in where_clauses)}
            GROUP BY mr.provider, mr.model, mr.task_type
            ORDER BY total_runs DESC, mr.provider ASC, mr.model ASC, mr.task_type ASC
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
                "feedback_useful_count": int(row_value(row, "feedback_useful_count", 0) or 0),
                "feedback_not_useful_count": int(row_value(row, "feedback_not_useful_count", 0) or 0),
                "feedback_used_other_count": int(row_value(row, "feedback_used_other_count", 0) or 0),
                "feedback_total": int(row_value(row, "feedback_total", 0) or 0),
            }
        )

    return summary


def get_best_model_hint(
    *,
    task_type: str = "generic",
    source_app: str = "",
    workflow: str = "",
) -> dict | None:
    normalized_task_type = str(task_type or "generic").strip() or "generic"
    summary = get_model_run_summary(limit=500, source_app=source_app, workflow=workflow)
    candidates = [
        row
        for row in summary
        if str(row.get("task_type") or "").strip() == normalized_task_type
        and int(row.get("total_runs") or 0) > 0
    ]
    if not candidates:
        return None

    task_runs = list_model_runs(
        limit=1000,
        source_app=source_app,
        workflow=workflow,
        task_type=normalized_task_type,
    )
    grouped_task_runs: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
    for row in task_runs:
        key = (
            str(row_value(row, "provider", "") or "").strip(),
            str(row_value(row, "model", "") or "").strip(),
            str(row_value(row, "task_type", "") or "").strip(),
        )
        grouped_task_runs.setdefault(key, []).append(row)

    def parse_created_at(value: str) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    def recency_weight(created_at: str) -> float | None:
        dt = parse_created_at(created_at)
        if dt is None:
            return None
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        age_days = max(0.0, (now - dt).total_seconds() / 86400.0)
        if age_days <= 3:
            return 1.0
        if age_days <= 14:
            return 0.7
        return 0.4

    def weighted_binary_rate(rows: list[sqlite3.Row], field_name: str) -> tuple[float | None, bool]:
        if not rows:
            return None, False

        weighted_total = 0.0
        weighted_hits = 0.0
        has_valid_timestamp = False
        for row in rows:
            weight = recency_weight(str(row_value(row, "created_at", "") or ""))
            if weight is None:
                weight = 1.0
            else:
                has_valid_timestamp = True
            weighted_total += weight
            if int(row_value(row, field_name, 0) or 0) != 0:
                weighted_hits += weight

        if weighted_total <= 0 or not has_valid_timestamp:
            return None, False
        return round(weighted_hits / weighted_total, 4), True

    def positive_metric(row: dict, field_name: str) -> float | None:
        try:
            value = float(row.get(field_name)) if row.get(field_name) is not None else None
        except (TypeError, ValueError):
            return None
        if value is None or value <= 0:
            return None
        return value

    valid_costs = [
        value
        for row in candidates
        for value in [positive_metric(row, "avg_cost_usd")]
        if value is not None
    ]
    valid_latencies = [
        value
        for row in candidates
        for value in [positive_metric(row, "avg_latency_ms")]
        if value is not None
    ]
    min_cost = min(valid_costs) if valid_costs else None
    min_latency = min(valid_latencies) if valid_latencies else None

    def candidate_metrics(row: dict) -> tuple[float, float, float, float, bool]:
        key = (
            str(row.get("provider") or "").strip(),
            str(row.get("model") or "").strip(),
            str(row.get("task_type") or "").strip(),
        )
        rows = grouped_task_runs.get(key, [])
        weighted_conversion_rate, conversion_weighted = weighted_binary_rate(rows, "converted_to_asset")
        weighted_reuse_rate, reuse_weighted = weighted_binary_rate(rows, "reused_later")
        if conversion_weighted and reuse_weighted:
            conversion_rate = float(weighted_conversion_rate or 0.0)
            reuse_rate = float(weighted_reuse_rate or 0.0)
            weighting_enabled = True
        else:
            conversion_rate = float(row.get("conversion_rate") or 0.0)
            reuse_rate = float(row.get("reuse_rate") or 0.0)
            weighting_enabled = False

        quality_score = round((conversion_rate * 0.6) + (reuse_rate * 0.4), 4)
        reliability_score = compute_reliability_score(row)

        cost_value = positive_metric(row, "avg_cost_usd")
        latency_value = positive_metric(row, "avg_latency_ms")
        cost_efficiency = 1.0 if min_cost is None or cost_value is None else round(min_cost / cost_value, 4)
        latency_efficiency = (
            1.0 if min_latency is None or latency_value is None else round(min_latency / latency_value, 4)
        )

        cost_efficiency = clamp01(cost_efficiency)
        latency_efficiency = clamp01(latency_efficiency)

        return quality_score, cost_efficiency, latency_efficiency, reliability_score, weighting_enabled

    def score(row: dict) -> float:
        quality_score, cost_efficiency, latency_efficiency, reliability_score, _ = candidate_metrics(row)
        return round(
            (quality_score * 0.65)
            + (cost_efficiency * 0.15)
            + (latency_efficiency * 0.10)
            + (reliability_score * 0.10),
            4,
        )

    def confidence_label(total_runs: int) -> str:
        if total_runs < 5:
            return "low"
        if total_runs < 20:
            return "medium"
        return "high"

    ordered = sorted(
        candidates,
        key=lambda row: (
            score(row),
            candidate_metrics(row)[0],
            candidate_metrics(row)[3],
            float(row.get("success_rate") or 0.0),
            int(row.get("total_runs") or 0),
        ),
        reverse=True,
    )
    best = ordered[0]
    total_runs = int(best.get("total_runs") or 0)
    confidence = confidence_label(total_runs)
    quality_score, cost_efficiency, latency_efficiency, reliability_score, weighting_enabled = candidate_metrics(best)
    weighting_state = "enabled" if weighting_enabled else "fallback"

    return {
        "provider": best.get("provider"),
        "model": best.get("model"),
        "task_type": best.get("task_type"),
        "score": score(best),
        "quality_score": quality_score,
        "cost_efficiency": cost_efficiency,
        "latency_efficiency": latency_efficiency,
        "reliability_score": reliability_score,
        "total_runs": total_runs,
        "confidence": confidence,
        "reason": (
            f"quality={quality_score:.4f}, "
            f"cost_efficiency={cost_efficiency:.4f}, "
            f"latency_efficiency={latency_efficiency:.4f}, "
            f"reliability={reliability_score:.4f}, "
            f"runs={total_runs}, "
            f"confidence={confidence}, "
            f"recent_weighting={weighting_state}"
        ),
    }


def delete_model_runs(run_ids: list[int]) -> None:
    if not run_ids:
        return
    placeholders = ", ".join(["?"] * len(run_ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM model_runs WHERE id IN ({placeholders})", tuple(run_ids))


def delete_model_feedback(feedback_ids: list[int]) -> None:
    if not feedback_ids:
        return
    placeholders = ", ".join(["?"] * len(feedback_ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM model_feedback WHERE id IN ({placeholders})", tuple(feedback_ids))


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
