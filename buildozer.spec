[app]
title = Duck Decode
package.name = duckdecode
package.domain = org.duckdecode
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Android settings - use API 28 (Android 9) which is widely available
android.api = 28
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

# Permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# UI settings
orientation = portrait
fullscreen = 0

# Build settings
android.gradle_build = True
android.enable_androidx = True

# Python
python.version = 3.9
p4a.branch = master
android.entrypoint = org.kivy.android.PythonActivity

# Requirements
requirements = python3,kivy,numpy,pil,pillow,pyjnius,android

# Logging
log_level = 2
android.log_level = info