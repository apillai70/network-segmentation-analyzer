# ⚠️ CRITICAL NOTES FOR CUSTOMER DEPLOYMENT

## DO NOT USE `start_system.py` FOR REAL CUSTOMER DATA!

### ❌ WRONG (Will Delete Your Data!)

```bash
# This is for DEMOS ONLY!
python start_system.py --web --generate-data 50
```

**This will:**
- Delete all existing data in `outputs_final/`
- Delete processed file tracking
- Generate synthetic/fake data
- NOT use your real customer files

### ✅ CORRECT (For Customer Deployment)

```bash
# Step 1: Add real customer files
cp /path/to/App_Code_*.csv data/input/

# Step 2: Process files
python run_incremental_learning.py --batch

# Step 3: Generate diagrams (REQUIRED FIRST!)
python generate_application_reports.py

# Step 4: Generate documents (embeds diagrams)
python generate_solution_design_docs.py
```

---

## Report Generation: Correct Order

### ❌ WRONG Order

```bash
# This will create documents with "diagram not found" errors!
python generate_solution_design_docs.py  # NO diagrams exist yet!
```

### ✅ CORRECT Order

```bash
# 1. Generate diagrams FIRST (creates PNG files)
python generate_application_reports.py

# 2. Generate documents SECOND (embeds PNG files)
python generate_solution_design_docs.py
```

**Why?** Word documents embed diagrams that must already exist!

---

## When CAN You Use `start_system.py`?

### Safe Usage:

```bash
# If you want the web UI with real data:
python start_system.py --web --skip-cleanup

# The --skip-cleanup flag prevents data deletion!
```

### Use Cases:

| Scenario | Command | Safe? |
|----------|---------|-------|
| Demo with fake data | `start_system.py --web --generate-data 50` | ✓ Safe for demos |
| Customer deployment | `start_system.py --web` | ❌ Will delete data! |
| Customer deployment with UI | `start_system.py --web --skip-cleanup` | ✓ Safe with flag |
| Customer deployment (no UI) | `run_incremental_learning.py --batch` | ✅ Recommended |

---

## File Naming: Must Be Exact

### ❌ WRONG

```
data/input/
├── myapp_flows.csv        # Wrong name!
├── application_data.csv   # Wrong name!
└── XECHK.csv             # Missing prefix!
```

### ✅ CORRECT

```
data/input/
├── App_Code_XECHK.csv    # ✓ Correct format
├── App_Code_ACDA.csv     # ✓ Correct format
└── App_Code_DPAPI.csv    # ✓ Correct format
```

**Format:** `App_Code_{APP_ID}.csv`

---

## Configuration: JSON Mode

### ❌ WRONG (Requires PostgreSQL)

```yaml
database:
  postgresql:
    enabled: true  # Will fail if no database!
```

### ✅ CORRECT (JSON-only mode)

```yaml
database:
  postgresql:
    enabled: false  # Uses JSON files instead
```

---

## Complete Workflow Checklist

- [ ] Files named correctly: `App_Code_{APP_ID}.csv`
- [ ] Config set to JSON mode: `postgresql.enabled = false`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Files copied to: `data/input/`
- [ ] Process files: `run_incremental_learning.py --batch`
- [ ] Generate diagrams FIRST: `generate_application_reports.py`
- [ ] Generate documents SECOND: `generate_solution_design_docs.py`
- [ ] Did NOT use `start_system.py` without `--skip-cleanup`

---

## Quick Command Summary

```bash
# 1. Setup (once)
pip install -r requirements.txt
vi config.yaml  # Set postgresql.enabled = false

# 2. Process customer files
cp /customer/files/App_Code_*.csv data/input/
python run_incremental_learning.py --batch

# 3. Generate reports (IN THIS ORDER!)
python generate_application_reports.py       # Step 1: Diagrams
python generate_solution_design_docs.py      # Step 2: Documents

# 4. Optional: Web UI (with safety flag)
python start_system.py --web --skip-cleanup
```

---

## Emergency Recovery

### If You Accidentally Ran `start_system.py`

```bash
# Your data has been deleted! Restore from backup:
tar -xzf backup_latest.tar.gz

# Or reprocess all files:
python scripts/manage_file_tracking.py --reset
cp /customer/files/App_Code_*.csv data/input/
python run_incremental_learning.py --batch
```

**Prevention:** Always use `--skip-cleanup` flag or avoid `start_system.py` entirely!

---

## Contact

If confused, always refer to:
- **CUSTOMER_DEPLOYMENT_GUIDE.md** - Complete guide
- **QUICK_REFERENCE_CARD.md** - Quick commands
- **This file (CRITICAL_NOTES.md)** - Common mistakes

**Remember:** When in doubt, use `run_incremental_learning.py` directly!

---

**Last Updated:** October 2025
