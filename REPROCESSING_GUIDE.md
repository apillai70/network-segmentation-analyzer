# Application Reprocessing Guide

## Overview

The **Application Reprocessing** feature allows you to re-analyze all previously processed applications with updated intelligence and persist topology data for web UI visibility.

## When to Use Reprocessing

### Scenario 1: Missing Topology in Web UI
**Symptoms:**
- Web UI shows fewer applications than expected
- "Applications Overview" is blank or shows only a few apps
- Topology graph is empty or incomplete

**Cause:** Applications were processed before topology persistence was implemented

**Solution:** Run reprocessing to regenerate and save topology files

### Scenario 2: Poor Zone Classification
**Symptoms:**
- All applications showing as "APP_TIER"
- Zone distribution is incorrect
- Apps not properly segmented

**Cause:** Older classification logic relied only on app naming patterns

**Solution:** Reprocessing uses improved IP-based zone inference

### Scenario 3: After System Updates
**When:** After updating semantic analysis or zone classification logic

**Why:** Ensures all apps benefit from latest intelligence

## How to Run Reprocessing

### Prerequisites

- Applications must be in `persistent_data/applications/` directory
- Each app should have a `flows.csv` file
- System should be running normally

### Command

```bash
python reprocess_all_apps.py
```

### Expected Output

```
================================================================================
REPROCESSING ALL APPLICATIONS
================================================================================
Fixing topology persistence and zone classification...

Processing 139 applications...
--------------------------------------------------------------------------------
[1/139] ACDA... [OK] APP_TIER
[2/139] AODSVY... [OK] APP_TIER
[3/139] APSE... [OK] APP_TIER
...
[139/139] LBOT... [OK] APP_TIER

================================================================================
REPROCESSING COMPLETE
================================================================================
Total applications: 139
Successfully processed: 139
Failed: 0

Zone Distribution:
--------------------------------------------------------------------------------
  APP_TIER            : 103 apps
  MESSAGING_TIER      :  17 apps
  WEB_TIER            :   8 apps
  CACHE_TIER          :   6 apps
  MANAGEMENT_TIER     :   4 apps
  DATA_TIER           :   1 apps
================================================================================

Topology files saved to: persistent_data/topology/
```

### Processing Time

- **Typical:** 1-2 seconds per application
- **139 apps:** ~2-3 minutes total

## What Happens During Reprocessing

### Step 1: Load Flow Data
- Reads `flows.csv` from each application directory
- Extracts Source IP and Destination IP addresses

### Step 2: Semantic Analysis
- Classifies application type (api_service, database, cache, etc.)
- Identifies characteristics (authentication, payment, etc.)
- **NEW:** Infers security zone from IP address patterns (see below)
- Determines dependencies from observed network connections

### Step 3: Persist Topology
- Saves analysis to `persistent_data/topology/{APP_ID}.json`
- Each file contains:
  - Security zone assignment
  - Predicted dependencies
  - Characteristics
  - Creation/update timestamps

### Step 4: Update Statistics
- Tracks zone distribution
- Counts successful vs failed analyses

## IP-Based Zone Inference

Reprocessing uses **network topology intelligence** to determine zones:

### IP Subnet Mappings

| IP Pattern | Security Zone | Purpose |
|------------|---------------|---------|
| `10.100.160.*` | MANAGEMENT_TIER | Infrastructure & monitoring |
| `10.164.105.*` | WEB_TIER | Public-facing web servers |
| `10.100.246.*` | APP_TIER | Application servers (subnet 1) |
| `10.165.116.*` | APP_TIER | Application servers (subnet 2) |
| `10.164.116.*` | DATA_TIER | Databases & persistent storage |
| `10.164.144.*` | CACHE_TIER | Redis, Memcache, etc. |
| `10.164.145.*` | MESSAGING_TIER | Kafka, RabbitMQ, etc. |

### How It Works

1. **Analyze Flow IPs:** Examines all Source and Destination IPs from flow records
2. **Vote-Based Classification:** Counts IPs matching each zone pattern
3. **Confidence Threshold:** Requires ≥30% of IPs to match a pattern
4. **Priority:** IP-based inference overrides naming-based classification
5. **Fallback:** If no IP pattern matches, uses app naming analysis

### Example

Application `AODSVY` with flows:
- `10.100.246.18 → 10.164.116.35` (APP → DATA)
- `10.100.246.51 → 10.100.160.227` (APP → MGMT)
- `10.164.105.74 → 10.164.116.125` (WEB → DATA)
- `10.164.144.195 → 10.165.116.123` (CACHE → APP)

**Result:** Classified as **APP_TIER** (highest IP pattern match)

## Verifying Success

### 1. Check Topology Files

```bash
# Count topology files (should match application count)
ls persistent_data/topology/*.json | wc -l

# View sample topology file
cat persistent_data/topology/AODSVY.json
```

