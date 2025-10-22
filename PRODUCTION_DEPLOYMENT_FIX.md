# Production Deployment Fix Guide

## Issue
On production site (RC34361), getting:
```
ImportError: cannot import name 'TrafficAnalyzer' from 'src.analysis'
(C:\Users\RC34361\network-segmentation-analyzer\src\analysis\__init__.py)
```

This indicates that on production, `src.analysis` is a **directory** (not a file), conflicting with `src/analysis.py`.

---

## Quick Fix (Apply These Changes to Production)

### Step 1: Check for Directory Conflict
On your production server, run:
```bash
# Check if analysis is a directory
dir C:\Users\RC34361\network-segmentation-analyzer\src\analysis

# Or use PowerShell
Test-Path "C:\Users\RC34361\network-segmentation-analyzer\src\analysis" -PathType Container
```

**If the directory exists:**
- It's creating a conflict with `src/analysis.py`
- You need to choose which one to keep

---

## Solution Options

### **Option A: Remove Conflicting Directory** (Recommended if not needed)

If `src/analysis/` directory is not needed:
```bash
# Backup first
mv C:\Users\RC34361\network-segmentation-analyzer\src\analysis C:\Users\RC34361\network-segmentation-analyzer\src\analysis.backup

# Or delete if you're sure
rmdir /s C:\Users\RC34361\network-segmentation-analyzer\src\analysis
```

Then copy the correct files from development:
```bash
# Copy analysis.py to production
copy src\analysis.py C:\Users\RC34361\network-segmentation-analyzer\src\analysis.py

# Copy updated test file
copy tests\test_analysis.py C:\Users\RC34361\network-segmentation-analyzer\tests\test_analysis.py

# Copy updated analysis_modules __init__.py
copy src\analysis_modules\__init__.py C:\Users\RC34361\network-segmentation-analyzer\src\analysis_modules\__init__.py
```

---

### **Option B: Keep Directory Structure** (If analysis/ directory is needed)

If you need to keep `src/analysis/` as a directory, restructure it:

**1. On production, create `src/analysis/__init__.py`:**
```python
"""
Analysis Module
===============
Main traffic analysis and segmentation classes.
"""

# Import from the module file
from .traffic_analyzer import TrafficAnalyzer, SegmentationRule, NetworkZone

__all__ = ['TrafficAnalyzer', 'SegmentationRule', 'NetworkZone']
```

**2. Rename `src/analysis.py` → `src/analysis/traffic_analyzer.py`:**
```bash
# On production
move C:\Users\RC34361\network-segmentation-analyzer\src\analysis.py C:\Users\RC34361\network-segmentation-analyzer\src\analysis\traffic_analyzer.py
```

**3. Update imports across the codebase** (see list below)

---

### **Option C: Use Updated Import Logic** (Already Done)

The files have been updated with fallback imports:

**Files updated in development (copy to production):**

1. ✅ `tests/test_analysis.py` - Now tries multiple import methods
2. ✅ `src/analysis_modules/__init__.py` - Robust import with fallbacks

**Copy these files to production:**
```bash
# Copy updated files
scp tests/test_analysis.py RC34361@production:/path/to/tests/
scp src/analysis_modules/__init__.py RC34361@production:/path/to/src/analysis_modules/
```

---

## Files Changed (Ready to Deploy)

### 1. `tests/test_analysis.py`
**Change:** Added fallback import logic
```python
# Old:
from src.analysis import TrafficAnalyzer, SegmentationRule, NetworkZone

# New: (with fallbacks)
try:
    from src.analysis import TrafficAnalyzer, SegmentationRule, NetworkZone
except ImportError:
    from src.analysis_modules import TrafficAnalyzer, SegmentationRule, NetworkZone
```

### 2. `src/analysis_modules/__init__.py`
**Change:** More robust relative imports
```python
# Now tries relative import first
from ..analysis import TrafficAnalyzer, SegmentationRule, NetworkZone
```

---

## Verification Steps (Run on Production)

After deploying the changes:

### 1. Test Import
```bash
cd C:\Users\RC34361\network-segmentation-analyzer
python -c "from src.analysis import TrafficAnalyzer; print('✓ Import works')"
```

### 2. Run Tests
```bash
python -m pytest tests/test_analysis.py -v
```

### 3. Check Structure
```bash
# Verify file structure
dir src\analysis*
```

Expected output:
```
src\analysis.py          <- This should exist (the file)
src\analysis_modules\    <- This directory should exist
```

Should NOT have:
```
src\analysis\            <- This should NOT exist (unless you chose Option B)
```

---

## Root Cause Analysis

### Development Environment (Working)
```
src/
├── analysis.py          ← Single file with classes
├── analysis_modules/    ← Different module
│   └── __init__.py
└── parser.py
```

### Production Environment (Broken)
```
src/
├── analysis/            ← DIRECTORY (conflict!)
│   └── __init__.py
├── analysis.py          ← File being shadowed
├── analysis_modules/
│   └── __init__.py
└── parser.py
```

Python finds the **directory first** and ignores the `.py` file!

---

## Quick Deployment Commands

### For Windows PowerShell (Production):
```powershell
# Navigate to project
cd C:\Users\RC34361\network-segmentation-analyzer

# Check for conflicts
if (Test-Path "src\analysis" -PathType Container) {
    Write-Host "⚠️ WARNING: src\analysis directory exists - CONFLICT!"
    Write-Host "Backing up..."
    Rename-Item "src\analysis" "src\analysis.backup.$(Get-Date -Format 'yyyyMMdd')"
}

# Verify analysis.py exists
if (Test-Path "src\analysis.py") {
    Write-Host "✓ src\analysis.py exists"
} else {
    Write-Host "❌ ERROR: src\analysis.py is missing!"
}

# Run tests
python -m pytest tests/test_analysis.py -v
```

### For Git Deployment:
```bash
# On development machine
git add tests/test_analysis.py src/analysis_modules/__init__.py
git commit -m "Fix: Add fallback imports for production compatibility"
git push

# On production machine
cd C:\Users\RC34361\network-segmentation-analyzer
git pull
python -m pytest tests/test_analysis.py -v
```

---

## If Issues Persist

### Debug Import Issues:
```python
# Run this on production to diagnose
import sys
from pathlib import Path

project_root = Path(r"C:\Users\RC34361\network-segmentation-analyzer")
sys.path.insert(0, str(project_root))

print("Python path:")
for p in sys.path[:5]:
    print(f"  {p}")

print("\nTrying imports...")
try:
    import src.analysis
    print(f"✓ src.analysis found at: {src.analysis.__file__}")
except Exception as e:
    print(f"✗ src.analysis failed: {e}")

try:
    from src.analysis import TrafficAnalyzer
    print(f"✓ TrafficAnalyzer imported successfully")
except Exception as e:
    print(f"✗ TrafficAnalyzer import failed: {e}")

# Check for conflicts
analysis_file = project_root / "src" / "analysis.py"
analysis_dir = project_root / "src" / "analysis"
print(f"\nsrc/analysis.py exists: {analysis_file.exists()}")
print(f"src/analysis/ dir exists: {analysis_dir.exists()}")
```

---

## Summary

**Files to deploy to production:**
1. ✅ `tests/test_analysis.py` (updated with fallback imports)
2. ✅ `src/analysis_modules/__init__.py` (updated with relative imports)
3. ✅ Verify `src/analysis.py` exists (not a directory)

**After deployment, run:**
```bash
python -m pytest tests/test_analysis.py -v
```

**Expected result:** All 15 tests should pass ✓
