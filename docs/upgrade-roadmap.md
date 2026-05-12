# Upgrade Roadmap

This roadmap expands the post-foundation work into small, verifiable slices.
Use it together with `docs/specs/upgrades.md`.

## U1: Scheduled Read-Only Alerts

Status: complete

- [x] Add alert configuration: `ENABLE_ALERTS`, interval, cooldown, CPU/RAM/disk thresholds.
- [x] Add read-only threshold evaluator for system snapshots.
- [x] Add scheduler startup wiring with alerts disabled by default.
- [x] Send Vietnamese Telegram alerts to `OWNER_IDS` only.
- [x] Add cooldown/dedup state to avoid repeated spam.
- [x] Record emitted alerts in audit or alert history.
- [x] Add safe command suggestions to alert text.

Checkpoint:

- [x] Disabled alerts do not register scheduler jobs.
- [x] CPU/RAM/disk threshold alerts are tested with mocked snapshots.
- [x] Owner routing is tested with fake Telegram sends.
- [x] Repeated same alert respects cooldown.
- [x] Alert checks perform no host mutation.

## U2: AI Command Flow

Status: complete

- [x] Add AI command module under `app/commands`.
- [x] Register `/ask`, `/summarize_log`, and `/incident`.
- [x] Add an AI orchestration service that accepts an injected Responses client.
- [x] Build bounded sanitized context for log-focused commands.
- [x] Route model-requested tools only through `app.ai.router`.
- [x] Return concise Vietnamese responses.

Checkpoint:

- [x] Unknown users are denied before OpenAI is called.
- [x] Viewer can summarize only allowlisted logs.
- [x] Fake OpenAI client tests cover text-only and tool-call responses.
- [x] No real OpenAI API call is required by default tests.

## U3: AI Tool Call Audit

Status: complete

- [x] Define audit action naming for AI tools, such as `ai_tool.read_log`.
- [x] Add audit recording around every AI tool call.
- [x] Audit unknown tool requests as rejected.
- [x] Audit RBAC and allowlist denials.
- [x] Sanitize error text before audit persistence.

Checkpoint:

- [x] Successful AI tool calls create audit records.
- [x] Rejected AI tool calls create audit records.
- [x] Audit rows include user, role, command, tool, target, result, and sanitized error.
- [x] Tests verify audit without real OpenAI calls.

## U4: Mocked Full AI Loop Tests

Status: complete

- [x] Add fake Responses client fixtures.
- [x] Add fake tool-call response fixtures.
- [x] Test `/ask` authorization behavior.
- [x] Test `/summarize_log` with secret redaction.
- [x] Test unknown AI tool rejection and audit.
- [x] Test Vietnamese response behavior.

Checkpoint:

- [x] Tests prove Telegram command -> AI client -> tool router -> response.
- [x] No external network, Telegram, Docker, systemd, or OpenAI dependency in default tests.
- [x] Test failures produce actionable diagnostics.

## U5: Owner Audit Command

Status: complete

- [x] Add `/audit [limit]` command.
- [x] Enforce owner-only `VIEW_AUDIT`.
- [x] Add bounded limit parsing.
- [x] Format recent audit rows for Telegram.
- [x] Redact and truncate error text.

Checkpoint:

- [x] Owner can view recent audit rows.
- [x] Non-owner roles are denied.
- [x] Invalid limits are rejected with Vietnamese usage text.
- [x] Output remains compact for mobile incident use.

## U6: Dependency Locking

Status: complete

- [x] Choose one lock strategy: `uv` or `pip-tools`.
- [x] Generate and commit the lock file.
- [x] Update local setup docs.
- [x] Update Dockerfile to install from locked dependencies.
- [x] Document dependency update workflow.

Checkpoint:

- [x] Local install and Docker build use the same locked dependency set.
- [x] `pytest`, `ruff`, Docker build, and init-only smoke checks pass from a clean environment.
- [x] Dependency update process is documented.

## U7: Docker Socket Safety

Status: complete

- [x] Add `ENABLE_DOCKER_TOOLS=false` default or documented deployment default.
- [x] Gate `/docker`, `/docker_logs`, and Docker AI tools behind that setting.
- [x] Return safe Vietnamese disabled messages.
- [x] Document Docker socket risk and safer deployment options.
- [x] Evaluate Docker socket proxy allowlisting.

Checkpoint:

- [x] Docker commands fail safely when disabled.
- [x] Docker commands work only when explicitly enabled and targets are allowlisted.
- [x] Tests cover enabled and disabled behavior.
- [x] Deployment docs explain the tradeoff clearly.

## U8: Final README Production Review

Status: complete

- [x] Review `README.md` against the implemented command set and actual files.
- [x] Remove or clearly mark planned-but-not-implemented features.
- [x] Normalize setup, `.env`, Docker Compose, systemd, and Makefile instructions.
- [x] Document all supported Telegram commands with role requirements.
- [x] Document security boundaries, confirmation behavior, audit behavior, and alert behavior.
- [x] Add a concise production runbook for install, start, update, rollback, and log inspection.
- [x] Add troubleshooting notes for Telegram, OpenAI, Docker socket, SQLite data, and permissions.
- [x] Confirm examples use Vietnamese-first user-facing behavior where applicable.

Checkpoint:

- [x] README matches actual code behavior.
- [x] A new operator can configure `.env` safely from `.env.example`.
- [x] Production startup steps are accurate for Docker Compose and systemd.
- [x] Security warnings are explicit and not buried.
- [x] Verification commands in README pass on a clean checkout.

## Production Readiness Gate

Before treating the bot as production-ready:

- [ ] All default tests pass.
- [ ] Docker image builds from locked dependencies.
- [ ] `docker compose config` passes with real `.env`.
- [ ] `SERVEROPS_INIT_ONLY=true` container smoke check passes.
- [ ] Real server `docker compose up -d --build` is tested with real Telegram/OpenAI credentials.
- [ ] No `.env`, tokens, SQLite DBs, logs, or runtime artifacts are committed.
- [ ] Docker socket exposure is explicitly accepted or mitigated.
- [ ] Scheduled alerts are explicitly enabled and tested on the real server.
- [ ] README has passed final production-use review and cleanup.
