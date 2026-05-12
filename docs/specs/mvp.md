# Spec: ServerOps AI Bot MVP

## Objective

Build a safe Telegram operations assistant for one Linux server or VPS. The bot should help an owner inspect health, read logs, inspect Docker status, restart allowlisted services/containers, and ask OpenAI for troubleshooting summaries without giving the model arbitrary shell access.

## Users

- Owner: full allowlisted operations, audit access, dangerous action confirmation.
- Admin: limited operational actions such as status, logs, and service restarts.
- Viewer: read-only status and log access.

## MVP Scope

### Included

- Telegram bot command handling.
- Environment-based configuration.
- RBAC for owner/admin/viewer Telegram IDs.
- SQLite audit log.
- Structured logging.
- System status commands: `/status`, `/health`, `/cpu`, `/ram`, `/disk`, `/uptime`.
- Log commands: `/log <service>`, `/errors`, `/nginx_errors`.
- Docker read commands: `/docker`, `/docker_logs <container>`.
- Allowlisted restart command: `/restart <service>`.
- OpenAI Responses API integration for log and incident summarization.
- Tool router that validates every AI tool call before execution.
- Confirmation flow for dangerous actions.
- Docker Compose deployment.

### Deferred

- Multi-server support.
- Web dashboard.
- Kubernetes support.
- Backup automation.
- Self-healing workflows.
- Metrics history beyond audit/log records.

## Tech Stack

- Python 3.11+
- python-telegram-bot
- OpenAI Responses API
- Pydantic
- APScheduler
- structlog
- psutil
- Docker SDK
- SQLite
- Docker Compose
- systemd wrapper for production hosts

## Commands

```bash
.venv/bin/python -m app.main
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
docker compose up -d --build
```

## Project Structure

```txt
app/
  main.py
  config.py
  bot.py
  ai/
  commands/
  core/
  db/
  tools/
tests/
data/
docs/
```

## Core Contracts

### Command Handler Contract

Each Telegram command should:

1. Parse command arguments.
2. Resolve user role from Telegram ID.
3. Validate authorization.
4. Call an application service or tool wrapper.
5. Write audit records for privileged or sensitive actions.
6. Return concise text suitable for mobile incident response.

### Tool Execution Contract

All host operations must pass through:

```txt
ValidatedInput -> RBAC -> Allowlist -> ConfirmationIfNeeded -> Executor -> AuditLog -> SanitizedResult
```

Direct free-form shell execution is outside MVP scope and must not be added.

### AI Contract

OpenAI may summarize logs, explain likely causes, and request approved tools. The model output is untrusted until validated by Pydantic schemas, RBAC, allowlists, and confirmation state.

## Security Boundaries

Always:

- Validate external input at boundaries.
- Use allowlists for services, containers, log files, and deploy targets.
- Redact tokens, environment values, and secrets from logs and model context.
- Require confirmation for restart, deploy, stop, rebuild, reboot, restore, or cleanup actions.
- Prefer read-only host mounts.

Never:

- Let OpenAI execute arbitrary shell commands.
- Mount the whole host filesystem.
- Commit `.env`, runtime databases, logs, tokens, or API keys.
- Treat AI output as trusted instructions.

## Testing Strategy

Prioritize fast tests for:

- Config loading and required environment variables.
- RBAC matrix.
- Command parsing.
- Tool schema validation.
- Allowlist rejection.
- Confirmation flow.
- Audit record creation.
- Secret redaction.

Use mocked executors for Docker, systemd, git, OpenAI, and Telegram APIs by default.

## Success Criteria

- A configured owner can run read-only health/status/log commands.
- Unauthorized users are rejected before any host access.
- Restart actions work only for allowlisted targets and require confirmation when configured as dangerous.
- AI summaries can inspect sanitized logs but cannot see secrets or call unapproved tools.
- Every privileged action creates an audit record.
- Docker Compose can run the bot with persistent `data/`.

## Open Questions

- Which exact services, containers, projects, and log files should be allowlisted for the first deployment?
- Should `/restart <service>` require confirmation for all roles or only non-owner roles?
- Should deployment commands be included in MVP or delayed until the safe executor is proven?
