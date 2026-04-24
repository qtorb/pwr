#!/usr/bin/env python3
"""Minimal route smoke for the parallel Next.js shell over FastAPI."""

from __future__ import annotations

import os
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend-nextjs"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
BACKEND_HOST = "127.0.0.1"
DB_PATH = ROOT / "pwr_data" / "pwr.db"
WINDOWS_SHELL = os.environ.get("ComSpec", r"C:\WINDOWS\system32\cmd.exe")


def safe_text(message: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")


def ok(message: str) -> None:
    print(safe_text(f"[OK] {message}"))


def fail(message: str) -> None:
    print(safe_text(f"[FAIL] {message}"))


def free_port(start: int, end: int) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((BACKEND_HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found between {start} and {end}")


def wait_for_http(url: str, expected_status: int = 200, timeout: float = 25.0) -> str:
    deadline = time.time() + timeout
    last_error = "unknown error"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status == expected_status:
                    return body
                last_error = f"unexpected status {response.status}"
        except urllib.error.HTTPError as exc:
            last_error = f"http {exc.code}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"{url} did not become ready: {last_error}")


def request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def cleanup_controlled_task(task_id: int | None) -> None:
    if not task_id:
        return
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT artifact_md_path, artifact_json_path FROM executions_history WHERE task_id = ?",
            (task_id,),
        ).fetchall()
        conn.execute("DELETE FROM executions_history WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    for row in rows:
        for rel_path in row:
            if not rel_path:
                continue
            artifact_path = ROOT / str(rel_path).replace("/", os.sep)
            if artifact_path.exists():
                with suppress(OSError):
                    artifact_path.unlink()


def terminate_process_tree(proc: subprocess.Popen | None) -> None:
    if not proc:
        return
    if proc.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    print("PWR Next.js route smoke")
    print("=" * 30)

    failures = 0
    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None
    controlled_task_id: int | None = None
    temp_log_file = tempfile.NamedTemporaryFile(
        prefix="pwr-nextjs-route-smoke-",
        suffix=".log",
        delete=False,
    )
    temp_log_file.close()
    frontend_log = Path(temp_log_file.name)
    frontend_log_handle = None

    try:
        backend_port = free_port(8100, 8199)
        frontend_port = free_port(3200, 3299)

        backend_proc = subprocess.Popen(
            [
                str(PYTHON),
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(backend_port),
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        backend_base = f"http://{BACKEND_HOST}:{backend_port}"
        wait_for_http(f"{backend_base}/health")
        ok(f"backend ready on {backend_base}")

        env = os.environ.copy()
        env["PWR_API_BASE_URL"] = backend_base
        frontend_base = ""
        home_html = ""
        startup_error = ""
        for _ in range(5):
            shutil.rmtree(FRONTEND_DIR / ".next", ignore_errors=True)
            frontend_port = free_port(frontend_port, 3299)
            frontend_log_handle = frontend_log.open("w", encoding="utf-8")
            frontend_proc = subprocess.Popen(
                [
                    WINDOWS_SHELL,
                    "/c",
                    "npm.cmd",
                    "run",
                    "dev",
                    "--",
                    "--hostname",
                    BACKEND_HOST,
                    "--port",
                    str(frontend_port),
                ],
                cwd=FRONTEND_DIR,
                env=env,
                stdout=frontend_log_handle,
                stderr=subprocess.STDOUT,
            )
            frontend_base = f"http://{BACKEND_HOST}:{frontend_port}"
            time.sleep(3)
            frontend_log_handle.close()
            frontend_log_handle = None
            if frontend_proc.poll() not in (None, 0):
                startup_error = safe_text(frontend_log.read_text(encoding="utf-8", errors="replace").strip())
                terminate_process_tree(frontend_proc)
                frontend_proc = None
                if "EADDRINUSE" not in startup_error:
                    raise RuntimeError(
                        f"nextjs shell exited early with code 1: {startup_error or '(no output)'}"
                    )
                frontend_port += 1
                continue

            try:
                home_html = wait_for_http(f"{frontend_base}/", timeout=60.0)
                ok(f"frontend ready on {frontend_base}")
                break
            except Exception as exc:
                startup_error = safe_text(
                    frontend_log.read_text(encoding="utf-8", errors="replace").strip()
                )
                terminate_process_tree(frontend_proc)
                frontend_proc = None
                frontend_port += 1
                if _ == 4:
                    raise RuntimeError(
                        f"{frontend_base}/ did not become ready: {exc}\n{startup_error or '(no output)'}"
                    ) from exc
        else:
            raise RuntimeError(
                f"nextjs shell could not start after retrying ports: {startup_error or '(no output)'}"
            )

        if "Home MVP paralela" in home_html and "Proyectos" in home_html and "Para retomar" in home_html:
            ok("home route renders expected readonly shell content")
        else:
            fail("home route is missing expected content")
            failures += 1

        project_items = request_json(f"{backend_base}/api/projects").get("items", [])
        if not project_items:
            fail("backend returned no projects for readonly workspace smoke")
            return 1

        project_id = int(project_items[0]["id"])
        controlled_task = request_json(
            f"{backend_base}/api/projects/{project_id}/tasks",
            method="POST",
            payload={
                "title": "Next.js route smoke task",
                "description": "Tarea controlada para validar detalle readonly en Next.js.",
                "task_type": "Pensar",
                "context": "Contexto controlado para el smoke de /tasks/{id}.",
            },
        )
        controlled_task_id = int(controlled_task["id"])
        ok(f"created controlled task id={controlled_task_id} for route smoke")

        project_html = wait_for_http(f"{frontend_base}/projects/{project_id}", timeout=60.0)
        if (
            "Contexto del proyecto" in project_html
            and "Tareas" in project_html
            and "Activos relacionados" in project_html
            and "Solo lectura" in project_html
            and f"/tasks/{controlled_task_id}" in project_html
        ):
            ok(f"project readonly route renders expected content for project_id={project_id}")
        else:
            fail("project readonly route is missing expected content")
            failures += 1

        task_html = wait_for_http(f"{frontend_base}/tasks/{controlled_task_id}", timeout=60.0)
        if (
            controlled_task["title"] in task_html
            and "Contexto" in task_html
            and "Ejecucion" in task_html
            and "Output" in task_html
            and "Historial" in task_html
            and f"/projects/{project_id}" in task_html
            and "Ejecutar ahora" in task_html
        ):
            ok(f"task readonly route renders expected content for task_id={controlled_task_id}")
        else:
            fail("task readonly route is missing expected content")
            failures += 1

        execute_payload = request_json(f"{backend_base}/api/tasks/{controlled_task_id}/execute", method="POST")
        next_state = str(execute_payload.get("status") or "").lower()
        if next_state in {"preview", "failed", "executed"} and execute_payload.get("execution_id"):
            ok(f"task execute route updates status={next_state} for task_id={controlled_task_id}")
        else:
            fail("task execute route did not return a valid execution result")
            failures += 1

        latest_run = request_json(f"{backend_base}/api/tasks/{controlled_task_id}/executions/latest").get("item")
        latest_task = request_json(f"{backend_base}/api/tasks/{controlled_task_id}")
        if latest_run and str(latest_task.get("execution_status") or "").lower() == next_state:
            ok(f"backend reflects updated task state={next_state}")
        else:
            fail("backend state did not update after task execution")
            failures += 1

        updated_task_html = wait_for_http(
            f"{frontend_base}/tasks/{controlled_task_id}?updated=1&status={next_state}",
            timeout=60.0,
        )
        expected_button = {
            "preview": "Continuar",
            "failed": "Reintentar",
            "executed": "Ejecutar de nuevo",
        }.get(next_state, "")
        if (
            "Actualizado" in updated_task_html
            and expected_button in updated_task_html
            and "Sin ejecuciones todavia" not in updated_task_html
        ):
            ok(f"task route refreshes after execution with CTA={expected_button}")
        else:
            fail("task route did not refresh with updated execution state")
            failures += 1

    except Exception as exc:
        fail(f"unexpected error: {type(exc).__name__}: {exc}")
        failures += 1
    finally:
        cleanup_controlled_task(controlled_task_id)
        terminate_process_tree(frontend_proc)
        terminate_process_tree(backend_proc)
        if frontend_log_handle:
            frontend_log_handle.close()
        if frontend_log.exists():
            with suppress(PermissionError):
                frontend_log.unlink()

    print("=" * 30)
    if failures:
        fail(f"{failures} Next.js route smoke issue(s)")
        return 1

    ok("Next.js shell routes respond correctly against FastAPI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
