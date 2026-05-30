import json
from unittest.mock import MagicMock, patch
import pytest
from agent.nodes import extract_node, respond_node
from agent.state import AgentState


def _base_state(**overrides) -> AgentState:
    state: AgentState = {
        "task": "upload",
        "image_b64": "aW1hZ2VkYXRh",
        "image_media_type": "image/jpeg",
        "receipt_data": None,
        "category": None,
        "receipt_id": None,
        "user_message": None,
        "response": None,
        "error": None,
    }
    state.update(overrides)
    return state


FAKE_RECEIPT = {
    "merchant": "Starbucks",
    "date": "2024-05-01",
    "items": [{"description": "Latte", "quantity": 1, "unit_price": 5.50, "total": 5.50}],
    "subtotal": 5.50,
    "tax": 0.44,
    "total": 5.94,
    "currency": "USD",
}


@patch("agent.nodes._client")
def test_extract_node_parses_json(mock_client):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(FAKE_RECEIPT))]
    mock_client.messages.create.return_value = mock_msg

    result = extract_node(_base_state())

    assert result["error"] is None
    assert result["receipt_data"]["merchant"] == "Starbucks"
    assert result["receipt_data"]["total"] == 5.94


@patch("agent.nodes._client")
def test_extract_node_handles_bad_json(mock_client):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Sorry, I can't read that image.")]
    mock_client.messages.create.return_value = mock_msg

    result = extract_node(_base_state())

    assert result["error"] is not None
    assert result["receipt_data"] is None


def test_respond_node_formats_upload_message():
    state = _base_state(
        receipt_data=FAKE_RECEIPT,
        category="food",
        receipt_id=42,
    )
    result = respond_node(state)

    assert "Starbucks" in result["response"]
    assert "food" in result["response"]
    assert "5.94" in result["response"]


def test_respond_node_formats_error():
    state = _base_state(error="DB connection refused")
    result = respond_node(state)

    assert "❌" in result["response"]
    assert "DB connection refused" in result["response"]
