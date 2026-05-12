# Roadmap

This roadmap is intentionally small. Build one safe vertical slice at a time.

## Phase 0: Bootstrap

Status: in progress

- [x] README with product intent.
- [x] AGENTS guide.
- [x] Local `.skills` workflow pack.
- [x] MVP spec, architecture notes, and roadmap.

Checkpoint:

- [ ] Docs reviewed and accepted by project owner.

## Phase 1: Safe Foundation

- [ ] Scaffold Python package and tests.
- [ ] Add config loading with required env validation.
- [ ] Add structured logging and secret redaction.
- [ ] Add SQLite audit store.
- [ ] Add RBAC role resolver and permission matrix.

Checkpoint:

- [ ] `pytest` passes.
- [ ] Missing required config fails fast.
- [ ] RBAC and redaction tests pass.

## Phase 2: Read-Only Operations

- [ ] Add Telegram bot startup and command registration.
- [ ] Implement `/status`, `/health`, `/cpu`, `/ram`, `/disk`, `/uptime`.
- [ ] Implement allowlisted log reads: `/log <service>`, `/errors`, `/nginx-errors`.
- [ ] Implement Docker read status: `/docker`, `/docker-logs <container>`.

Checkpoint:

- [ ] Viewer can use read-only commands.
- [ ] Unknown users are denied.
- [ ] Log output is capped and sanitized.

## Phase 3: Controlled Actions

- [ ] Implement confirmation store and confirmation text matching.
- [ ] Implement `/restart <service>` for allowlisted services.
- [ ] Implement `/docker-restart <container>` for allowlisted containers.
- [ ] Audit every privileged action.

Checkpoint:

- [ ] Non-allowlisted targets are rejected.
- [ ] Dangerous actions require confirmation.
- [ ] Audit records include user, role, action, target, result, and confirmation status.

## Phase 4: AI Assistant

- [ ] Add OpenAI Responses API client.
- [ ] Define Pydantic tool schemas.
- [ ] Add tool router with RBAC and allowlist checks.
- [ ] Add log and incident summarization prompts.

Checkpoint:

- [ ] AI cannot call tools outside the approved schema.
- [ ] AI sees sanitized, bounded context only.
- [ ] Tool-call rejection paths are tested.

## Phase 5: Deployment

- [ ] Add Dockerfile.
- [ ] Add docker-compose.yml.
- [ ] Add `.env.example`.
- [ ] Add systemd service example.
- [ ] Add basic health check or startup validation.

Checkpoint:

- [ ] `docker compose up -d --build` starts the bot.
- [ ] Persistent data is written under `data/`.
- [ ] Deployment docs match actual files.

## Later

- Multi-server support.
- Web dashboard.
- Metrics history.
- Backup automation.
- Kubernetes support.
- MCP integration.
- Self-healing workflows.

