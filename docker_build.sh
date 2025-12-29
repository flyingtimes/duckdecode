#!/bin/bash
# Docker build script for Duck Decode APK
# Auto-accept Android SDK licenses

cd /home/user/apphost

# Prepare main file
cp duck_decode_android.py main.py

# Accept licenses and build
yes | buildozer android debug 2>&1