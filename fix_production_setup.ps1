#!/usr/bin/env pwsh
# Fix Production Setup.py Encoding Issue
# This script ensures setup.py has UTF-8 encoding for README.md

Write-Host "=== Production Setup.py Encoding Fix ===" -ForegroundColor Cyan
Write-Host ""

$setupFile = "setup.py"

# Check if setup.py exists
if (-not (Test-Path $setupFile)) {
    Write-Host "ERROR: setup.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the project root" -ForegroundColor Yellow
    exit 1
}

# Read current setup.py
Write-Host "Reading current setup.py..." -ForegroundColor Yellow
$content = Get-Content $setupFile -Raw -Encoding UTF8

# Check if it already has the fix
if ($content -match 'open\("README\.md",\s*encoding="utf-8"\)') {
    Write-Host "✓ setup.py already has UTF-8 encoding fix" -ForegroundColor Green
    Write-Host ""
    Write-Host "Trying pip install -e . to verify..." -ForegroundColor Yellow
    pip install -e .
    exit $LASTEXITCODE
}

# Create backup
$backupFile = "setup.py.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "Creating backup: $backupFile" -ForegroundColor Yellow
Copy-Item $setupFile $backupFile

# Apply fix - replace the open() call to include encoding
Write-Host "Applying UTF-8 encoding fix..." -ForegroundColor Yellow

$fixedContent = $content -replace `
    'with open\("README\.md"\) as f:', `
    'with open("README.md", encoding="utf-8") as f:'

$fixedContent = $fixedContent -replace `
    "with open\('README\.md'\) as f:", `
    "with open('README.md', encoding='utf-8') as f:"

# Write fixed content
Set-Content -Path $setupFile -Value $fixedContent -Encoding UTF8 -NoNewline

Write-Host "✓ Applied fix to setup.py" -ForegroundColor Green
Write-Host ""

# Show the change
Write-Host "Changes made:" -ForegroundColor Cyan
Write-Host "  OLD: with open(`"README.md`") as f:" -ForegroundColor Red
Write-Host "  NEW: with open(`"README.md`", encoding=`"utf-8`") as f:" -ForegroundColor Green
Write-Host ""

# Try installing
Write-Host "Testing pip install -e ..." -ForegroundColor Yellow
Write-Host ""

pip install -e .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ SUCCESS! Package installed successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backup saved as: $backupFile" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "ERROR: Installation failed" -ForegroundColor Red
    Write-Host "Restoring backup..." -ForegroundColor Yellow
    Copy-Item $backupFile $setupFile -Force
    Write-Host "Backup restored. Original setup.py preserved." -ForegroundColor Yellow
    exit 1
}
