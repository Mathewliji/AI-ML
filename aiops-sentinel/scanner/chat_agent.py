"""
Chat Agent — conversational AI over Ollama, optionally injected with
live scan context so the LLM can answer questions about the user's
specific infrastructure.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from ollama import AsyncClient

log = logging.getLogger(__name__)

_SYSTEM_TEMPLATE = """\
You are the AI assistant for AIOps Sentinel, an infrastructure \
end-of-life (EOL) monitoring platform.

You help DevOps and platform engineers understand EOL risks, \
prioritise upgrades, and plan remediation work.

{context_block}

Guidelines:
- Be concise, technical, and actionable.
- Prioritise by severity: expired > critical > unknown > ok.
- Suggest specific upgrade versions where you know them.
- Mention security implications of running EOL software.
- Use bullet points for multi-item answers.
- Keep responses under 200 words unless a detailed plan is requested.\
"""

_CONTEXT_BLOCK = """\
## Current Scan Results
Scan ID : {scan_id}
Scanned : {scanned_at}
Total   : {total}  |  At-risk : {at_risk}

Components:
{rows}
"""


class ChatAgent:
    def __init__(self, host: str = "http://ollama:11434", model: str = "llama3.2"):
        self.host = host
        self.model = model

    def _build_system(self, scan_context: dict | None) -> str:
        if not scan_context:
            return _SYSTEM_TEMPLATE.format(
                context_block=(
                    "No scan results loaded yet. Help the user understand EOL "
                    "concepts and how to use AIOps Sentinel."
                )
            )
        rows = "\n".join(
            f"  • {r['name']} v{r['version']} — {r['status'].upper()}"
            f"  (EOL: {r.get('eol_date') or 'N/A'}, {r.get('days_remaining', -1)}d)"
            for r in scan_context.get("results", [])
        )
        context_block = _CONTEXT_BLOCK.format(
            scan_id=scan_context.get("scan_id", "?"),
            scanned_at=scan_context.get("scanned_at", "?")[:19].replace("T", " "),
            total=scan_context.get("total", 0),
            at_risk=scan_context.get("at_risk", 0),
            rows=rows or "  (no results)",
        )
        return _SYSTEM_TEMPLATE.format(context_block=context_block)

    async def stream(
        self,
        messages: list[dict],
        scan_context: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        system = self._build_system(scan_context)
        full_messages = [{"role": "system", "content": system}] + messages

        client = AsyncClient(host=self.host)
        try:
            async for chunk in await client.chat(
                model=self.model,
                messages=full_messages,
                stream=True,
            ):
                content = chunk.message.content
                if content:
                    yield content
        except Exception as exc:
            log.error("ChatAgent.stream failed: %s", exc)
            yield (
                f"\n\n⚠️ Could not reach Ollama: {exc}\n\n"
                "Make sure Ollama is running:\n"
                "  docker compose up ollama\n"
                "  docker exec -it <ollama-container> ollama pull llama3.2"
            )
