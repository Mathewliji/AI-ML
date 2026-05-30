import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.database import init_db
from api.routes import receipts, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Receipt Tracker AI",
    description="Claude Vision + LangGraph receipt extraction and spending analytics",
    version="1.0.0",
    lifespan=lifespan,
)

_UI_ORIGIN = os.getenv("UI_ORIGIN", "http://localhost:8501")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_UI_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(receipts.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}
