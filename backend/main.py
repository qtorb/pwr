from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from db import init_db
from services.assets import build_asset_reuse_payload, get_asset, get_project_assets, create_asset
from services.executions import get_execution_history, get_latest_execution_run
from services.model_observatory import (
    create_model_run,
    get_model_run,
    get_model_run_summary,
    list_model_runs,
)
from services.projects import get_project, get_projects
from services.tasks import (
    get_project_tasks,
    get_recent_home_tasks,
    get_reentry_tasks,
    get_task,
    create_task,
)
from state_contract import (
    AMBIGUOUS_RUNTIME_TRANSITIONS,
    HOME_ACTIVITY_STATES,
    HOME_RETAKE_STATES,
    REENTRY_CONTEXT_STATES,
    STATE_CONTRACT,
    VALID_RUNTIME_TRANSITIONS,
)


def row_to_dict(row) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    if isinstance(row, dict):
        return dict(row)
    raise TypeError(f"Unsupported row type: {type(row)!r}")


def require_project(project_id: int):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def require_task(task_id: int):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


def require_asset(asset_id: int):
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return asset


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    task_type: str = "Pensar"
    context: str = ""


class CreateAssetRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    summary: str = ""
    asset_type: str = "output"
    task_id: int | None = None
    source_execution_id: int | None = None
    source_execution_status: str = ""


class CreateModelRunRequest(BaseModel):
    source_app: str = Field(..., min_length=1)
    project_id: int | None = None
    task_id: int | None = None
    workflow: str = ""
    task_type: str = ""
    agent_role: str = ""
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    quality_rating: float | None = None
    converted_to_asset: bool = False
    reused_later: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PWR Minimal API",
    version="0.1.0",
    description="Minimal HTTP surface over the extracted PWR services layer.",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "PWR Minimal API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/state-contract")
def state_contract() -> dict[str, Any]:
    return {
        "states": STATE_CONTRACT,
        "home_activity_states": list(HOME_ACTIVITY_STATES),
        "home_retake_states": list(HOME_RETAKE_STATES),
        "reentry_context_states": sorted(REENTRY_CONTEXT_STATES),
        "valid_runtime_transitions": {
            state: sorted(targets) for state, targets in VALID_RUNTIME_TRANSITIONS.items()
        },
        "ambiguous_runtime_transitions": {
            f"{source}->{target}": note
            for (source, target), note in AMBIGUOUS_RUNTIME_TRANSITIONS.items()
        },
    }


@app.get("/api/home/activity")
def home_activity(
    limit: int = Query(default=5, ge=1, le=50),
    today_only: bool = False,
) -> dict[str, Any]:
    return {"items": get_recent_home_tasks(limit=limit, today_only=today_only)}


@app.get("/api/home/reentry")
def home_reentry(limit: int = Query(default=5, ge=1, le=50)) -> dict[str, Any]:
    return {"items": get_reentry_tasks(limit=limit)}


@app.get("/api/projects")
def list_projects() -> dict[str, Any]:
    return {"items": [row_to_dict(project) for project in get_projects()]}


@app.get("/api/model-runs/summary")
def model_runs_summary(
    limit: int = Query(default=100, ge=1, le=500),
    source_app: str = "",
    workflow: str = "",
) -> dict[str, Any]:
    items = [row_to_dict(row) for row in get_model_run_summary(limit=limit, source_app=source_app, workflow=workflow)]
    return {
        "items": items,
        "total_runs": sum(int(item.get("run_count", 0) or 0) for item in items),
    }


@app.get("/api/model-runs")
def model_runs(
    limit: int = Query(default=50, ge=1, le=500),
    source_app: str = "",
    provider: str = "",
    model: str = "",
    workflow: str = "",
    task_type: str = "",
    status: str = "",
) -> dict[str, Any]:
    return {
        "items": [
            row_to_dict(run)
            for run in list_model_runs(
                limit=limit,
                source_app=source_app,
                provider=provider,
                model=model,
                workflow=workflow,
                task_type=task_type,
                status=status,
            )
        ]
    }


