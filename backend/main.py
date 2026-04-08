from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pwr.ui import router as ui_router

app = FastAPI(title="PWR")

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(ui_router)