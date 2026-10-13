[CmdletBinding()]
param(
    [string]$DataDir = $(if ($env:DATA_DIR) { $env:DATA_DIR } else { "data/raw" }),
    [string]$ModelPath = $(if ($env:MODEL_PATH) { $env:MODEL_PATH } else { "models/churn_model.joblib" }),
    [int]$Seed = 42,
    [switch]$Search
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Stop-WithMessage([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

Write-Host "=== Churn targeting training preflight ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host "Data directory: $DataDir"
Write-Host "Model path: $ModelPath"

if (-not (Get-Command churn-targeting -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "The churn-targeting CLI is unavailable. Activate .venv and run: python -m pip install -e '.[api,graph,dev]'"
}

$ClientPath = Join-Path $DataDir "Client.csv"
$RecordPath = Join-Path $DataDir "Record.csv"
foreach ($Path in @($ClientPath, $RecordPath)) {
    if (-not (Test-Path $Path -PathType Leaf)) {
        Stop-WithMessage "Required source file not found: $Path. Restore the authorised assignment file; this script will not generate or substitute customer data."
    }
    $Item = Get-Item $Path
    Write-Host ("FOUND: {0} ({1:N0} bytes)" -f $Path, $Item.Length) -ForegroundColor Green
}

Write-Host "`n=== Validate source data ===" -ForegroundColor Cyan
churn-targeting validate --data-dir $DataDir
if ($LASTEXITCODE -ne 0) { Stop-WithMessage "Data validation failed (exit code $LASTEXITCODE). No training was attempted." }

Write-Host "`n=== Train model ===" -ForegroundColor Cyan
$TrainArgs = @("train", "--data-dir", $DataDir, "--out", $ModelPath, "--seed", "$Seed")
if ($Search) { $TrainArgs += "--search" }
churn-targeting @TrainArgs
if ($LASTEXITCODE -ne 0) { Stop-WithMessage "Training failed (exit code $LASTEXITCODE). Review the CLI output above." }

$MetadataPath = [System.IO.Path]::ChangeExtension($ModelPath, ".json")
$Expected = @($ModelPath, $MetadataPath)
$Missing = @($Expected | Where-Object { -not (Test-Path $_ -PathType Leaf) })
if ($Missing.Count -gt 0) {
    Write-Host "Expected output file(s) not found:" -ForegroundColor Red
    $Missing | ForEach-Object { Write-Host " - $_" }
    Stop-WithMessage "Check the training output path and model persistence implementation."
}

Write-Host "`nTraining and artifact verification succeeded." -ForegroundColor Green
Write-Host "Model: $ModelPath"
Write-Host "Metadata: $MetadataPath"
Write-Host "Next: restart the API process, then verify GET /health reports model_loaded=true."
