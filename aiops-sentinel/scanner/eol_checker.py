"""
EOL Checker — queries the public endoflife.date API and falls back to an
LLM when the API has no record for a product.
"""

from __future__ import annotations

import difflib
import logging
import re
from datetime import date, datetime
from typing import Optional

import httpx

from scanner.models import EOLResult, EOLStatus

log = logging.getLogger(__name__)

EOL_API_BASE = "https://endoflife.date/api"
REQUEST_TIMEOUT = 10  # seconds


def _normalize_version(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"\d+(\.\d+){0,2}", raw)
    return m.group(0) if m else raw


def _compute_status(eol_date_str: str | None, days_warn: int = 45) -> tuple[EOLStatus, int]:
    if not eol_date_str or eol_date_str in ("Unknown", "ALIVE", "False", "None", ""):
        if eol_date_str == "ALIVE":
            return EOLStatus.ACTIVE, 99_999
        return EOLStatus.UNKNOWN, -1

    try:
        eol_dt = datetime.strptime(eol_date_str, "%Y-%m-%d").date()
        days_left = (eol_dt - date.today()).days
        if days_left < 0:
            return EOLStatus.EXPIRED, days_left
        if days_left <= days_warn:
            return EOLStatus.CRITICAL, days_left
        return EOLStatus.OK, days_left
    except ValueError:
        return EOLStatus.UNKNOWN, -1


class EOLChecker:
    """
    Checks whether a software product/version has reached End-of-Life.

    Lookup strategy:
      1. Fetch the full product catalogue from endoflife.date.
      2. Fuzzy-match the product name against the catalogue.
      3. If a match is found, query the specific version endpoint.
      4. If no match or the API returns nothing useful, delegate to the LLM.
    """

    def __init__(self, llm_analyzer=None, days_warn: int = 45):
        self._all_products: list[str] | None = None
        self.llm = llm_analyzer
        self.days_warn = days_warn

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def check(self, name: str, version: str) -> EOLResult:
        name_clean = name.strip().lower()
        ver_clean = _normalize_version(version)

        eol_date, source = self._api_lookup(name_clean, ver_clean)

        if not eol_date and self.llm:
            log.info("API lookup missed for %s %s — asking LLM", name, version)
            eol_date = self.llm.ask_eol(name, version)
            source = "llm" if eol_date else "unknown"

        status, days_left = _compute_status(eol_date, self.days_warn)

        return EOLResult(
            name=name,
            version=version,
            eol_date=eol_date,
            status=status,
            days_remaining=days_left,
            source=source,
        )

    def check_batch(self, items: list[dict]) -> list[EOLResult]:
        return [self.check(i["name"], i["version"]) for i in items]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_all_products(self) -> list[str]:
        if self._all_products is not None:
            return self._all_products
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.get(f"{EOL_API_BASE}/all.json")
                resp.raise_for_status()
                self._all_products = resp.json()
        except Exception as exc:
            log.warning("Failed to fetch product catalogue: %s", exc)
            self._all_products = []
        return self._all_products

    def _resolve_slug(self, name: str) -> Optional[str]:
        all_products = self._fetch_all_products()
        if name in all_products:
            return name
        matches = difflib.get_close_matches(name, all_products, n=1, cutoff=0.80)
        return matches[0] if matches else None

    def _api_lookup(self, name: str, version: str) -> tuple[Optional[str], str]:
        slug = self._resolve_slug(name)
        if not slug:
            return None, "no_match"

        parts = version.split(".")
        candidates: list[str] = []
        if len(parts) >= 3:
            candidates.append(".".join(parts[:3]))
        if len(parts) >= 2:
            candidates.append(".".join(parts[:2]))
        candidates.append(parts[0])
        candidates = list(dict.fromkeys(candidates))  # deduplicate, preserve order

        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            for ver in candidates:
                url = f"{EOL_API_BASE}/{slug}/{ver}.json"
                try:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        eol_val = resp.json().get("eol")
                        if eol_val is False:
                            return "ALIVE", "api"
                        return str(eol_val) if eol_val else None, "api"
                except Exception as exc:
                    log.debug("API call failed for %s/%s: %s", slug, ver, exc)

        return None, "api_miss"
