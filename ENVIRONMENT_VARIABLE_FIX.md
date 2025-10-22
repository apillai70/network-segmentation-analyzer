# Environment Variable Fix - Production Database Connection

## 🔴 Root Cause

The system **has** `.env.production` file, but it's not being loaded because the `ENVIRONMENT` variable defaults to `'development'`.

```python
# From src/config.py line 34:
self.environment = environment or os.getenv('ENVIRONMENT', 'development')
                                                           ^^^^^^^^^^^^
                                                           DEFAULTS TO development!
```

This means the system looks for `.env.development` instead of `.env.production`.

---

## ✅ Solution Options

### Option 1: Set ENVIRONMENT System Variable (RECOMMENDED)

Set a **Windows system environment variable** on the production VDI:

#### Via GUI (Permanent):
1. Right-click **This PC** → **Properties**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **System variables**, click **New**
5. Variable name: `ENVIRONMENT`
6. Variable value: `production`
7. Click **OK** on all dialogs
8. **Restart any open command prompts or Python processes**

#### Via PowerShell (Permanent):
```powershell
# Set system-wide environment variable (requires admin)
[System.Environment]::SetEnvironmentVariable('ENVIRONMENT', 'production', [System.EnvironmentVariableTarget]::Machine)

# Verify
[System.Environment]::GetEnvironmentVariable('ENVIRONMENT', [System.EnvironmentVariableTarget]::Machine)
```

#### Via Command Prompt (Session-only):
```cmd
# Set for current session only (not permanent)
set ENVIRONMENT=production

# Verify
echo %ENVIRONMENT%

# Run application
python run_batch_processing.py
```

---

### Option 2: Modify run_batch_processing.py

Add explicit environment setting at the top of your main script:

```python
# At the very top of run_batch_processing.py, BEFORE any imports
import os
os.environ['ENVIRONMENT'] = 'production'

# Then proceed with normal imports
from src.config import Config
from src.persistence.unified_persistence import UnifiedPersistenceManager
# ... rest of code
```

---

### Option 3: Create Wrapper Script (BEST FOR PRODUCTION)

Create a production launcher script:

**File:** `run_production.py`
```python
#!/usr/bin/env python3
"""
Production Environment Launcher
================================
Sets environment to production and runs batch processing.
"""

import os
import sys

# Force production environment
os.environ['ENVIRONMENT'] = 'production'

print("=" * 80)
print("PRODUCTION MODE")
print("=" * 80)
print(f"Environment: {os.environ.get('ENVIRONMENT')}")
print()

# Import and run main script
from run_batch_processing import main

if __name__ == '__main__':
    main()
```

**Usage:**
```bash
python run_production.py
```

---

### Option 4: Check .env.production Contents

Ensure your `.env.production` file includes `ENVIRONMENT=production` at the top:

**File:** `.env.production`
```bash
# Force production environment
ENVIRONMENT=production

# PostgreSQL Configuration
POSTGRES_HOST=your_server_here
POSTGRES_PORT=5432
POSTGRES_DB=network_segmentation
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
DB_SCHEMA=network_analysis
```

**BUT NOTE:** This only works if something loads `.env.production` first, which creates the chicken-and-egg problem.

---

## 🔍 Diagnostic Steps

### Step 1: Check Current Environment

```bash
# Windows Command Prompt
echo %ENVIRONMENT%

# PowerShell
$env:ENVIRONMENT

# Python
python -c "import os; print(f'ENVIRONMENT={os.getenv(\"ENVIRONMENT\", \"NOT SET\")}')"
```

**Expected:** `production`
**If you see:** `NOT SET` or `development`, that's the problem!

### Step 2: Check Which .env File is Loading

```bash
python -c "
from src.config import Config
config = Config()
print(f'Environment: {config.environment}')
print(f'Project root: {config.project_root}')
import os
print(f'POSTGRES_HOST: {os.getenv(\"POSTGRES_HOST\", \"NOT SET\")}')
"
```

**Expected Output:**
```
Environment: production
Project root: c:\Users\AjayPillai\project\network-segmentation-analyzer
POSTGRES_HOST: your_actual_server
```

**If you see:**
```
Environment: development
POSTGRES_HOST: localhost or NOT SET
```
Then the `.env.production` file is NOT being loaded!

### Step 3: Verify .env.production Exists and is Readable

```bash
cd c:\Users\AjayPillai\project\network-segmentation-analyzer

# Check file exists
dir .env.production

# Display contents (be careful - contains passwords!)
type .env.production

# Check file is not empty
wc .env.production
```

---

## 🛠️ Recommended Production Setup

### Create run_production.bat

