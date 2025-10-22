# Production Database Connection Fix

## 🔴 Issue

PostgreSQL is trying to connect to `localhost` instead of the production server.

**Error Message:**
```
PostgreSQL connection failed: connection to server at "localhost" (127.0.0.1), port 5432 failed
Connection refused (0x0000274D/10061)
Is the server running on that host and accepting TCP/IP connections?
```

**Root Cause:**
The `.env.production` file is missing or not properly configured on the client/production VDI, causing the system to use default `localhost` instead of the actual PostgreSQL server address.

---

## ✅ Solution

### Step 1: Create `.env.production` File

On the **client/production VDI**, create a file named `.env.production` in the project root directory:

```bash
# Navigate to project directory
cd c:\Users\AjayPillai\project\network-segmentation-analyzer

# Create .env.production file
notepad .env.production
```

### Step 2: Add PostgreSQL Configuration

Add the following content to `.env.production` (replace with your actual values):

```bash
# ============================================================================
# PRODUCTION DATABASE CONFIGURATION
# ============================================================================
# NEVER commit this file to git!
# This file contains production credentials and should be kept secure.

# PostgreSQL Server Settings
# ---------------------------
# Replace these values with your actual production PostgreSQL server details

# PostgreSQL server hostname or IP address
# Example: pgserver.company.com or 10.10.10.50
POSTGRES_HOST=YOUR_POSTGRES_SERVER_HERE

# PostgreSQL port (usually 5432)
POSTGRES_PORT=5432

# Database name
POSTGRES_DB=network_segmentation

# Database user
POSTGRES_USER=YOUR_DB_USERNAME_HERE

# Database password
POSTGRES_PASSWORD=YOUR_DB_PASSWORD_HERE

# Database schema (optional, defaults to 'network_analysis')
DB_SCHEMA=network_analysis

# Environment indicator
ENVIRONMENT=production

# ============================================================================
# OPTIONAL: Additional Settings
# ============================================================================

# Connection timeout (seconds)
DB_CONNECT_TIMEOUT=10

# Connection pool size
DB_POOL_SIZE=10

# Enable connection pooling
DB_POOLING=true

# ============================================================================
# IMPORTANT SECURITY NOTES
# ============================================================================
# 1. NEVER commit this file to git
# 2. Keep file permissions restricted
# 3. Use strong passwords
# 4. Rotate credentials regularly
# 5. Only share via secure channels
```

### Step 3: Set Actual Values

