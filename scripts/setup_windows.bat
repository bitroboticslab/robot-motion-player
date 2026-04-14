@echo off
setlocal

echo ========================================
echo   Robot Motion Player - Windows Setup
echo ========================================

:: Check conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Conda not found. Please install Miniconda/Anaconda first.
    exit /b 1
)

:: Config
set ENV_NAME=rmp
set PYTHON_VERSION=3.11

echo.
echo [1/4] Creating conda environment: %ENV_NAME%
call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y

echo.
echo [2/4] Activating environment
call conda activate %ENV_NAME%

echo.
echo [3/4] Installing Pinocchio (IK backend)
call conda install -c conda-forge pinocchio -y

echo.
echo [4/4] Installing Robot Motion Player

:: 判断是否在 repo 内
if exist "pyproject.toml" (
    echo Installing from source (editable mode)
    pip install -e ".[mujoco,gui,video]"
) else (
    echo Installing from PyPI
    pip install robot-motion-player[mujoco,gui,video]
)

echo.
echo ========================================
echo   Setup completed successfully!
echo ========================================
echo.
echo To activate environment:
echo     conda activate %ENV_NAME%
echo.
echo Try:
echo     motion_player gui
echo.

endlocal