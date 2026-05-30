# AI / ML Projects

A growing collection of AI, ML, and MLOps projects — each self-contained in its own folder.

---

## Projects

| # | Project | Description | Stack |
|---|---------|-------------|-------|
| 01 | [aiops-sentinel](./aiops-sentinel/) | LLM-powered infrastructure EOL monitoring | Airflow · FastAPI · Ollama · Docker |

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
└── <your-next-project>/    ← project 02, 03, ...
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
