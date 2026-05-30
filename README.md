# AI / ML Projects

A growing collection of AI, ML, and MLOps projects — each self-contained in its own folder.

---

## Projects

| # | Project | Description | Stack |
|---|---------|-------------|-------|
| 01 | [aiops-sentinel](./aiops-sentinel/) | LLM-powered infrastructure EOL monitoring | Airflow · FastAPI · Ollama · Docker |
| 02 | [receipt-tracker](./receipt-tracker/) | WhatsApp-style AI receipt & expense tracker | Claude Vision · LangGraph · FastAPI · PostgreSQL · Streamlit |

---

## Repository Layout

```
AI-ML/
├── README.md               ← you are here (portfolio index)
├── LICENSE
├── .gitignore
├── _template/              ← copy this to start a new project
│
├── aiops-sentinel/         ← project 01
├── receipt-tracker/        ← project 02
└── <your-next-project>/    ← project 03, 04, ...
```

Each project folder is fully self-contained:
- its own `README.md`, `requirements.txt` / `package.json`
- its own `Dockerfile` / `docker-compose.yml` if needed
- its own `tests/`

---

## Starting a New Project

```bash
cp -r _template my-new-project
cd my-new-project
# edit README.md, then start building
```

---

## License

MIT — see [LICENSE](LICENSE).
