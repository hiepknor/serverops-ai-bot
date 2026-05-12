# Project Docs

This directory is the compact context pack for humans and AI agents working on ServerOps AI Bot.

Read in this order:

1. `../AGENTS.md` - project rules, safety boundaries, and skill usage.
2. `specs/mvp.md` - current product scope and acceptance criteria.
3. `architecture.md` - runtime boundaries and module responsibilities.
4. `roadmap.md` - build order and checkpoints.
5. `development.md` - local setup and verification commands.
6. `../README.md` - user-facing overview and deployment examples.

## Current Phase

The repository is in safe foundation setup. README, AGENTS, skills, docs, Python package scaffolding, config validation, RBAC, redaction, audit store, and basic tests exist.

## Source Of Truth

- Product intent: `../README.md`
- Agent behavior: `../AGENTS.md`
- MVP scope: `specs/mvp.md`
- Build order: `roadmap.md`
- Security architecture: `architecture.md`
- Local setup: `development.md`

When these files conflict, prefer the most specific file for the task and surface the conflict before editing code.
