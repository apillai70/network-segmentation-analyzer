# PowerShell Script to Fix Production Import Error
# =================================================
# Run this ON THE PRODUCTION SERVER (RC34361)

$ErrorActionPreference = "Stop"
$production_path = "C:\Users\RC34361\network-segmentation-analyzer"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Production Import Fix Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Navigate to project
Write-Host "[1/5] Navigating to project..." -ForegroundColor Yellow
if (Test-Path $production_path) {
    cd $production_path
    Write-Host "✓ Project found at: $production_path`n" -ForegroundColor Green
} else {
    Write-Host "✗ ERROR: Project not found at $production_path" -ForegroundColor Red
    exit 1
}

# Step 2: Check current structure
Write-Host "[2/5] Checking current structure..." -ForegroundColor Yellow
Write-Host "Files in src/:" -ForegroundColor Gray
Get-ChildItem src\analysis* | ForEach-Object { Write-Host "  - $($_.Name) ($($_.PSIsContainer ? 'directory' : 'file'))" -ForegroundColor Gray }
Write-Host ""

# Step 3: Check if analysis.py exists
$src_analysis_py = Join-Path $production_path "src\analysis.py"
$src_analysis_dir = Join-Path $production_path "src\analysis"
$src_analysis_init = Join-Path $production_path "src\analysis\__init__.py"

Write-Host "[3/5] Checking for source files..." -ForegroundColor Yellow

$has_analysis_py = Test-Path $src_analysis_py
$has_analysis_dir = Test-Path $src_analysis_dir
$has_analysis_init = Test-Path $src_analysis_init

Write-Host "  src/analysis.py exists: $has_analysis_py" -ForegroundColor $(if($has_analysis_py){"Green"}else{"Red"})
Write-Host "  src/analysis/ dir exists: $has_analysis_dir" -ForegroundColor $(if($has_analysis_dir){"Yellow"}else{"Gray"})
Write-Host "  src/analysis/__init__.py exists: $has_analysis_init" -ForegroundColor $(if($has_analysis_init){"Green"}else{"Red"})
Write-Host ""

# Step 4: Apply fix
Write-Host "[4/5] Applying fix..." -ForegroundColor Yellow

if ($has_analysis_py -and $has_analysis_dir) {
    Write-Host "  Scenario: Both analysis.py (file) and analysis/ (dir) exist" -ForegroundColor Cyan
    Write-Host "  Action: Copying analysis.py -> analysis/__init__.py" -ForegroundColor Cyan

    # Backup existing __init__.py if it exists
    if ($has_analysis_init) {
        $backup = "$src_analysis_init.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item $src_analysis_init $backup
        Write-Host "  ✓ Backed up existing __init__.py to: $(Split-Path $backup -Leaf)" -ForegroundColor Green
    }

    # Copy analysis.py to analysis/__init__.py
    Copy-Item $src_analysis_py $src_analysis_init -Force
    Write-Host "  ✓ Copied analysis.py -> analysis/__init__.py" -ForegroundColor Green

} elseif ($has_analysis_dir -and -not $has_analysis_init) {
    Write-Host "  ✗ ERROR: analysis/ directory exists but no __init__.py and no analysis.py to copy from" -ForegroundColor Red
    Write-Host "  Solution: You need to get analysis.py from development or Git" -ForegroundColor Yellow
    Write-Host "`n  Run: git pull" -ForegroundColor Yellow
    Write-Host "  Or copy analysis.py manually from development" -ForegroundColor Yellow
    exit 1

} elseif (-not $has_analysis_dir -and $has_analysis_py) {
    Write-Host "  ✓ Only analysis.py exists (correct structure)" -ForegroundColor Green
    Write-Host "  No fix needed - this is the expected structure" -ForegroundColor Green

} else {
    Write-Host "  ✗ ERROR: Neither analysis.py nor analysis/ found" -ForegroundColor Red
    Write-Host "  Solution: Run 'git pull' to get the files" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 5: Verify fix
Write-Host "[5/5] Verifying fix..." -ForegroundColor Yellow

Write-Host "  Testing import..." -ForegroundColor Gray
$test_result = & python -c "from src.analysis import TrafficAnalyzer; print('SUCCESS')" 2>&1

if ($LASTEXITCODE -eq 0 -and $test_result -match "SUCCESS") {
    Write-Host "  ✓ Import successful!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Import failed:" -ForegroundColor Red
    Write-Host "  $test_result" -ForegroundColor Red
    exit 1
}

Write-Host "`n  Running tests..." -ForegroundColor Gray
$test_output = & python -m pytest tests/test_analysis.py -v 2>&1

if ($LASTEXITCODE -eq 0) {
    $passed = ($test_output | Select-String "passed").Line
    Write-Host "  ✓ Tests passed: $passed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Some tests failed" -ForegroundColor Red
    Write-Host "  Run manually: python -m pytest tests/test_analysis.py -v" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✓ Fix Applied Successfully!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run full test suite: python -m pytest tests/ -v" -ForegroundColor White
Write-Host "  2. Fix UTF-8 encoding: python fix_encoding_issues.py --scan" -ForegroundColor White
Write-Host ""
