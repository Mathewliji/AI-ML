"""
/reports endpoints — list and summarise completed scans.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routes.scan import _scan_store

router = APIRouter()


class ReportSummary(BaseModel):
    scan_id: str
    scanned_at: str
    total: int
    at_risk: int


@router.get("/", response_model=list[ReportSummary])
async def list_reports():
    """List all completed scans (most recent first)."""
    return [
        ReportSummary(
            scan_id=r.scan_id,
            scanned_at=r.scanned_at,
            total=r.total,
            at_risk=r.at_risk,
        )
        for r in sorted(_scan_store.values(), key=lambda x: x.scanned_at, reverse=True)
    ]


@router.get("/{scan_id}/summary")
async def report_summary(scan_id: str):
    """Get status breakdown for a specific scan."""
    report = _scan_store.get(scan_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id!r} not found.")
    return {
        "scan_id": scan_id,
        "scanned_at": report.scanned_at,
        "total": report.total,
        "at_risk": report.at_risk,
        "breakdown": report.summary,
        "at_risk_items": [r.model_dump() for r in report.results if r.is_at_risk],
    }
