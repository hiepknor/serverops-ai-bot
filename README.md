# ServerOps AI Bot

Telegram bot for safe Linux, Docker, log, monitoring, and AI-assisted server
operations. The bot is intentionally constrained: all host actions must pass
through allowlisted tools, RBAC, confirmations, and audit logging.

ServerOps AI Bot is built for one personal server, VPS, homelab, or lightweight
production box. It is not a generic shell bot.

## What Works Today

- Read-only system status: `/status`, `/health`, `/cpu`, `/ram`, `/disk`, `/uptime`
- Allowlisted log reads: `/log <name>`, `/errors`, `/nginx_errors`
- Docker status/log reads, disabled by default: `/docker`, `/docker_logs <container>`
- Confirmed restart actions: `/restart <service>`, `/docker_restart <container>`
- AI help through OpenAI Responses API: `/ask`, `/summarize_log`, `/incident`
- Scheduled read-only CPU/RAM/disk alerts to owners, disabled by default
- Owner audit inspection: `/audit [limit]`
- Docker Compose and systemd deployment examples

Planned but not implemented here: deploy/pull/rebuild workflows, arbitrary
service start/stop, backup automation, multi-server support, web dashboard, and
self-healing actions.

## Safety Model

The model may analyze logs, summarize incidents, and request approved tools. It
cannot execute arbitrary shell commands, access secrets, bypass RBAC, bypass
confirmation gates, or invent tool targets.

Runtime flow:

```txt
Telegram -> RBAC/Auth -> OpenAI Responses API -> Tool Router -> Allowlisted Tools
```

Security boundaries:

- Telegram users are resolved to owner, admin, viewer, or unknown.
- Unknown users are denied before OpenAI or host access.
- Read-only tools still require RBAC and allowlisted targets.
- Restart actions require exact confirmation text.
- Docker tools are disabled by default with `ENABLE_DOCKER_TOOLS=false`.
- Secrets are redacted before Telegram responses, AI context, logs, and audit rows.
- Privileged actions and AI tool calls are audited.

## Roles And Commands

| Command | Owner | Admin | Viewer | Notes |
| --- | --- | --- | --- | --- |
| `/status` | yes | yes | yes | CPU, RAM, disk, uptime summary |
| `/health` | yes | yes | yes | Warns on high CPU/RAM/disk |
| `/cpu`, `/ram`, `/disk`, `/uptime` | yes | yes | yes | Single metric commands |
| `/log <name>` | yes | yes | yes | `name` must be in `ALLOWED_LOG_FILES` |
| `/errors`, `/nginx_errors` | yes | yes | yes | Predefined allowlisted log names |
| `/docker` | yes | yes | yes | Requires `ENABLE_DOCKER_TOOLS=true` |
| `/docker_logs <container>` | yes | yes | yes | Container must be allowlisted |
| `/ask <question>` | yes | yes | yes | AI may request approved tools |
| `/summarize_log <name>` | yes | yes | yes | Reads sanitized allowlisted log context |
| `/incident <name>` | yes | yes | yes | Incident-style AI log summary |
| `/restart <service>` | yes | yes | no | Requires confirmation and allowlist |
| `/docker_restart <container>` | yes | yes | no | Requires Docker enabled, confirmation, allowlist |
| `/audit [limit]` | yes | no | no | Limit defaults to 10, max 50 |

## Configuration

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Required values:

```env
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
OWNER_IDS=
```

Common settings:

```env
OPENAI_MODEL=gpt-4.1-mini
DATABASE_URL=sqlite:///data/serverops.db
LOG_LEVEL=INFO
BOT_LANGUAGE=vi
SERVEROPS_INIT_ONLY=false

LOG_TAIL_LINES=200
ENABLE_DOCKER_TOOLS=false
DOCKER_LOG_TAIL_LINES=200

ENABLE_ALERTS=false
ALERT_INTERVAL_SECONDS=60
ALERT_COOLDOWN_SECONDS=900
ALERT_CPU_PERCENT=90
ALERT_RAM_PERCENT=90
ALERT_DISK_PERCENT=90
ALERT_DOCKER_ENABLED=false

ALLOWED_SERVICES=nginx
ALLOWED_CONTAINERS=nginx,api
ALLOWED_LOG_FILES=nginx_errors:/host/var/log/nginx/error.log
```

