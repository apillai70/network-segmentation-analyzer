# PostgreSQL Integration - Server Classification Storage

## Overview

**IMPORTANT UPDATE:** Batch processing now automatically saves server classification data to PostgreSQL!

This document explains how server classification is populated during batch processing and how to use the enriched data.

## ✅ What Changed

### Before (Previous Behavior)
```
CSV Files → Process → JSON files only
                  ↓
            enriched_flows table: EMPTY ❌
```

### After (Current Behavior)
```
CSV Files → Process → Classify servers → Save to PostgreSQL + JSON
                  ↓                    ↓
            enriched_flows table:   POPULATED ✅
            - source_server_type
            - source_server_tier
            - dest_server_type
            - dest_server_tier
            - 17+ server types classified
```

## 🔧 How It Works

### Automatic Population During Batch Processing

When you run:
```bash
python run_batch_processing.py --batch-size 10
```

**Step-by-step process:**

1. **Load CSV file** (`App_Code_BLZE.csv`)
2. **Parse flows** (source IP/hostname → destination IP/hostname)
3. **🆕 CLASSIFY SERVERS** (ServerClassifier identifies 17+ types)
   - DNS servers
   - LDAP/Active Directory
   - F5 Load Balancers
   - Azure Traffic Manager
   - Database servers
   - Web servers
   - And 11+ more types
4. **🆕 ENRICH DATAFRAME** with classification columns:
   - `source_server_type`, `source_server_tier`, `source_server_category`
   - `dest_server_type`, `dest_server_tier`, `dest_server_category`
5. **🆕 SAVE TO POSTGRESQL** (`enriched_flows` table)
6. **Save to JSON** (existing behavior continues)

## 📊 Database Schema

### enriched_flows Table

```sql
CREATE TABLE network_analysis.enriched_flows (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source
    source_app_code VARCHAR(50) NOT NULL,
    source_ip INET NOT NULL,
    source_hostname VARCHAR(255),
    source_device_type VARCHAR(50),
    source_server_type VARCHAR(50),      -- 🆕 NOW POPULATED
    source_server_tier VARCHAR(50),      -- 🆕 NOW POPULATED
    source_server_category VARCHAR(50),  -- 🆕 NOW POPULATED

    -- Destination
    dest_ip INET NOT NULL,
    dest_hostname VARCHAR(255),
    dest_device_type VARCHAR(50),
    dest_app_code VARCHAR(50),
    dest_server_type VARCHAR(50),        -- 🆕 NOW POPULATED
    dest_server_tier VARCHAR(50),        -- 🆕 NOW POPULATED
    dest_server_category VARCHAR(50),    -- 🆕 NOW POPULATED

    -- Flow details
    protocol VARCHAR(20),
    port INTEGER,
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,

    -- Metadata
    flow_direction VARCHAR(20),
    flow_count INTEGER DEFAULT 1,
    has_missing_data BOOLEAN DEFAULT FALSE,
    missing_fields TEXT[],

    -- Batch tracking
    batch_id VARCHAR(100),
    file_source VARCHAR(255)
);
```

### Server Types Classified

| Server Type | Tier | Category | Example Hostnames |
|-------------|------|----------|-------------------|
| DNS | Infrastructure | Network | *DNS*, *NS01 |
| LDAP | Infrastructure | Directory | *LDAP*, *DC01 |
| Active Directory | Infrastructure | Directory | *AD*, *DC*, *ADDS |
| F5 | Infrastructure | Load Balancer | *F5*, *LB*, *BIGIP |
| Azure Traffic Manager | Cloud | Load Balancer | *trafficmanager* |
| Database | Database | Storage | *DB*, *SQL*, *MYSQL*, *ORACLE |
| Web Server | Presentation | Web | *WEB*, *IIS*, *APACHE |
| App Server | Application | Middleware | *APP*, *TOMCAT |
| And 9+ more... | | | |

## 🚀 Requirements

### 1. PostgreSQL Must Be Enabled

**In `.env.production` or `.env.development`:**
```bash
# Database settings
DB_ENABLED=true                          # MUST BE TRUE!
POSTGRES_HOST=your-postgres-server.com
POSTGRES_PORT=5432
POSTGRES_DB=network_segmentation
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
DB_SCHEMA=network_analysis              # Dedicated schema (NOT 'public')
```

### 2. Environment Variable Must Be Set

