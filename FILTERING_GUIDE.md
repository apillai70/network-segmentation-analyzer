# Flow Filtering Guide - Remove Non-Existent Domains

## Quick Start

### Enable Filtering (Default - Recommended)

```bash
# Default - filtering enabled automatically
python run_batch_processing.py --batch-size 10

# Explicitly enable filtering
python run_batch_processing.py --batch-size 10 --filter-nonexistent
```

### Disable Filtering (Show All Flows)

```bash
# Disable filtering - show all flows including non-existent
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent
```

---

## What Gets Filtered?

The system filters **ONLY** flows where **BOTH** source AND destination have non-existent DNS entries (NXDOMAIN).

### Filtering Logic

| Source IP | Destination IP | Filtered? | Reason |
|-----------|----------------|-----------|---------|
| `server-not-found` | `server-not-found` | **YES** | Both non-existent |
| `web-server-01` | `server-not-found` | **NO** | Only destination non-existent |
| `server-not-found` | `db-server-01` | **NO** | Only source non-existent |
| `web-server-01` | `db-server-01` | **NO** | Both exist |

**Conservative approach:** We keep flows where at least ONE endpoint is valid.

---

## Command Examples

### Standard Usage

```bash
# Process with filtering (default)
python run_batch_processing.py --batch-size 10

# Same as above (explicit)
python run_batch_processing.py --batch-size 10 --filter-nonexistent
```

### Show All Flows (No Filtering)

```bash
# Disable filtering
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent
```

### Control Labeling

```bash
# Filter AND show "server-not-found" labels (default)
python run_batch_processing.py --batch-size 10 --filter-nonexistent --mark-nonexistent

# Filter but show raw IP addresses
python run_batch_processing.py --batch-size 10 --filter-nonexistent --no-mark-nonexistent

# No filtering, but mark non-existent IPs
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --mark-nonexistent
```

---

## Output Examples

### With Filtering Enabled (Default)

**Before filtering:**
```
Total flows: 1,523
  - web-server-01 → db-server-01: 450 flows
  - api-server-02 → cache-server-01: 320 flows
  - server-not-found → server-not-found: 18 flows  ← Will be filtered
  - 10.1.2.3 → web-server-01: 45 flows  ← Kept (only source non-existent)
```

**After filtering:**
```
✓ Flow filtering complete:
  Total flows: 1,523
  Filtered out: 18 (1.2%)
  Flows kept: 1,505
  Non-existent IPs found: 23

Flows in reports/diagrams: 1,505
```

### With Filtering Disabled

**Output:**
```
Total flows: 1,523
Filtering: Disabled
Flows in reports/diagrams: 1,523 (all flows shown)
```

---

## Where Filtering Applies

Filtering is applied to:

✅ **Mermaid Diagrams** (.mmd, .html, .png)
- Application diagrams
- Overall network diagram
- Zone flow diagrams

✅ **Word Reports**
- Network segmentation reports
- Architecture documents
- Solution design documents

✅ **Lucidchart Exports** (CSV files)

✅ **D3 Visualizations**
- Interactive network graphs
- Topology visualizations

---

## Configuration Options

### Flag Combinations

```bash
# ============================================
# RECOMMENDED: Filter + Mark (Default)
# ============================================
python run_batch_processing.py --batch-size 10
# Result: Clean diagrams, clear labels

# ============================================
# TROUBLESHOOTING: No Filter + Mark
# ============================================
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent
# Result: See all flows, identify DNS issues

# ============================================
# AUDIT: No Filter + No Mark
# ============================================
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --no-mark-nonexistent
# Result: Complete raw traffic view

# ============================================
# CUSTOM: Filter + No Mark
# ============================================
python run_batch_processing.py --batch-size 10 --filter-nonexistent --no-mark-nonexistent
# Result: Clean diagrams with raw IPs
```

---

## Statistics and Logging

### Console Output

```
================================================================================
BATCH PROCESSING ORCHESTRATOR
================================================================================
Batch size: 10 files per batch
Max batches: unlimited
Clear tracking first: No
Output format: BOTH
  - Mermaid diagrams: Yes
  - Lucidchart CSVs: Yes
Generate netseg reports: Yes
Generate architecture docs: Yes (requires PNGs)
Flow filtering:
  - Filter non-existent: Yes
  - Mark non-existent: Yes (server-not-found)
================================================================================
```

### During Processing

```
🔍 PHASE 0: Flow Filtering
--------------------------------------------------------------------------------
Resolving hostnames for 1,523 flows...
Filtering flows where both IPs are non-existent...
✓ Flow filtering complete:
  Total flows: 1,523
  Filtered out: 18 (1.2%)
  Flows kept: 1,505
  Non-existent IPs found: 23

Filter reasons:
  - both_nonexistent: 18
```

