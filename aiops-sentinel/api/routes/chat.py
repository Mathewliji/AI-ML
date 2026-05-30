"""
/chat endpoints — streaming conversational AI over scan results.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.routes.scan import _scan_store
from scanner.chat_agent import ChatAgent

router = APIRouter()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    scan_id: Optional[str] = None


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream an AI response as Server-Sent Events.

    Supply a `scan_id` (from a previous `/scan/sync` call) to give the LLM
    full context about the scanned components so it can answer questions like
    "what should I upgrade first?" or "what are the security risks here?".
    """
    scan_context = None
    if request.scan_id and request.scan_id in _scan_store:
        scan_context = _scan_store[request.scan_id].model_dump()

    messages = [m.model_dump() for m in request.messages]
    agent = ChatAgent(host=OLLAMA_HOST, model=OLLAMA_MODEL)

    async def generate():
        try:
            async for chunk in agent.stream(messages, scan_context):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
