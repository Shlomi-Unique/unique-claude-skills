# setup_whisper_model.ps1
# One-time setup for Hebrew video subtitles skill.

# Don't abort on stderr messages from native commands
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false 2>$null

$DefaultModelDir = "$env:USERPROFILE\Documents\Camtasia Studio\.whisper-model"

Write-Host ""
Write-Host "=== Hebrew Whisper Model Setup ===" -ForegroundColor Cyan
Write-Host ""

# Find Python
$PyCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $v = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $PyCmd = $cmd
            Write-Host "[OK] Found Python as '$cmd': $v"
            break
        }
    } catch { }
}

if (-not $PyCmd) {
    Write-Host "[ERROR] Python not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install from Microsoft Store (search 'Python 3.12') or python.org,"
    Write-Host "then OPEN A NEW PowerShell window and re-run this script."
    exit 1
}

Write-Host ""
Write-Host "Step 1/2: Installing ivrit + dependencies (this takes 1-3 min)..." -ForegroundColor Yellow

# Capture stderr into stdout and redirect all to null so PS does not complain.
# We check success via $LASTEXITCODE afterwards.
$pipArgs = @("-m", "pip", "install", "--upgrade", "--user", "--quiet",
             "ivrit", "faster-whisper", "huggingface_hub")
& $PyCmd @pipArgs *>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed (exit $LASTEXITCODE)." -ForegroundColor Red
    Write-Host "Try manually: $PyCmd -m pip install --upgrade --user ivrit faster-whisper huggingface_hub"
    exit 1
}
Write-Host "[OK] Packages installed"

# Verify import works
$checkImport = & $PyCmd -c "import ivrit, faster_whisper, huggingface_hub; print('OK')" 2>&1
if ($checkImport -notmatch "OK") {
    Write-Host "[WARN] Import check: $checkImport"
} else {
    Write-Host "[OK] Import check passed"
}

Write-Host ""
Write-Host "Model will be saved to:"
Write-Host "  $DefaultModelDir"
$custom = Read-Host "Press Enter to accept, or type a different full path"
if ($custom) { $DefaultModelDir = $custom }

if (-not (Test-Path $DefaultModelDir)) {
    New-Item -ItemType Directory -Path $DefaultModelDir -Force | Out-Null
}

# Skip download if already present
$existingModel = Join-Path $DefaultModelDir "model.bin"
if (Test-Path $existingModel) {
    Write-Host ""
    Write-Host "[OK] Model already downloaded at $DefaultModelDir (skipping)"
} else {
    Write-Host ""
    Write-Host "Step 2/2: Downloading ivrit-ai/whisper-large-v3-turbo-ct2 (~1.5GB)..." -ForegroundColor Yellow
    Write-Host "This takes 3-10 minutes depending on your connection."
    Write-Host ""

    $pyCode = @"
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id='ivrit-ai/whisper-large-v3-turbo-ct2',
    local_dir=r'$DefaultModelDir',
)
print('DOWNLOADED_TO:', path)
"@

    $pyCode | & $PyCmd - 2>&1 | ForEach-Object {
        # Show progress lines, suppress known warnings
        if ($_ -match "^\s*WARNING" -or $_ -match "not on PATH") { return }
        Write-Host $_
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Model download failed (exit $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
}

# Sentinel
$SentinelPath = Join-Path $DefaultModelDir "SETUP_COMPLETE.txt"
$info = @"
Hebrew Whisper model setup complete.
Model: ivrit-ai/whisper-large-v3-turbo-ct2
Location: $DefaultModelDir
Python: $PyCmd
Setup date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@
Set-Content -Path $SentinelPath -Value $info -Encoding UTF8

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Model saved to: $DefaultModelDir"
Write-Host ""
Write-Host "Tell Claude in Cowork:"
Write-Host '  "add captions to project <name>"'
Write-Host "and the rest happens automatically."
Write-Host ""
