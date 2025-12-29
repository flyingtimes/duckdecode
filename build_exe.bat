@echo off
REM Duck Decode GUI Build Script
REM Build Python program to Windows EXE

echo ========================================
echo   Duck Decode GUI Build Tool
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Set pip mirror
set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
set PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

REM Check venv
if exist "venv\Scripts\activate.bat" (
    echo [Info] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [Info] No venv found, using global Python
)

echo.
echo [1/3] Installing dependencies (Tsinghua mirror)...
pip install -q -r requirements.txt -i %PIP_INDEX_URL%
if errorlevel 1 (
    echo [Error] Dependencies installation failed
    pause
    exit /b 1
)

echo [Done] Dependencies installed
echo.
echo [2/3] Cleaning old build files...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo [Done] Cleaned
echo.
echo [3/3] Building EXE (this may take a few minutes)...
pyinstaller --clean duck_decode_gui.spec

if errorlevel 1 (
    echo.
    echo [Error] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo EXE location: dist\DuckDecode.exe
echo.

REM Open dist directory
if exist "dist\DuckDecode.exe" (
    explorer dist
) else (
    echo [Warning] EXE file not found
)

pause