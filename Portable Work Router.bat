@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo .venv not found. Run instalar_pwr.bat first.
  pause
  exit /b 1
)
start "" http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app_main.py
pause
