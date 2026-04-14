#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${ENV_NAME:-rmp}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

echo "========================================"
echo " Robot Motion Player - Linux Setup"
echo "========================================"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] Conda not found. Please install Miniconda or Anaconda first."
  exit 1
fi

# Enable 'conda activate' in non-interactive shell
eval "$(conda shell.bash hook)"

echo
echo "[1/4] Creating conda environment: ${ENV_NAME}"
conda create -n "${ENV_NAME}" "python=${PYTHON_VERSION}" -y

echo
echo "[2/4] Activating environment"
conda activate "${ENV_NAME}"

echo
echo "[3/4] Upgrading pip"
python -m pip install --upgrade pip setuptools wheel

echo
echo "[4/4] Installing Robot Motion Player"
if [[ -f "pyproject.toml" ]]; then
  echo "Installing from source (editable mode)"
  pip install -e ".[all]"
else
  echo "Installing from PyPI"
  pip install "robot-motion-player[all]"
fi

echo
echo "========================================"
echo " Setup completed successfully!"
echo "========================================"
echo
echo "To activate environment:"
echo "  conda activate ${ENV_NAME}"
echo
echo "Try:"
echo "  motion_player --help"