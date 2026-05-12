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

Status: planned

- [ ] Add fake Responses client fixtures.
- [ ] Add fake tool-call response fixtures.
- [ ] Test `/ask` authorization behavior.
- [ ] Test `/summarize_log` with secret redaction.
- [ ] Test unknown AI tool rejection and audit.
- [ ] Test Vietnamese response behavior.

Checkpoint:

- [ ] Tests prove Telegram command -> AI client -> tool router -> response.
- [ ] No external network, Telegram, Docker, systemd, or OpenAI dependency in default tests.
- [ ] Test failures produce actionable diagnostics.

## U5: Owner Audit Command

Status: planned

- [ ] Add `/audit [limit]` command.
- [ ] Enforce owner-only `VIEW_AUDIT`.
- [ ] Add bounded limit parsing.
- [ ] Format recent audit rows for Telegram.
- [ ] Redact and truncate error text.

Checkpoint:

- [ ] Owner can view recent audit rows.
- [ ] Non-owner roles are denied.
- [ ] Invalid limits are rejected with Vietnamese usage text.
- [ ] Output remains compact for mobile incident use.

## U6: Dependency Locking

Status: planned

- [ ] Choose one lock strategy: `uv` or `pip-tools`.
- [ ] Generate and commit the lock file.
- [ ] Update local setup docs.
- [ ] Update Dockerfile to install from locked dependencies.
- [ ] Document dependency update workflow.

Checkpoint:

- [ ] Local install and Docker build use the same locked dependency set.
- [ ] `pytest`, `ruff`, Docker build, and init-only smoke checks pass from a clean environment.
- [ ] Dependency update process is documented.

## U7: Docker Socket Safety

Status: planned

- [ ] Add `ENABLE_DOCKER_TOOLS=false` default or documented deployment default.
- [ ] Gate `/docker`, `/docker_logs`, and Docker AI tools behind that setting.
- [ ] Return safe Vietnamese disabled messages.
- [ ] Document Docker socket risk and safer deployment options.
- [ ] Evaluate Docker socket proxy allowlisting.

Checkpoint:

- [ ] Docker commands fail safely when disabled.
- [ ] Docker commands work only when explicitly enabled and targets are allowlisted.
- [ ] Tests cover enabled and disabled behavior.
- [ ] Deployment docs explain the tradeoff clearly.

## U8: Final README Production Review

Status: planned

- [ ] Review `README.md` against the implemented command set and actual files.
- [ ] Remove or clearly mark planned-but-not-implemented features.
- [ ] Normalize setup, `.env`, Docker Compose, systemd, and Makefile instructions.
- [ ] Document all supported Telegram commands with role requirements.
- [ ] Document security boundaries, confirmation behavior, audit behavior, and alert behavior.
- [ ] Add a concise production runbook for install, start, update, rollback, and log inspection.
- [ ] Add troubleshooting notes for Telegram, OpenAI, Docker socket, SQLite data, and permissions.
- [ ] Confirm examples use Vietnamese-first user-facing behavior where applicable.

Checkpoint:

- [ ] README matches actual code behavior.
- [ ] A new operator can configure `.env` safely from `.env.example`.
- [ ] Production startup steps are accurate for Docker Compose and systemd.
- [ ] Security warnings are explicit and not buried.
- [ ] Verification commands in README pass on a clean checkout.

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
