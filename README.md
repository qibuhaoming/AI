# AI Text Assistant

A tiny, self-contained **text-analysis assistant**. It exposes a JSON API and a
small web UI that computes sentiment, keywords, and reading stats for any text —
entirely offline, with no external model or API key required.

## Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/)
- **Frontend:** static HTML/CSS/JS served by the backend
- **Tests:** pytest
- **Lint:** ruff
- **Python:** 3.12+

## Getting started

```bash
# 1. Create a virtualenv and install dependencies
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt

# 2. Run the dev server
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open http://localhost:8000 in your browser.

## API

| Method | Path           | Description                        |
| ------ | -------------- | ---------------------------------- |
| GET    | `/api/health`  | Health check                       |
| POST   | `/api/analyze` | Analyze a block of text            |
| GET    | `/`            | Web UI                             |

Example:

```bash
curl -s -X POST http://localhost:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text": "I really love this project, it works great!"}'
```

## Development

```bash
# Run the tests
.venv/bin/pytest

# Lint
.venv/bin/ruff check .
```

## Cloud Agent environment

This repository ships a [`.cursor/environment.json`](.cursor/environment.json)
that installs dependencies into `.venv` and runs the dev server on port 8000, so
Cloud Agents can build, test, and run the app out of the box.