---

## Use Cases

### Use Case 1: Production Analysis (Recommended)

**Goal:** Clean, focused analysis of legitimate traffic

```bash
python run_batch_processing.py --batch-size 10 --filter-nonexistent
```

**Benefits:**
- Clean diagrams (no noise)
- Faster processing
- Clear reports
- Focused security analysis

### Use Case 2: DNS Troubleshooting

**Goal:** Identify all DNS resolution issues

```bash
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --mark-nonexistent
```

**Benefits:**
- See all flows (including non-existent)
- Clear labeling of DNS failures
- Identify stale IP addresses
- Find misconfigured systems

### Use Case 3: Complete Network Audit

**Goal:** See every single flow without any filtering

```bash
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --no-mark-nonexistent
```

**Benefits:**
- Complete visibility
- No data loss
- Raw network view
- Comprehensive audit trail

---

## FAQ

### Q: How do I know if flows are being filtered?

**A:** Check the console output during processing:

```
✓ Flow filtering complete:
  Total flows: 1,523
  Filtered out: 18 (1.2%)  ← Look here
  Flows kept: 1,505
```

### Q: Can I see which specific flows were filtered?

**A:** Yes, check the log file:

```
logs/batch_processing_YYYYMMDD_HHMMSS.log
```

Look for lines like:
```
DEBUG: Filtering flow: 10.1.2.3 -> 10.5.6.7 (both non-existent)
```

### Q: What if I want to filter more aggressively?

**A:** The current filtering is conservative (only filters if BOTH IPs are non-existent). To filter more aggressively, you would need to modify the filtering logic in `src/utils/flow_filter.py`.

### Q: Does filtering affect machine learning models?

**A:** Yes, filtered flows are removed BEFORE analysis, so ML models train only on valid traffic. This improves prediction accuracy.

### Q: Can I apply filtering retroactively?

**A:** Yes! Regenerate diagrams with filtering:

```bash
python regenerate_diagrams_with_hostnames.py --filter-nonexistent
```

---

## Performance Impact

### With Filtering (Default)

| Metric | Impact |
|--------|--------|
| Processing Time | **Faster** (fewer flows to process) |
| Diagram Size | **Smaller** (cleaner, more readable) |
| Memory Usage | **Lower** (fewer objects in memory) |
| Report Size | **Smaller** (fewer pages in Word docs) |

### Without Filtering

| Metric | Impact |
|--------|--------|
| Processing Time | Slower (more flows) |
| Diagram Size | Larger (may be cluttered) |
| Memory Usage | Higher |
| Report Size | Larger |

**Typical filtering rate:** 1-5% of flows removed (depends on network health)

---

## Related Documentation

- **NONEXISTENT_DOMAIN_HANDLING.md** - Technical details about DNS resolution and filtering
- **HOSTNAME_RESOLUTION_GUIDE.md** - Hostname resolution configuration
- **BATCH_PROCESSING_GUIDE.md** - Complete batch processing guide

---

## Troubleshooting

### Issue: "No flows after filtering"

**Cause:** All flows had non-existent endpoints

**Solution:**
1. Check if DNS resolution is working properly
2. Try running without filtering to see all flows:
   ```bash
   python run_batch_processing.py --batch-size 10 --no-filter-nonexistent
   ```
3. Verify your CSV files have valid IP addresses

### Issue: "Too many flows filtered"

**Cause:** DNS lookup may be failing for many IPs

**Solution:**
1. Check DNS configuration
2. Verify network connectivity
3. Try demo mode (synthetic hostnames):
   ```python
   # In your code
   resolver = HostnameResolver(demo_mode=True, filter_nonexistent=False)
   ```

### Issue: "Want to filter flows with ANY non-existent IP"

**Cause:** Current logic only filters if BOTH IPs are non-existent

**Solution:**
Modify `src/utils/flow_filter.py`:

```python
# Change this:
if hostname_resolver.should_filter_flow(src_ip, dst_ip):

# To this (filters if ANY IP is non-existent):
if hostname_resolver.is_nonexistent(src_ip) or hostname_resolver.is_nonexistent(dst_ip):
```

---

## Summary

**Default Behavior (Recommended):**
- ✅ Filtering: **Enabled**
- ✅ Marking: **Enabled**
- ✅ Logic: Filter ONLY if **BOTH** IPs are non-existent
- ✅ Result: Clean diagrams, focused analysis

**Quick Commands:**
```bash
# Enable filtering (default)
python run_batch_processing.py --batch-size 10

# Disable filtering
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent

# Filter without marking
python run_batch_processing.py --batch-size 10 --no-mark-nonexistent
```

For more details, see **NONEXISTENT_DOMAIN_HANDLING.md**
