"""
docker_eol_monitor — Airflow 3.x DAG
=====================================
Runs on a weekly schedule.  Reads a YAML/JSON inventory of Docker base
images, checks every component against the public endoflife.date API with
an Ollama LLM as fallback, and fires a Slack alert when at-risk items are
found.

Fan-out pattern (dynamic task mapping):
    load_inventory → check_eol.expand(item=...) → aggregate → notify

This DAG intentionally uses only public APIs and the Ollama SDK so it can
be run by anyone with Docker — no private credentials required beyond the
optional Slack webhook.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import pendulum
from airflow.sdk import DAG, Param, Variable, task

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers — graceful fallbacks so the DAG works without any Variables
# ---------------------------------------------------------------------------

def _var(key: str, default: str = "") -> str:
    try:
        return Variable.get(key, default_var=default)
    except Exception:
        return default


OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DAYS_WARN    = int(os.getenv("DAYS_WARN", "45"))

# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="docker_eol_monitor",
    schedule="0 8 * * 1",          # Every Monday at 08:00 UTC
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["eol", "docker", "security", "aiops"],
    params={
        "days_warn": Param(
            default=DAYS_WARN,
            type="integer",
            minimum=1,
            maximum=365,
            description="Flag items with fewer than this many days until EOL.",
        ),
        "inventory": Param(
            default=[
                {"name": "nginx",   "version": "1.20"},
                {"name": "redis",   "version": "6.2"},
                {"name": "python",  "version": "3.9"},
                {"name": "postgres","version": "13"},
                {"name": "debian",  "version": "10"},
                {"name": "node",    "version": "16"},
            ],
            type="array",
            description="List of {name, version} dicts to scan.",
        ),
    },
    doc_md=__doc__,
) as dag:

    # -----------------------------------------------------------------------
    # Task 1 — Load inventory (from DAG params or Airflow Variable)
    # -----------------------------------------------------------------------

    @task()
    def load_inventory(**context) -> list[dict]:
        """Return the list of {name, version} items to scan."""
        params = context["params"]
        inventory = params.get("inventory")

        # Allow overriding via Airflow Variable for production use
        variable_inventory = _var("AIOPS_SENTINEL_INVENTORY", "")
        if variable_inventory:
            try:
                inventory = json.loads(variable_inventory)
                log.info("Loaded %d items from Airflow Variable.", len(inventory))
            except json.JSONDecodeError:
                log.warning("AIOPS_SENTINEL_INVENTORY is not valid JSON — using params.")

        log.info("Inventory loaded: %d items", len(inventory))
        return inventory

    # -----------------------------------------------------------------------
    # Task 2 — Check EOL for a single item (dynamically mapped)
    # -----------------------------------------------------------------------

    @task()
    def check_eol(item: dict, **context) -> dict:
        """
        Check a single {name, version} against endoflife.date with LLM fallback.
        Mapped dynamically over every item in the inventory.
        """
        # Import here so Airflow workers only need these packages installed
        from scanner.eol_checker import EOLChecker
        from scanner.llm_analyzer import LLMAnalyzer

        days_warn = context["params"].get("days_warn", DAYS_WARN)

        llm = LLMAnalyzer(host=OLLAMA_HOST, model=OLLAMA_MODEL)
        checker = EOLChecker(llm_analyzer=llm, days_warn=days_warn)

        result = checker.check(item["name"], item["version"])
        log.info(
            "%-20s %-10s → %-10s (EOL: %s, %d days, source: %s)",
            result.name, result.version, result.status.value,
            result.eol_date, result.days_remaining, result.source,
        )
        return result.model_dump()

    # -----------------------------------------------------------------------
    # Task 3 — Aggregate all results into a summary
    # -----------------------------------------------------------------------

    @task()
    def aggregate(results: list[dict], **context) -> dict:
        """Combine per-item results into a scan report."""
        scan_id = context["run_id"]
        at_risk = [r for r in results if r["status"] in ("expired", "critical", "unknown")]

        report = {
            "scan_id": scan_id,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "at_risk": len(at_risk),
            "results": results,
        }
        log.info(
            "Scan complete — %d total, %d at risk.", report["total"], report["at_risk"]
        )
        return report

    # -----------------------------------------------------------------------
    # Task 4 — Generate AI risk narrative
    # -----------------------------------------------------------------------

    @task()
    def generate_narrative(report: dict) -> str:
        """Ask the LLM to produce a plain-English risk summary."""
        from scanner.llm_analyzer import LLMAnalyzer

        at_risk = [r for r in report["results"] if r["status"] in ("expired", "critical", "unknown")]
        if not at_risk:
            return "✅ All components are within their support lifecycle."

        llm = LLMAnalyzer(host=OLLAMA_HOST, model=OLLAMA_MODEL)
        return llm.summarize_risks(at_risk)

    # -----------------------------------------------------------------------
    # Task 5 — Send Slack alert (optional; skipped if webhook not configured)
    # -----------------------------------------------------------------------

    @task()
    def notify(report: dict, narrative: str) -> None:
        """Send a Slack alert if SLACK_WEBHOOK_URL is configured."""
        from scanner.models import EOLResult, EOLStatus, ScanReport
        from scanner.notifier import send_slack_alert

        webhook = _var("SLACK_WEBHOOK_URL", os.getenv("SLACK_WEBHOOK_URL", ""))
        if not webhook:
            log.info("SLACK_WEBHOOK_URL not set — skipping notification.")
            return

        # Reconstruct the typed ScanReport from the XCom dict
        typed_results = [
            EOLResult(
                name=r["name"],
                version=r["version"],
                eol_date=r.get("eol_date"),
                status=EOLStatus(r["status"]),
                days_remaining=r.get("days_remaining", -1),
                source=r.get("source", "unknown"),
            )
            for r in report["results"]
        ]
        typed_report = ScanReport(
            scan_id=report["scan_id"],
            scanned_at=report["scanned_at"],
            total=report["total"],
            at_risk=report["at_risk"],
            results=typed_results,
        )
        send_slack_alert(typed_report, webhook, ai_summary=narrative)

    # -----------------------------------------------------------------------
    # Wire up the DAG
    # -----------------------------------------------------------------------
    inventory   = load_inventory()
    eol_results = check_eol.expand(item=inventory)   # ← dynamic task mapping
    report      = aggregate(eol_results)
    narrative   = generate_narrative(report)
    notify(report, narrative)
