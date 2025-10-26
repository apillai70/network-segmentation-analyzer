# Production Deployment Guide

## Environment Configuration

Your system uses environment-based configuration with `.env` files that are **NEVER** committed to git.

### How It Works

1. **Environment Detection**: The system automatically loads the correct `.env` file based on the `ENVIRONMENT` variable
2. **Configuration Priority**:
   - `.env.production` (for production environment)
   - `.env.development` (for development environment)
   - `.env` (fallback if neither exists)

### Production Setup

#### Step 1: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:ENVIRONMENT = "production"
```

**Windows (CMD):**
```cmd
set ENVIRONMENT=production
```

**Linux/Mac:**
```bash
export ENVIRONMENT=production
```

#### Step 2: Verify .env.production Exists

Your production environment file is already configured:
```
C:\Users\AjayPillai\project\network-segmentation-analyzer\.env.production
```

**Current Production Settings:**
- Database Host: `udideapdb01.unix.rgbk.com`
- Database Name: `prutech_bais`
- Database Schema: `activenet`
- Database User: `activenet_admin`
- SSL Mode: `disable`

#### Step 3: Run in Production Mode

**Single Command (RECOMMENDED):**
```bash
# Windows PowerShell
$env:ENVIRONMENT = "production"; python run_batch_processing.py --batch-size 10

# Linux/Mac
ENVIRONMENT=production python run_batch_processing.py --batch-size 10
```

**Persistent Environment (Set Once):**
```powershell
# Windows - Add to your PowerShell profile
$env:ENVIRONMENT = "production"

# Then just run:
python run_batch_processing.py --batch-size 10
```

### Configuration Usage in Scripts

All scripts automatically use the production environment:

```python
from src.config import get_config

# Load configuration (automatically uses ENVIRONMENT variable)
config = get_config()

# Access production database credentials
db_host = config.db_host          # udideapdb01.unix.rgbk.com
db_name = config.db_name          # prutech_bais
db_schema = config.db_schema      # activenet
db_connection = config.db_connection_string

# Check environment
if config.is_production:
    print("Running in PRODUCTION mode")
```

### Security Best Practices

#### ✅ Already Configured Correctly:

1. **`.env.production` is in `.gitignore`** - Credentials never committed
2. **Separate environment files** - Development and production isolated
3. **Password masking in logs** - Config `__repr__` hides passwords
4. **Dedicated schema** - Using `activenet` schema, not `public`

#### ⚠️ Important Warnings:

1. **NEVER commit `.env.production` to git**
   - Already protected in `.gitignore`
   - Contains production database password

2. **NEVER share credentials in chat/email**
   - Use secure credential management systems
   - Rotate passwords regularly

3. **Use environment variables on production servers**
   - Better: Use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault
   - For now: Ensure `.env.production` has proper file permissions

### File Permissions (Linux/Mac)

```bash
# Make .env.production readable only by owner
chmod 600 .env.production

# Verify permissions
ls -la .env.production
# Should show: -rw------- (600)
```

### Verification

Test your production configuration:

```bash
# Set production environment
export ENVIRONMENT=production

# Test configuration loading
python -c "from src.config import get_config; config = get_config(); print(config)"
```

**Expected Output:**
```
Config(
  environment=production
  db_host=udideapdb01.unix.rgbk.com
  db_port=5432
  db_name=prutech_bais
  db_schema=activenet
  db_user=activenet_admin
  db_password=*** (hidden)
  db_enabled=True
  debug=False
)
```

### Running Complete Pipeline in Production

#### Option 1: Single Command (Recommended)

```bash
# Windows PowerShell
$env:ENVIRONMENT = "production"; python run_batch_processing.py --batch-size 10

# Linux/Mac
ENVIRONMENT=production python run_batch_processing.py --batch-size 10
```

#### Option 2: Set Environment First

```bash
# Windows
set ENVIRONMENT=production
python run_batch_processing.py --batch-size 10

# Linux/Mac
export ENVIRONMENT=production
python run_batch_processing.py --batch-size 10
```

#### Option 3: Create Production Run Script

**Windows: `run_production.bat`**
```batch
@echo off
set ENVIRONMENT=production
python run_batch_processing.py --batch-size 10
pause
```

**Linux/Mac: `run_production.sh`**
```bash
#!/bin/bash
export ENVIRONMENT=production
python run_batch_processing.py --batch-size 10
```

Make executable:
```bash
chmod +x run_production.sh
./run_production.sh
```

### Deployment Checklist

#### Before Deploying to Client:

- [ ] Verify `.env.production` exists and has correct credentials
- [ ] Test database connection: `python test_db_connection.py`
- [ ] Set `ENVIRONMENT=production` environment variable
- [ ] Run test batch: `python run_batch_processing.py --batch-size 1`
- [ ] Verify outputs in `outputs_final/` and `outputs/docx/`
- [ ] Check logs for any errors
- [ ] Ensure `.env.production` is NOT in git: `git status`

#### On Client Server:

1. **Clone Repository:**
   ```bash
   git clone https://github.com/apillai70/network-segmentation-analyzer.git
   cd network-segmentation-analyzer
   ```

2. **Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Configure Production Environment:**
   ```bash
   # Copy example and edit with client credentials
   cp .env.example .env.production
   nano .env.production  # Edit with client DB credentials
   ```

4. **Set Environment:**
   ```bash
   export ENVIRONMENT=production  # Linux/Mac
   set ENVIRONMENT=production     # Windows
   ```

5. **Run Pipeline:**
   ```bash
   python run_batch_processing.py --batch-size 10
   ```

### Environment Variables Reference

| Variable | Production Value | Description |
|----------|-----------------|-------------|
| `ENVIRONMENT` | `production` | Determines which `.env` file to load |
| `DB_HOST` | `udideapdb01.unix.rgbk.com` | PostgreSQL server hostname |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `prutech_bais` | Database name |
| `DB_SCHEMA` | `activenet` | Schema name (NEVER use 'public'!) |
| `DB_USER` | `activenet_admin` | Database username |
| `DB_PASSWORD` | `(secured)` | Database password |
| `DB_SSL_MODE` | `disable` | SSL mode for connection |
| `DEBUG` | `false` | Debug mode (always false in production) |
| `LOG_LEVEL` | `INFO` | Logging level |

### Troubleshooting

#### Issue: "No .env file found"

**Solution:**
```bash
# Verify .env.production exists
ls -la .env.production

# If missing, copy from example
cp .env.example .env.production
# Edit with production credentials
```

#### Issue: "Using development database"

**Solution:**
```bash
# Check environment variable
echo $ENVIRONMENT  # Linux/Mac
echo %ENVIRONMENT% # Windows

# Should output: production
# If not, set it:
export ENVIRONMENT=production  # Linux/Mac
set ENVIRONMENT=production     # Windows
```

#### Issue: "Connection refused"

**Solution:**
```bash
# Test database connectivity
python test_db_connection.py

# Check .env.production has correct host
cat .env.production | grep DB_HOST

# Verify network access to database server
ping udideapdb01.unix.rgbk.com
telnet udideapdb01.unix.rgbk.com 5432
```

### Summary

Your production environment is **already configured correctly**:

✅ `.env.production` exists with production credentials
✅ `.gitignore` protects credentials from git
✅ `src/config.py` automatically loads correct environment
✅ All scripts use `get_config()` for environment-aware configuration

**To run in production:**
```bash
ENVIRONMENT=production python run_batch_processing.py --batch-size 10
```

That's it! The system will automatically use production database credentials and settings.
