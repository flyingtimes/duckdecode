[app]
title = Duck Decode
package.name = duckdecode
package.domain = org.duckdecode
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Android settings - use API 30 (Android 11) which is widely available
android.api = 30
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

# Permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

# UI settings
orientation = portrait
fullscreen = 0

# Build settings
android.gradle_build = True
android.enable_androidx = True
android.skip_update = False
android.accept_sdk_license = True

# Python
python.version = 3.11
p4a.branch = master
android.entrypoint = org.kivy.android.PythonActivity

# Requirements (use pillow instead of pil)
requirements = python3,kivy,numpy,pillow,pyjnius,android

# Logging
log_level = 2
android.log_level = info