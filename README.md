# X Digest → Methodology

Fetch the interesting posts from your **X (Twitter) following**, organize them
into **Markdown**, and synthesize a **methodology** from what you collected.

The pipeline is:

```
X following timeline  →  filter by your interests  →  organized Markdown  →  methodology.md
```

It ships with two data sources so it runs end-to-end today:

- **`x`** — the official [X API v2](https://developer.x.com/en/docs/x-api) home
  timeline (reverse-chronological posts from accounts you follow). This is the
  ToS-compliant way to read your following; it uses an OAuth 2.0 **access token**,
  never your raw account password.
- **`fixture`** — a bundled sample timeline (`xdigest/data/sample_timeline.json`)
  so the whole pipeline works offline, with no credentials, for development,
  tests, and demos.

## Stack

- **Python:** 3.12+
- **Pipeline / CLI:** `xdigest` package (`python -m xdigest`)
- **Web demo:** [FastAPI](https://fastapi.tiangolo.com/) + a small static UI
- **Tests:** pytest · **Lint:** ruff

## Getting started

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt
```

### Run the pipeline (offline demo)

```bash
.venv/bin/python -m xdigest run \
  --source fixture \
  --out output \
  --interests focus,writing,productivity,learning,leverage,habit,hiring \
  --min-engagement 100
```

This writes:

- `output/index.md` — a ranked index of the selected posts
- `output/posts/*.md` — one Markdown file per selected post
- `output/methodology.md` — the synthesized methodology

### Run against your real X following

You need an X API v2 **OAuth 2.0 user-context access token** with the
`tweet.read`, `users.read`, and `follows.read` scopes. Reading the home
timeline requires a paid X API tier (Basic or above).

```bash
export X_BEARER_TOKEN="<your-oauth2-user-access-token>"
.venv/bin/python -m xdigest run --source x --out output --interests ai,startups
```

> Set the token via the Cloud Agent **Secrets** panel (`X_BEARER_TOKEN`) rather
> than committing it. The tool never asks for your account password.

### Web demo

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- http://localhost:8000/ — text analyzer
- http://localhost:8000/digest — build a digest and view the methodology

## Development

```bash
.venv/bin/pytest        # run tests
.venv/bin/ruff check .  # lint
```

## Project layout

```
app/                FastAPI web demo (text analyzer + digest viewer)
xdigest/            The digest pipeline
  models.py         Post / Author data models
  sources/          fixture + X API v2 sources
  filtering.py      interest scoring & selection
  markdown.py       Markdown export
  methodology.py    methodology synthesis
  pipeline.py       orchestration
  cli.py            command-line interface
tests/              pytest suite (offline, fixture-based)
```

## Cloud Agent environment

This repository ships a [`.cursor/environment.json`](.cursor/environment.json)
that installs dependencies into `.venv` and runs the web demo on port 8000, so
Cloud Agents can build, test, and run the app out of the box.

## Roadmap / notes

- Interest matching and theme extraction are currently English-oriented; CJK
  support is a planned enhancement.
- An optional LLM-backed methodology synthesizer can be added behind an API key;
  the default synthesizer is heuristic and fully offline.
