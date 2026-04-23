# PWR Local Runtime

Portable Work Router (PWR) is currently operated locally from `app_main.py`.
The live loop is:

`capture task -> project workspace -> execution view -> Gemini/run preview -> persisted result -> portable artifact`

## Canonical Local Setup

Use Python 3.11.9 and the repo-local virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Gemini Key

PWR reads `GEMINI_API_KEY` from the process environment. For a local PowerShell session:

```powershell
$env:GEMINI_API_KEY = "your-gemini-key"
```

If the key is missing, the app should still boot locally, but real Gemini execution will fall back to preview/error handling.

## Run The App

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_main.py
```

Open `http://localhost:8501`.

## Validate

Basic setup check:

```powershell
.\.venv\Scripts\python.exe validate_setup.py
```

Local smoke check for the live Streamlit runtime:

```powershell
.\.venv\Scripts\python.exe run_smoke_test.py
```

Real Gemini smoke, after `GEMINI_API_KEY` is available in the same PowerShell process:

```powershell
.\.venv\Scripts\python.exe run_smoke_test.py --live-gemini
```

Manual views to verify after changes:

- Inicio
- Nueva tarea
- Proyectos / task workspace
- Radar

## Runtime Data

Local SQLite database:

`pwr_data/pwr.db`

Portable run artifacts:

`pwr_data/portable_runs/`

Artifact paths in `executions_history` are stored relative to the repo when they point inside this workspace.

## Out Of Scope For Local Iterations

Railway, Docker, Procfile and remote deployment config are not part of the local runtime path unless explicitly requested.
