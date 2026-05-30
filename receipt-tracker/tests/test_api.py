import io
import json
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

FAKE_GRAPH_RESULT = {
    "task": "upload",
    "image_b64": None,
    "image_media_type": None,
    "receipt_data": {
        "merchant": "Test Café",
        "date": "2024-05-01",
        "items": [],
        "subtotal": 10.00,
        "tax": 0.80,
        "total": 10.80,
        "currency": "USD",
    },
    "category": "food",
    "receipt_id": 1,
    "user_message": None,
    "response": "✅ Receipt saved!\n\n🏪 **Test Café**",
    "error": None,
}


@patch("api.routes.receipts.graph")
def test_upload_receipt_success(mock_graph):
    mock_graph.invoke.return_value = FAKE_GRAPH_RESULT

    image_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG header
    response = client.post(
        "/receipts/upload",
        files={"file": ("receipt.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "food"
    assert body["receipt_id"] == 1
    assert "Test Café" in body["message"]


@patch("api.routes.receipts.graph")
def test_upload_receipt_rejects_pdf(mock_graph):
    response = client.post(
        "/receipts/upload",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
    )
    assert response.status_code == 400


@patch("api.routes.receipts.graph")
def test_chat_endpoint(mock_graph):
    mock_graph.invoke.return_value = {**FAKE_GRAPH_RESULT, "task": "query", "response": "You spent $42.00 on food."}
    response = client.post("/receipts/chat", json={"message": "How much did I spend on food?"})

    assert response.status_code == 200
    assert "42.00" in response.json()["response"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
