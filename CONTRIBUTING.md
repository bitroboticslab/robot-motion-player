# Contributing Guidelines
We welcome all contributions to Robot Motion Player! This document outlines the process and standards for contributing.
## 📋 Prerequisites
1. Python 3.9+
2. Conda (recommended for Pinocchio installation)
3. All development dependencies installed: `pip install -e ".[all,dev]" && pre-commit install`
## 🚀 Development Workflow
1. **Fork the repository** and clone your fork locally
2. **Create a new branch** for your feature/bugfix:
   - Feature branches: `feature/your-feature-name`
   - Bugfix branches: `fix/your-bugfix-name`
   - Documentation branches: `docs/your-doc-name`
3. **Make your changes** following the code standards below
4. **✅ MANDATORY: Run full local checks using official make commands BEFORE submitting PR**
   We strictly enforce using Makefile commands for consistency across all environments, DO NOT run lint/test manually:
   ```bash
   make check   # Run all required checks in one go (lint + full test suite)
   # Or run separately if you need to debug:
   make lint    # Run all pre-commit formatting & static analysis checks
   make test    # Run full unit test suite
   ```
   *All checks must pass before PR submission. CI runs exactly the same Makefile commands, so if it passes locally it will pass CI.*
5. **Commit your changes** with clear and descriptive commit messages following [Conventional Commits](https://www.conventionalcommits.org/) standard:
   - `feat: add X feature`
   - `fix: resolve Y bug`
   - `docs: update Z documentation`
   - `refactor: refactor A module`
6. **Submit a Pull Request** to the `main` branch
## 📝 PR Requirements
All PRs must meet the following criteria to be merged:
1. **CI Checks Pass**: All 9 CI checks must be green (lint, unit tests on all platforms)
2. **Description Clear**: PR description must clearly explain what the change does, why it is needed, and link to related issues if applicable
3. **Tests Added**: For new features or bugfixes, add corresponding unit tests to prevent regression
4. **Documentation Updated**: If the change affects user-facing functionality, update README and related documentation
5. **No Breaking Changes**: If your change introduces breaking changes, clearly mark it in the PR description and discuss with maintainers first
## 🎯 Code Standards
- Follow Python PEP 8 standards (enforced by Ruff)
- Keep code modular and well-commented
- Write type hints for all public functions and methods
- Keep functions small and focused (single responsibility principle)
## 🐛 Reporting Issues
When submitting issues:
1. Use the appropriate issue template (Bug Report / Feature Request / Question)
2. Provide all required information (environment details, reproduction steps, error logs)
3. For bug reports, include a minimal reproducible example if possible
## 💬 Community
If you have questions or need help:
- Open a [Discussion](https://github.com/bitroboticslab/robot-motion-player/discussions)
- Join our community chat (coming soon)
## 📄 License
By contributing to this project, you agree that your contributions will be licensed under the Apache 2.0 License.
