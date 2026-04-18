#!/usr/bin/env python3
import subprocess
import sys
import os

print("Installing Python dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])

print("Starting Streamlit app...")
os.execvp("streamlit", ["streamlit", "run", "app_main.py",
                         "--server.port", os.environ.get("PORT", "8501"),
                         "--server.address", "0.0.0.0",
                         "--server.headless", "true"])
