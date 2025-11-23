# Backend API - Postman Collections Test Runner (PowerShell)
# This script runs all Postman collections using Newman via npx

$ErrorActionPreference = "Continue"

# Configuration
$PostmanDir = $PSScriptRoot
$Environment = Join-Path $PostmanDir "Backend-API.Environment.postman_environment.json"
$ReportDir = Join-Path $PostmanDir "reports"

# Create reports directory
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend API - Postman Test Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if npx is available
try {
    $null = Get-Command npx -ErrorAction Stop
    Write-Host "[OK] npx found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] npx is not installed" -ForegroundColor Red
    Write-Host "Install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Track results
$Total = 0
$Passed = 0
$Failed = 0
$FailedCollections = @()

# Function to run a collection
function Run-Collection {
    param (
        [string]$CollectionName
    )
    
    $CollectionFile = Join-Path $PostmanDir "$CollectionName.postman_collection.json"
    $script:Total++
    
    Write-Host "Running: $CollectionName" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    $ReportFile = Join-Path $ReportDir "$CollectionName-report.json"
    
    # Run newman with access token if available
    if ($script:accessToken) {
        npx newman run $CollectionFile `
            -e $Environment `
            --env-var "access_token=$($script:accessToken)" `
            --reporters cli `
            --color on `
            --timeout-request 10000
    } else {
        npx newman run $CollectionFile `
            -e $Environment `
            --reporters cli `
            --color on `
            --timeout-request 10000
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASSED] $CollectionName" -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host "[FAILED] $CollectionName" -ForegroundColor Red
        $script:Failed++
        $script:FailedCollections += $CollectionName
    }
    
    Write-Host ""
}

# Login with superuser first to get access token
Write-Host "Logging in with superuser credentials..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$loginBody = @{
    username = "testuser"
    password = "SecurePassword123!"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    $script:accessToken = $loginResponse.access_token
    Write-Host "[OK] Logged in successfully" -ForegroundColor Green
    Write-Host "Access token: $($script:accessToken.Substring(0, 20))..." -ForegroundColor Gray
    Write-Host "Access token will be passed to all collections" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "[WARNING] Could not login with superuser credentials" -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Tests requiring authentication may fail" -ForegroundColor Yellow
    Write-Host ""
    $script:accessToken = $null
}

# Run collections in order
Run-Collection "Backend-API.Health"

# Note: Authentication collection logs out at the end, which invalidates the token
# So we skip it and test authentication separately if needed
# Run-Collection "Backend-API.Authentication"

Run-Collection "Backend-API.Users"
Run-Collection "Backend-API.Dashboard"
Run-Collection "Backend-API.Metrics"
Run-Collection "Backend-API.Export"

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Collections: $Total" -ForegroundColor White
Write-Host "Passed: $Passed" -ForegroundColor Green
Write-Host "Failed: $Failed" -ForegroundColor $(if ($Failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($FailedCollections.Count -gt 0) {
    Write-Host "Failed Collections:" -ForegroundColor Red
    foreach ($collection in $FailedCollections) {
        Write-Host "  - $collection" -ForegroundColor Red
    }
    Write-Host ""
}

# Reports location
Write-Host "Reports saved to: $ReportDir" -ForegroundColor Cyan
Write-Host ""

# Exit with appropriate code
if ($Failed -eq 0) {
    Write-Host "[SUCCESS] All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAILED] Some tests failed" -ForegroundColor Red
    exit 1
}
