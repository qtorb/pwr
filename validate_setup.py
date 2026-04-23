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
    "state_contract.py",
    "requirements.txt",
    "router/domain.py",
    "router/providers.py",
    "router/execution_service.py",
    "router/decision_engine.py",
    "router/model_catalog.py",
    ".env.example",
]
EXPECTED_DB = ROOT / "pwr_data" / "pwr.db"


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

    for rel_path in ("app_main.py", "state_contract.py"):
        try:
            py_compile.compile(str(ROOT / rel_path), doraise=True)
            ok(f"{rel_path} compiles")
        except py_compile.PyCompileError as exc:
            fail(f"{rel_path} does not compile: {exc.msg}")
            failures += 1

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
