# Shimul Audio

Kivy/KivyMD music player with playlists, seeking, shuffle/repeat and Android
MediaPlayer support.

## Downloads

Both builds run automatically on every push to `main` and can be started
manually from the **Actions** tab:

| Platform | Workflow | Artifact |
|---|---|---|
| Android | Build Android APK | `shimul-audio-apk` (`bin/*.apk`) |
| Windows | Build Windows EXE | `shimul-audio-exe` (`dist/Shimul Audio.exe`) |

Open a completed run and download the artifact from the **Artifacts** section.

## Local development (Windows)

```bat
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

The desktop backend prefers pygame because Kivy's SDL2 audio provider has a
no-op `seek()`; without pygame the progress slider moves but audio does not.

## Build notes

- Android: Buildozer + python-for-android, arm64-v8a, API 33, NDK 25b.
- Windows: PyInstaller onefile, no console, KivyMD collected with
  `--collect-all kivymd`.
