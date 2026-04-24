#!/usr/bin/env python3
"""Validate the current local PWR runtime."""

import importlib.util
import os
import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_PYTHON = (3, 11)
REQUIRED_FILES = [
    "app_main.py",
    "db.py",
    "backend/main.py",
    "state_contract.py",
    "requirements.txt",
    "services/__init__.py",
    "services/projects.py",
    "services/tasks.py",
    "services/executions.py",
    "services/assets.py",
    "check_fastapi_backend.py",
    "router/domain.py",
    "router/providers.py",
    "router/execution_service.py",
    "router/decision_engine.py",
    "router/model_catalog.py",
    ".env.example",
]
EXPECTED_DB = ROOT / "pwr_data" / "pwr.db"
SERVICE_FILES = [
    ROOT / "services" / "projects.py",
    ROOT / "services" / "tasks.py",
    ROOT / "services" / "executions.py",
    ROOT / "services" / "assets.py",
]


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> int:
    print("PWR local setup validation")
    print("=" * 32)

    failures = 0

    if sys.version_info[:2] == EXPECTED_PYTHON:
        ok(f"Python {sys.version.split()[0]} matches 3.11.x")
    else:
        fail(f"Python {sys.version.split()[0]} detected; expected 3.11.x")
        failures += 1

    for rel_path in REQUIRED_FILES:
        if (ROOT / rel_path).exists():
            ok(rel_path)
        else:
            fail(f"{rel_path} missing")
            failures += 1

    if has_module("streamlit"):
        ok("streamlit importable")
    else:
        fail("streamlit missing; run .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        failures += 1

    if has_module("fastapi"):
        ok("fastapi importable")
    else:
        fail("fastapi missing; run .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        failures += 1

    if has_module("uvicorn"):
        ok("uvicorn importable")
    else:
        fail("uvicorn missing; run .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        failures += 1

    if has_module("google.genai"):
        ok("google-genai importable")
    else:
        fail("google-genai missing; run .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        failures += 1

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        masked = api_key[:4] + "*" * max(len(api_key) - 8, 0) + api_key[-4:]
        ok(f"GEMINI_API_KEY available in process: {masked}")
        ok("real Gemini smoke is eligible: .\\.venv\\Scripts\\python.exe run_smoke_test.py --live-gemini")
    else:
        warn("GEMINI_API_KEY is not available in this process; real Gemini smoke remains pending")
        warn("PowerShell: $env:GEMINI_API_KEY = \"your-gemini-key\"")

    for rel_path in (
        "app_main.py",
        "db.py",
        "backend/main.py",
        "state_contract.py",
        "check_fastapi_backend.py",
        "services/projects.py",
        "services/tasks.py",
        "services/executions.py",
        "services/assets.py",
    ):
        try:
            py_compile.compile(str(ROOT / rel_path), doraise=True)
            ok(f"{rel_path} compiles")
        except py_compile.PyCompileError as exc:
            fail(f"{rel_path} does not compile: {exc.msg}")
            failures += 1

    for service_path in SERVICE_FILES:
        text = service_path.read_text(encoding="utf-8")
        if "import streamlit" in text or "from streamlit" in text:
            fail(f"{service_path.relative_to(ROOT)} imports streamlit; services must stay UI-free")
            failures += 1
        else:
            ok(f"{service_path.relative_to(ROOT)} stays streamlit-free")

    if EXPECTED_DB.exists():
        ok("pwr_data/pwr.db exists")
    else:
        warn("pwr_data/pwr.db does not exist yet; first Streamlit run should create it")

    print("=" * 32)
    if failures:
        fail(f"{failures} blocking setup issue(s)")
        return 1

    ok("local setup looks runnable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
