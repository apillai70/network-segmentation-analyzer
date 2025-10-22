# Quick Fix: PostgreSQL Connection to localhost

## 🔴 Problem
```
PostgreSQL connection failed: connection to server at "localhost" (127.0.0.1)
```

## ✅ Solution (Choose ONE)

### Option 1: Set Windows Environment Variable (RECOMMENDED)
```cmd
REM Run as Administrator
setx ENVIRONMENT production /M

REM Then restart command prompt and run:
python run_batch_processing.py
```

### Option 2: Create Wrapper Script
Create `run_production.bat`:
```batch
@echo off
set ENVIRONMENT=production
python run_batch_processing.py
pause
```

Run: `run_production.bat`

### Option 3: Modify Main Script
Add at the TOP of `run_batch_processing.py` (before imports):
```python
import os
os.environ['ENVIRONMENT'] = 'production'
```

## 🔍 Verify Fix
```bash
REM Should print: production
python -c "import os; print(os.getenv('ENVIRONMENT'))"

REM Should print: postgres (not json)
python -c "from src.persistence.unified_persistence import UnifiedPersistenceManager; m=UnifiedPersistenceManager(); print(m.backend)"
```

## 📋 Root Cause
- `.env.production` file exists ✓
- But `ENVIRONMENT` variable not set
- System defaults to `development`
- Looks for `.env.development` instead
- Falls back to `localhost` default

## 📖 Full Documentation
See: `ENVIRONMENT_VARIABLE_FIX.md` for complete details

---
**Quick Reference Created:** 2025-10-22
