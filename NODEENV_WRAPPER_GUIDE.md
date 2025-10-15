# Nodeenv Wrapper Scripts Guide

## Problem on Customer Machine

When running `python run_batch_processing.py`, mmdc (Mermaid CLI) cannot be found even though it's installed in nodeenv, resulting in:
- ✅ Lucidchart CSVs generated
- ❌ No Mermaid diagrams (.mmd files)
- ❌ No PNG files
- ❌ No Word documents

## Root Cause

The nodeenv needs to be **activated** before running Python scripts so that mmdc is in the PATH.

## Solution: Use Wrapper Scripts

We've created wrapper scripts that:
1. Activate the nodeenv (or source .bashrc)
2. Check if mmdc is available
3. Install mmdc if not found
4. Run batch processing with mmdc accessible

---

## Usage on Customer Machine

### Option 1: Shell Script (Linux/Mac/Git Bash)

```bash
# Make executable (first time only)
chmod +x run_batch_with_nodeenv.sh

# Run with default settings (batch size 10)
./run_batch_with_nodeenv.sh --batch-size 10 --clear-first

# Run with custom batch size
./run_batch_with_nodeenv.sh --batch-size 20 --clear-first

# With all filtering options
./run_batch_with_nodeenv.sh --batch-size 10 --clear-first --filter-nonexistent
```

**What it does:**
1. Sources `~/.bashrc` to set up environment
2. Activates `nodeenv/bin/activate` if exists
3. Checks for mmdc
4. Installs mmdc via npm if not found
5. Runs `python run_batch_processing.py` with your arguments

### Option 2: Batch File (Windows cmd.exe)

```cmd
REM Run with default settings
run_batch_with_nodeenv.bat --batch-size 10 --clear-first

REM Run with custom batch size
run_batch_with_nodeenv.bat --batch-size 20
```

### Option 3: PowerShell (Windows)

```powershell
# First time: Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run with default settings
.\run_batch_with_nodeenv.ps1 -BatchSize 10 -ClearFirst

# Run with custom batch size
.\run_batch_with_nodeenv.ps1 -BatchSize 20
```

---

## Diagnostic Script

If you're still having issues, run the diagnostic:

```bash
python test_mmdc_detection.py
```

**This will show:**
- ✓/✗ Whether mmdc is in PATH
- ✓/✗ Whether mmdc exists in nodeenv
- ✓/✗ Whether mmdc exists in npm global
- 📋 Your environment details
- 💡 Specific recommendations

---

## Manual Approach (If Wrappers Don't Work)

### Step 1: Activate Nodeenv

```bash
# Linux/Mac
source nodeenv/bin/activate

# Windows (cmd.exe)
nodeenv\Scripts\activate.bat

# Windows (PowerShell)
.\nodeenv\Scripts\Activate.ps1

# Windows (Git Bash)
source nodeenv/Scripts/activate
```

### Step 2: Verify mmdc

```bash
mmdc --version
# Should show: 11.12.0

which mmdc  # Linux/Mac
where mmdc  # Windows
```

### Step 3: Run Batch Processing

```bash
python run_batch_processing.py --batch-size 10 --clear-first
```

---

## Installation of mmdc (If Not Found)

If mmdc is not installed in your nodeenv:

```bash
# Activate nodeenv first
source nodeenv/bin/activate  # Linux/Mac
# OR
nodeenv\Scripts\activate.bat  # Windows

# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Verify
mmdc --version
```

---

## Example: Complete Workflow on Customer Machine

```bash
# 1. Navigate to project
cd C:\Users\RC34361\network-segmentation-analyzer

# 2. Run diagnostic (optional)
python test_mmdc_detection.py

# 3. Run batch processing with wrapper
./run_batch_with_nodeenv.sh --batch-size 10 --clear-first

# 4. Check outputs
ls -lh outputs_final/diagrams/*.png | wc -l          # Should show 139
ls -lh outputs_final/word_reports/architecture/*.docx | wc -l  # Should show 139
```

---

## Expected Output (Success)

