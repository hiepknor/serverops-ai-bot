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
`BOT_LANGUAGE` accepts `vi` or `en`; the default is `vi`.

For one-shot startup validation without connecting to Telegram:

```bash
SERVEROPS_INIT_ONLY=true .venv/bin/python -m app.main
```

## Commands

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m app.main
```

`app.main` initializes configuration, logging, and the SQLite audit store. Telegram/OpenAI runtime wiring is added in later phases.

Equivalent Make targets:

```bash
make install
make check
make run
```

## Docker

```bash
make docker-build
make docker-check
make docker-up
make docker-logs
make docker-down
```

`make docker-build` does not require `.env`. `make docker-check` and `make docker-up` require a populated `.env`.

`docker-compose.yml` mounts:

- `./data:/app/data` for SQLite and runtime state.
- `/var/log:/host/var/log:ro` for allowlisted log reads.
- `/var/run/docker.sock:/var/run/docker.sock:ro` for Docker SDK inspection.

The Docker socket is a high-trust host boundary even when mounted read-only. Keep `ALLOWED_CONTAINERS` narrow and do not run the container as privileged.

## Safety Defaults

- `.env`, `.venv`, `data/`, logs, and SQLite files are gitignored.
- Missing required config fails fast.
- Tests use local/mocked boundaries by default.
