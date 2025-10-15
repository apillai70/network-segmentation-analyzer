# Clean Up and Fresh Start Guide

## Problem: System Has Old Data

If you see:
- "Tracked files: 140" (but you haven't processed 140 files)
- "Files processed: 140"
- Old applications in topology that you didn't add

**This means:** System has data from previous runs (demo/synthetic data)

---

## Solution: Complete Clean Up

### Step 1: Stop Any Running Processes

```bash
# Press Ctrl+C if run_incremental_learning.py is running
# Or kill it:
pkill -f run_incremental_learning.py
```

### Step 2: Clean Up Command (All-in-One)

```bash
# Navigate to project directory
cd /path/to/network-segmentation-analyzer

# Run cleanup script
python scripts/cleanup_for_fresh_start.py
```

**If script doesn't exist, use manual cleanup below:**

### Step 3: Manual Complete Cleanup

```bash
# Delete processed file tracking
rm -f outputs_final/persistent_data/file_tracking.json
rm -f outputs_final/persistent_data/.file_tracker

# Delete topology data
rm -f outputs_final/incremental_topology.json
rm -rf outputs_final/persistent_data/topology/
rm -rf outputs_final/persistent_data/flows/

# Delete all generated outputs
rm -rf outputs_final/diagrams/*.png
rm -rf outputs_final/diagrams/*.mmd
rm -rf outputs_final/diagrams/*.html
rm -rf outputs_final/word_reports/*

# Delete model checkpoints
rm -rf models/incremental/*
rm -rf models/ensemble/*

# Delete old logs (optional)
rm -f logs/*.log

# Keep only applicationList.csv, delete generated files
cd data/input
find . -name "App_Code_*.csv" -delete
# Keep applicationList.csv
```

**On Windows:**
```cmd
del /Q outputs_final\persistent_data\file_tracking.json
del /Q outputs_final\incremental_topology.json
rmdir /S /Q outputs_final\persistent_data\topology
rmdir /S /Q outputs_final\persistent_data\flows
del /Q outputs_final\diagrams\*.png
del /Q outputs_final\diagrams\*.mmd
del /Q outputs_final\diagrams\*.html
rmdir /S /Q outputs_final\word_reports
rmdir /S /Q models\incremental
rmdir /S /Q models\ensemble
cd data\input
del /Q App_Code_*.csv
```

### Step 4: Recreate Directories

```bash
mkdir -p outputs_final/persistent_data/topology
mkdir -p outputs_final/persistent_data/flows
mkdir -p outputs_final/diagrams
mkdir -p outputs_final/word_reports/architecture
mkdir -p outputs_final/word_reports/netseg
mkdir -p models/incremental
mkdir -p models/ensemble
mkdir -p logs
```

### Step 5: Move Your File to Correct Location

```bash
# Your file is in data/ but needs to be in data/input/
mv data/App_Code_AODSVY.csv data/input/App_Code_AODSVY.csv

# Verify
ls -l data/input/
# Should show: applicationList.csv and App_Code_AODSVY.csv
```

**On Windows:**
```cmd
move data\App_Code_AODSVY.csv data\input\App_Code_AODSVY.csv
dir data\input\
```

### Step 6: Verify Clean State

```bash
# Check file tracking
python scripts/manage_file_tracking.py --list
# Should show: "No files tracked"

# Check topology
cat outputs_final/incremental_topology.json 2>/dev/null || echo "File doesn't exist - Good!"

# Check input directory
ls -l data/input/
# Should show ONLY:
# - applicationList.csv
# - App_Code_AODSVY.csv
```

---

## Now Process Your First Real File

### Step 1: Verify File is in Correct Location

```bash
ls -l data/input/App_Code_AODSVY.csv
# Should exist!

# Check first few lines
head -5 data/input/App_Code_AODSVY.csv
```

### Step 2: Run Processing

```bash
python run_incremental_learning.py --batch
```

**Expected Output:**
```
================================================================================
INCREMENTAL LEARNING SYSTEM v3.0
================================================================================
[CONTINUOUS] Topology discovery as files arrive...

📦 Initializing components...
✓ All components initialized

📊 Running in BATCH mode...
Processing 1 new file(s)...
[1/1] App_Code_AODSVY.csv
  ✓ Processed: 1 files
  ✓ Flows: XX flows

✅ Batch processing complete!
  Files processed: 1        # <-- Should be 1, not 140!
  Successful: 1
  Failed: 0
```

### Step 3: Verify Results

```bash
# Check tracking
python scripts/manage_file_tracking.py --list
# Should show: 1 file (App_Code_AODSVY.csv)

# Check topology
python -c "
import json
with open('outputs_final/incremental_topology.json', 'r') as f:
    data = json.load(f)
    print(f'Total Apps: {data[\"total_apps\"]}')
    print(f'Apps: {data[\"apps_observed\"]}')
"
# Should show: Total Apps: 1, Apps: ['AODSVY']
```

### Step 4: Generate Reports

```bash
# Generate diagrams
python generate_application_reports.py

# Generate documents
python generate_solution_design_docs.py

# Check outputs
ls -lh outputs_final/diagrams/AODSVY*
ls -lh outputs_final/word_reports/architecture/Solution_Design-AODSVY.docx
```

---

## Quick Cleanup Command (Copy-Paste Ready)

### Linux/Mac

```bash
#!/bin/bash
echo "🧹 Cleaning up for fresh start..."

# Delete tracking and data
rm -f outputs_final/persistent_data/file_tracking.json
rm -f outputs_final/incremental_topology.json
rm -rf outputs_final/persistent_data/topology/
rm -rf outputs_final/persistent_data/flows/
rm -rf outputs_final/diagrams/*
rm -rf outputs_final/word_reports/*
rm -rf models/incremental/*
rm -rf models/ensemble/*

# Recreate structure
mkdir -p outputs_final/{persistent_data/{topology,flows},diagrams,word_reports/{architecture,netseg}}
mkdir -p models/{incremental,ensemble}
mkdir -p logs

# Move file if needed
if [ -f "data/App_Code_AODSVY.csv" ]; then
    mv data/App_Code_AODSVY.csv data/input/
    echo "✓ Moved App_Code_AODSVY.csv to data/input/"
fi

echo "✅ Cleanup complete!"
echo "📁 Files in data/input/:"
ls -l data/input/

echo ""
echo "🚀 Ready to run:"
echo "   python run_incremental_learning.py --batch"
```

### Windows (PowerShell)

```powershell
Write-Host "🧹 Cleaning up for fresh start..." -ForegroundColor Yellow

# Delete tracking and data
Remove-Item -Force -ErrorAction SilentlyContinue outputs_final\persistent_data\file_tracking.json
Remove-Item -Force -ErrorAction SilentlyContinue outputs_final\incremental_topology.json
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue outputs_final\persistent_data\topology
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue outputs_final\persistent_data\flows
Remove-Item -Force -ErrorAction SilentlyContinue outputs_final\diagrams\*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue outputs_final\word_reports\*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue models\incremental\*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue models\ensemble\*

# Recreate structure
New-Item -ItemType Directory -Force -Path outputs_final\persistent_data\topology | Out-Null
New-Item -ItemType Directory -Force -Path outputs_final\persistent_data\flows | Out-Null
New-Item -ItemType Directory -Force -Path outputs_final\diagrams | Out-Null
New-Item -ItemType Directory -Force -Path outputs_final\word_reports\architecture | Out-Null
New-Item -ItemType Directory -Force -Path outputs_final\word_reports\netseg | Out-Null
New-Item -ItemType Directory -Force -Path models\incremental | Out-Null
New-Item -ItemType Directory -Force -Path models\ensemble | Out-Null

# Move file if needed
if (Test-Path "data\App_Code_AODSVY.csv") {
    Move-Item data\App_Code_AODSVY.csv data\input\App_Code_AODSVY.csv -Force
    Write-Host "✓ Moved App_Code_AODSVY.csv to data\input\" -ForegroundColor Green
}

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host "📁 Files in data\input\:" -ForegroundColor Cyan
Get-ChildItem data\input\

Write-Host ""
Write-Host "🚀 Ready to run:" -ForegroundColor Yellow
Write-Host "   python run_incremental_learning.py --batch"
```

---

## Troubleshooting After Cleanup

### Issue: Still Says "Tracked files: 140"

```bash
# Force reset tracking
python scripts/manage_file_tracking.py --reset

# Or manually delete
rm -f outputs_final/persistent_data/file_tracking.json
rm -f outputs_final/persistent_data/.file_tracker
```

### Issue: File Not Found After Moving

```bash
# Check all locations
find . -name "App_Code_AODSVY.csv"

# Should be in: ./data/input/App_Code_AODSVY.csv
```

### Issue: Permission Denied

```bash
# Fix permissions
chmod -R u+w outputs_final/
chmod -R u+w models/

# Or use sudo (if needed)
sudo rm -rf outputs_final/persistent_data/*
```

---

## Verification Checklist

After cleanup, verify:

- [ ] `python scripts/manage_file_tracking.py --list` shows 0 or "No files tracked"
- [ ] `outputs_final/incremental_topology.json` doesn't exist or is empty
- [ ] `data/input/App_Code_AODSVY.csv` exists
- [ ] `data/input/applicationList.csv` exists
- [ ] No other `App_Code_*.csv` files in `data/input/`

Then run:
```bash
python run_incremental_learning.py --batch
```

Should show:
- "Processing 1 new file(s)"
- "Files processed: 1"
- "Total Apps: 1"

---

## Summary

**Your Issue:** System had 140 tracked files from previous demo/synthetic data generation

**Solution:**
1. Clean up all old data (tracking, topology, models)
2. Move your file from `data/` to `data/input/`
3. Run processing fresh
4. Verify only 1 file processed

**Key Point:** Always start with a clean state when switching from demo to real customer data!

---

**Next Steps After Successful Processing:**

```bash
# 1. Verify single app processed
python scripts/manage_file_tracking.py --list
# Should show: 1 file

# 2. Generate diagrams
python generate_application_reports.py

# 3. Generate documents
python generate_solution_design_docs.py

# 4. Add next file
cp /path/to/App_Code_NEXTAPP.csv data/input/
python run_incremental_learning.py --batch
```
