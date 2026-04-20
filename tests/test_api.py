"""Integration-style tests for the FastAPI endpoints — no live network calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from scanner.models import EOLResult, EOLStatus, ScanReport


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Synchronous scan endpoint
# ---------------------------------------------------------------------------

@patch("api.routes.scan.EOLChecker")
def test_sync_scan_returns_results(mock_checker_cls, client):
    mock_result = EOLResult(
        name="nginx",
        version="1.24",
        eol_date="2099-01-01",
        status=EOLStatus.OK,
        days_remaining=27000,
        source="api",
    )
    mock_checker_cls.return_value.check_batch.return_value = [mock_result]

    payload = {"items": [{"name": "nginx", "version": "1.24"}]}
    resp = client.post("/scan/sync", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["at_risk"] == 0
    assert body["results"][0]["name"] == "nginx"
    assert body["results"][0]["status"] == "ok"


@patch("api.routes.scan.EOLChecker")
def test_sync_scan_flags_expired(mock_checker_cls, client):
    mock_result = EOLResult(
        name="debian",
        version="9",
        eol_date="2022-06-30",
        status=EOLStatus.EXPIRED,
        days_remaining=-700,
        source="api",
    )
    mock_checker_cls.return_value.check_batch.return_value = [mock_result]

    payload = {"items": [{"name": "debian", "version": "9"}]}
    resp = client.post("/scan/sync", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["at_risk"] == 1


# ---------------------------------------------------------------------------
# Async scan + polling
# ---------------------------------------------------------------------------

@patch("api.routes.scan.EOLChecker")
def test_async_scan_and_poll(mock_checker_cls, client):
    mock_result = EOLResult(
        name="redis",
        version="7.0",
        eol_date="2099-01-01",
        status=EOLStatus.OK,
        days_remaining=27000,
        source="api",
    )
    mock_checker_cls.return_value.check_batch.return_value = [mock_result]

    # Start the scan
    payload = {"items": [{"name": "redis", "version": "7.0"}]}
    start_resp = client.post("/scan/", json=payload)
    assert start_resp.status_code == 202
    scan_id = start_resp.json()["scan_id"]
    assert scan_id

    # Poll (TestClient runs tasks synchronously so result is immediate)
    poll_resp = client.get(f"/scan/{scan_id}")
    assert poll_resp.status_code == 200
    body = poll_resp.json()
    assert body["scan_id"] == scan_id


def test_poll_unknown_scan_id(client):
    resp = client.get("/scan/nonexistent-id-xyz")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Reports endpoints
# ---------------------------------------------------------------------------

@patch("api.routes.scan.EOLChecker")
def test_reports_list_after_sync_scan(mock_checker_cls, client):
    mock_result = EOLResult(
        name="python",
        version="3.11",
        eol_date="2027-10-01",
        status=EOLStatus.OK,
        days_remaining=500,
        source="api",
    )
    mock_checker_cls.return_value.check_batch.return_value = [mock_result]

    client.post("/scan/sync", json={"items": [{"name": "python", "version": "3.11"}]})

    resp = client.get("/reports/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1
