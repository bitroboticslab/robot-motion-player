# RELEASING.md

This guide describes the standard OSS release workflow for `robot-motion-player`.

## 1) Pre-release checks

1. Confirm release scope and collect release notes in `CHANGELOG.md`.
2. Update the `## [Unreleased]` section and promote release entries to `## [X.Y.Z] - YYYY-MM-DD`.
3. Synchronize version markers by role:
   - `pyproject.toml`: `[project].version = "X.Y.Z"` (release version)
   - `motion_player/__init__.py`: metadata fallback `"X.Y.Z.dev0"`
   - `motion_player/cli/main.py`: `_get_version()` fallback `"X.Y.Z.dev0"`
4. Keep OSS user docs aligned with the release behavior:
   - `docs/QUICKSTART_en.md`
   - `docs/QUICKSTART_zh.md`
   - `docs/IK_USAGE.md`
5. Run validations:
   - `make release-check`
   - optional: `make precommit`

## 2) Tag and publish

1. Commit release changes (version sync, changelog, docs).
2. Create annotated tag:
   - `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push branch and tag:
   - `git push origin <branch>`
   - `git push origin vX.Y.Z`
4. Create GitHub release from `vX.Y.Z` and use the corresponding `CHANGELOG.md` section as the release body.

## 3) Post-release checks

1. Verify the Git tag and GitHub release point to the intended commit.
2. Verify version markers from local source files:
   - `motion_player --version`
3. Keep `## [Unreleased]` in `CHANGELOG.md` ready for the next cycle.
