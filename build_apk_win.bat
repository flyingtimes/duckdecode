@echo off
REM Build APK Script for Duck Decode Android App (Windows)
REM This script requires WSL or Docker to run buildozer

echo ========================================
echo   Duck Decode - APK Build Tool
echo   Windows Version
echo ========================================
echo.

echo [Info] Building APK on Windows requires WSL or Docker
echo.
echo Please choose your setup:
echo.
echo   1. Use WSL (Windows Subsystem for Linux)
echo   2. Use Docker
echo   3. Manual setup instructions
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto wsl_setup
if "%choice%"=="2" goto docker_setup
if "%choice%"=="3" goto manual_help
goto end

:wsl_setup
echo.
echo [WSL Mode] Checking WSL installation...
wsl --version >nul 2>&1
if errorlevel 1 (
    echo [Error] WSL not installed. Please install WSL first:
    echo   wsl --install
    pause
    exit /b 1
)

echo.
echo [WSL Mode] Installing buildozer in WSL...
wsl bash -c "sudo apt update && sudo apt install -y build-essential git python3-pip python3-setuptools python3-wheel openjdk-17-jdk"
wsl bash -c "pip3 install --user buildozer cython"

echo.
echo [WSL Mode] Starting build process...
wsl bash -c "cd /mnt/c/Users/13802/code/decode-image-from-RH && bash build_apk.sh"
goto end

:docker_setup
echo.
echo [Docker Mode] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Docker not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo.
echo [Docker Mode] Pulling Kivy Buildozer image...
docker pull kivy/buildozer

echo.
echo [Docker Mode] Building APK...
docker run --privileged -v %cd%:/home/user/apphost kivy/buildozer
goto end

:manual_help
echo.
echo ========================================
echo   Manual Build Instructions
echo ========================================
echo.
echo To build the APK manually, you need:
echo.
echo 1. Linux environment (Ubuntu 20.04+ recommended)
echo    - Or WSL on Windows
echo    - Or Docker with kivy/buildozer image
echo.
echo 2. Install dependencies:
echo    sudo apt update
echo    sudo apt install -y build-essential git python3-pip
echo    sudo apt install -y python3-setuptools python3-wheel
echo    sudo apt install -y openjdk-17-jdk
echo    pip3 install --user buildozer cython
echo.
echo 3. Build APK:
echo    cd /path/to/decode-image-from-RH
echo    buildozer android debug
echo.
echo 4. Find APK in: bin/duckdecode-*.apk
echo.
echo Online build services:
echo   - https://github.com/HeaTTheatR/KivyMD-Templates
echo   - Use Google Colab with buildozer
echo.

:end
pause