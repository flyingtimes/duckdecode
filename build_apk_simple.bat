@echo off
REM Simple APK build script using Docker
echo ========================================
echo   Duck Decode - APK Build
echo   Using Docker with pre-compiled SDK
echo ========================================
echo.

echo Using API 28 (Android 9) for better compatibility...

cd /d %~dp0

docker run --rm --privileged ^
  -v "%CD%:/apphost" ^
  kivy/buildozer:patched ^
  bash -c "cd /apphost && cp duck_decode_android.py main.py && yes ^| buildozer android debug 2>&1"

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
if exist "bin\*.apk" (
    echo APK files:
    dir /b bin\*.apk
) else (
    echo No APK found in bin/ directory
)
echo.
pause