```
================================================================================
BATCH PROCESSING WITH NODEENV
================================================================================

1. Setting up environment...
   Sourcing ~/.bashrc...
   ✓ Environment loaded
   Activating nodeenv...
   ✓ Nodeenv activated

2. Checking for mmdc (mermaid-cli)...
   ✓ Found: mmdc 11.12.0
   ✓ Location: /c/Users/RC34361/network-segmentation-analyzer/nodeenv/Scripts/mmdc

4. Starting batch processing...
   Command: python run_batch_processing.py --batch-size 10 --clear-first

================================================================================

BATCH PROCESSING ORCHESTRATOR
================================================================================
Batch size: 10 files per batch
...
STEP 2B: VERIFYING PNG FILES
✓ Found mmdc in nodeenv: C:\Users\RC34361\...\nodeenv\Scripts\mmdc
  ✓ ACDA.png
  ✓ ALE.png
  ...
PNG generation: 139/139 successful

✓ Architecture docs generated: 139
================================================================================
```

---

## Troubleshooting

### Issue: "nodeenv not found"

**Check if nodeenv exists:**
```bash
ls -la nodeenv/
ls -la nodeenv/Scripts/  # Windows
ls -la nodeenv/bin/      # Linux/Mac
```

**If missing, create nodeenv:**
```bash
pip install nodeenv
nodeenv nodeenv
```

### Issue: "npm not found"

**Install Node.js:**
- Download from https://nodejs.org/
- Or use nodeenv to get Node.js:
  ```bash
  pip install nodeenv
  nodeenv --node=18.0.0 nodeenv
  ```

### Issue: "mmdc still not found after activation"

**Install mmdc in nodeenv:**
```bash
# Activate nodeenv
source nodeenv/bin/activate  # Linux/Mac
nodeenv\Scripts\activate.bat  # Windows

# Install
npm install -g @mermaid-js/mermaid-cli

# Verify
mmdc --version
which mmdc
```

### Issue: "Permission denied"

**Make script executable:**
```bash
chmod +x run_batch_with_nodeenv.sh
chmod +x test_mmdc_detection.py
```

**Or run with bash directly:**
```bash
bash run_batch_with_nodeenv.sh --batch-size 10 --clear-first
```

---

## File Descriptions

| File | Purpose | Platform |
|------|---------|----------|
| `run_batch_with_nodeenv.sh` | Shell wrapper (RECOMMENDED) | Linux, Mac, Git Bash |
| `run_batch_with_nodeenv.bat` | Batch file wrapper | Windows cmd.exe |
| `run_batch_with_nodeenv.ps1` | PowerShell wrapper | Windows PowerShell |
| `test_mmdc_detection.py` | Diagnostic tool | All platforms |

---

## Quick Reference

```bash
# DIAGNOSTIC
python test_mmdc_detection.py

# WRAPPER (Linux/Mac/Git Bash) - RECOMMENDED
./run_batch_with_nodeenv.sh --batch-size 10 --clear-first

# WRAPPER (Windows cmd.exe)
run_batch_with_nodeenv.bat --batch-size 10 --clear-first

# WRAPPER (Windows PowerShell)
.\run_batch_with_nodeenv.ps1 -BatchSize 10 -ClearFirst

# MANUAL (if wrappers don't work)
source nodeenv/bin/activate  # or nodeenv\Scripts\activate.bat
python run_batch_processing.py --batch-size 10 --clear-first
```

---

## Success Criteria

After running the wrapper, you should have:

- ✅ **139 .mmd files** in `outputs_final/diagrams/`
- ✅ **139 .png files** in `outputs_final/diagrams/`
- ✅ **139 architecture .docx files** in `outputs_final/word_reports/architecture/`
- ✅ **Lucidchart CSVs** in `outputs_final/diagrams/`

**Verify:**
```bash
find outputs_final/diagrams -name "*_application_diagram.mmd" | wc -l   # Should be 139
find outputs_final/diagrams -name "*_application_diagram.png" | wc -l   # Should be 139
find outputs_final/word_reports -name "*.docx" | wc -l                  # Should be 278+
```

---

## Support

If none of these solutions work, provide:

1. Output of: `python test_mmdc_detection.py`
2. Output of: `echo $PATH` (or `echo %PATH%` on Windows)
3. Output of: `source nodeenv/bin/activate && mmdc --version`
4. Log file: `logs/batch_processing_*.log`
