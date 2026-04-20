"""Shared data models for the scanner layer."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EOLStatus(str, Enum):
    OK = "ok"              # Supported, > days_warn remaining
    CRITICAL = "critical"  # <= days_warn days remaining
    EXPIRED = "expired"    # Past EOL date
    ACTIVE = "active"      # Rolling release / no defined EOL
    UNKNOWN = "unknown"    # Could not determine


class EOLResult(BaseModel):
    name: str
    version: str
    eol_date: Optional[str] = None
    status: EOLStatus
    days_remaining: int = Field(default=-1)
    source: str = "unknown"   # "api" | "llm" | "unknown"

    @property
    def is_at_risk(self) -> bool:
        return self.status in (EOLStatus.EXPIRED, EOLStatus.CRITICAL, EOLStatus.UNKNOWN)


class ScanRequest(BaseModel):
    items: list[dict] = Field(
        ...,
        examples=[[{"name": "nginx", "version": "1.20"}, {"name": "redis", "version": "6.2"}]],
        min_length=1,
    )
    days_warn: int = Field(default=45, ge=1, le=365)
    notify_slack: bool = False


class ScanReport(BaseModel):
    scan_id: str
    scanned_at: str
    total: int
    at_risk: int
    results: list[EOLResult]

    @property
    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts
