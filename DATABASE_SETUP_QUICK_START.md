# Database Setup - Quick Start Guide

## 🚀 One-Command Setup

Run the consolidated setup script:

```bash
python setup_database.py
```

This single script handles **everything**:
- ✅ Tests database connection
- ✅ Creates dedicated schema
- ✅ Creates all tables (enriched_flows, dns_cache, flow_aggregates)
- ✅ Creates indexes for performance
- ✅ Verifies setup
- ✅ Saves configuration to .env.production

## 📋 Prerequisites

Before running setup:

1. **PostgreSQL server must be running and accessible**
2. **You need connection details:**
   - Host (e.g., `your-server.com` or `localhost`)
   - Port (default: `5432`)
   - Database name (e.g., `network_segmentation`)
   - Username (e.g., `postgres`)
   - Password
3. **User must have permissions to:**
   - CREATE SCHEMA
   - CREATE TABLE
   - CREATE INDEX

## 🎯 Setup Steps

### Step 1: Run Setup Script

```bash
python setup_database.py
```

**You'll be prompted for:**

```
PostgreSQL Host [localhost]: your-server.com
PostgreSQL Port [5432]: 5432
Database Name [network_segmentation]: network_segmentation
Username [postgres]: your_username
Password: ********
Schema Name [network_analysis]: network_analysis
```

