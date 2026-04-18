from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PROJECTS = []
TASKS = []
CAPTURES = []

CURRENT_PROJECT_ID: Optional[int] = None


def get_current_project():
    global CURRENT_PROJECT_ID
    if CURRENT_PROJECT_ID is None:
        return None
    for project in PROJECTS:
        if project["id"] == CURRENT_PROJECT_ID:
            return project
    return None


def get_project(project_id: int):
    for project in PROJECTS:
        if project["id"] == project_id:
            return project
    return None


def get_task(task_id: int):
    for task in TASKS:
        if task["id"] == task_id:
            return task
    return None


@router.get("/")
def home(request: Request):
    current_project = get_current_project()
    current_project_tasks = []
    if current_project:
        current_project_tasks = [t for t in TASKS if t["project_id"] == current_project["id"]]

    recent_captures = CAPTURES[-10:][::-1]

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "current_project": current_project,
            "tasks": current_project_tasks[::-1],
            "captures": recent_captures,
        },
    )


@router.get("/projects")
def projects_page(request: Request):
    return templates.TemplateResponse(
        request,
        "projects.html",
        {
            "projects": PROJECTS[::-1],
            "current_project_id": CURRENT_PROJECT_ID,
        },
    )


@router.post("/projects/create")
def create_project(name: str = Form(...)):
    global CURRENT_PROJECT_ID

    project_id = len(PROJECTS) + 1
    slug = name.strip().lower().replace(" ", "-")

    project = {
        "id": project_id,
        "name": name.strip(),
        "slug": slug,
    }
    PROJECTS.append(project)

    if CURRENT_PROJECT_ID is None:
        CURRENT_PROJECT_ID = project_id

    return RedirectResponse(url="/projects", status_code=303)


@router.post("/projects/{project_id}/set-current")
def set_current_project(project_id: int):
    global CURRENT_PROJECT_ID
    CURRENT_PROJECT_ID = project_id
    return RedirectResponse(url="/projects", status_code=303)


@router.get("/projects/{project_id}")
def project_page(request: Request, project_id: int):
    project = get_project(project_id)
    if not project:
        return RedirectResponse(url="/projects", status_code=303)

    project_tasks = [t for t in TASKS if t["project_id"] == project_id][::-1]
    project_captures = [c for c in CAPTURES if c.get("project_id") == project_id][::-1]

    return templates.TemplateResponse(
        request,
        "project.html",
        {
            "project": project,
            "tasks": project_tasks,
            "captures": project_captures,
            "current_project_id": CURRENT_PROJECT_ID,
        },
    )


@router.post("/tasks/create")
def create_task(
    title: str = Form(...),
    goal: str = Form(""),
    project_id: Optional[int] = Form(None),
):
    if project_id is None:
        current = get_current_project()
        if not current:
            return RedirectResponse(url="/projects", status_code=303)
        project_id = current["id"]

    task_id = len(TASKS) + 1
    task = {
        "id": task_id,
        "project_id": project_id,
        "title": title.strip(),
        "goal": goal.strip(),
        "briefing": "",
        "runs": [],
        "assets": [],
    }
    TASKS.append(task)

    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.get("/tasks/{task_id}")
def task_page(request: Request, task_id: int):
    task = get_task(task_id)
    if not task:
        return RedirectResponse(url="/", status_code=303)

    project = get_project(task["project_id"])

    return templates.TemplateResponse(
        request,
        "task.html",
        {
            "task": task,
            "project": project,
        },
    )


@router.post("/tasks/{task_id}/generate-briefing")
def generate_briefing(task_id: int):
    task = get_task(task_id)
    if not task:
        return RedirectResponse(url="/", status_code=303)

    project = get_project(task["project_id"])
    project_name = project["name"] if project else "Sin proyecto"

    briefing = f"""# Task
{task["title"]}

## Goal
{task["goal"] or "Sin goal definido"}

## Project
{project_name}

## Instructions
Ayúdame a avanzar esta tarea de forma clara, estructurada y reusable.
Genera una respuesta práctica, bien organizada y fácil de convertir en activo reusable.
"""
    task["briefing"] = briefing
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.post("/tasks/{task_id}/runs/create")
def create_run(task_id: int, summary: str = Form(...)):
    task = get_task(task_id)
    if not task:
        return RedirectResponse(url="/", status_code=303)

    task["runs"].append(summary.strip())
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.post("/tasks/{task_id}/assets/create")
def create_asset(task_id: int, title: str = Form(...)):
    task = get_task(task_id)
    if not task:
        return RedirectResponse(url="/", status_code=303)

    task["assets"].append(title.strip())
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.get("/captures")
def captures_page(request: Request):
    return templates.TemplateResponse(
        request,
        "captures.html",
        {
            "captures": CAPTURES[::-1],
            "current_project": get_current_project(),
        },
    )


@router.post("/captures/create")
def create_capture(text: str = Form(...), source: str = Form("")):
    current = get_current_project()
    capture_id = len(CAPTURES) + 1

    CAPTURES.append(
        {
            "id": capture_id,
            "text": text.strip(),
            "source": source.strip(),
            "status": "pending",
            "project_id": current["id"] if current else None,
        }
    )

    return RedirectResponse(url="/captures", status_code=303)


@router.post("/captures/{capture_id}/discard")
def discard_capture(capture_id: int):
    for capture in CAPTURES:
        if capture["id"] == capture_id:
            capture["status"] = "discarded"
            break
    return RedirectResponse(url="/captures", status_code=303)