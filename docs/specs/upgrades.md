# Spec: Upgrade Tracks

This spec defines the next upgrade categories after the safe MVP foundation.
Each upgrade must preserve the core product boundary: ServerOps AI Bot is a
constrained operations assistant, not a generic shell bot.

## Upgrade Principles

Always:

- Keep Telegram user-facing messages Vietnamese-first when `BOT_LANGUAGE=vi`.
- Keep command names, audit action IDs, tool names, targets, and confirmation text stable.
- Validate Telegram input, OpenAI output, tool arguments, environment values, and external SDK responses.
- Enforce RBAC before AI tool selection and again before execution.
- Use allowlists for every host-facing target.
- Audit privileged actions, AI tool calls, and emitted alerts.
- Test with mocks by default; avoid real Telegram, OpenAI, Docker, or systemd dependencies in unit tests.

Never:

- Add arbitrary shell execution.
- Let OpenAI bypass RBAC, allowlists, confirmation, or audit.
- Send secrets to OpenAI, Telegram, logs, or audit records.
- Treat Docker socket access as harmless, even when mounted read-only.
- Auto-restart, auto-cleanup, auto-deploy, or otherwise mutate the host from alert checks.

## Track A: Scheduled Read-Only Alerts

### Objective

Notify owners when the server crosses clear read-only health thresholds, without
performing any automatic remediation.

### Configuration

Initial environment variables:

```env
ENABLE_ALERTS=false
ALERT_INTERVAL_SECONDS=60
ALERT_COOLDOWN_SECONDS=900
ALERT_CPU_PERCENT=90
ALERT_RAM_PERCENT=90
ALERT_DISK_PERCENT=90
ALERT_DOCKER_ENABLED=false
```

Alerts must be disabled by default unless explicitly enabled.

### Checks

Initial checks:

- CPU percent threshold.
- RAM percent threshold.
- Disk percent threshold.

Deferred checks:

- Allowlisted Docker container stopped or unhealthy.
- Allowlisted log error spike.
- Application heartbeat/stale scheduler detection.

### Behavior

The scheduler must:

1. Run read-only checks on a bounded interval.
2. Evaluate thresholds deterministically.
3. Deduplicate repeated alerts with cooldown.
4. Send Vietnamese Telegram messages to `OWNER_IDS` only.
5. Record an audit or alert-history row for emitted alerts.
6. Suggest safe manual commands such as `/status`, `/disk`, `/docker`, or `/log`.

### Acceptance Criteria

- Disabled alerts do not start scheduler jobs.
- Only owner IDs receive automatic alerts.
- Repeated identical alerts respect cooldown.
- Alert messages are concise, Vietnamese, and sanitized.
- Alert checks do not mutate services, containers, files, or Docker state.
- Tests mock system snapshots, Telegram sends, time, and Docker clients.

### Non-Goals

- Automatic restart, cleanup, deploy, rollback, or self-healing.
- Free-form AI-generated alert checks.
- Sending alerts to admin/viewer roles by default.
- Reading non-allowlisted logs.

## Track B: AI Command Flow

### Objective

Expose a safe Telegram command flow for asking the AI to summarize logs,
explain incidents, and request approved read-only tools.

### Commands

Initial commands:

- `/ask <question>` - general operational question with bounded context.
- `/summarize_log <allowed-log-name>` - summarize a sanitized tail from an allowlisted log.
- `/incident <allowed-log-name>` - produce a concise incident-style analysis from a sanitized log tail.

Deferred commands:

- `/ask_docker <container>` - Docker-focused analysis.
- `/explain_last_error <allowed-log-name>` - narrower error explanation.

### Behavior

The command handler must:

1. Resolve the Telegram user role.
2. Reject unknown users before any OpenAI or host access.
3. Validate command arguments.
4. Build bounded, sanitized context.
5. Call the OpenAI Responses API with strict tool definitions.
6. Validate every AI tool call through the router.
7. Return a concise Vietnamese response.

### Acceptance Criteria

