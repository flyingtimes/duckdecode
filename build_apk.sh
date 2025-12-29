#!/bin/bash
# Build APK Script for Duck Decode Android App
# This script requires Linux or WSL with buildozer installed

echo "========================================"
echo "  Duck Decode - APK Build Tool"
echo "========================================"
echo ""

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "[Error] buildozer not found!"
    echo ""
    echo "Please install buildozer first:"
    echo "  pip install buildozer"
    echo ""
    echo "Or use Docker:"
    echo "  docker pull kivy/buildozer"
    echo "  docker run --privileged -v ~/.buildozer:/root/.buildozer -v $(pwd):/home/user/apphost kivy/buildozer"
    echo ""
    exit 1
fi

# Check for required dependencies
echo "[1/4] Checking dependencies..."
if ! command -v git &> /dev/null; then
    echo "[Error] git not found. Please install git."
    exit 1
fi
echo "[Done] Dependencies check passed"

echo ""
echo "[2/4] Initializing buildozer..."
buildozer init
if [ -f "buildozer.spec" ]; then
    echo "[Done] buildozer.spec found"
fi

echo ""
echo "[3/4] Downloading Android SDK/NDK (first time only)..."
echo "This may take a while on first run..."

echo ""
echo "[4/4] Building APK (debug mode)..."
echo "This process may take 10-30 minutes..."

buildozer -v android debug

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  Build Complete!"
    echo "========================================"
    echo ""
    echo "APK location: bin/"
    ls -lh bin/*.apk 2>/dev/null || echo "APK not found in bin/"
    echo ""
    echo "To install on Android device:"
    echo "  adb install -r bin/duckdecode-*.apk"
    echo ""
    echo "Or transfer the APK file to your device."
else
    echo ""
    echo "[Error] Build failed!"
    echo "Check the output above for details."
    exit 1
fi