**IMPORTANT:** Schema name **MUST NOT** be `public`. Use a dedicated schema like:
- `network_analysis` (recommended)
- `activenet` (if that's your production schema)
- Any other name except `public`

### Step 2: Verify Success

The script will automatically:

1. **Test connection**
   ```
   ✓ Connected successfully!
     PostgreSQL version: PostgreSQL 14.x
   ```

2. **Create schema**
   ```
   ✓ Schema 'network_analysis' created successfully
   ```

3. **Create tables**
   ```
   ✓ Tables created/verified:
     - network_analysis.enriched_flows
     - network_analysis.dns_cache
     - network_analysis.flow_aggregates
   ```

4. **Create indexes**
   ```
   ✓ Indexes created/verified:
     - idx_enriched_flows_src_app
     - idx_enriched_flows_dst_app
     - idx_enriched_flows_src_ip
     - idx_enriched_flows_dst_ip
     ...
   ```

5. **Verify setup**
   ```
   ✓ Schema 'network_analysis' exists
   ✓ Table 'enriched_flows' exists
   ✓ Column 'source_server_type' exists
   ✓ Column 'dest_server_type' exists
   ...
   ```

6. **Save configuration**
   ```
   ✓ Configuration saved to .env.production
   ```

### Step 3: Set Environment Variable

**On Windows (client VDI):**
```cmd
setx ENVIRONMENT production /M
```

**On Linux/Mac:**
```bash
export ENVIRONMENT=production
# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export ENVIRONMENT=production' >> ~/.bashrc
```

### Step 4: Verify Setup

```bash
python -c "from src.database import FlowRepository; repo = FlowRepository(); print('✓ Database connected!' if repo.connection_pool else '❌ Connection failed')"
```

**Expected output:**
```
✓ Database connected!
```

## 🎨 Advanced Options

### Use Existing .env File

If you already have `.env.production` configured:

```bash
python setup_database.py --use-env
```

### Test Connection Only (No Changes)

```bash
python setup_database.py --test-only
```

### Force Recreate Tables

⚠️ **WARNING: This deletes all existing data!**

```bash
python setup_database.py --force-recreate
```

### Skip Saving to .env

```bash
python setup_database.py --skip-save
```

## 📊 What Gets Created

### Schema

```sql
CREATE SCHEMA network_analysis;
```

### Tables

#### 1. enriched_flows (Main table)
```sql
CREATE TABLE network_analysis.enriched_flows (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source
    source_app_code VARCHAR(50) NOT NULL,
    source_ip INET NOT NULL,
    source_hostname VARCHAR(255),
    source_server_type VARCHAR(50),      -- 🆕 Server classification
    source_server_tier VARCHAR(50),      -- 🆕 Infrastructure/App/DB tier
    source_server_category VARCHAR(50),  -- 🆕 Category

    -- Destination
    dest_ip INET NOT NULL,
    dest_hostname VARCHAR(255),
    dest_server_type VARCHAR(50),        -- 🆕 Server classification
    dest_server_tier VARCHAR(50),        -- 🆕 Infrastructure/App/DB tier
    dest_server_category VARCHAR(50),    -- 🆕 Category

    -- Flow details
    protocol VARCHAR(20),
    port INTEGER,
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,
    flow_direction VARCHAR(20),
    flow_count INTEGER DEFAULT 1,

    -- Metadata
    has_missing_data BOOLEAN DEFAULT FALSE,
    missing_fields TEXT[],
    batch_id VARCHAR(100),
    file_source VARCHAR(255)
);
```

#### 2. dns_cache (Performance optimization)
```sql
CREATE TABLE network_analysis.dns_cache (
    ip INET PRIMARY KEY,
    hostname VARCHAR(255),
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl INTEGER DEFAULT 86400
);
```

#### 3. flow_aggregates (Fast queries)
```sql
CREATE TABLE network_analysis.flow_aggregates (
    id SERIAL PRIMARY KEY,
    source_app_code VARCHAR(50),
    dest_app_code VARCHAR(50),
    flow_direction VARCHAR(20),
    total_flows INTEGER,
    total_bytes_in BIGINT,
    total_bytes_out BIGINT,
    unique_source_ips INTEGER,
    unique_dest_ips INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_app_code, dest_app_code, flow_direction)
);
```

### Indexes (9 total)

Performance indexes created:
- `idx_enriched_flows_src_app` (source_app_code)
- `idx_enriched_flows_dst_app` (dest_app_code)
- `idx_enriched_flows_src_ip` (source_ip)
- `idx_enriched_flows_dst_ip` (dest_ip)
- `idx_enriched_flows_flow_direction` (flow_direction)
- `idx_enriched_flows_created_at` (created_at)
- `idx_enriched_flows_src_server_type` (source_server_type) 🆕
- `idx_enriched_flows_dst_server_type` (dest_server_type) 🆕
- `idx_enriched_flows_src_server_tier` (source_server_tier) 🆕
- `idx_enriched_flows_dst_server_tier` (dest_server_tier) 🆕

## ⚠️ Troubleshooting

### Connection Failed

**Error:**
```
❌ DATABASE CONNECTION TEST: FAILED
   Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   # Windows
   services.msc  # Look for PostgreSQL service

   # Linux
   systemctl status postgresql
   ```

2. **Check host/port:**
   - Verify correct hostname
   - Verify correct port (default 5432)
   - Try `localhost` vs actual hostname

3. **Check firewall:**
   - Port 5432 must be open
   - Network connectivity to server

4. **Check credentials:**
   - Username exists
   - Password is correct
   - User has permissions

5. **Check database exists:**
   ```bash
   psql -h your-server.com -U postgres -l
   ```

### Schema Validation Error

**Error:**
```
❌ SCHEMA VALIDATION FAILED: Cannot use 'public' schema!
```

**Solution:**
Use a dedicated schema name (NOT `public`):
- `network_analysis` ✅
- `activenet` ✅
- `public` ❌

### Permission Denied

**Error:**
```
ERROR: permission denied to create extension "uuid-ossp"
ERROR: permission denied for schema network_analysis
```

**Solution:**
Contact your DBA to grant permissions:
```sql
GRANT CREATE ON DATABASE network_segmentation TO your_username;
GRANT ALL ON SCHEMA network_analysis TO your_username;
```

### Tables Not Found After Setup

**Check if tables exist:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'network_analysis';
```

**If empty, rerun with force-recreate:**
```bash
python setup_database.py --force-recreate
```

## ✅ After Setup

### Next Steps

1. **Run batch processing:**
   ```bash
   python run_batch_processing.py --batch-size 10
   ```

2. **Verify data is populated:**
   ```bash
   python -c "from src.database import FlowRepository; print(FlowRepository().get_statistics())"
   ```

   **Expected output:**
   ```python
   {
       'total_flows': 125430,  # Should be > 0 after processing
       'total_apps': 154,
       'dns_cache_entries': 8920,
       'schema': 'network_analysis'
   }
   ```

3. **Generate enhanced diagrams:**
   ```bash
   python generate_diagrams_from_db.py
   ```

### Query Your Data

**Count by server type:**
```sql
SELECT dest_server_type, COUNT(*)
FROM network_analysis.enriched_flows
GROUP BY dest_server_type
ORDER BY COUNT(*) DESC;
```

**Find load balancers:**
```sql
SELECT DISTINCT dest_hostname, dest_server_type
FROM network_analysis.enriched_flows
WHERE dest_server_type IN ('F5', 'Azure Traffic Manager');
```

**Unknown connections:**
```sql
SELECT source_app_code, dest_ip, dest_hostname, COUNT(*)
FROM network_analysis.enriched_flows
WHERE dest_server_type = 'Unknown'
GROUP BY source_app_code, dest_ip, dest_hostname
ORDER BY COUNT(*) DESC;
```

## 📚 Related Documentation

- [POSTGRESQL_INTEGRATION.md](POSTGRESQL_INTEGRATION.md) - Complete PostgreSQL integration guide
- [POST_PROCESSING_DIAGRAMS.md](POST_PROCESSING_DIAGRAMS.md) - Enhanced diagram generation
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Detailed database documentation

---

**Created:** 2025-10-22
**Purpose:** Quick start guide for PostgreSQL database setup
**Status:** Ready to use
