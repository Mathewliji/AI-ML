# Receipt Tracker AI 🧾

> Upload a photo of any receipt → Claude Vision extracts every detail → LangGraph agent categorises & stores it → ask questions about your spending in plain English.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36-FF4B4B?logo=streamlit)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-blueviolet)](https://langchain-ai.github.io/langgraph/)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Why this is different from every other receipt scanner

Every OCR-based scanner extracts *text*. This one sends the image directly to **Claude Vision** — the model understands context, handles handwritten receipts, corrects OCR errors, and infers missing fields. The **LangGraph** pipeline then routes the output through categorisation, storage, and response generation as discrete, testable nodes.

---

## Architecture

```
User uploads image
        │
        ▼
  ┌─────────────────────────────────────────────────┐
  │              LangGraph Agent                    │
  │                                                 │
  │  extract_node  → categorise_node → save_node   │
  │  (Claude Vision)   (YOUR CODE)    (PostgreSQL)  │
  │                         │                       │
  │                    respond_node                 │
  └─────────────────────────────────────────────────┘
        │
        ▼
  FastAPI  ←→  Streamlit (WhatsApp-style UI)

  User asks "show me this week's food spending"
        │
        ▼
  query_node (Claude Haiku) → respond_node
```

---

## Quick Start

```bash
# 1. Clone & enter project
cd receipt-tracker

# 2. Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# 3. Start everything
docker compose up -d

# 4. Open the chat UI
open http://localhost:8501

# 5. API docs
open http://localhost:8000/docs
```

---

## Project Structure

```
receipt-tracker/
├── agent/
│   ├── state.py          # LangGraph TypedDict state
│   ├── nodes.py          # extract · categorise · save · query · respond
│   └── graph.py          # graph construction & routing
├── api/
│   ├── main.py           # FastAPI app (CORS, lifespan, DB init)
│   └── routes/
│       ├── receipts.py   # POST /receipts/upload · POST /receipts/chat · GET /receipts/
│       └── reports.py    # GET /reports/summary · /weekly · /by-category
├── db/
│   ├── database.py       # SQLAlchemy engine + session + init_db
│   └── models.py         # Receipt · LineItem
├── ui/
│   └── app.py            # Streamlit WhatsApp-style chat UI
├── tests/
│   ├── test_nodes.py     # unit tests (Anthropic client mocked)
│   └── test_api.py       # API integration tests (TestClient)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Your Contribution: `categorise_node`

The scaffolding is complete — one function is left for you to implement.

**File:** `agent/nodes.py` → `categorise_node(state)`

**Goal:** set `state["category"]` to one of:
`food` · `travel` · `shopping` · `utilities` · `healthcare` · `entertainment` · `other`

**Two approaches to consider:**

| | Option A — Rule-based | Option B — LLM-based |
|---|---|---|
| **How** | keyword dict on merchant/items | ask `claude-haiku` |
| **Cost** | free | ~20 tokens per receipt |
| **Coverage** | known merchant names | any merchant |
| **Deterministic** | yes | no |

---

## API Reference

### `POST /receipts/upload`
Multipart image upload → runs the full LangGraph pipeline.

### `POST /receipts/chat`
```json
{"message": "show me this week's food spending"}
```

### `GET /reports/summary?days=30`
Totals by category for the last N days.

### `GET /reports/weekly`
Day-by-day breakdown for the past 7 days.

### `GET /reports/by-category`
All-time totals sorted by spend.

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Vision AI | Anthropic Claude (`claude-sonnet-4-6`) |
| Agent workflow | LangGraph 0.2 |
| Spending queries | Claude Haiku (fast, cheap) |
| Backend | FastAPI + Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Frontend | Streamlit (WhatsApp-style UI) |
| Containers | Docker Compose |
| Testing | pytest + unittest.mock + FastAPI TestClient |

---

## License

MIT — see [LICENSE](../LICENSE).
