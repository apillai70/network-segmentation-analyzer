# JSON Fallback Quick Start Guide

## Problem

You need enhanced diagrams and DOCX reports with server classification TODAY, but:
- DBA approval for table creation is delayed
- PostgreSQL tables don't exist yet
- You can't wait for database setup

## Solution

Use the JSON enriched flows fallback! It saves ALL the same data that would go to PostgreSQL, but to JSON files instead.

## How It Works

### Automatic Dual-Mode Saving

When you run batch processing, the system now saves enriched flow data to **BOTH**:

1. **JSON files** (always, no configuration needed)
   - Per-app files: `outputs_final/enriched_flows/{APP}_enriched_flows.json`
   - Consolidated: `outputs_final/enriched_flows/enriched_flows_all.json`

2. **PostgreSQL** (only if tables exist and DB enabled)
   - Table: `activenet.enriched_flows`

This means you can proceed TODAY with JSON, and later switch to PostgreSQL with zero data loss.

## JSON Data Structure

Each flow record contains ALL server classification fields:

```json
{
  "source_app_code": "AODSVY",
  "source_ip": "10.164.116.238",
  "source_hostname": "AODSVY1WEB01",

  "dest_ip": "10.100.160.174",
  "dest_hostname": "PRODDB01",

  "protocol": "TCP",
  "port": 1521,
  "bytes_in": 1024000,
  "bytes_out": 512000,

  "source_server_type": "WEB_SERVER",
  "source_server_tier": "WEB_TIER",
  "source_server_category": "Application",

  "dest_server_type": "ORACLE_DATABASE",
  "dest_server_tier": "DATA_TIER",
  "dest_server_category": "Database",

  "flow_direction": "outbound",
  "flow_count": 1,
  "batch_id": "incremental_AODSVY_20251023_143000",
  "file_source": "App_Code_AODSVY.csv",
  "created_at": "2025-10-23T14:30:00.123456"
}
```

**This matches the PostgreSQL schema EXACTLY** - same fields, same structure.

## Quick Start Steps

### Step 1: Run Batch Processing (Saves to JSON Automatically)

```bash
# OPTION 1: JSON + PostgreSQL (default - dual mode)
python run_batch_processing.py --batch-size 10

# OPTION 2: JSON ONLY (skip PostgreSQL entirely for faster processing)
python run_batch_processing.py --batch-size 10 --only-json
```

