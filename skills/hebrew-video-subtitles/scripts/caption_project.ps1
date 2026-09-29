# caption_project.ps1 - Fully-automated Hebrew captions pipeline on Windows.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File caption_project.ps1 "<project.tscproj>"
#
# This runs the entire pipeline on YOUR Windows machine using the ivrit-ai
# model you downloaded with setup_whisper_model.ps1:
#   1. Extract audio from the project's source media (.trec/.mp4)
#   2. Transcribe with faster-whisper + ivrit Hebrew model
#   3. Write Camtasia-compatible SRT next to the project
#   4. Inject captions directly into the .tscproj JSON
#
# Takes roughly real-time-divided-by-3 on CPU (turbo model), seconds on GPU.

param(
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [string]$ModelDir = "$env:USERPROFILE\Documents\Camtasia Studio\.whisper-model",
    [string]$ScriptsDir = $PSScriptRoot,
    [switch]$NoInject
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=== Hebrew Video Captions Pipeline ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectPath"
Write-Host "Model  : $ModelDir"
Write-Host ""

# Verify project exists
if (-not (Test-Path $ProjectPath)) {
    Write-Host "[ERROR] Project not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

# Verify model exists
if (-not (Test-Path (Join-Path $ModelDir "model.bin"))) {
    Write-Host "[ERROR] Model not found. Run setup_whisper_model.ps1 first." -ForegroundColor Red
    exit 1
}

# Resolve scripts directory - look for Python scripts
$extractScript = Join-Path $ScriptsDir "extract_audio.py"
$transcribeScript = Join-Path $ScriptsDir "transcribe_local.py"
$injectScript = Join-Path $ScriptsDir "inject_captions_tscproj.py"

foreach ($s in @($extractScript, $transcribeScript, $injectScript)) {
    if (-not (Test-Path $s)) {
        Write-Host "[ERROR] Script missing: $s" -ForegroundColor Red
        Write-Host "Extract hebrew-video-subtitles.skill into $ScriptsDir" -ForegroundColor Yellow
        exit 1
    }
}

$env:HEBREW_WHISPER_MODEL = $ModelDir

# Find source media inside the .tscproj folder
$projectDir = if ((Get-Item $ProjectPath).PSIsContainer) { $ProjectPath } else { (Get-Item $ProjectPath).DirectoryName }
$sourceMedia = Get-ChildItem -Path $projectDir -Include "*.trec","*.mp4","*.mov","*.mkv" -File | Select-Object -First 1
if (-not $sourceMedia) {
    Write-Host "[ERROR] No source media found in $projectDir" -ForegroundColor Red
    exit 1
}
Write-Host "Source : $($sourceMedia.Name)"

# Outputs
$tempDir = [System.IO.Path]::GetTempPath()
$audioPath = Join-Path $tempDir "caption_audio.mp3"
$srtPath = Join-Path $projectDir "captions.srt"

# 1. Extract audio
Write-Host ""
Write-Host "Step 1/3: Extracting audio..." -ForegroundColor Yellow
python $extractScript $sourceMedia.FullName $audioPath
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] audio extraction failed" -ForegroundColor Red; exit 1 }

# 2. Transcribe
Write-Host ""
Write-Host "Step 2/3: Transcribing (this takes a few minutes)..." -ForegroundColor Yellow
python $transcribeScript $audioPath $srtPath --model-path $ModelDir
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] transcription failed" -ForegroundColor Red; exit 1 }

# 3. Inject into .tscproj
if ($NoInject) {
    Write-Host ""
    Write-Host "Done. SRT at: $srtPath (skipped tscproj injection per --NoInject)" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Step 3/3: Injecting captions into .tscproj..." -ForegroundColor Yellow
Write-Host "IMPORTANT: close the project in Camtasia before this step\!" -ForegroundColor Yellow
python $injectScript $ProjectPath $srtPath --in-place
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] injection failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Green
Write-Host "Open your project in Camtasia - captions are on a new track."