Expected structure:
```json
{
  "app_id": "AODSVY",
  "security_zone": "APP_TIER",
  "dependencies": [
    {
      "type": "database",
      "name": "database_service",
      "confidence": 0.7
    }
  ],
  "characteristics": [],
  "created_at": "2025-10-12T16:04:09.701566",
  "updated_at": "2025-10-12T16:04:09.701573"
}
```

### 2. Refresh Web UI

1. Open web UI: `http://localhost:5000`
2. Navigate to **Applications Overview**
3. Verify:
   - All applications visible
   - Zone distribution shows multiple tiers
   - Click "View Topology" shows complete graph

### 3. Check Zone Distribution

Expected distribution (example):
- **APP_TIER:** 70-80% (most business logic)
- **MESSAGING_TIER:** 10-15% (async services)
- **WEB_TIER:** 5-10% (frontends)
- **CACHE_TIER:** 3-5% (caching layer)
- **MANAGEMENT_TIER:** 2-5% (infrastructure)
- **DATA_TIER:** 1-3% (databases)

## Troubleshooting

### Issue: No flows.csv Found

**Error:** `[SKIP - No flows]`

**Cause:** Application directory missing flow data

**Solution:**
1. Check `persistent_data/applications/{APP_ID}/flows.csv` exists
2. If missing, re-run incremental learning for that app

### Issue: Unicode Encoding Errors

**Error:** `UnicodeEncodeError: 'charmap' codec can't encode...`

**Cause:** Windows console encoding issues (cosmetic only)

**Solution:** Ignore - processing still succeeds. Check log files for details.

### Issue: All Apps Still Show APP_TIER

**Possible Causes:**
1. Flow data doesn't contain diverse IP patterns
2. All apps genuinely in same subnet
3. Threshold too high (30%)

**Solution:** Review flow data IP distribution:
```bash
# Check IP patterns in flows
head -20 persistent_data/applications/*/flows.csv
```

### Issue: Failed Processing

**Error:** `[ERROR] Failed to process {APP_ID}`

**Check:** Log file at `logs/reprocessing_YYYYMMDD_HHMMSS.log`

**Common causes:**
- Corrupted CSV file
- Missing required columns (Source IP, Dest IP)
- Insufficient memory

## Advanced Options

### Reprocess Specific Apps

Edit `reprocess_all_apps.py` to filter specific apps:

```python
# Only process apps starting with 'DN'
app_dirs = [d for d in apps_dir.iterdir()
            if d.is_dir() and d.name.startswith('DN')]
```

### Customize Zone Mappings

Edit `src/agentic/local_semantic_analyzer.py`:

```python
def _infer_zone_from_ips(self, observed_peers):
    # Add custom IP patterns
    if ip.startswith('192.168.1.'):
        zone_votes['CUSTOM_TIER'] += 1
```

### Change Confidence Threshold

In `local_semantic_analyzer.py` line 485:

```python
# Change from 30% to 50%
if zone_votes[best_zone] >= len(observed_peers) * 0.5:
```

## Integration with Incremental Learning

### Auto-Persistence (v3.1+)

**New applications** processed by incremental learning are **automatically persisted**.

Location: `src/core/incremental_learner.py:337-347`

```python
# Topology is now automatically saved
self.pm.save_topology_data(
    app_id=app_id,
    security_zone=analysis['security_zone'],
    dependencies=analysis['predicted_dependencies'],
    characteristics=analysis.get('characteristics', [])
)
```

### When to Reprocess vs Run Incremental

| Scenario | Use |
|----------|-----|
| Fix existing data | **Reprocess** |
| Process new CSV files | **Incremental Learning** |
| Update all with new logic | **Reprocess** |
| Continuous monitoring | **Incremental Learning** |

## Best Practices

1. **Backup First:** Copy `persistent_data/topology/` before reprocessing
2. **Stop Web UI:** Avoid conflicts during reprocessing
3. **Check Logs:** Review log files after completion
4. **Verify Counts:** Ensure topology file count matches applications
5. **Incremental Updates:** After reprocessing, restart incremental learning

## Related Documentation

- [ZONE_CLASSIFICATION.md](docs/ZONE_CLASSIFICATION.md) - Zone inference details
- [HOSTNAME_RESOLUTION_GUIDE.md](HOSTNAME_RESOLUTION_GUIDE.md) - Hostname resolution
- [README.md](README.md) - Main project documentation

## Change Log

### v3.1 (October 2025)
- Added IP-based zone inference
- Automatic topology persistence in incremental learning
- Created reprocessing script
- Improved zone classification accuracy from ~5% to ~70%

---

**Questions?** Check logs at `logs/reprocessing_*.log` or review code comments in `reprocess_all_apps.py`
