# CLAUDE.md

## Scope
- Applies to the full `robot-motion-player-oss` repository.
- Instruction precedence: system/developer rules > `AGENTS.md` > this file > default docs.

## Source of Truth (OSS)
- User onboarding: `README.md`, `docs/QUICKSTART_en.md`, `docs/QUICKSTART_zh.md`
- IK behavior and workflows: `docs/IK_USAGE.md`
- Release-facing history: `CHANGELOG.md`

## Standard Workflow
1. Install development dependencies with `make install-dev`.
2. Validate changes with:
   - `make lint`
   - `make test` (or `make test-quick` while iterating)
   - `make check` before handoff
3. For release or docs-governance updates, also run `make release-check`.
4. Update tests/docs whenever user-facing behavior changes.

## Implementation Guardrails
- State explicit assumptions when requirements are ambiguous.
- Prefer the simplest viable solution; avoid speculative abstractions.
- Keep changes surgical and within task scope.
- Keep OSS tests scoped to OSS-owned files only.

## Release-Sensitive Rules
- Keep version markers synchronized by role:
  - `pyproject.toml`: release version `X.Y.Z`
  - `motion_player/__init__.py`: metadata fallback `X.Y.Z.dev0`
  - `motion_player/cli/main.py`: `_get_version` fallback `X.Y.Z.dev0`
- Keep `CHANGELOG.md`, `docs/QUICKSTART_en.md`, `docs/QUICKSTART_zh.md`, and `docs/IK_USAGE.md` aligned with release behavior.
- Run `make release-check` before tagging.
