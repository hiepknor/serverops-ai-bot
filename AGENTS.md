# Agent Guide: ServerOps AI Bot

This file defines how AI coding agents should work in this repository.

ServerOps AI Bot is a Python 3.11+ Telegram bot for safe Linux, Docker, deployment, log, monitoring, and troubleshooting workflows using OpenAI tool calling. The product goal is useful AI-assisted operations without giving the model arbitrary host control.

## Project Priorities

1. Security and least privilege come first.
2. All host actions must flow through explicit, allowlisted tools.
3. RBAC and confirmation gates are product behavior, not optional polish.
4. Logs, audit trails, and failure messages must be useful during incidents.
5. Keep the implementation small, boring, testable, and deployable by Docker Compose or systemd.

## Skill System

Project skills live in `./.skills`. Before doing non-trivial work, read `./.skills/using-agent-skills/SKILL.md` and pick the smallest relevant set.

Use these skills by default:

- `spec-driven-development`: new modules, commands, tool contracts, or multi-file behavior.
- `planning-and-task-breakdown`: features that need several implementation steps.
- `incremental-implementation`: any multi-file code change.
- `test-driven-development`: new logic, bug fixes, RBAC behavior, tool routing, parsing, and monitoring.
- `security-and-hardening`: every command, executor, RBAC, config, Telegram input, OpenAI tool call, Docker, systemd, or filesystem/log access change.
- `api-and-interface-design`: command handlers, tool schemas, module boundaries, OpenAI structured outputs, and internal service contracts.
- `debugging-and-error-recovery`: production issues, failed commands, failing containers, log analysis bugs, and regressions.
- `git-workflow-and-versioning`: commits, branches, and release preparation.
- `documentation-and-adrs`: README updates, architecture decisions, deployment docs, and security rationale.
- `ci-cd-and-automation`, `shipping-and-launch`: Docker, compose, systemd, deployment, health checks, and release work.

Only use frontend/browser skills if a future web dashboard is being built.

## Expected Architecture

Follow the README structure unless a reviewed spec changes it:

```txt
app/
  main.py
  config.py
  bot.py
  ai/
  commands/
  tools/
  core/
  db/
data/
docker-compose.yml
Dockerfile
requirements.txt
.env.example
serverops-ai-bot.service
```

Primary runtime flow:

```txt
Telegram -> RBAC/Auth -> OpenAI Responses API -> Tool Router -> Whitelist Executor -> Linux/Docker/Logs
```

Do not let implementation drift into a generic shell bot. The bot is an operations assistant with constrained actions.

## Security Boundaries

Always:

- Validate Telegram updates, command arguments, environment variables, OpenAI tool inputs, and third-party API responses with explicit schemas.
- Enforce RBAC before tool selection and again before execution.
- Keep owner/admin/viewer capabilities separate.
- Require explicit confirmation for dangerous actions such as deploy, restart, stop, rebuild, reboot, backup restore, or destructive cleanup.
- Use allowlists for services, containers, log files, deployment projects, and git working directories.
- Log sensitive actions with user, action, target, time, result, and confirmation status.
- Use read-only host mounts when possible.
- Return safe error messages to users while preserving diagnostic detail in internal logs.

Ask first:

- Adding new privileged actions.
- Changing RBAC semantics.
- Mounting more host paths or Docker socket permissions.
- Adding new external integrations.
- Changing deployment topology, service names, or production defaults.
- Storing new sensitive data.

Never:

- Add arbitrary shell execution.
- Pass free-form LLM output to `subprocess`, Docker, systemd, git, or filesystem operations.
- Expose secrets to the LLM prompt, Telegram messages, logs, or audit records.
- Commit `.env`, tokens, SSH keys, API keys, database files, or production logs.
- Run privileged containers unless the user explicitly approves a documented reason.
- Let the LLM bypass RBAC, confirmation, allowlists, or audit logging.

## Command And Tool Design

Design command handlers and OpenAI tools contract-first.

Command handlers should:

- Parse and validate user input.
- Identify the Telegram user and role.
- Call application services instead of embedding operational logic.
- Produce concise Telegram responses suitable for incident use.

Tool schemas should:

- Use Pydantic models and constrained types such as `Literal`, enums, bounded integers, and validated paths.
- Prefer IDs or allowlisted names over free-form strings.
- Include dry-run or confirmation state where an action is risky.
- Return structured results that the AI can summarize without seeing secrets.

Executors should:

- Be deterministic wrappers around specific operations.
- Avoid shell=True.
- Use argument arrays when subprocesses are necessary.
- Set timeouts.
- Capture stdout/stderr safely.
- Redact secrets and tokens before logging or returning output.

## Testing Expectations

Use tests as proof for behavior.

Prioritize tests for:

- RBAC permission matrix.
- Confirmation flow for dangerous actions.
- Tool router allowlist and rejection paths.
- Pydantic schema validation.
- Executor timeout, failure, and redaction behavior.
- Log tailing and summarization boundaries.
- Docker/service/git wrappers with mocked or local-safe execution.
- Config loading from environment variables.

Prefer fast unit tests for pure logic and medium integration tests for command routing, database, and executor boundaries. Avoid tests that require a real production Docker daemon, systemd host, Telegram API, or OpenAI API unless explicitly marked and opt-in.

## Configuration

Configuration must come from environment variables or `.env` loaded by the app. Keep `.env.example` complete and safe.

Expected variables include:

```env
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OWNER_IDS=
ADMIN_IDS=
VIEWER_IDS=
DATABASE_URL=sqlite:///data/serverops.db
LOG_LEVEL=INFO
```

Fail fast on missing required config. Do not silently run with insecure defaults for tokens, owner IDs, writable host mounts, or privileged executors.

## Observability And Audit

Use structured logging, preferably via `structlog`.

Every privileged action should produce an audit record with:

- Telegram user ID and role.
- Command or tool name.
- Target service/container/project/path.
- Confirmation status.
- Start and end time.
- Result status.
- Sanitized error text when failed.

Monitoring and alerts should be actionable: include the failing service/container, likely cause when available, and safe suggested commands.

## OpenAI Usage

Use the OpenAI Responses API with tool calling and structured outputs.

The model may:

- Analyze logs.
- Summarize incidents.
- Select approved tools.
- Explain safe next steps.

The model must not:

- Receive secrets.
- Execute free-form commands.
- Invent available services, containers, paths, or deployment targets.
- Override RBAC or confirmation requirements.

Treat model output as untrusted. Validate every tool call before execution.

## Git Workflow

Use `master` as the current default branch for this repository unless the user changes it.

Keep commits atomic:

- `docs:` for README, AGENTS.md, ADRs, and docs.
- `feat:` for product behavior.
- `fix:` for bug fixes.
- `test:` for test-only changes.
- `chore:` for tooling, dependencies, Docker, and CI.

Do not commit generated secrets, runtime databases, logs, cache directories, or local environment files.

## Definition Of Done

A change is done when:

- It matches the README product goals and this agent guide.
- Security boundaries are preserved.
- Tests or a documented verification command prove the behavior.
- Docs or examples are updated when user-facing behavior changes.
- The working tree contains only intentional changes.