`OWNER_IDS`, `ADMIN_IDS`, `VIEWER_IDS`, `ALLOWED_SERVICES`,
`ALLOWED_CONTAINERS`, and `ALLOWED_LOG_FILES` are comma-separated.

`BOT_LANGUAGE=vi` is the default for Telegram user-facing messages. Use
`BOT_LANGUAGE=en` for English. Command names, audit action IDs, target names,
and confirmation text remain machine-stable.

## Local Development

Dependencies are pinned with `pip-tools`.

```bash
make install
make check
```

Useful commands:

```bash
make test
make lint
make init-only
make lock
```

Lock files:

- `requirements.lock` pins runtime dependencies for Docker.
- `requirements-dev.lock` pins runtime plus test/lint tooling.
- Run `make lock` after changing dependency ranges in `pyproject.toml`.

## Docker Compose Deployment

Build and start:

```bash
make docker-up
```

Inspect:

```bash
make docker-ps
make docker-logs
```

Stop:

```bash
make docker-down
```

Smoke check:

```bash
make docker-check
```

`docker-compose.yml` mounts:

- `./data:/app/data` for SQLite and runtime state.
- `/var/log:/host/var/log:ro` for allowlisted log reads.
- `/var/run/docker.sock:/var/run/docker.sock:ro` for Docker SDK access.

The Docker socket is a high-trust host boundary even when mounted read-only.
Prefer running without the socket if Docker commands are not needed. If you do
mount it, keep `ENABLE_DOCKER_TOOLS=false` until explicitly needed, keep
`ALLOWED_CONTAINERS` narrow, do not run the container as privileged, and consider
a Docker socket proxy that allowlists only the endpoints this bot needs.

## systemd Wrapper

The included `serverops-ai-bot.service` wraps Docker Compose:

```bash
sudo cp serverops-ai-bot.service /etc/systemd/system/serverops-ai-bot.service
sudo systemctl daemon-reload
sudo systemctl enable serverops-ai-bot
sudo systemctl start serverops-ai-bot
sudo systemctl status serverops-ai-bot
```

Update flow:

```bash
git pull --ff-only
make docker-up
make docker-ps
```

Rollback flow:

```bash
git log --oneline
git checkout <known-good-commit>
make docker-up
```

## Confirmation Flow

Restart commands create a pending confirmation. The bot returns exact text that
must be sent back unchanged.

Example:

```txt
/restart nginx
```

Reply exactly with the generated confirmation text:

```txt
CONFIRM RESTART SERVICE NGINX
```

Docker restart uses the Telegram-safe command name:

```txt
/docker_restart api
```

## Alerts

Scheduled alerts are disabled by default. When `ENABLE_ALERTS=true`, the bot
checks CPU, RAM, and disk thresholds on a bounded interval and sends concise
Vietnamese alerts to `OWNER_IDS` only. Alert checks are read-only and cooldown
protected.

## Audit

Audit rows include user ID, role, command/action/tool, target, result,
confirmation status, timestamp, and sanitized error text. Owners can inspect
recent rows from Telegram:

```txt
/audit
/audit 25
```

## Troubleshooting

Telegram:

- Verify `TELEGRAM_BOT_TOKEN`.
- Verify the Telegram user ID is present in `OWNER_IDS`, `ADMIN_IDS`, or `VIEWER_IDS`.
- Unknown users are intentionally denied.

OpenAI:

- Verify `OPENAI_API_KEY`.
- Confirm outbound network access from the container.
- Default tests never call the OpenAI API.

Docker:

- Keep `ENABLE_DOCKER_TOOLS=false` unless Docker commands are required.
- If Docker commands are enabled, verify the socket mount and `ALLOWED_CONTAINERS`.
- A read-only Docker socket is still powerful; prefer a socket proxy for production.

SQLite/data:

- Runtime state lives under `data/`.
- Ensure the container can write to `./data`.
- Do not commit `.env`, database files, logs, or runtime artifacts.

Logs:

- Host logs must be mounted under `/host/var/log`.
- Every readable log target must be listed as `name:path` in `ALLOWED_LOG_FILES`.

## Project Docs

- `AGENTS.md` - agent rules, safety boundaries, and workflow.
- `docs/README.md` - compact context map.
- `docs/specs/mvp.md` - MVP scope and acceptance criteria.
- `docs/specs/upgrades.md` - post-MVP upgrade tracks.
- `docs/architecture.md` - module boundaries and safe executor design.
- `docs/roadmap.md` - phased build order.
- `docs/development.md` - local development and verification commands.
