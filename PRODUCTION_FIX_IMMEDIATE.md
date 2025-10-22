# IMMEDIATE PRODUCTION FIX

## Problem on Production
Production has `src/analysis/` as a **directory**, not `src/analysis.py` as a **file**.

The directory has an empty or incorrect `__init__.py` file.

---

## Solution: Create/Update `src/analysis/__init__.py` on Production

### Option 1: SSH/Remote into Production and Create the File

On production server, create this file:

**File:** `C:\Users\RC34361\network-segmentation-analyzer\src\analysis\__init__.py`

**Content:**
```python
"""
Analysis Module
===============
Network Traffic Analysis and Segmentation
"""

# Import from the main analysis module file
# This file re-exports classes for backward compatibility

import sys
from pathlib import Path

# Add parent to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import the actual analysis.py file (should be in src/)
# Try multiple approaches
try:
    # Try importing from sibling analysis.py
    import importlib.util
    analysis_file = Path(__file__).parent.parent / 'analysis.py'
    if analysis_file.exists():
        spec = importlib.util.spec_from_file_location("_analysis_impl", analysis_file)
        _analysis_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_analysis_module)

        TrafficAnalyzer = _analysis_module.TrafficAnalyzer
        SegmentationRule = _analysis_module.SegmentationRule
        NetworkZone = _analysis_module.NetworkZone
    else:
        raise ImportError("analysis.py not found")
except Exception as e:
    # Fallback: try direct import
    print(f"Warning: Fallback import method used: {e}")
    import analysis as _analysis_module
    TrafficAnalyzer = _analysis_module.TrafficAnalyzer
    SegmentationRule = _analysis_module.SegmentationRule
    NetworkZone = _analysis_module.NetworkZone

__all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone']
```

### Option 2: Even Simpler - Copy analysis.py Content

**Better solution:** Copy the entire content of `src/analysis.py` into `src/analysis/__init__.py`

On production:
```bash
cd C:\Users\RC34361\network-segmentation-analyzer\src

# Check if analysis.py exists
ls analysis.py

# If it exists, copy its content into analysis/__init__.py
cp analysis.py analysis/__init__.py

# Or if you want to keep both, just copy
cat analysis.py > analysis/__init__.py
```

### Option 3: Restructure (Cleanest Solution)

**On production, do this:**

```bash
cd C:\Users\RC34361\network-segmentation-analyzer\src

# Backup current structure
cp -r analysis analysis.backup

# If analysis.py exists as a file in src/, move it into the analysis/ directory
if [ -f "analysis.py" ]; then
    cp analysis.py analysis/main.py
fi

# Create proper __init__.py
cat > analysis/__init__.py << 'EOF'
"""
Analysis Module - Traffic Analysis and Segmentation
"""
from .main import TrafficAnalyzer, SegmentationRule, NetworkZone

__all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone']
EOF
```

---

## Quick Commands for Production (Copy-Paste)

### PowerShell (On Production):

```powershell
cd C:\Users\RC34361\network-segmentation-analyzer\src

# Check current structure
Write-Host "Current structure:"
Get-ChildItem analysis*

# Check if analysis.py exists in src/
if (Test-Path "analysis.py") {
    Write-Host "`n✓ analysis.py exists as file"

    # Copy it into the analysis/ directory as __init__.py
    Copy-Item "analysis.py" "analysis\__init__.py" -Force
    Write-Host "✓ Copied analysis.py -> analysis\__init__.py"

} else {
    Write-Host "`n✗ analysis.py NOT found in src/"
    Write-Host "Need to copy from development"
}

# Verify
Write-Host "`nChecking analysis/__init__.py:"
if (Test-Path "analysis\__init__.py") {
    $lines = (Get-Content "analysis\__init__.py" | Measure-Object -Line).Lines
    Write-Host "✓ analysis/__init__.py exists ($lines lines)"
} else {
    Write-Host "✗ analysis/__init__.py MISSING"
}
```

### Git Bash (On Production):

```bash
cd /c/Users/RC34361/network-segmentation-analyzer/src

# Check structure
echo "Current structure:"
ls -la analysis*

# If analysis.py exists, copy it
if [ -f "analysis.py" ]; then
    echo "✓ Found analysis.py"
    cp analysis.py analysis/__init__.py
    echo "✓ Copied to analysis/__init__.py"
else
    echo "✗ analysis.py not found"
fi

# Verify
if [ -f "analysis/__init__.py" ]; then
    lines=$(wc -l < analysis/__init__.py)
    echo "✓ analysis/__init__.py exists ($lines lines)"
else
    echo "✗ analysis/__init__.py MISSING"
fi
```

---

## After Applying Fix

Run tests again:
```bash
cd C:\Users\RC34361\network-segmentation-analyzer
python -m pytest tests/test_analysis.py -v
```

Should see:
```
============================= 15 passed in 0.24s ==============================
```

---

## If analysis.py Doesn't Exist on Production

You need to copy it from development:

### From Development Machine:
```bash
# Copy analysis.py to production
scp src/analysis.py RC34361@production:C:/Users/RC34361/network-segmentation-analyzer/src/

# Then on production
cd C:\Users\RC34361\network-segmentation-analyzer\src
cp analysis.py analysis/__init__.py
```

Or use Git:
```bash
# On development
git add src/analysis.py
git commit -m "Add analysis.py for production"
git push

# On production
git pull
cp src/analysis.py src/analysis/__init__.py
```

---

## Verification Checklist

After fix, verify on production:

- [ ] `src/analysis/__init__.py` exists
- [ ] File has content (not empty)
- [ ] Contains `TrafficAnalyzer`, `SegmentationRule`, `NetworkZone` classes
- [ ] `python -c "from src.analysis import TrafficAnalyzer; print('OK')"` works
- [ ] All 15 tests pass

---

## Why This Happened

**Development:** Has `src/analysis.py` (file)
**Production:** Has `src/analysis/` (directory)

Python always checks for **directory first**, so on production, it finds `src/analysis/` and looks for `__init__.py` inside it, ignoring any `analysis.py` file that might exist.

The fix is to populate `src/analysis/__init__.py` with the classes.
