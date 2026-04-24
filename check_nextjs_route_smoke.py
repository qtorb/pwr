#!/usr/bin/env python3
"""Minimal route smoke for the parallel Next.js shell over FastAPI."""

from __future__ import annotations

import os
import json
import socket
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
        startup_error = ""
        for _ in range(5):
            frontend_port = free_port(frontend_port, 3299)
            frontend_log_handle = frontend_log.open("w", encoding="utf-8")
            frontend_proc = subprocess.Popen(
                [
                    "cmd.exe",
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
            time.sleep(2)
            frontend_log_handle.close()
            frontend_log_handle = None
            if frontend_proc.poll() in (None, 0):
                break

            startup_error = safe_text(frontend_log.read_text(encoding="utf-8", errors="replace").strip())
            terminate_process_tree(frontend_proc)
            frontend_proc = None
            if "EADDRINUSE" not in startup_error:
                raise RuntimeError(
                    f"nextjs shell exited early with code 1: {startup_error or '(no output)'}"
                )
            frontend_port += 1
        else:
            raise RuntimeError(
                f"nextjs shell could not start after retrying ports: {startup_error or '(no output)'}"
            )

        home_html = wait_for_http(f"{frontend_base}/", timeout=40.0)
        ok(f"frontend ready on {frontend_base}")

        if "Home MVP paralela" in home_html and "Proyectos" in home_html and "Para retomar" in home_html:
            ok("home route renders expected readonly shell content")
        else:
            fail("home route is missing expected content")
            failures += 1

        with urllib.request.urlopen(f"{backend_base}/api/projects", timeout=5) as response:
            project_items = json.loads(response.read().decode("utf-8")).get("items", [])
        if not project_items:
            fail("backend returned no projects for readonly workspace smoke")
            return 1

        project_id = int(project_items[0]["id"])
        project_html = wait_for_http(f"{frontend_base}/projects/{project_id}", timeout=40.0)
        if (
            "Contexto del proyecto" in project_html
            and "Tareas" in project_html
            and "Activos relacionados" in project_html
            and "Solo lectura" in project_html
        ):
            ok(f"project readonly route renders expected content for project_id={project_id}")
        else:
            fail("project readonly route is missing expected content")
            failures += 1

    except Exception as exc:
        fail(f"unexpected error: {type(exc).__name__}: {exc}")
        failures += 1
    finally:
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
