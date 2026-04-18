.PHONY: help install-dev lint test test-quick check precommit release release-check

.DEFAULT_GOAL := help

PIP ?= pip
PYTEST ?= pytest

help: ## Show available development targets
	@echo "robot-motion-player development commands"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-14s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

install-dev: ## Install package with development dependencies
	$(PIP) install -e ".[dev]"

lint: ## Run Ruff lint checks
	ruff check motion_player tests

test: ## Run full pytest suite
	$(PYTEST) tests/ -v --tb=short

test-quick: ## Run targeted fast test subset
	$(PYTEST) tests/gui/test_dearpygui_panel.py tests/backends/test_mujoco_viewer.py tests/core/test_ui.py -q

check: lint test ## Run lint and tests

precommit: ## Run pre-commit on all files
	pre-commit run --all-files

release: release-check ## Run release validation gates

release-check: lint test ## Run OSS release checks
	$(PYTEST) -q tests/test_docs_version_state.py tests/test_release_backfill_state.py tests/test_roadmap_versions.py