**Example with real values** (DO NOT use these - they're examples):

```bash
# PostgreSQL server on VDI
POSTGRES_HOST=10.147.20.100
POSTGRES_PORT=5432
POSTGRES_DB=network_segmentation
POSTGRES_USER=network_admin
POSTGRES_PASSWORD=SecureP@ssw0rd123!
DB_SCHEMA=network_analysis
ENVIRONMENT=production
```

### Step 4: Verify Configuration

Run this test script to verify the connection:

```bash
python -c "
import os
from src.config import Config
from src.persistence.unified_persistence import UnifiedPersistenceManager

# Load config
config = Config(environment='production')

# Test connection
persistence = UnifiedPersistenceManager()

print('✓ Configuration loaded')
print(f'✓ Backend: {persistence.backend}')
print(f'✓ Host: {os.getenv(\"POSTGRES_HOST\")}')
print(f'✓ Database: {os.getenv(\"POSTGRES_DB\")}')
"
```

**Expected Output:**
```
✓ Configuration loaded
✓ Backend: postgres
✓ Host: 10.147.20.100
✓ Database: network_segmentation
```

---

## 🔍 How the System Works

### Configuration Loading Priority

The system loads configuration in this order:

1. **Environment-specific file** (`.env.production`)
2. **Generic .env file** (`.env`)
3. **Default values** (`localhost` - ❌ this is the problem!)

```python
# From src/config.py
def _load_env_file(self):
    env_file = self.project_root / f'.env.{self.environment}'
    fallback_env = self.project_root / '.env'

    # Priority 1: .env.production
    if env_file.exists():
        self._parse_env_file(env_file)
    # Priority 2: .env
    elif fallback_env.exists():
        self._parse_env_file(fallback_env)
    # Priority 3: Defaults (PROBLEM!)
    else:
        logger.warning("No .env file found. Using defaults.")
```

### Default Values (Used When .env Missing)

```python
# From src/persistence/unified_persistence.py
def _load_default_postgres_config(self):
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),      # ← DEFAULTS TO localhost!
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'network_segmentation'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
```

---

## 📋 Checklist for Production Setup

### On Client/Production VDI:

- [ ] Create `.env.production` file in project root
- [ ] Add PostgreSQL server hostname/IP
- [ ] Add database name
- [ ] Add username and password
- [ ] Verify file exists: `dir .env.production`
- [ ] Check file is not empty: `type .env.production`
- [ ] Verify PostgreSQL server is accessible from VDI
- [ ] Test connection with Python script (see Step 4 above)
- [ ] Run application: `python run_batch_processing.py`
- [ ] Verify "Backend: postgres" in logs (not "Backend: json")

### Security Checklist:

- [ ] .env.production is NOT committed to git
- [ ] File permissions restrict access (Windows: Right-click → Properties → Security)
- [ ] Credentials are stored securely
- [ ] Password meets complexity requirements
- [ ] Connection uses SSL/TLS if available

---

## 🛠️ Troubleshooting

### Issue 1: Still Connecting to localhost

**Symptom:** Even after creating .env.production, still seeing localhost errors

**Causes & Fixes:**

1. **Wrong filename**
   ```bash
   # Check exact filename
   dir .env*

   # Should show:
   # .env.production (NOT .env.production.txt)
   ```

2. **File in wrong directory**
   ```bash
   # Must be in project root
   cd c:\Users\AjayPillai\project\network-segmentation-analyzer
   dir .env.production
   ```

3. **Environment variable not set**
   ```bash
   # Check environment
   python -c "import os; print(os.getenv('ENVIRONMENT', 'NOT SET'))"

   # Should print: production
   ```

4. **Syntax errors in .env file**
   ```bash
   # No spaces around = sign
   POSTGRES_HOST=server.com  # ✓ CORRECT
   POSTGRES_HOST = server.com  # ✗ WRONG
   ```

### Issue 2: Connection Refused

**Symptom:** Correct host, but connection refused

**Fixes:**

1. **Check PostgreSQL is running**
   ```bash
   # From VDI, test connection
   psql -h YOUR_SERVER -U YOUR_USER -d network_segmentation
   ```

2. **Check firewall allows connection**
   - Port 5432 must be open
   - VDI must have network access to server

3. **Check pg_hba.conf on server**
   - Must allow connections from VDI IP
   - Example: `host all all 10.147.20.0/24 md5`

4. **Check postgresql.conf on server**
   - `listen_addresses = '*'` or specific IP
   - Restart PostgreSQL after changes

### Issue 3: Authentication Failed

**Symptom:** Connection attempted, but authentication fails

**Fixes:**

1. **Verify credentials**
   ```bash
   # Test with psql
   psql -h YOUR_SERVER -U YOUR_USER -d network_segmentation
   ```

2. **Check username case sensitivity**
   - PostgreSQL usernames are case-sensitive
   - Use exact case from server

3. **Check password special characters**
   - Escape special characters in .env file
   - Or wrap in quotes if needed

---

## 📖 Alternative: Use SQLAlchemy URL

If you prefer, you can use a single SQLAlchemy connection URL instead:

### Option 1: Individual Variables (Current)
```bash
POSTGRES_HOST=server.com
POSTGRES_PORT=5432
POSTGRES_DB=network_segmentation
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
```

### Option 2: Single URL
```bash
# SQLAlchemy connection string format
DATABASE_URL=postgresql://admin:password@server.com:5432/network_segmentation
```

**Code to support this** (if needed, can be added to unified_persistence.py):
```python
# Check for DATABASE_URL first
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Parse URL and extract components
    from sqlalchemy.engine.url import make_url
    url = make_url(database_url)
    return {
        'host': url.host,
        'port': url.port,
        'database': url.database,
        'user': url.username,
        'password': url.password
    }
```

---

## ✅ Quick Fix Summary

**Immediate Actions:**

1. **On production VDI**, create `.env.production` file
2. **Add your PostgreSQL server details**
3. **Run test:** `python -c "from src.persistence.unified_persistence import UnifiedPersistenceManager; m=UnifiedPersistenceManager(); print(m.backend)"`
4. **Should print:** `postgres` (NOT `json`)
5. **Run application:** `python run_batch_processing.py`

**Expected Log Output:**
```
INFO - Configuration loaded for environment: production
INFO - [OK] PostgreSQL connection successful
INFO - [OK] Using PostgreSQL backend
INFO - Backend: postgres
```

**NOT this:**
```
WARNING - PostgreSQL connection failed: connection to server at "localhost"
INFO - [OK] Using JSON file backend (fallback)
INFO - Backend: json
```

---

## 📞 Need Help?

### Common Questions:

**Q: Where do I get the PostgreSQL server address?**
A: Contact your DBA or system administrator. It should be provided in your deployment documentation.

**Q: Can I use IP address instead of hostname?**
A: Yes! Example: `POSTGRES_HOST=10.147.20.100`

**Q: Will this work with SQLAlchemy?**
A: Yes, the system uses psycopg2 which is compatible with SQLAlchemy.

**Q: What if I don't have .env.production on the server?**
A: The file doesn't exist by default (for security). You must create it manually on each environment.

**Q: Can I copy .env.production from my local machine?**
A: NO! Local uses different credentials. Each environment needs its own .env file with environment-specific credentials.

---

**Created:** 2025-10-22
**Issue:** PostgreSQL connecting to localhost instead of production server
**Fix:** Create `.env.production` with correct server details
**Status:** Documented - Ready for client implementation
