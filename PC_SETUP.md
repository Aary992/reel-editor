# Setting up the Reel engine on the PC

For the desktop PC only (Windows user `Admin`). The engine goes in `D:\My Data\Documents\cc\reel-editor`,
next to voidrush. That's the folder Claude Code launches from on the PC, so the skill and paths line up.
All commands are PowerShell.

## 1. Check the basics (once)

```powershell
git --version
winget --version
py -0p
```
- `py -0p` must list **3.14**. If it doesn't, run `py install 3.14`, then open a new PowerShell window.
- If `git` or `winget` are missing, install them first (Git for Windows; winget comes with App Installer
  from the Microsoft Store).

## 2. Get the code

```powershell
cd "D:\My Data\Documents\cc"
git clone https://github.com/Aary992/reel-editor.git
cd reel-editor
```

## 3. Run the setup (about 5 minutes)

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```
It installs exactly what the laptop uses, skipping anything already there:
- **ffmpeg 9.0.2** (winget)
- **Pillow 12.2.0 and numpy 2.4.4** for Python 3.14
- **The Whisper environment** at `C:\Users\Admin\.venvs\autoclipper`, with the pinned packages from
  `requirements.lock.txt` (including `av==18.1.0`, see Troubleshooting)
- **Fonts:** Figtree Bold and ExtraBold (Fontsource 5.3.0) into `fonts\`
- **Sound effects:** the 6 Mixkit sounds into `sfx\` (free licence, stays on this PC)
- **`config.json`** with this PC's paths
- **The Claude skill:** `C:\Users\Admin\.claude\skills\reel-edit`

Close and reopen PowerShell afterwards, so the new ffmpeg is on PATH.

## 4. Check it worked

```powershell
cd "D:\My Data\Documents\cc\reel-editor"
Get-Content config.json
Test-Path "$HOME\.claude\skills\reel-edit\SKILL.md"
py -3.14 reel.py prep "C:\Users\Admin\Downloads\<any talking-head video>.mp4" --name "pc test"
```
- `config.json` should show:
  - an ffmpeg path
  - `C:\Users\Admin\.venvs\autoclipper\Scripts\python.exe`
  - a Python 3.14 path
  - `C:\Users\Admin\Downloads`
- `Test-Path` should print `True`.
- The test run should end with `ready:` and leave a preview at `reels\pc test\pc test preview.mp4`.
  The first run also downloads the Whisper model (about 464 MB), so it takes longer.

Delete the test folder afterwards if you like: `Remove-Item -Recurse "reels\pc test"`.

## 5. Use it

Open Claude Code from `D:\My Data\Documents\cc` (restart it once after setup so it loads the
`reel-edit` skill), then send it your video. Claude runs the whole thing:
1. It preps the video, then hands you the Flow prompts, a preview and 3 cover frames.
2. You save your Flow clips into `reels\<name>\` and send your cover line.
3. It renders the final into Downloads.

The look is fixed in `STYLE.md`.

## 6. Keep the laptop and PC in sync

```powershell
# sitting down at the PC
cd "D:\My Data\Documents\cc\reel-editor"; git pull

# after changing the engine on the PC
git add -A; git commit -m "describe the change"; git push
```
`reels\` (your videos and Flow clips), `sfx\*.wav`, the fonts and `config.json` are never committed, so
each machine keeps its own. To move a Reel in progress between machines, copy its `reels\<name>` folder.

## Troubleshooting

- **`ffmpeg not found`.** Open a new PowerShell window. If it still fails, put the full path in
  `config.json` ("ffmpeg"). It lives under
  `C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe`.
- **Transcription fails with `TypeError: open() got an unexpected keyword argument 'metadata_errors'`.**
  PyAV got upgraded. Fix:
  `C:\Users\Admin\.venvs\autoclipper\Scripts\python.exe -m pip install av==18.1.0`.
- **`Python 3.14 missing`** when running setup. Run `py install 3.14`, open a new window, and run
  setup again.
- **"running scripts is disabled"** errors. Use the exact `powershell -ExecutionPolicy Bypass -File .\setup.ps1`
  line; it doesn't change any system setting.
- **Fonts or sounds missing.** Run `setup.ps1` again. It only downloads what's missing.
- **Claude doesn't use the reel skill.** Restart Claude Code, since skills load when a session starts.
  Check `C:\Users\Admin\.claude\skills\reel-edit\SKILL.md` exists.