**File:** `run_production.bat`
```batch
@echo off
REM ============================================================================
REM Production Environment Launcher
REM ============================================================================
REM This script ensures the application runs in production mode

echo ============================================================================
echo NETWORK SEGMENTATION ANALYZER - PRODUCTION MODE
echo ============================================================================

REM Set production environment
set ENVIRONMENT=production

REM Display environment
echo.
echo Environment: %ENVIRONMENT%
echo.

REM Run Python script
python run_batch_processing.py

REM Pause to see results
pause
```

**Usage:**
```bash
# Double-click run_production.bat
# OR
run_production.bat
```

---

## 📋 Verification Checklist

After applying the fix, verify:

- [ ] `ENVIRONMENT` variable is set to `production`
  ```bash
  echo %ENVIRONMENT%
  ```

- [ ] `.env.production` file exists
  ```bash
  dir .env.production
  ```

- [ ] `.env.production` contains correct PostgreSQL server (NOT localhost)
  ```bash
  findstr POSTGRES_HOST .env.production
  ```

- [ ] Python loads production config
  ```bash
  python -c "from src.config import Config; c=Config(); print(c.environment)"
  ```

- [ ] PostgreSQL connects to production server
  ```bash
  python -c "from src.persistence.unified_persistence import UnifiedPersistenceManager; m=UnifiedPersistenceManager(); print(f'Backend: {m.backend}')"
  ```

- [ ] Application runs without localhost errors
  ```bash
  python run_batch_processing.py | findstr "localhost"
  # Should return NOTHING (no matches)
  ```

---

## 🎯 Quick Fix for Client VDI

**Tell the client to run these commands:**

```bash
# Option A: Set system environment variable (permanent)
setx ENVIRONMENT production /M
# Note: Requires administrator privileges
# Note: Must restart command prompt after this

# Option B: Set for current session (temporary)
set ENVIRONMENT=production
python run_batch_processing.py

# Option C: Use wrapper script (recommended)
# 1. Create run_production.bat (see above)
# 2. Run: run_production.bat
```

---

## 📊 Expected vs Actual Behavior

### ❌ Current (Broken) Behavior

```
1. Application starts
2. Config loads: environment defaults to 'development'
3. Looks for: .env.development (doesn't exist)
4. Falls back to: .env (if exists) or defaults
5. POSTGRES_HOST defaults to: localhost
6. Connection fails: "connection to server at localhost"
7. Falls back to: JSON backend
```

### ✅ Fixed Behavior

```
1. Application starts
2. ENVIRONMENT=production is set (system variable or script)
3. Config loads: environment = 'production'
4. Looks for: .env.production (exists!)
5. Loads: POSTGRES_HOST=your_actual_server
6. Connection succeeds: "PostgreSQL connection successful"
7. Uses: postgres backend
```

---

## 🔧 Code Fix (If Needed)

If you want to make the code smarter about detecting production, you can modify `src/config.py`:

```python
def __init__(self, environment: Optional[str] = None):
    """Initialize configuration"""
    self.project_root = Path(__file__).parent.parent

    # Smart environment detection
    if environment:
        self.environment = environment
    else:
        # 1. Check ENVIRONMENT variable
        env = os.getenv('ENVIRONMENT')

        # 2. If not set, detect from .env files
        if not env:
            if (self.project_root / '.env.production').exists():
                env = 'production'
            elif (self.project_root / '.env.development').exists():
                env = 'development'
            else:
                env = 'development'  # Default

        self.environment = env

    # Load configurations
    self._load_env_file()
    self._load_yaml_config()
```

But this is a workaround - **Option 1 (system variable) is the proper solution**.

---

## 📞 Summary

**Problem:** `.env.production` exists but isn't being loaded because `ENVIRONMENT` defaults to `development`.

**Solution:** Set `ENVIRONMENT=production` via:
1. System environment variable (permanent, recommended)
2. Wrapper script (run_production.py or run_production.bat)
3. Set in code before imports

**Verification:**
```bash
# Should print: production
python -c "import os; print(os.getenv('ENVIRONMENT'))"

# Should print: postgres (not json)
python -c "from src.persistence.unified_persistence import UnifiedPersistenceManager; m=UnifiedPersistenceManager(); print(m.backend)"

# Should NOT contain "localhost"
python run_batch_processing.py 2>&1 | findstr "localhost"
```

---

**Created:** 2025-10-22
**Issue:** `.env.production` exists but not loading
**Root Cause:** `ENVIRONMENT` variable not set to `production`
**Fix:** Set system variable `ENVIRONMENT=production`
**Status:** Documented - Ready for client implementation
