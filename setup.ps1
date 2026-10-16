# One-time setup for the Reel engine on a new Windows machine (the PC). Safe to re-run: it skips what exists.
# Run from the reel-editor folder:   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Pinned to the versions used on the laptop when the style was locked (2026-10-17).
param(
  [string]$VenvPath = "$HOME\.venvs\autoclipper"
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }

Step "ffmpeg 9.0.2"
$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff) {
  $ff = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -Last 1 -ExpandProperty FullName
}
if (-not $ff) {
  winget install --id Gyan.FFmpeg -e --version 9.0.2 --accept-source-agreements --accept-package-agreements --disable-interactivity
  $ff = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe" | Select-Object -Last 1 -ExpandProperty FullName
}
Write-Host "ffmpeg: $ff"

Step "Python 3.14 (system: Pillow + numpy for rendering)"
try { py -3.14 --version } catch { Write-Host "Python 3.14 missing: install it with 'py install 3.14' (Python install manager), then re-run."; exit 1 }
py -3.14 -m pip install --quiet "pillow==12.2.0" "numpy==2.4.4"

Step "Whisper venv at $VenvPath"
if (-not (Test-Path "$VenvPath\Scripts\python.exe")) { py -3.14 -m venv $VenvPath }
& "$VenvPath\Scripts\python.exe" -m pip install --quiet --upgrade pip
# av is pinned to 18.1.0 on purpose: av 19 dropped an argument faster-whisper 1.2.1 still passes
& "$VenvPath\Scripts\python.exe" -m pip install --quiet --only-binary=:all: -r "$root\requirements.lock.txt"

Step "Fonts (Fontsource 5.3.0, OFL)"
$fonts = @{ "figtree-800" = "https://cdn.jsdelivr.net/fontsource/fonts/figtree@5.3.0/latin-800-normal.ttf";
            "figtree-700" = "https://cdn.jsdelivr.net/fontsource/fonts/figtree@5.3.0/latin-700-normal.ttf" }
foreach ($k in $fonts.Keys) {
  $dir = "$root\fonts\$k"; New-Item -ItemType Directory -Force $dir | Out-Null
  if (-not (Test-Path "$dir\$k.ttf")) { Invoke-WebRequest $fonts[$k] -OutFile "$dir\$k.ttf" -UseBasicParsing }
}

Step "Sound effects (Mixkit free licence: keep them local, never redistribute)"
$sfx = @{ "whoosh_fast_1490.wav" = 1490; "whoosh_cinematic_1492.wav" = 1492; "whoosh_air_1489.wav" = 1489;
          "pop_light_3005.wav" = 3005; "pop_hard_click_2364.wav" = 2364; "pop_dry_2356.wav" = 2356 }
New-Item -ItemType Directory -Force "$root\sfx" | Out-Null
foreach ($k in $sfx.Keys) {
  if (-not (Test-Path "$root\sfx\$k")) { Invoke-WebRequest "https://assets.mixkit.co/active_storage/sfx/$($sfx[$k])/$($sfx[$k]).wav" -OutFile "$root\sfx\$k" -UseBasicParsing }
}

Step "config.json for this machine"
$py = (py -3.14 -c "import sys; print(sys.executable)").Trim()
@{ ffmpeg = $ff; whisper_python = "$VenvPath\Scripts\python.exe"; python = $py; deliver_dir = "$HOME\Downloads" } |
  ConvertTo-Json | Set-Content "$root\config.json" -Encoding ascii

Step "Claude skill"
$skill = "$HOME\.claude\skills\reel-edit"
New-Item -ItemType Directory -Force $skill | Out-Null
Copy-Item "$root\skill\SKILL.md" "$skill\SKILL.md" -Force

Write-Host "`nDone. The Whisper model (~464 MB) downloads on the first transcription." -ForegroundColor Green