- Unknown users get a Vietnamese denial before OpenAI is called.
- Viewers can use read-only AI summary commands only for allowlisted targets.
- AI cannot request unregistered tools.
- AI cannot request non-allowlisted logs or containers.
- AI responses do not include secrets.
- Tests use a fake OpenAI client and fake tool calls.

## Track C: AI Tool Call Audit

### Objective

Record every AI-requested tool call and rejection in the audit database.

### Audit Fields

Each AI tool audit event should include:

- Telegram user ID.
- Role.
- Command that triggered the AI request.
- Tool name.
- Target when available.
- Result: `success`, `denied`, `failed`, or `rejected`.
- Confirmation status: `not_required`.
- Sanitized error text when failed or rejected.

### Behavior

- Audit before returning tool results to the AI orchestration layer.
- Keep full secrets out of audit rows.
- Preserve machine-stable action names such as `ai_tool.read_log`.

### Acceptance Criteria

- Successful AI tool calls create audit rows.
- Rejected unknown tools create audit rows.
- RBAC denials create audit rows.
- Allowlist denials create audit rows.
- Tests verify audit rows without real OpenAI calls.

## Track D: Mocked Full AI Loop Tests

### Objective

Prove the user-facing AI flow without depending on external APIs.

### Required Test Cases

- `/ask` rejects unknown user before OpenAI.
- `/summarize_log app` reads only allowlisted log content and redacts secrets.
- Fake AI tool call to `read_log` routes through RBAC and allowlist checks.
- Fake AI tool call to an unknown tool is rejected and audited.
- Vietnamese response text is returned while machine tokens remain unchanged.

### Non-Goals

- Real OpenAI API tests in default CI.
- Real Telegram network tests in default CI.
- Real Docker daemon tests in default CI.

## Track E: Dependency Locking

### Objective

Make local and Docker builds reproducible.

### Preferred Approach

Use one lock workflow consistently:

- Option 1: `uv.lock` with `uv sync` and Docker installation from the lock.
- Option 2: `requirements.lock` generated by `pip-tools`.

Pick one; do not maintain both unless there is a documented reason.

### Acceptance Criteria

- Docker build installs locked dependency versions.
- Local install instructions match the selected lock workflow.
- CI/test commands use the same dependency set.
- Security update workflow is documented.

## Track F: Docker Socket Safety

### Objective

Reduce risk from mounting `/var/run/docker.sock`.

### Options

Preferred progression:

1. Add `ENABLE_DOCKER_TOOLS=false` default for deployments that do not need Docker commands.
2. Fail Docker commands with a clear Vietnamese message when disabled.
3. Document the risk of Docker socket access.
4. Consider a Docker socket proxy that allowlists read-only endpoints.

### Acceptance Criteria

- Docker commands are disabled unless explicitly enabled.
- `/docker` and `/docker_logs` fail safely when disabled.
- Docker socket mount guidance is explicit in docs.
- Tests cover enabled and disabled modes.

## Track G: Owner Audit Command

### Objective

Let the owner inspect recent audit events from Telegram during incidents.

### Command

- `/audit [limit]`

### Behavior

- Owner only.
- Limit is optional, bounded, and defaults to 10.
- Output is concise and Vietnamese.
- Secrets and long errors are redacted or truncated.
- Viewer/admin/unknown users are denied and denied attempts are audited when appropriate.

### Acceptance Criteria

- Owner can view recent audit rows.
- Admin/viewer/unknown cannot view audit rows.
- Limit validation rejects invalid or excessive values.
- Output includes timestamp, role, action/tool, target, result, and sanitized error summary.

## Recommended Implementation Order

1. Track A: scheduled read-only alerts.
2. Track B: AI command flow.
3. Track C: AI tool call audit.
4. Track D: mocked full AI loop tests.
5. Track G: owner audit command.
6. Track E: dependency locking.
7. Track F: Docker socket safety.

Rationale: owner alerts provide high operational value with limited risk when
kept read-only. Then finish the incomplete Phase 4 AI user flow and make it
auditable and provable. Audit visibility helps operate the system. Reproducible
builds and Docker socket hardening are important before production expansion.
