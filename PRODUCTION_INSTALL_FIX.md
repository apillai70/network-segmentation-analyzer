# Production Installation Fix

## Problem

On production server RC34361, `pip install -e .` fails with:

```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 14806: character maps to <undefined>
```

**Root cause**: The production `setup.py` tries to read `README.md` without specifying UTF-8 encoding, so Windows defaults to cp1252 encoding which can't handle UTF-8 characters.

## Solution

The fix is already in your development `setup.py` (line 4), but production needs to be updated.

### Quick Fix (Manual - 30 seconds)

**On production server RC34361:**

```bash
cd ~/network-segmentation-analyzer

# Make backup
cp setup.py setup.py.backup

# Edit setup.py line 4
# Change:     with open("README.md") as f:
# To:         with open("README.md", encoding="utf-8") as f:
```

**Edit with nano/vim:**
```bash
nano setup.py
```

Find line 4 and change it from:
```python
with open("README.md") as f:
```

To:
```python
with open("README.md", encoding="utf-8") as f:
```

Save and try again:
```bash
pip install -e .
```

---

### Automated Fix (Recommended)

Use the provided scripts to automatically apply the fix:

#### Option 1: Using Git Bash (on Windows)

```bash
cd ~/network-segmentation-analyzer

# Pull latest code (includes the fix scripts)
git pull

# Run the bash script
bash fix_production_setup.sh
```

#### Option 2: Using PowerShell

```powershell
cd C:\Users\RC34361\network-segmentation-analyzer

# Pull latest code (includes the fix scripts)
git pull

# Run the PowerShell script
.\fix_production_setup.ps1
```

The script will:
- ✅ Check if setup.py needs fixing
- ✅ Create automatic backup
- ✅ Apply the UTF-8 encoding fix
- ✅ Test `pip install -e .`
- ✅ Restore backup if anything fails

---

## Verification

After applying the fix, verify it works:

```bash
# Should succeed without errors
pip install -e .

# Should output: Successfully installed network-segmentation-analyzer-1.0.0

# Verify imports work
python -c "from src.analysis import TrafficAnalyzer; print('✓ Import successful')"

# Run tests
python -m pytest tests/ -v
```

**Expected**: All 35 tests pass ✅

---

## The Complete Fix

Your updated `setup.py` should look like this:

```python
from setuptools import setup, find_packages

# Read README with UTF-8 encoding to avoid Windows encoding issues
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="network-segmentation-analyzer",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "networkx>=3.0",
        "scikit-learn>=1.3.0",
    ],
    python_requires=">=3.8",
    author="Your Team",
    description="Enterprise Network Segmentation Analysis with ML/DL",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
```

**Key change**: Line 4 now has `encoding="utf-8"` parameter.

---

## Alternative: Deploy from Development

If you can't edit files on production directly:

```bash
# On development machine (where you are now)
git add setup.py fix_production_setup.sh fix_production_setup.ps1 PRODUCTION_INSTALL_FIX.md
git commit -m "Fix: Add UTF-8 encoding to setup.py for Windows compatibility"
git push

# On production RC34361
cd ~/network-segmentation-analyzer
git pull
pip install -e .
```

---

## Why This Happens

1. **README.md contains UTF-8 characters** (emojis, special symbols, etc.)
2. **Windows defaults to cp1252 encoding** when opening files
3. **cp1252 can't decode UTF-8 byte 0x90** → UnicodeDecodeError
4. **Solution**: Always specify `encoding="utf-8"` when opening text files on Windows

---

## Related Issues

If you see similar errors elsewhere in the codebase, use the same fix:

```python
# BAD (Windows will fail on UTF-8 files)
with open("file.txt") as f:
    content = f.read()

# GOOD (Works on all platforms)
with open("file.txt", encoding="utf-8") as f:
    content = f.read()
```

Run the encoding scanner to find all such issues:
```bash
python fix_encoding_issues.py --scan --dirs src tests
```

---

## Summary

| Step | Command | Expected Result |
|------|---------|----------------|
| 1. Pull latest code | `git pull` | Already up to date |
| 2. Run fix script | `bash fix_production_setup.sh` | ✓ Applied fix |
| 3. Install package | `pip install -e .` | Successfully installed |
| 4. Verify import | `python -c "from src.analysis import TrafficAnalyzer"` | No errors |
| 5. Run tests | `python -m pytest tests/ -v` | 35 passed ✅ |

**Estimated time**: 2 minutes
