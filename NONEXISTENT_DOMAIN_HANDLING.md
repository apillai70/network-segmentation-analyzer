# Non-Existent Domain Handling Guide

## Overview

The hostname resolver now includes intelligent handling of non-existent domains (NXDOMAIN) from DNS lookups. This helps clean up your network analysis by identifying and optionally filtering flows where DNS resolution fails.

## Features

### 1. **Detection of Non-Existent Domains**

When DNS lookup fails with "host not found" or "name or service not known", the IP is marked as **non-existent**.

### 2. **Marking Non-Existent IPs**

Non-existent domains are displayed as **"server-not-found"** instead of showing the raw IP address. This makes it immediately clear which hosts don't have valid DNS entries.

**Before:**
```
10.1.2.3 -> 10.5.6.7
```

**After (with marking enabled):**
```
server-not-found -> server-not-found
```

### 3. **Automatic Filtering**

Flows where **BOTH** source and destination are non-existent can be automatically filtered from analysis. This helps focus on legitimate network traffic.

**Example:**
- Flow: `10.1.2.3 -> 10.5.6.7` (both non-existent) → **FILTERED**
- Flow: `web-server-01 -> 10.5.6.7` (only dest non-existent) → **KEPT**
- Flow: `10.1.2.3 -> db-server-01` (only src non-existent) → **KEPT**

## Configuration Flags

### `filter_nonexistent` (default: `True`)

Controls whether flows with non-existent domains should be marked for filtering.

- **True**: Flows where both source AND destination are non-existent will be filtered
- **False**: All flows are kept, regardless of DNS status

### `mark_nonexistent` (default: `True`)

Controls how non-existent domains are displayed.

- **True**: Show as "server-not-found"
- **False**: Show the raw IP address

## Usage Examples

### Example 1: Enable Both Features (Default)

```python
from src.utils.hostname_resolver import HostnameResolver

resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=True,   # Filter flows with both IPs non-existent
    mark_nonexistent=True       # Show "server-not-found" label
)
```

**Result:**
- Non-existent IPs are labeled "server-not-found"
- Flows with both IPs non-existent are filtered out

### Example 2: Mark But Don't Filter

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=False,   # Keep all flows
    mark_nonexistent=True        # Show "server-not-found" label
)
```

**Result:**
- Non-existent IPs are labeled "server-not-found"
- All flows are kept in analysis (nothing filtered)

### Example 3: Filter But Don't Mark

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=True,    # Filter flows with both IPs non-existent
    mark_nonexistent=False       # Show raw IP address
)
```

**Result:**
- Non-existent IPs show as raw IP addresses
- Flows with both IPs non-existent are still filtered out

### Example 4: Disable Both Features

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=False,   # Keep all flows
    mark_nonexistent=False       # Show raw IP address
)
```

**Result:**
- Original behavior: non-existent IPs show as raw IP addresses
- All flows are kept (nothing filtered)

## Helper Methods

### Check if IP is Non-Existent

```python
if resolver.is_nonexistent('10.1.2.3'):
    print("IP has no DNS entry")
```

### Check if Flow Should be Filtered

```python
if resolver.should_filter_flow('10.1.2.3', '10.5.6.7'):
    print("This flow will be filtered (both IPs non-existent)")
```

### Get Non-Existent Count

```python
count = resolver.get_nonexistent_count()
print(f"Found {count} IPs without DNS entries")
```

### Get Statistics

```python
stats = resolver.get_cache_stats()
print(f"Cached hostnames: {stats['cached_hostnames']}")
print(f"Non-existent IPs: {stats['nonexistent_ips']}")
```

## Integration with Flow Processing

When processing network flows, use the resolver to filter:

```python
hostname_resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=True,
    mark_nonexistent=True
)

# Process flows
filtered_flows = []
for flow in all_flows:
    # Resolve hostnames (this marks non-existent IPs)
    src_hostname = hostname_resolver.resolve(flow.src_ip)
    dst_hostname = hostname_resolver.resolve(flow.dst_ip)

    # Check if flow should be filtered
    if hostname_resolver.should_filter_flow(flow.src_ip, flow.dst_ip):
        logger.debug(f"Filtering flow: {flow.src_ip} -> {flow.dst_ip} (both non-existent)")
        continue

    # Keep this flow
    filtered_flows.append(flow)

print(f"Original flows: {len(all_flows)}")
print(f"Filtered flows: {len(filtered_flows)}")
print(f"Removed: {len(all_flows) - len(filtered_flows)}")
```

## Command-Line Configuration

When using batch processing or diagram regeneration scripts, you can configure the resolver using command-line flags.

### Quick Start

#### Batch Processing (Default - Recommended)

```bash
# Default behavior: filtering enabled, marking enabled
python run_batch_processing.py --batch-size 10

# Same as above (explicit flags)
python run_batch_processing.py --batch-size 10 --filter-nonexistent --mark-nonexistent
```

#### Disable Filtering (Show All Flows)

```bash
# Keep all flows, even if both IPs are non-existent
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent
```

#### Advanced Configurations

```bash
# Filter flows but show raw IP addresses (no "server-not-found" labels)
python run_batch_processing.py --batch-size 10 --filter-nonexistent --no-mark-nonexistent

# Keep all flows but mark non-existent IPs with labels (for troubleshooting)
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --mark-nonexistent