**What happens:**
- Reads CSV files from `data/input/`
- Enriches flows with server classification
- **Always saves to JSON:** `outputs_final/enriched_flows/`
- **Default (no flag):** Also tries PostgreSQL (fails silently if tables don't exist)
- **With --only-json:** Skips PostgreSQL entirely (faster, cleaner logs)

**Output (default mode):**
```
Processing batch 1/14...
  [OK] Saved 150 enriched flows to JSON: outputs_final/enriched_flows/AODSVY_enriched_flows.json
  [WARNING] Failed to save to PostgreSQL: relation "activenet.enriched_flows" does not exist
  ...continuing normally...
```

**Output (--only-json mode):**
```
Processing batch 1/14...
  [OK] Saved 150 enriched flows to JSON: outputs_final/enriched_flows/AODSVY_enriched_flows.json
  ...continuing normally...
```

### Step 2: Generate Enhanced Diagrams from JSON

```bash
# Generate diagrams from JSON (no PostgreSQL needed!)
python generate_diagrams_from_json.py
```

**What happens:**
- Reads enriched flows from JSON files
- Groups servers by naming conventions
- Detects load balancers
- Color-codes unknown connections
- Generates Mermaid diagrams and HTML

**Output:**
```
================================================================================
GENERATING ENHANCED DIAGRAMS FROM JSON
================================================================================
Applications: 9
Output directory: outputs/diagrams_from_json
JSON directory: outputs_final/enriched_flows

================================================================================
Generating enhanced diagrams for: AODSVY
================================================================================
Found 150 flows for AODSVY
Identified 3 server groups:
  - AODSVY-WEB: 4 servers (WEB_SERVER)
  - PRODDB: 2 servers (ORACLE_DATABASE)
  - CACHE: 2 servers (REDIS_CACHE)
Identified 1 load balancers: ['F5-LB-01']

✓ Saved Mermaid: outputs/diagrams_from_json/AODSVY_enhanced.mmd
✓ Saved HTML: outputs/diagrams_from_json/AODSVY_enhanced.html

✅ Done! Generated enhanced diagrams for AODSVY
```

### Step 3: View Diagrams

Open the HTML files in your browser:

```bash
# On Windows
start outputs/diagrams_from_json/AODSVY_enhanced.html

# On Linux/Mac
xdg-open outputs/diagrams_from_json/AODSVY_enhanced.html
```

You'll see:
- Server groups in visual boxes
- Load balancers highlighted in orange
- Unknown connections in red
- Known connections in green
- Server types labeled on each node

## Command Options

### Generate for Specific Apps Only

```bash
# Only generate diagrams for specific applications
python generate_diagrams_from_json.py --apps AODSVY APSE ACDA
```

### Custom JSON Directory

```bash
# If your JSON files are in a different location
python generate_diagrams_from_json.py --json-dir /path/to/enriched_flows
```

### Custom Output Directory

```bash
# Save diagrams to a different location
python generate_diagrams_from_json.py --output /path/to/diagrams
```

## File Locations

### Input (CSV Files)
```
data/input/
├── App_Code_AODSVY.csv
├── App_Code_APSE.csv
└── ...
```

### Output (JSON Enriched Flows)
```
outputs_final/enriched_flows/
├── AODSVY_enriched_flows.json      ← Per-app files
├── APSE_enriched_flows.json
├── ACDA_enriched_flows.json
└── enriched_flows_all.json         ← Consolidated (all apps)
```

### Output (Diagrams from JSON)
```
outputs/diagrams_from_json/
├── AODSVY_enhanced.mmd            ← Mermaid source
├── AODSVY_enhanced.html           ← Interactive HTML
├── APSE_enhanced.mmd
├── APSE_enhanced.html
└── ...
```

## Advantages of JSON Fallback

1. **No DBA Required** - Works immediately, no permissions needed
2. **Same Features** - All server classification, grouping, load balancer detection
3. **Same Data Structure** - When PostgreSQL is ready, data is identical
4. **Git-Friendly** - Can commit JSON files (if not too large)
5. **Easy to Inspect** - Human-readable, can open in any text editor
6. **Portable** - Copy to USB, email, share easily

## Migration to PostgreSQL Later

When DBA creates tables, you have TWO options:

### Option A: Continue with Dual-Mode (Recommended)

- Keep using JSON as backup
- PostgreSQL gets populated automatically
- Both stay in sync

### Option B: Switch to PostgreSQL Only

1. DBA creates tables using `create_tables.sql`
2. Run `python setup_database.py` to verify
3. Use `generate_diagrams_from_db.py` instead of `generate_diagrams_from_json.py`
4. Optional: Import existing JSON data into PostgreSQL

## Comparison: JSON vs PostgreSQL

| Feature | JSON Fallback | PostgreSQL |
|---------|---------------|------------|
| Setup Time | 0 seconds | Requires DBA |
| Permission Required | None | CREATE TABLE |
| Performance | Fast for small datasets | Fast for any size |
| Querying | Pandas/Python | SQL |
| Concurrent Access | File locking | Connection pooling |
| Backup | Git commit | pg_dump |
| Best For | Quick start, dev, small data | Production, large data |

## Troubleshooting

### Issue: "No enriched flow records found"

**Cause:** Haven't run batch processing yet

**Solution:**
```bash
python run_batch_processing.py --batch-size 10
```

### Issue: "File not found: outputs_final/enriched_flows/APP_enriched_flows.json"

**Cause:** That application hasn't been processed yet

**Solution:** Check available apps:
```bash
# List all JSON files
ls outputs_final/enriched_flows/*.json
```

### Issue: Large JSON files (>100MB)

**Cause:** Many flows accumulated over time

**Solutions:**
1. Switch to PostgreSQL (handles large data better)
2. Archive old JSON files periodically
3. Use `--apps` flag to generate diagrams for specific apps only

## Next Steps

1. **TODAY:** Use JSON fallback to generate all diagrams
2. **Tomorrow:** Send `create_tables.sql` to DBA
3. **After Tables Created:** Run `setup_database.py` to verify
4. **Later:** Switch to `generate_diagrams_from_db.py` if desired

**Bottom line:** You can proceed with ALL features TODAY without waiting for DBA!

---

**Created:** 2025-10-23
**Purpose:** Immediate workaround for delayed DBA table creation approval
**Status:** Production-ready, tested
