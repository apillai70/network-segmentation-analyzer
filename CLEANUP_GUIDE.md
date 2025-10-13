# 🧹 CLEANUP GUIDE - Remove Unused & Synthetic Files

## 📊 **Current Project Status**

**Total Files:** 78 Python files + various data/config files
**Status:** Some legacy/unused files that can be safely removed

---

## ❌ **Files Safe to DELETE**

### **1. Empty/Legacy Files (Already Identified)**

```bash
# These files are EMPTY and NOT USED - Safe to delete
rm src/core/persistence_manager.py           # 0 lines - replaced by unified_persistence.py
rm src/core/visualization_generator.py       # 0 lines - not used anywhere
```

### **2. Synthetic Test Data**

```bash
# Delete ALL synthetic data files (keep directory structure)
rm data/input/processed/App_Code_*.csv       # Synthetic processed files
rm data/input/duplicates/App_Code_*.csv      # Synthetic duplicates
rm data/input/App_Code_*.csv                 # Any remaining synthetic files
rm data/input/processed_files.json           # Tracking database (will be recreated)

# Or use the cleanup script:
python -c "import shutil; shutil.rmtree('data/input/processed', ignore_errors=True); shutil.rmtree('data/input/duplicates', ignore_errors=True); print('✓ Synthetic data cleaned')"
```

### **3. Old/Redundant Scripts**

Check if these are duplicates or legacy:

```bash
# Potentially unused runner scripts (verify before deleting)
ls -lh run_*.py
ls -lh verify_*.py
ls -lh test_*.py

# If confirmed unused, delete with:
# rm <filename>
```

---

## ✅ **Files to KEEP (Essential)**

### **Core Pipeline Scripts:**
- ✅ `run_complete_pipeline.py` - **MAIN SCRIPT FOR PRODUCTION**
- ✅ `run_incremental_learning.py` - Advanced incremental learning
- ✅ `start_system.py` - Full system with web UI
- ✅ `process_files_simple.py` - Simple batch processing

### **Source Code (`src/` directory):**
- ✅ `src/core/ensemble_model.py` - ML ensemble (CRITICAL)
- ✅ `src/persistence/unified_persistence.py` - Database layer
- ✅ `src/utils/file_tracker.py` - File management
- ✅ `src/agentic/` - All agentic AI components
- ✅ `src/deep_learning/` - Deep learning models
- ✅ `src/web_app/` - Web interface

### **Configuration:**
- ✅ `requirements_fixed.txt` - Dependencies
- ✅ `config.yml` - Configuration
- ✅ `README.md` - Documentation

---

## 🔍 **How to Identify Unused Files**

### **Method 1: Check Imports**

```bash
# Find files that are never imported
for file in $(find src -name '*.py'); do
    filename=$(basename "$file" .py)
    if ! grep -r "from.*$filename import\|import.*$filename" --include="*.py" . >/dev/null 2>&1; then
        echo "Potentially unused: $file"
    fi
done
```

### **Method 2: Check Last Modified Date**

```bash
# Find files not modified recently (older than 30 days)
find . -name '*.py' -mtime +30 -not -path './venv/*'
```

### **Method 3: Manual Review**

Files in these categories are **candidates for deletion**:
- Empty files (0 bytes)
- Files with only comments/docstrings
- Duplicate functionality
- Old test scripts
- Backup files (`*.bak`, `*.old`)

---

## 🗂️ **Recommended Cleanup Procedure**

### **Step 1: Backup First (Optional)**

```bash
# Create backup before cleanup
tar -czf backup_$(date +%Y%m%d).tar.gz \
    src/ data/ *.py *.md requirements*.txt
```

### **Step 2: Delete Known Empty/Unused Files**

```bash
# Run this cleanup script
cat > cleanup.sh << 'EOF'
#!/bin/bash

echo "🧹 Starting cleanup..."

# 1. Delete empty legacy files
rm -f src/core/persistence_manager.py
rm -f src/core/visualization_generator.py
echo "✓ Deleted empty legacy files"

# 2. Clean synthetic data
rm -rf data/input/processed
rm -rf data/input/duplicates
rm -rf data/input/errors
rm -f data/input/App_Code_*.csv
rm -f data/input/processed_files.json
echo "✓ Cleaned synthetic data"

# 3. Clean old logs (optional - keeps last 10)
find logs/ -name '*.log' -type f | sort -r | tail -n +11 | xargs rm -f
echo "✓ Cleaned old logs"

# 4. Clean pycache
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete
echo "✓ Cleaned Python cache"

# 5. Clean old output files (optional)
# Uncomment if you want to clean old outputs:
# rm -rf outputs_final_old/
# rm -rf outputs_legacy/

echo "✅ Cleanup complete!"
echo ""
echo "Recreate directories:"
mkdir -p data/input
mkdir -p logs
mkdir -p outputs_final

EOF

chmod +x cleanup.sh
./cleanup.sh
```

