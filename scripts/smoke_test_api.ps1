[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$ApiKey = $env:API_KEY
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd('/')
$Headers = @{}
if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
    $Headers["X-API-Key"] = $ApiKey
}

function Get-HttpStatus($ErrorRecord) {
    try { return [int]$ErrorRecord.Exception.Response.StatusCode } catch { return 0 }
}

function Invoke-Api([string]$Method, [string]$Path, $Body = $null) {
    $Params = @{
        Method = $Method
        Uri = "$BaseUrl$Path"
        Headers = $Headers
        ErrorAction = "Stop"
    }
    if ($null -ne $Body) {
        $Params.ContentType = "application/json"
        $Params.Body = $Body | ConvertTo-Json -Depth 20
    }
    try {
        $Result = Invoke-RestMethod @Params
        return [PSCustomObject]@{ Status = 200; Body = $Result }
    } catch {
        $Status = Get-HttpStatus $_
        $Message = $_.ErrorDetails.Message
        if (-not $Message) { $Message = $_.Exception.Message }
        return [PSCustomObject]@{ Status = $Status; Body = $Message }
    }
}

function Assert-Status([string]$Name, $Result, [int]$Expected) {
    if ($Result.Status -ne $Expected) {
        Write-Host "FAIL: $Name (expected HTTP $Expected, got $($Result.Status))" -ForegroundColor Red
        Write-Host ($Result.Body | ConvertTo-Json -Depth 10 -ErrorAction SilentlyContinue)
        exit 1
    }
    Write-Host "PASS: $Name (HTTP $Expected)" -ForegroundColor Green
}

Write-Host "=== Churn targeting API smoke test ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl"

$Health = Invoke-Api "GET" "/health"
Assert-Status "Health endpoint" $Health 200
if (-not $Health.Body.model_loaded) {
    Write-Host "FAIL: API is live but model_loaded is false. Train the model and restart the API before scoring tests." -ForegroundColor Red
    exit 1
}
Write-Host "PASS: trained model is loaded" -ForegroundColor Green

$Model = Invoke-Api "GET" "/model"
Assert-Status "Model metadata" $Model 200

$SingleBody = @{ customer = @{ eqpdays = 350; months = 14; area = "NEW YORK CITY AREA" } }
$Single = Invoke-Api "POST" "/score" $SingleBody
Assert-Status "Single-customer scoring" $Single 200
foreach ($Field in @("churn_probability_calibrated", "churn_probability_at_base_rate", "base_rate", "missing_features")) {
    if ($null -eq $Single.Body.$Field) { Write-Host "FAIL: score response missing '$Field'" -ForegroundColor Red; exit 1 }
}
foreach ($Field in @("churn_probability_calibrated", "churn_probability_at_base_rate")) {
    $Value = [double]$Single.Body.$Field
    if ($Value -lt 0 -or $Value -gt 1) { Write-Host "FAIL: $Field is outside [0,1]" -ForegroundColor Red; exit 1 }
}
Write-Host "PASS: score response schema and probability ranges" -ForegroundColor Green

$BatchBody = @{ customers = @(
    @{ eqpdays = 350; months = 14 },
    @{ eqpdays = 100; months = 36 },
    @{ eqpdays = 400; months = 8 }
) }
$Batch = Invoke-Api "POST" "/score/batch" $BatchBody
Assert-Status "Batch scoring" $Batch 200
if ($Batch.Body.results.Count -ne 3) { Write-Host "FAIL: batch result count was not 3" -ForegroundColor Red; exit 1 }
Write-Host "PASS: batch result count matches input count" -ForegroundColor Green

$EconomicsBody = @{
    n_treated = 1000; churn_prob = 0.05; avg_monthly_rev = 50
    save_rate = 0.10; margin = 0.40; months = 12; contact_cost = 0.50
}
$Economics = Invoke-Api "POST" "/finance/economics" $EconomicsBody
Assert-Status "Economics calculation" $Economics 200
if ([math]::Abs(([double]$Economics.Body.net_variable_benefit) - 700.0) -gt 0.001) {
    Write-Host "FAIL: economics calculation differs from expected net_variable_benefit=700" -ForegroundColor Red
    exit 1
}
Write-Host "PASS: economics calculation matches hand check" -ForegroundColor Green

$Pilot = Invoke-Api "POST" "/pilot/size" @{ baseline_churn_prob = 0.10; relative_effect = 0.20 }
Assert-Status "Pilot sample-size calculation" $Pilot 200
if ($Pilot.Body.total_customers -ne (2 * $Pilot.Body.n_per_arm)) {
    Write-Host "FAIL: total_customers should equal 2 * n_per_arm" -ForegroundColor Red
    exit 1
}
Write-Host "PASS: pilot sizing arithmetic" -ForegroundColor Green

$InvalidEconomics = Invoke-Api "POST" "/finance/economics" @{
    n_treated = 10; churn_prob = 2; avg_monthly_rev = 1
    save_rate = 0.1; margin = 0.4; months = 12; contact_cost = 0.5
}
Assert-Status "Reject invalid churn probability" $InvalidEconomics 422

$EmptyBatch = Invoke-Api "POST" "/score/batch" @{ customers = @() }
Assert-Status "Reject empty batch" $EmptyBatch 422

$UnknownCohort = Invoke-Api "GET" "/cohorts/nope"
Assert-Status "Reject unknown cohort dimension" $UnknownCohort 404

Write-Host "`nAll API smoke tests passed." -ForegroundColor Green
