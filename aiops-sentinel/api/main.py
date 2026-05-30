"""
AIOps Sentinel — FastAPI application entry point.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import chat, reports, scan

log = logging.getLogger(__name__)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s — %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("AIOps Sentinel starting up …")
    yield
    log.info("AIOps Sentinel shutting down.")


app = FastAPI(
    title="AIOps Sentinel",
    description=(
        "LLM-powered infrastructure EOL intelligence platform. "
        "Checks software components against the public endoflife.date API "
        "and falls back to a local Ollama LLM for unknown products."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router,    prefix="/scan",    tags=["Scan"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(chat.router,    prefix="/chat",    tags=["Chat"])

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "aiops-sentinel"}


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(_static_dir / "index.html"))