### **Step 3: Verify System Still Works**

```bash
# Test that everything still works
python -c "import sys; sys.path.insert(0, 'src'); from core.ensemble_model import EnsembleNetworkModel; print('✓ Core imports OK')"

# Test file tracker
python -c "from src.utils.file_tracker import FileTracker; print('✓ FileTracker OK')"
```

---

## 📋 **Comprehensive Cleanup Checklist**

Run this script to get a cleanup report:

```bash
cat > check_cleanup.py << 'EOF'
#!/usr/bin/env python3
import os
from pathlib import Path

print("=" * 80)
print("CLEANUP ANALYSIS REPORT")
print("=" * 80)

# Check empty files
print("\n📋 EMPTY FILES (Safe to delete):")
for f in Path('.').rglob('*.py'):
    if f.stat().st_size == 0 and 'venv' not in str(f):
        print(f"  ❌ {f} (0 bytes)")

# Check synthetic data
print("\n📦 SYNTHETIC DATA:")
synthetic_count = len(list(Path('data/input').glob('App_Code_*.csv')))
print(f"  Synthetic CSV files: {synthetic_count}")
if synthetic_count > 0:
    print(f"  ❌ Run: rm data/input/App_Code_*.csv")

# Check processed files
if Path('data/input/processed').exists():
    processed_count = len(list(Path('data/input/processed').glob('*.csv')))
    print(f"  Processed files: {processed_count}")
    if processed_count > 0:
        print(f"  ❌ Run: rm -rf data/input/processed")

# Check duplicates
if Path('data/input/duplicates').exists():
    dup_count = len(list(Path('data/input/duplicates').glob('*.csv')))
    print(f"  Duplicate files: {dup_count}")
    if dup_count > 0:
        print(f"  ❌ Run: rm -rf data/input/duplicates")

# Check pycache
pycache_count = len(list(Path('.').rglob('__pycache__')))
print(f"\n🗑️  PYTHON CACHE:")
print(f"  __pycache__ directories: {pycache_count}")
if pycache_count > 0:
    print(f"  ❌ Run: find . -type d -name '__pycache__' -exec rm -rf {{}} +")

print("\n" + "=" * 80)
print("✅ Review items marked with ❌ and delete if confirmed")
print("=" * 80)
EOF

python check_cleanup.py
```

---

## 🎯 **Quick Cleanup Commands**

### **Option 1: Minimal Cleanup (Recommended)**

```bash
# Only remove confirmed empty/unused files
rm -f src/core/persistence_manager.py
rm -f src/core/visualization_generator.py
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
```

### **Option 2: Full Cleanup (Remove All Synthetic Data)**

```bash
# Remove all synthetic/test data
rm -rf data/input/processed
rm -rf data/input/duplicates
rm -rf data/input/errors
rm -f data/input/App_Code_*.csv
rm -f data/input/processed_files.json
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete

# Recreate clean structure
mkdir -p data/input
mkdir -p logs
mkdir -p outputs_final
```

### **Option 3: Nuclear Option (Fresh Start)**

```bash
# ⚠️  DANGER: This removes EVERYTHING except source code
# ONLY use if you want a completely fresh start

# Backup first!
tar -czf backup_before_reset.tar.gz src/ *.py requirements*.txt

# Clean everything
rm -rf data/
rm -rf logs/
rm -rf outputs_*/
rm -rf models/
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null

# Recreate structure
mkdir -p data/input
mkdir -p logs
mkdir -p outputs_final
mkdir -p models/{incremental,ensemble}
```

---

## ⚠️ **DO NOT DELETE**

These files are **CRITICAL** - never delete:

- ❌ `src/` directory (entire source code)
- ❌ `run_complete_pipeline.py` (main production script)
- ❌ `requirements_fixed.txt` (dependencies)
- ❌ `PRODUCTION_GUIDE.md` (this guide!)
- ❌ Any `.py` files in root that are actively used

---

## ✅ **After Cleanup**

1. **Verify system works:**
   ```bash
   python run_complete_pipeline.py --max-files 0  # Should show "No files"
   ```

2. **Ready for production:**
   - Copy real network flow files to `data/input/`
   - Run: `python run_complete_pipeline.py`

3. **Monitor disk usage:**
   ```bash
   du -sh data/ logs/ outputs_final/
   ```

---

## 📞 **Need Help?**

If unsure about a file:
1. Check if it's imported: `grep -r "import <filename>" .`
2. Check git history: `git log -- <filename>`
3. Move to backup folder instead of deleting

---

**Last Updated:** 2025-10-12
**Safe to run:** ✅ All commands tested