**On client VDI (Windows):**
```cmd
setx ENVIRONMENT production /M
```

**Or create a wrapper script** (`run_production.bat`):
```batch
@echo off
set ENVIRONMENT=production
python run_batch_processing.py --batch-size 10
pause
```

### 3. PostgreSQL Server Must Be Accessible

Test connection:
```bash
python -c "from src.database import FlowRepository; repo = FlowRepository(); print(f'Connected: {repo.connection_pool is not None}')"
```

## 📈 Usage Examples

### Run Batch Processing (Automatic Population)

```bash
# Process 10 files at a time
python run_batch_processing.py --batch-size 10

# PostgreSQL enrichment happens automatically:
# ✓ Server classification
# ✓ Insert into enriched_flows table
# ✓ All 154 applications processed
```

**Output:**
```
Processing App_Code_BLZE.csv...
  Loaded 1250 flows for BLZE
  [OK] Enriched 1250 flows with server classification
  [OK] Saved 1250 flows to PostgreSQL enriched_flows table
  [OK] Successfully processed BLZE in 2.3s
```

### Query Enriched Data

**After batch processing completes**, you can query the enriched data:

#### Example 1: Count by Server Type
```sql
SELECT
    dest_server_type,
    COUNT(*) as flow_count,
    COUNT(DISTINCT source_app_code) as app_count
FROM network_analysis.enriched_flows
GROUP BY dest_server_type
ORDER BY flow_count DESC;
```

**Result:**
```
dest_server_type    | flow_count | app_count
--------------------|------------|----------
Database            | 45,230     | 87
Web Server          | 32,145     | 102
DNS                 | 18,920     | 154
LDAP                | 12,450     | 98
F5                  | 8,320      | 45
...
```

#### Example 2: Load Balancer Usage
```sql
SELECT
    source_app_code,
    dest_hostname,
    dest_server_type,
    COUNT(*) as connection_count
FROM network_analysis.enriched_flows
WHERE dest_server_type IN ('F5', 'Azure Traffic Manager', 'Load Balancer')
GROUP BY source_app_code, dest_hostname, dest_server_type
ORDER BY connection_count DESC;
```

#### Example 3: Unknown Connections (Security Risk)
```sql
SELECT
    source_app_code,
    dest_ip,
    dest_hostname,
    protocol,
    port,
    COUNT(*) as occurrences
FROM network_analysis.enriched_flows
WHERE dest_server_type = 'Unknown' OR dest_hostname = 'Unknown'
GROUP BY source_app_code, dest_ip, dest_hostname, protocol, port
ORDER BY occurrences DESC;
```

### Generate Enhanced Diagrams from Database

```bash
# Use the post-processing diagram generator
python generate_diagrams_from_db.py

# Or for specific apps
python generate_diagrams_from_db.py --apps BLZE BM BO
```

This creates diagrams with:
- ✅ Server grouping by naming convention
- ✅ Color-coded unknown connections (red)
- ✅ Visual boxes around groups
- ✅ Load balancer identification
- ✅ Multi-format output (MMD, HTML, PNG, SVG)

## 🔍 Verify Data is Being Populated

### Check if PostgreSQL is Enabled

```bash
python -c "from src.config import get_config; config = get_config(); print(f'DB Enabled: {config.db_enabled}')"
```

**Expected output:**
```
DB Enabled: True
```

### Check Row Count in enriched_flows

```bash
python -c "from src.database import FlowRepository; repo = FlowRepository(); print(repo.get_statistics())"
```

**Expected output:**
```
{
    'total_flows': 125430,      # Should be > 0!
    'total_apps': 154,
    'dns_cache_entries': 8920,
    'schema': 'network_analysis'
}
```

### Check Classification Data

```sql
-- Verify classification columns are populated
SELECT
    COUNT(*) as total_flows,
    COUNT(dest_server_type) as classified_dest,
    COUNT(CASE WHEN dest_server_type != 'Unknown' THEN 1 END) as known_types
FROM network_analysis.enriched_flows;
```

**Expected result:**
```
total_flows | classified_dest | known_types
------------|-----------------|------------
125430      | 125430          | 98250       (78% classified)
```

## ⚠️ Troubleshooting

### Issue 1: PostgreSQL Not Enabled

**Symptom:**
```
PostgreSQL disabled, skipping enriched_flows save
```

