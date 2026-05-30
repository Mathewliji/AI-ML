"""
LLM Analyzer — Ollama-backed fallback when the endoflife.date API
has no record for a product/version.

Uses the ollama Python SDK.  Defaults to llama3.2 (3 B, runs comfortably
on CPU) but any model pulled into the Ollama container will work.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ollama import Client

log = logging.getLogger(__name__)

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

_SYSTEM_PROMPT = """You are a Software Lifecycle Expert with comprehensive knowledge
of software release schedules, support timelines, and end-of-life (EOL) dates.
Always respond with only the requested data — no explanations unless asked."""

_EOL_PROMPT_TEMPLATE = """What is the End-of-Life (EOL) date for {name} version {version}?

Rules:
1. If this is a rolling release with no defined EOL (e.g. Arch Linux, MinIO), respond: ALIVE
2. If the version is actively supported with no announced EOL, respond: ALIVE
3. If EOL is known, respond with only the date in YYYY-MM-DD format.
4. If you are uncertain, respond: UNKNOWN
5. Respond with ONLY the date string, ALIVE, or UNKNOWN — nothing else."""


class LLMAnalyzer:
    """
    Wraps an Ollama client to answer EOL questions when the public API
    cannot provide an answer.
    """

    def __init__(self, host: str = "http://ollama:11434", model: str = "llama3.2"):
        self.client = Client(host=host)
        self.model = model

    def ask_eol(self, name: str, version: str) -> Optional[str]:
        prompt = _EOL_PROMPT_TEMPLATE.format(name=name, version=version)
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )
            raw = response["message"]["content"].strip().upper()
            log.debug("LLM response for %s %s: %r", name, version, raw)

            if "ALIVE" in raw or "SUPPORTED" in raw:
                return "ALIVE"
            date_match = _DATE_RE.search(raw)
            if date_match:
                return date_match.group(0)
            return None
        except Exception as exc:
            log.error("LLM query failed for %s %s: %s", name, version, exc)
            return None

    def summarize_risks(self, at_risk_items: list[dict]) -> str:
        """
        Generate a human-readable risk summary for Slack / email notifications.
        """
        if not at_risk_items:
            return "No at-risk items found."

        lines = "\n".join(
            f"- {i['name']} {i['version']} (status: {i['status']}, EOL: {i.get('eol_date', 'N/A')})"
            for i in at_risk_items
        )
        prompt = f"""The following software components are at or near End-of-Life:

{lines}

Write a concise (3–5 sentence) risk summary suitable for a DevOps team Slack channel.
Include urgency and recommended next steps."""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )
            return response["message"]["content"].strip()
        except Exception as exc:
            log.error("LLM summarize_risks failed: %s", exc)
            return "Could not generate AI summary."
