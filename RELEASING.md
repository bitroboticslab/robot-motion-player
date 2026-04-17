# RELEASING.md

This guide describes the standard release workflow for `robot-motion-player`.

## 1) Pre-release checks

1. Confirm release scope and prepare notes in `docs/releases/vX.Y.Z.md`.
2. Update `CHANGELOG.md`:
   - move relevant items from `[Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD`.
3. Synchronize version markers by role:
   - `pyproject.toml`: `[project].version = "X.Y.Z"` (release version)
   - `motion_player/__init__.py`: metadata fallback `"X.Y.Z.dev0"`
   - `motion_player/cli/main.py`: `_get_version()` fallback `"X.Y.Z.dev0"`
4. Run validations:
   - `make release-check`
   - optional: `make precommit`

## 2) Tag and publish

1. Commit release changes (version sync, changelog, release notes).
2. Create annotated tag:
   - `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
3. Push branch and tag:
   - `git push origin <branch>`
   - `git push origin vX.Y.Z`
4. Create GitHub release from `vX.Y.Z` and use `docs/releases/vX.Y.Z.md` as the release body.
5. For historical release backfill workflows, use:
   - `bash scripts/release/backfill_releases.sh`

## 3) Post-release checks

1. Verify the Git tag and GitHub release point to the intended commit.
2. Verify version markers from local source files:
   - `python scripts/release/check_release_markers.py`
   - optional installed-package sanity check: `motion_player --version`
3. Ensure release docs are synchronized:
   - `CHANGELOG.md`
   - `docs/releases/RELEASE_TAG_MAP.md`
4. Keep `## [Unreleased]` in `CHANGELOG.md` ready for the next cycle.
