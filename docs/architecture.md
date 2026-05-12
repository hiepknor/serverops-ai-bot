# Architecture

ServerOps AI Bot is a constrained operations assistant, not a shell bot.

## Runtime Flow

```txt
Telegram
  -> app.bot
  -> app.commands
  -> app.core.security
  -> app.ai.router
  -> app.tools
  -> app.core.executor
  -> Linux / Docker / Logs
```

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `app.main` | Process entrypoint and startup wiring. |
| `app.config` | Environment loading, validation, and safe defaults. |
| `app.bot` | Telegram application setup and command registration. |
| `app.commands` | Telegram command parsing and response formatting. |
| `app.ai` | OpenAI client, prompts, tool schemas, and tool routing. |
| `app.tools` | Narrow wrappers around system, Docker, services, git, and logs. |
| `app.core.security` | RBAC, allowlists, confirmation policy, and redaction. |
| `app.core.executor` | Timeout-bound subprocess or SDK execution. |
| `app.core.audit` | Audit records for privileged actions. |
| `app.core.alerts` | Scheduled checks and alert formatting. |
| `app.alerts` | Scheduler wiring and Telegram alert delivery. |
| `app.db` | SQLite connection and models. |

## Trust Boundaries

Untrusted:

- Telegram messages and user IDs until validated.
- OpenAI responses and tool calls.
- Log contents.
- Docker labels, names, and status strings.
- Environment variables until parsed by config schemas.

Trusted after validation:

- Pydantic config objects.
- Internal enums and allowlisted target IDs.
- Application service return types.

## Safe Executor Pattern

Executors should be small and explicit:

```txt
Input schema -> target allowlist -> role check -> optional confirmation -> operation -> sanitized result
```

Implementation rules:

- Prefer SDK calls for Docker where practical.
- Use `subprocess.run([...], shell=False, timeout=...)` when a command is necessary.
- Never concatenate user or AI text into a shell command.
- Cap log output length before sending it to Telegram or OpenAI.
- Redact secrets before logging, auditing, or returning results.

## Data Model Sketch

Minimum SQLite tables:

- `audit_events`: privileged action history.
- `confirmations`: pending dangerous-action confirmations.
- `alerts`: optional emitted alert history.

Planned upgrade tables should be added only when needed by a reviewed spec. AI
tool-call audit should reuse `audit_events` first unless querying needs prove a
separate table is warranted.

Configuration remains environment-driven; do not store secrets in SQLite.

## Deployment Shape

Default deployment is Docker Compose:

```txt
container
  /app/data -> ./data
  /host/var/log -> /var/log read-only
  /var/run/docker.sock -> Docker socket read-only when possible
```

Use systemd only as a host-level wrapper around Docker Compose.

## Upgrade Architecture Notes

- AI command flow should be implemented as a small orchestration service that can
  accept a fake Responses client in tests.
- AI tool calls must continue to enter through `app.ai.router`; command handlers
  must not execute host tools directly on behalf of model output.
- Owner audit views should read sanitized `audit_events` rows and should not expose
  raw secrets, stack traces, or unbounded error text.
- Scheduled alerts should be read-only, disabled by default, routed only to
  owners, cooldown-protected, and tested with fake clocks and fake Telegram sends.
- Docker socket access should be gated by configuration before expanding Docker
  features.
