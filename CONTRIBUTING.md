# Contributing to Robot Motion Player

Thank you for your interest in contributing to Robot Motion Player!

## Development Setup

```bash
# Clone repository
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[all,dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .
```

## Prerequisites

- Python 3.9+
- MuJoCo 3.0+ (for playback backend)
- Pinocchio (optional, for IK backend)

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Line length: 100 characters
- All public APIs should have docstrings (Google style)
- Run `ruff format` before committing

### Docstring Example

```python
def load_motion(filepath: str, format: str = "auto") -> MotionData:
    """Load motion data from file.

    Args:
        filepath: Path to motion file (.pkl, .npz, etc.)
        format: File format. If "auto", infer from extension.

    Returns:
        MotionData object containing joint positions and timestamps.

    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If format is unsupported.
    """
    pass
```

## Pull Request Process

1. Fork and create a feature branch from `main`
2. Ensure all tests pass: `pytest`
3. Add tests for new functionality
4. Update documentation:
   - Docstrings for new APIs
   - README.md if adding user-facing features
   - docs/ for detailed guides
5. Submit PR with a clear description of changes and motivation

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`ruff format`)
- [ ] No linting errors (`ruff check`)
- [ ] Docstrings added for new public APIs
- [ ] README updated if needed

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Test additions/changes |
| `refactor:` | Code restructuring |
| `perf:` | Performance improvement |
| `chore:` | Maintenance tasks |

### Examples

```
feat: add support for URDF robot models
fix: resolve IK solver convergence issue for near-singular poses
docs: add quick start guide with example data
test: add unit tests for motion data loader
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=motion_player

# Run specific test file
pytest tests/core/test_dataset.py

# Run specific test
pytest tests/core/test_dataset.py::test_load_motion
```

### Test Categories

- `tests/core/` - Core functionality (loader, metrics, IK)
- `tests/backends/` - MuJoCo and Isaac backends
- `tests/gui/` - GUI components
- `tests/cli/` - CLI commands

### Markers

```bash
# Skip tests requiring MuJoCo display
pytest -m "not mujoco_runtime"

# Run only headless integration tests
pytest -m "headless_integration"
```

## Project Structure

```
robot-motion-player/
├── motion_player/          # Main package
│   ├── core/              # Core algorithms (loader, metrics, IK)
│   ├── backends/          # Physics backends (MuJoCo, Isaac)
│   ├── gui/               # Dear PyGui interface
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
├── docs/                  # Documentation
├── example/               # Example assets
│   ├── robots/           # Robot models
│   └── standard_dataset/ # Sample motion data
└── assets/               # Demo media
```

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about usage
- Discussions about architecture

Thank you for contributing! 🦞
