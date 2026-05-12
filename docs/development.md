# Development Setup

## Local Environment

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

## Configuration

```bash
cp .env.example .env
```

Fill these required values before running the app:

```env
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
OWNER_IDS=
```

`OWNER_IDS`, `ADMIN_IDS`, `VIEWER_IDS`, and allowlists accept comma-separated values.

## Commands

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m app.main
```

`app.main` initializes configuration, logging, and the SQLite audit store. Telegram/OpenAI runtime wiring is added in later phases.

## Safety Defaults

- `.env`, `.venv`, `data/`, logs, and SQLite files are gitignored.
- Missing required config fails fast.
- Tests use local/mocked boundaries by default.

