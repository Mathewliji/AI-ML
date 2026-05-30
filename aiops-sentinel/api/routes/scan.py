"""
/scan endpoints — trigger a new EOL scan and retrieve results.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from scanner.eol_checker import EOLChecker
from scanner.llm_analyzer import LLMAnalyzer
from scanner.models import ScanReport, ScanRequest
from scanner.notifier import send_slack_alert

router = APIRouter()

# In-memory store for demo purposes.
# In production, swap with Redis or PostgreSQL.
_scan_store: dict[str, ScanReport] = {}

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")


def _run_scan(scan_id: str, request: ScanRequest) -> ScanReport:
    llm = LLMAnalyzer(host=OLLAMA_HOST, model=OLLAMA_MODEL)
    checker = EOLChecker(llm_analyzer=llm, days_warn=request.days_warn)

    results = checker.check_batch(request.items)
    at_risk_count = sum(1 for r in results if r.is_at_risk)

    report = ScanReport(
        scan_id=scan_id,
        scanned_at=datetime.now(timezone.utc).isoformat(),
        total=len(results),
        at_risk=at_risk_count,
        results=results,
    )

    _scan_store[scan_id] = report

    if request.notify_slack and SLACK_WEBHOOK:
        at_risk_dicts = [r.model_dump() for r in results if r.is_at_risk]
        ai_summary = llm.summarize_risks(at_risk_dicts) if at_risk_dicts else None
        send_slack_alert(report, SLACK_WEBHOOK, ai_summary)

    return report


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class ScanResponse(BaseModel):
    scan_id: str
    message: str


@router.post("/", response_model=ScanResponse, status_code=202)
async def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Trigger an asynchronous EOL scan for a list of software components.

    Returns a `scan_id` you can use to poll `/scan/{scan_id}` for results.

    **Example request body:**
    ```json
    {
      "items": [
        {"name": "nginx", "version": "1.20"},
        {"name": "redis", "version": "6.2"},
        {"name": "python", "version": "3.9"}
      ],
      "days_warn": 45,
      "notify_slack": false
    }
    ```
    """
    scan_id = str(uuid.uuid4())
    background_tasks.add_task(_run_scan, scan_id, request)
    return ScanResponse(scan_id=scan_id, message="Scan started. Poll /scan/{scan_id} for results.")


@router.get("/{scan_id}", response_model=ScanReport)
async def get_scan_result(scan_id: str):
    """Retrieve the results of a previously triggered scan."""
    report = _scan_store.get(scan_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id!r} not found or still running.")
    return report


@router.post("/sync", response_model=ScanReport)
async def scan_sync(request: ScanRequest):
    """
    Run a synchronous (blocking) EOL scan and return full results immediately.

    Suitable for small batches (< 20 items). Use the async `/scan/` endpoint
    for larger workloads.
    """
    scan_id = str(uuid.uuid4())
    return _run_scan(scan_id, request)
