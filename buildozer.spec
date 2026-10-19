[app]
title = Shimul Audio
package.name = shimulaudio
package.domain = com.shimul
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json,xml
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

# Let Android offer "Shimul Audio" in the "Open with" list when the user taps
# an audio file in another app (file manager, WhatsApp, browser, ...).
android.manifest.intent_filters = intent_filters.xml
# Reuse the running activity so a new file arrives via onNewIntent instead of
# starting a second copy of the app.
android.manifest.launch_mode = singleTop

# Pin python-for-android to the last release that builds Python 3.11.
# master/v2026.05.09 build Python 3.14, whose _PyLong_AsByteArray signature
# breaks Kivy 2.3.0's generated C code (expected 6 args, have 5).
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