@app.post("/api/model-runs")
def model_runs_create(payload: CreateModelRunRequest) -> dict[str, Any]:
    if payload.project_id is not None:
        require_project(payload.project_id)
    if payload.task_id is not None:
        require_task(payload.task_id)

    run_id = create_model_run(
        source_app=payload.source_app,
        project_id=payload.project_id,
        task_id=payload.task_id,
        workflow=payload.workflow,
        task_type=payload.task_type,
        agent_role=payload.agent_role,
        provider=payload.provider,
        model=payload.model,
        status=payload.status,
        latency_ms=payload.latency_ms,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        cost_usd=payload.cost_usd,
        quality_rating=payload.quality_rating,
        converted_to_asset=payload.converted_to_asset,
        reused_later=payload.reused_later,
        metadata_json=payload.metadata_json,
    )
    run = get_model_run(run_id)
    if not run:
        raise HTTPException(status_code=500, detail="Model run was created but could not be read back")
    return row_to_dict(run)


@app.get("/api/projects/{project_id}")
def project_detail(project_id: int) -> dict[str, Any]:
    project = require_project(project_id)
    return row_to_dict(project)


@app.get("/api/projects/{project_id}/tasks")
def project_tasks(project_id: int, search: str = "") -> dict[str, Any]:
    require_project(project_id)
    return {"items": [row_to_dict(task) for task in get_project_tasks(project_id, search=search)]}


@app.post("/api/projects/{project_id}/tasks")
def project_create_task(project_id: int, payload: CreateTaskRequest) -> dict[str, Any]:
    require_project(project_id)
    task_id = create_task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        context=payload.context,
        uploaded_files=None,
    )
    task = require_task(task_id)
    return row_to_dict(task)


@app.get("/api/tasks/{task_id}")
def task_detail(task_id: int) -> dict[str, Any]:
    task = require_task(task_id)
    return row_to_dict(task)


@app.get("/api/tasks/{task_id}/executions")
def task_executions(
    task_id: int,
    limit: int | None = Query(default=None, ge=1, le=100),
) -> dict[str, Any]:
    require_task(task_id)
    return {"items": [row_to_dict(run) for run in get_execution_history(task_id, limit=limit)]}


@app.get("/api/tasks/{task_id}/executions/latest")
def task_latest_execution(task_id: int) -> dict[str, Any]:
    require_task(task_id)
    latest = get_latest_execution_run(task_id)
    return {"item": row_to_dict(latest) if latest else None}


@app.get("/api/projects/{project_id}/assets")
def project_assets(project_id: int) -> dict[str, Any]:
    require_project(project_id)
    return {"items": [row_to_dict(asset) for asset in get_project_assets(project_id)]}


@app.post("/api/projects/{project_id}/assets")
def project_create_asset(project_id: int, payload: CreateAssetRequest) -> dict[str, Any]:
    require_project(project_id)
    if payload.task_id is not None:
        task = require_task(payload.task_id)
        if int(task["project_id"]) != project_id:
            raise HTTPException(status_code=400, detail="task_id does not belong to the target project")

    asset_id = create_asset(
        project_id=project_id,
        task_id=payload.task_id,
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        asset_type=payload.asset_type,
        source_execution_id=payload.source_execution_id,
        source_execution_status=payload.source_execution_status,
    )
    return row_to_dict(require_asset(asset_id))


@app.get("/api/assets/{asset_id}")
def asset_detail(asset_id: int) -> dict[str, Any]:
    return row_to_dict(require_asset(asset_id))


@app.post("/api/assets/{asset_id}/reuse")
def asset_reuse(asset_id: int) -> dict[str, Any]:
    asset = require_asset(asset_id)
    return build_asset_reuse_payload(asset)