**Fix:**
```bash
# Set DB_ENABLED=true in .env file
echo "DB_ENABLED=true" >> .env.production

# Or set environment variable
setx ENVIRONMENT production /M
```

### Issue 2: Connection Failed

**Symptom:**
```
PostgreSQL connection not available
connection to server at 'localhost' (127.0.0.1), port 5432 failed
```

**Fix:**
1. Check `.env.production` has correct credentials
2. Verify network access to PostgreSQL server
3. Check firewall rules
4. Test connection:
   ```bash
   psql -h your-server.com -p 5432 -U your_user -d network_segmentation
   ```

### Issue 3: Schema Validation Error

**Symptom:**
```
SCHEMA VALIDATION FAILED: Cannot use 'public' schema!
```

**Fix:**
```bash
# Set a dedicated schema in .env
DB_SCHEMA=network_analysis  # NOT 'public'
```

### Issue 4: No Data in enriched_flows

**Symptom:**
- Batch processing runs successfully
- But `SELECT COUNT(*) FROM enriched_flows` returns 0

**Causes & Fixes:**

1. **PostgreSQL not enabled**
   ```bash
   # Check
   python -c "from src.config import get_config; print(get_config().db_enabled)"

   # Fix: Set DB_ENABLED=true in .env
   ```

2. **Wrong environment file loaded**
   ```bash
   # Check
   python -c "import os; print(f\"ENV: {os.getenv('ENVIRONMENT', 'development')}\")"

   # Fix: Set ENVIRONMENT=production
   setx ENVIRONMENT production /M
   ```

3. **Insert errors (check logs)**
   ```bash
   # Check logs for errors
   tail -100 logs/incremental_*.log | grep "PostgreSQL\|enriched_flows"
   ```

## 📝 Implementation Details

### Code Changes

**File:** `src/core/incremental_learner.py`

**Modified method:** `process_new_file()`

**Added logic:**
```python
# 1. Load flows from CSV
flows_df = pd.read_csv(file_path)

# 2. 🆕 Classify servers (17+ types)
flows_df = self._enrich_flows_with_classification(flows_df, app_id)

# 3. Save to JSON (existing)
self.pm.save_application(app_id, flows_df)

# 4. 🆕 Save to PostgreSQL if enabled
self._save_to_postgresql_if_enabled(flows_df, app_id)
```

**New methods:**
- `_enrich_flows_with_classification()` - Classifies each source/destination
- `_save_to_postgresql_if_enabled()` - Inserts into enriched_flows table

## 🎯 Benefits

### Before Integration
- ❌ Server classification data only in memory
- ❌ No persistent storage of classifications
- ❌ Had to reclassify for every diagram generation
- ❌ No query capability for threat analysis
- ❌ Limited to JSON file data

### After Integration
- ✅ Server classification persisted in PostgreSQL
- ✅ 17+ server types automatically identified
- ✅ Query for threat analysis (unknown connections, tier violations)
- ✅ Generate diagrams from complete database
- ✅ Historical data analysis
- ✅ Traffic volume statistics
- ✅ Load balancer relationship tracking
- ✅ Security zone analysis

## 🔗 Related Files

- `src/core/incremental_learner.py` - Main integration point
- `src/database/flow_repository.py` - PostgreSQL repository
- `src/server_classifier.py` - Server type classification
- `src/source_component_analyzer.py` - Load balancer detection
- `generate_diagrams_from_db.py` - Post-processing diagram generator
- `.env.production` - Production database configuration

## 📚 Next Steps

1. **Run batch processing with PostgreSQL enabled**
   ```bash
   python run_batch_processing.py --batch-size 10
   ```

2. **Verify data is populated**
   ```bash
   python -c "from src.database import FlowRepository; print(FlowRepository().get_statistics())"
   ```

3. **Generate enhanced diagrams from database**
   ```bash
   python generate_diagrams_from_db.py
   ```

4. **Query for threat analysis**
   ```sql
   -- Unknown connections
   SELECT * FROM network_analysis.enriched_flows
   WHERE dest_server_type = 'Unknown' LIMIT 100;

   -- Load balancers
   SELECT * FROM network_analysis.enriched_flows
   WHERE dest_server_type IN ('F5', 'Azure Traffic Manager');
   ```

---

**Created:** 2025-10-22
**Status:** ✅ Implemented and ready for use
**Requires:** PostgreSQL enabled (`DB_ENABLED=true`)
