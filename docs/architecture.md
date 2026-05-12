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

