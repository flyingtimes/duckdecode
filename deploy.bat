@echo off
REM Duck Decode GUI Deploy Script
REM Use Tsinghua mirror for faster download

echo ========================================
echo   Duck Decode GUI Deploy Tool
echo   Using Tsinghua Mirror
echo ========================================
echo.

REM Set pip mirror
set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
set PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

echo [Info] Mirror: %PIP_INDEX_URL%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [Info] Python version:
python --version
echo.

REM Create venv if not exists
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [Error] Failed to create venv
        pause
        exit /b 1
    )
    echo [Done] Virtual environment created
) else (
    echo [1/4] Virtual environment exists, skipping
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [Error] Failed to activate venv
    pause
    exit /b 1
)
echo [Done] Virtual environment activated

echo.
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip -i %PIP_INDEX_URL%

echo.
echo [4/4] Installing dependencies...
echo Installing: PyQt5, Pillow, numpy, pyinstaller
echo.
pip install -r requirements.txt -i %PIP_INDEX_URL%

if errorlevel 1 (
    echo.
    echo [Error] Installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Deploy Complete!
echo ========================================
echo.
echo You can now:
echo.
echo   1. Run GUI program (test):
echo      python duck_decode_gui.py
echo.
echo   2. Build EXE file:
echo      build_exe.bat
echo.
echo Press any key to start GUI...
pause >nul

python duck_decode_gui.py