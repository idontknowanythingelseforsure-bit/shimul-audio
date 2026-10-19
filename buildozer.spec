[app]
title = Shimul Audio
package.name = shimulaudio
package.domain = com.shimul
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json
source.exclude_dirs = .git,.github,build,dist,bin,__pycache__,.venv
version = 1.0.0

# KivyMD 1.2.0 matches the widgets used in main.py
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pyjnius,android,pillow

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/assets/icon.png

android.permissions = READ_EXTERNAL_STORAGE,READ_MEDIA_AUDIO,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
