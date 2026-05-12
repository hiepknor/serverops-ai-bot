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

- [x] Scaffold Python package and tests.
- [x] Add config loading with required env validation.
- [x] Add structured logging and secret redaction.
- [x] Add SQLite audit store.
- [x] Add RBAC role resolver and permission matrix.

Checkpoint:

- [x] `pytest` passes.
- [x] Missing required config fails fast.
- [x] RBAC and redaction tests pass.

## Phase 2: Read-Only Operations

- [x] Add Telegram bot startup and command registration.
- [x] Implement `/status`, `/health`, `/cpu`, `/ram`, `/disk`, `/uptime`.
- [x] Implement allowlisted log reads: `/log <service>`, `/errors`, `/nginx_errors`.
- [x] Implement Docker read status: `/docker`, `/docker_logs <container>`.

Checkpoint:

- [x] Viewer can use read-only commands.
- [x] Unknown users are denied.
- [x] Log output is capped and sanitized.

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

- [x] Add Dockerfile.
- [x] Add docker-compose.yml.
- [x] Add `.env.example`.
- [x] Add systemd service example.
- [x] Add basic health check or startup validation.

Checkpoint:

- [x] Docker image builds successfully.
- [x] Container smoke check initializes SQLite audit DB with `SERVEROPS_INIT_ONLY=true`.
- [x] `docker compose config` and `docker compose build` pass with a temporary `.env`.
- [ ] `docker compose up -d --build` starts the bot on a server with real Telegram/OpenAI credentials.
- [x] Persistent data is written under `data/`.
- [x] Deployment docs match actual files.

## Later

- Multi-server support.
- Web dashboard.
- Metrics history.
- Backup automation.
- Kubernetes support.
- MCP integration.
- Self-healing workflows.
