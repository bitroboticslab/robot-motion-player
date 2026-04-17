.PHONY: help install-dev lint test test-quick check precommit release-check

.DEFAULT_GOAL := help

PIP ?= pip

help: ## Show available development targets
	@echo "robot-motion-player development commands"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-dev: ## Install package with development dependencies
	$(PIP) install -e ".[dev]"

lint: ## Run Ruff lint checks
	ruff check motion_player tests

test: ## Run full pytest suite
	pytest tests/ -v --tb=short

test-quick: ## Run targeted fast test subset
	pytest tests/gui/test_dearpygui_panel.py tests/backends/test_mujoco_viewer.py tests/core/test_ui.py -q

check: lint test ## Run lint and tests

precommit: ## Run pre-commit on all files
	pre-commit run --all-files

release-check: lint test ## Run release checks and verify version markers
	python scripts/release/check_release_markers.py
