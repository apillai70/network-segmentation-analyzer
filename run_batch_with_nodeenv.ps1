#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Batch Processing with Nodeenv - PowerShell Wrapper
.DESCRIPTION
    This script activates nodeenv before running batch processing,
    ensuring mmdc (mermaid-cli) is in PATH
.PARAMETER BatchSize
    Number of files to process per batch (default: 10)
.PARAMETER ClearFirst
    Clear file tracking and reprocess all files
.EXAMPLE
    .\run_batch_with_nodeenv.ps1 -BatchSize 10
.EXAMPLE
    .\run_batch_with_nodeenv.ps1 -BatchSize 10 -ClearFirst
#>

param(
    [int]$BatchSize = 10,
    [switch]$ClearFirst
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "BATCH PROCESSING WITH NODEENV" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if nodeenv exists
$nodeenvActivate = "nodeenv\Scripts\Activate.ps1"
if (-not (Test-Path $nodeenvActivate)) {
    Write-Host "ERROR: nodeenv not found at $nodeenvActivate" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please ensure nodeenv is set up in this directory." -ForegroundColor Yellow
    exit 1
}

# Activate nodeenv
Write-Host "Activating nodeenv..." -ForegroundColor Yellow
& $nodeenvActivate

# Check if mmdc is now accessible
Write-Host "Checking for mmdc..." -ForegroundColor Yellow
try {
    $mmdc_version = & mmdc --version 2>&1
    Write-Host "  Found mmdc: $mmdc_version" -ForegroundColor Green
} catch {
    Write-Host "WARNING: mmdc not found even after activating nodeenv" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to install mermaid-cli in nodeenv:" -ForegroundColor Yellow
    Write-Host "   npm install -g @mermaid-js/mermaid-cli" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Build command arguments
$args = @("run_batch_processing.py", "--batch-size", $BatchSize)
if ($ClearFirst) {
    $args += "--clear-first"
}

# Run batch processing
Write-Host "Starting batch processing..." -ForegroundColor Yellow
Write-Host "Command: python $($args -join ' ')" -ForegroundColor Gray
Write-Host ""

python @args

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Batch processing complete (exit code: $exitCode)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

exit $exitCode
