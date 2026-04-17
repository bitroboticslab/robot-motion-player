# CONTRIBUTING.md

Thanks for contributing to `robot-motion-player`.

## Source of truth

Before implementing changes, align with:
- `docs/requirements.md`
- `docs/design.md`
- `docs/summary.md`
- `AGENTS.md`

## Local workflow

1. Install development dependencies:
   - `make install-dev`
2. Run checks while iterating:
   - `make lint`
   - `make test-quick`
3. Run full validation before opening a PR:
   - `make check`

## Required checks for PRs

- Minimum: `make lint`
- Expected for functional changes: `make test`
- For release-related changes: `make release-check`
- Optional local hygiene: `make precommit`

## Changelog discipline

- Add user-visible changes under `## [Unreleased]` in `CHANGELOG.md`.
- Use Keep a Changelog sections (`Added`, `Changed`, `Fixed`).
- Keep entries concise, behavior-oriented, and scoped to the same PR.

## Release-sensitive change rules

If your change touches release/version surfaces:
- Follow `RELEASING.md`.
- Keep version markers synchronized by role:
  - `pyproject.toml` release version `X.Y.Z`
  - `motion_player/__init__.py` fallback `X.Y.Z.dev0`
  - `motion_player/cli/main.py` fallback `X.Y.Z.dev0`
- Add/update `docs/releases/vX.Y.Z.md` for the target release.

Avoid bundling unrelated refactors into release/version patches.