# Disable both features (raw IPs, no filtering)
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --no-mark-nonexistent
```

### Diagram Regeneration

The same flags work with diagram regeneration:

```bash
# Default: filtering enabled
python regenerate_diagrams_with_hostnames.py

# Disable filtering
python regenerate_diagrams_with_hostnames.py --no-filter-nonexistent

# Custom input/output paths with filtering
python regenerate_diagrams_with_hostnames.py \
  --input data/custom/flows.csv \
  --output outputs/custom_diagrams \
  --filter-nonexistent \
  --mark-nonexistent
```

### Expected Output

When running with filtering enabled, you'll see:

```
================================================================================
BATCH PROCESSING ORCHESTRATOR
================================================================================
Batch size: 10 files per batch
Output format: BOTH
  - Mermaid diagrams: Yes
  - Lucidchart CSVs: Yes
Generate netseg reports: Yes
Flow filtering:
  - Filter non-existent: Yes
  - Mark non-existent: Yes (server-not-found)
================================================================================

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

### Use Case Examples

#### Use Case 1: Production Analysis (Default)

**Goal:** Clean, focused analysis of legitimate traffic only

```bash
python run_batch_processing.py --batch-size 10
```

**Result:**
- Non-existent IPs labeled as "server-not-found"
- Flows with both IPs non-existent are filtered out
- Clean diagrams with minimal noise
- Faster processing

**Best for:** Production network analysis, security assessment, documentation

#### Use Case 2: DNS Troubleshooting

**Goal:** Identify all DNS resolution issues without losing data

```bash
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --mark-nonexistent
```

**Result:**
- All flows kept (nothing filtered)
- Non-existent IPs clearly marked as "server-not-found"
- See which systems communicate with non-existent endpoints
- Identify stale IP addresses and DNS misconfigurations

**Best for:** DNS troubleshooting, identifying stale systems, network audits

#### Use Case 3: Complete Network Audit

**Goal:** See every single flow without any modifications

```bash
python run_batch_processing.py --batch-size 10 --no-filter-nonexistent --no-mark-nonexistent
```

**Result:**
- All flows kept (nothing filtered)
- Raw IP addresses shown (no labels)
- Complete unfiltered view of network traffic
- No data loss

**Best for:** Comprehensive audits, regulatory compliance, baseline analysis

### Filtering Logic Summary

| Source IP | Destination IP | Filtered? | Displayed As (if marked) |
|-----------|----------------|-----------|--------------------------|
| `server-not-found` | `server-not-found` | **YES** | N/A (filtered out) |
| `web-server-01` | `server-not-found` | **NO** | `web-server-01 → server-not-found` |
| `server-not-found` | `db-server-01` | **NO** | `server-not-found → db-server-01` |
| `web-server-01` | `db-server-01` | **NO** | `web-server-01 → db-server-01` |

**Key Point:** Filtering is conservative - it only removes flows where BOTH endpoints are non-existent.

For more detailed information about flow filtering, see **FILTERING_GUIDE.md**

## Logging Output

When the feature is active, you'll see log messages like:

```
INFO: HostnameResolver initialized
INFO:   Demo mode: False
INFO:   DNS lookup: True
INFO:   Filter non-existent: True
INFO:   Mark non-existent: True

DEBUG: DNS lookup: 10.1.2.3 -> Non-existent domain
DEBUG: Marked 10.1.2.3 as server-not-found (NXDOMAIN)
DEBUG: DNS lookup: 10.5.6.7 -> Non-existent domain
DEBUG: Marked 10.5.6.7 as server-not-found (NXDOMAIN)
DEBUG: Filtering flow: 10.1.2.3 -> 10.5.6.7 (both non-existent)
```

## Statistics and Reporting

At the end of analysis, you'll see statistics:

```
Hostname Resolution Statistics:
  Cached hostnames: 1,523
  Provided hostnames: 234
  Non-existent IPs: 47
  Flows filtered (both non-existent): 18
```

## Benefits

1. **Cleaner Diagrams**: Non-existent hosts are clearly labeled as "server-not-found"
2. **Focused Analysis**: Filter out noise from failed/stale IP addresses
3. **Better Documentation**: Word reports show meaningful labels instead of cryptic IPs
4. **Faster Processing**: Fewer flows to process when filtering is enabled
5. **Security Insights**: Identify potentially stale or misconfigured systems

## Typical Use Cases

### Use Case 1: Clean Production Analysis

Enable both features to get clean, focused analysis:

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=True,
    mark_nonexistent=True
)
```

**Best for:** Production environments where you want to focus only on legitimate traffic.

### Use Case 2: Troubleshooting DNS Issues

Mark but don't filter to see all traffic while identifying DNS problems:

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=False,
    mark_nonexistent=True
)
```

**Best for:** Troubleshooting DNS configuration issues.

### Use Case 3: Audit All Traffic

Disable both features to see everything:

```python
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    filter_nonexistent=False,
    mark_nonexistent=False
)
```

**Best for:** Complete network audits where you need to see all flows.

## Summary

The non-existent domain handling feature provides:

- ✅ **Automatic detection** of IPs with no DNS entries
- ✅ **Clear labeling** with "server-not-found"
- ✅ **Smart filtering** (only when both IPs are non-existent)
- ✅ **Flexible configuration** via flags
- ✅ **Detailed logging** and statistics
- ✅ **Production-ready** with sensible defaults

**Default behavior:** Filter and mark non-existent domains (recommended for production).
