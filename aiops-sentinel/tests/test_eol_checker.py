"""Unit tests for the EOL checker — uses httpx mock to avoid live API calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scanner.eol_checker import EOLChecker, _compute_status, _normalize_version
from scanner.models import EOLStatus


# ---------------------------------------------------------------------------
# Pure-function tests (no network)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("1.20.4",  "1.20.4"),
    ("v3.2",    "3.2"),
    ("3.9.7-slim", "3.9.7"),
    ("latest",  "latest"),
])
def test_normalize_version(raw, expected):
    assert _normalize_version(raw) == expected


@pytest.mark.parametrize("eol_str,days_warn,expected_status", [
    ("2020-01-01", 45, EOLStatus.EXPIRED),
    ("2099-12-31", 45, EOLStatus.OK),
    ("ALIVE",      45, EOLStatus.ACTIVE),
    (None,         45, EOLStatus.UNKNOWN),
    ("Unknown",    45, EOLStatus.UNKNOWN),
])
def test_compute_status(eol_str, days_warn, expected_status):
    status, _ = _compute_status(eol_str, days_warn)
    assert status == expected_status


# ---------------------------------------------------------------------------
# EOLChecker — mocked HTTP
# ---------------------------------------------------------------------------

class TestEOLChecker:
    def _make_checker(self, api_response: dict | None = None):
        checker = EOLChecker(days_warn=45)
        # Patch internal HTTP so tests never touch the network
        checker._all_products = ["nginx", "redis", "python", "debian"]
        return checker

    @patch("scanner.eol_checker.httpx.Client")
    def test_known_product_ok(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"eol": "2099-12-31"}
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        checker = self._make_checker()
        result = checker.check("nginx", "1.24")

        assert result.name == "nginx"
        assert result.status == EOLStatus.OK
        assert result.source == "api"

    @patch("scanner.eol_checker.httpx.Client")
    def test_expired_product(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"eol": "2021-01-01"}
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        checker = self._make_checker()
        result = checker.check("python", "3.6")

        assert result.status == EOLStatus.EXPIRED
        assert result.days_remaining < 0

    @patch("scanner.eol_checker.httpx.Client")
    def test_alive_product(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"eol": False}
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        checker = self._make_checker()
        result = checker.check("redis", "7.0")

        assert result.status == EOLStatus.ACTIVE

    @patch("scanner.eol_checker.httpx.Client")
    def test_llm_fallback_triggered(self, mock_client_cls):
        """When API misses, the LLM should be called."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        mock_llm = MagicMock()
        mock_llm.ask_eol.return_value = "2023-06-01"

        checker = EOLChecker(llm_analyzer=mock_llm, days_warn=45)
        checker._all_products = []    # Force no API match

        result = checker.check("some-obscure-tool", "1.0")

        mock_llm.ask_eol.assert_called_once_with("some-obscure-tool", "1.0")
        assert result.source == "llm"

    @patch("scanner.eol_checker.httpx.Client")
    def test_batch_scan(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"eol": "2099-12-31"}
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

        checker = self._make_checker()
        items = [
            {"name": "nginx",  "version": "1.24"},
            {"name": "redis",  "version": "7.0"},
        ]
        results = checker.check_batch(items)
        assert len(results) == 2
