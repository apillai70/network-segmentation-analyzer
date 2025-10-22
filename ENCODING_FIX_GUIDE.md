# UTF-8 Encoding Fix Guide

## Problem
You're experiencing `UnicodeDecodeError: 'charmap' codec can't decode` errors because some file operations in the codebase don't explicitly specify UTF-8 encoding.

## Solution
Use the `fix_encoding_issues.py` script to find and fix all encoding issues automatically.

---

## Quick Start (For Production)

### Step 1: Scan for Issues
```bash
python fix_encoding_issues.py --scan --dirs src tests
```

This will:
- Scan all Python files in `src` and `tests` directories
- Generate a detailed report
- Save results to `encoding_issues_report.txt`

### Step 2: Apply Fixes Automatically
```bash
python fix_encoding_issues.py --fix --dirs src tests
```

This will:
- Create `.bak` backup files for all modified files
- Automatically add `encoding='utf-8'` to all file operations
- Show a summary of changes

**IMPORTANT:** The script will ask for confirmation before making changes.

### Step 3: Verify Fixes
```bash
# Run your tests to ensure everything still works
python -m pytest tests/ -v

# Or run specific tests
python -m pytest tests/test_analysis.py -v
```

---

## Current Issues Found

The scan found **45 encoding issues** across **15 files**:

### High Priority Files (Most Issues)
1. `src/persistence/unified_persistence.py` - 13 issues
2. `src/core/incremental_learner.py` - 5 issues
3. `tests/test_analysis.py` - 4 issues
4. `tests/test_parser.py` - 3 issues

### All Affected Files
- src/dns_validation_reporter.py (2 issues)
- src/encoding_helper.py (1 issue)
- src/enterprise_report_generator.py (2 issues)
- src/agentic/graph_topology_analyzer.py (1 issue)
- src/agentic/local_semantic_analyzer.py (2 issues)
- src/agentic/unified_topology_system.py (2 issues)
- src/core/ensemble_model.py (2 issues)
- src/core/incremental_learner.py (5 issues)
- src/exporters/lucidchart_exporter.py (2 issues)
- src/orchestration/production_orchestrator.py (3 issues)
- src/persistence/unified_persistence.py (13 issues)
- src/utils/file_tracker.py (2 issues)
- tests/test_analysis.py (4 issues)
- tests/test_diagrams.py (1 issue)
- tests/test_parser.py (3 issues)

---

## Manual Fix Examples

If you prefer to fix issues manually, here are the patterns:

### 1. Fix `open()` calls
**Before:**
```python
with open(file_path, 'r') as f:
    content = f.read()
```

**After:**
```python
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

### 2. Fix `pd.read_csv()` calls
**Before:**
```python
df = pd.read_csv(file_path)
```

**After:**
```python
df = pd.read_csv(file_path, encoding='utf-8')
```

### 3. Fix `.read_text()` calls
**Before:**
```python
content = file_path.read_text()
```

**After:**
```python
content = file_path.read_text(encoding='utf-8')
```

### 4. Fix `.write_text()` calls
**Before:**
```python
file_path.write_text(content)
```

**After:**
```python
file_path.write_text(content, encoding='utf-8')
```

### 5. Binary Files (DO NOT ADD encoding)
```python
# These are correct - binary mode doesn't use encoding
with open(file_path, 'rb') as f:  # ✓ Correct
with open(file_path, 'wb') as f:  # ✓ Correct
```

---

## Command Reference

### Scan specific directories
```bash
python fix_encoding_issues.py --scan --dirs src tests scripts
```

### Scan everything
```bash
python fix_encoding_issues.py --scan --dirs .
```

### Fix without creating backups (NOT RECOMMENDED)
```bash
python fix_encoding_issues.py --fix --no-backup --dirs src
```

### Scan from a different path
```bash
python fix_encoding_issues.py --scan --path /path/to/project --dirs src
```

---

## For CI/CD Pipeline

Add this check to your CI pipeline to prevent encoding issues:

```bash
# In your CI script
python fix_encoding_issues.py --scan --dirs src tests
if [ $? -ne 0 ]; then
    echo "Encoding issues found! Please fix before merging."
    exit 1
fi
```

---

## Troubleshooting

### Issue: Script shows encoding errors on Windows
**Solution:** The script now handles this automatically. If you still see issues, run:
```bash
chcp 65001
python fix_encoding_issues.py --scan
```

### Issue: Backups taking up space
**Solution:** After verifying fixes work, delete backup files:
```bash
# PowerShell
Get-ChildItem -Recurse -Filter "*.bak" | Remove-Item

# Bash
find . -name "*.bak" -delete
```

### Issue: Some files still have encoding errors
**Solution:** Check for data files (CSV, JSON, TXT) that may have mixed encodings:
```bash
# Use the encoding helper
python -c "from src.encoding_helper import detect_encoding; print(detect_encoding('your_file.csv'))"
```

---

## Best Practices Going Forward

1. **Always specify encoding** when opening text files:
   ```python
   with open(file, 'r', encoding='utf-8') as f:
   ```

2. **Use UTF-8 everywhere** - it's the standard for modern Python

3. **For binary files** use `'rb'` or `'wb'` mode (no encoding parameter)

4. **Run the scan** periodically to catch new issues:
   ```bash
   python fix_encoding_issues.py --scan
   ```

5. **Add to pre-commit hook** (optional):
   ```bash
   # .git/hooks/pre-commit
   python fix_encoding_issues.py --scan --dirs src tests
   ```

---

## Summary of Changes

After running the fix script, you'll see changes like this:

**Example from src/analysis.py:**
```diff
- with open(output_file, 'w', newline='') as f:
+ with open(output_file, 'w', newline='', encoding='utf-8') as f:
```

**Example from tests/test_analysis.py:**
```diff
- content = output_file.read_text()
+ content = output_file.read_text(encoding='utf-8')
```

---

## Questions?

- Check the detailed report: `encoding_issues_report.txt`
- Run with verbose output: `python fix_encoding_issues.py --scan --dirs src`
- Review the backup files (`.bak`) if you need to revert changes

**Note:** The script is safe to run - it creates backups and asks for confirmation before making changes.
