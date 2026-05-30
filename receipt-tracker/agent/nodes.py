import json
import datetime
import anthropic
from sqlalchemy import func
from agent.state import AgentState
from db.database import SessionLocal
from db.models import Receipt, LineItem

_client = anthropic.Anthropic()

EXTRACTION_SYSTEM = """\
You are a receipt data extractor. Extract structured information from receipt images.
Always respond with valid JSON — no markdown fences, no extra text — matching this schema exactly:
{
  "merchant": "string",
  "date": "YYYY-MM-DD or empty string if not visible",
  "items": [
    {"description": "string", "quantity": number, "unit_price": number, "total": number}
  ],
  "subtotal": number,
  "tax": number,
  "total": number,
  "currency": "3-letter ISO code e.g. USD"
}
Use 0 for any number not visible. Use an empty list for items if none are legible."""


# ── extract ───────────────────────────────────────────────────────────────────

def extract_node(state: AgentState) -> AgentState:
    try:
        response = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": EXTRACTION_SYSTEM,
                "cache_control": {"type": "ephemeral"},   # cache prompt across receipts
            }],
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": state["image_media_type"] or "image/jpeg",
                            "data": state["image_b64"],
                        },
                    },
                    {"type": "text", "text": "Extract all receipt data as JSON."},
                ],
            }],
        )

        raw = response.content[0].text
        start, end = raw.find("{"), raw.rfind("}") + 1
        state["receipt_data"] = json.loads(raw[start:end])
        state["error"] = None
    except Exception as exc:
        state["error"] = f"Extraction failed: {exc}"

    return state


# ── categorise ────────────────────────────────────────────────────────────────

VALID_CATEGORIES = frozenset(
    {"food", "travel", "shopping", "utilities", "healthcare", "entertainment", "other"}
)


def categorise_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("receipt_data"):
        return state

    data = state["receipt_data"]
    item_names = ", ".join(i.get("description", "") for i in data.get("items", []))

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                f"Merchant: {data.get('merchant', 'unknown')}\n"
                f"Items: {item_names or 'not listed'}\n\n"
                "Reply with ONE word — the spending category that best fits:\n"
                "food | travel | shopping | utilities | healthcare | entertainment | other"
            ),
        }],
    )

    raw = response.content[0].text.strip().lower()
    state["category"] = raw if raw in VALID_CATEGORIES else "other"
    return state


# ── save ──────────────────────────────────────────────────────────────────────

def save_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("receipt_data"):
        return state

    data = state["receipt_data"]
    db = SessionLocal()
    try:
        receipt = Receipt(
            merchant=data.get("merchant", "Unknown"),
            date=data.get("date", ""),
            subtotal=float(data.get("subtotal", 0)),
            tax=float(data.get("tax", 0)),
            total=float(data.get("total", 0)),
            currency=data.get("currency", "USD"),
            category=state.get("category", "other"),
            raw_text=json.dumps(data),
        )
        db.add(receipt)
        db.flush()  # get the id before commit

        for item in data.get("items", []):
            db.add(LineItem(
                receipt_id=receipt.id,
                description=item.get("description", ""),
                quantity=float(item.get("quantity", 1)),
                unit_price=float(item.get("unit_price", 0)),
                total=float(item.get("total", 0)),
            ))

        db.commit()
        state["receipt_id"] = receipt.id
    except Exception as exc:
        db.rollback()
        state["error"] = f"Save failed: {exc}"
    finally:
        db.close()

    return state


# ── query ─────────────────────────────────────────────────────────────────────

def query_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        since = datetime.datetime.utcnow() - datetime.timedelta(days=30)

        rows = (
            db.query(Receipt.category, func.sum(Receipt.total), func.count(Receipt.id))
            .filter(Receipt.created_at >= since)
            .group_by(Receipt.category)
            .all()
        )

        summary = {
            (cat or "other"): {"total": round(float(tot), 2), "count": int(cnt)}
            for cat, tot, cnt in rows
        }
        grand_total = round(sum(v["total"] for v in summary.values()), 2)

        response = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    f"User question: {state['user_message']}\n\n"
                    f"Spending data — last 30 days by category:\n{json.dumps(summary, indent=2)}\n"
                    f"Grand total: {grand_total}\n\n"
                    "Answer the question in a friendly, concise way. "
                    "Use emojis. Show currency totals with 2 decimal places."
                ),
            }],
        )

        state["response"] = response.content[0].text
    except Exception as exc:
        state["error"] = f"Query failed: {exc}"
    finally:
        db.close()

    return state


# ── respond ───────────────────────────────────────────────────────────────────

def respond_node(state: AgentState) -> AgentState:
    if state.get("error"):
        state["response"] = f"❌ {state['error']}"
        return state

    if state["task"] == "query":
        return state  # response already set by query_node

    data = state["receipt_data"]
    items = data.get("items", [])
    item_lines = "\n".join(
        f"  • {i.get('description', '—')} × {i.get('quantity', 1)} — "
        f"{data.get('currency', '')} {i.get('total', 0):.2f}"
        for i in items
    ) or "  (no line items detected)"

    CATEGORY_EMOJI = {
        "food": "🍔", "travel": "✈️", "shopping": "🛍️",
        "utilities": "💡", "healthcare": "🏥", "entertainment": "🎬", "other": "📦",
    }
    cat = state.get("category", "other")
    emoji = CATEGORY_EMOJI.get(cat, "📦")

    state["response"] = (
        f"✅ *Receipt saved!*\n\n"
        f"🏪 **{data.get('merchant', 'Unknown')}**\n"
        f"📅 {data.get('date', 'Date unknown')}\n"
        f"{emoji} Category: **{cat}**\n"
        f"💰 Total: **{data.get('currency', '')} {data.get('total', 0):.2f}**\n\n"
        f"*Items:*\n{item_lines}"
    )
    return state
