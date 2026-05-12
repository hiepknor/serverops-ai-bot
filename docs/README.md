# Project Docs

This directory is the compact context pack for humans and AI agents working on ServerOps AI Bot.

Read in this order:

1. `../AGENTS.md` - project rules, safety boundaries, and skill usage.
2. `specs/mvp.md` - current product scope and acceptance criteria.
3. `specs/upgrades.md` - post-MVP upgrade categories and acceptance criteria.
4. `architecture.md` - runtime boundaries and module responsibilities.
5. `roadmap.md` - main build order and checkpoints.
6. `upgrade-roadmap.md` - detailed upgrade execution plan.
7. `development.md` - local setup and verification commands.
8. `../README.md` - user-facing overview and deployment examples.

## Current Phase

The repository is in safe foundation setup. README, AGENTS, skills, docs, Python package scaffolding, config validation, RBAC, redaction, audit store, and basic tests exist.

## Source Of Truth

- Product intent: `../README.md`
- Agent behavior: `../AGENTS.md`
- MVP scope: `specs/mvp.md`
- Upgrade scope: `specs/upgrades.md`
- Build order: `roadmap.md`
- Upgrade build order: `upgrade-roadmap.md`
- Security architecture: `architecture.md`
- Local setup: `development.md`

When these files conflict, prefer the most specific file for the task and surface the conflict before editing code.
