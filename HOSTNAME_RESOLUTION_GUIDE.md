# 🔍 Hostname Resolution Feature

**Date:** 2025-10-12

## Overview

The Network Segmentation Analyzer now includes intelligent hostname resolution to display meaningful server names instead of just IP addresses in diagrams and reports.

## Features

### ✅ **Multiple Resolution Strategies**

1. **CSV Data** - If hostname columns exist in your input files
2. **Reverse DNS Lookup (nslookup)** - Standard DNS resolution
3. **Domain Controller Query** - Query Active Directory for computer names
4. **Synthetic Generation** - Smart hostname generation for demos

### ✅ **Two Operation Modes**

#### Demo Mode (Default)
- Generates realistic synthetic hostnames
- Perfect for presentations and demos
- Based on IP patterns and security zones
- No network dependencies

**Example Outputs:**
- `10.100.160.101` → `mgmt-mgmt-101` (Management subnet)
- `10.164.116.237` → `db-db-237` (Database subnet)
- `10.164.105.248` → `web-web-248` (Web tier subnet)
- `10.164.144.219` → `cache-cache-219` (Cache subnet)

#### Production Mode
- Uses reverse DNS lookups (nslookup)
- Can query Domain Controller via LDAP
- Caches results for performance
- Falls back to demo mode if resolution fails

## Configuration

### Quick Start (Demo Mode)

No configuration needed! The system automatically uses demo mode by default.

### Switch to Production Mode

Edit `config/hostname_config.yaml`:

```yaml
# Change mode to production
mode: production

# Enable DNS lookups
dns_lookup:
  enabled: true
  timeout: 2.0

# Configure Domain Controller (optional)
domain_controller:
  enabled: true
  server: "dc1.company.local"
  domain: "company.local"
  ldap:
    base_dn: "DC=company,DC=local"
    username: "svc_network_analyzer"
    password: "${NETWORK_ANALYZER_AD_PASSWORD}"  # Use environment variable!
```

### Environment Variable for AD Password

```bash
# Windows (PowerShell)
$env:NETWORK_ANALYZER_AD_PASSWORD="your-password-here"

# Linux/Mac
export NETWORK_ANALYZER_AD_PASSWORD="your-password-here"
```

## Usage in Diagrams

### Mermaid Diagrams

Hostnames are automatically displayed in all Mermaid diagrams:

**Before (IPs only):**
```
10_164_105_171["10.164.105.171"]
```

**After (with hostnames):**
```
10_164_105_171["web-web-171<br/>(10.164.105.171)"]
```

### Web UI Topology

The interactive topology view also shows hostnames in:
- Node labels
- Tooltips on hover
- Node details panel

## Programmatic Usage

### Python API

```python
from utils.hostname_resolver import HostnameResolver, configure_resolver

# Demo mode (default)
resolver = HostnameResolver(demo_mode=True)
hostname = resolver.resolve("10.164.116.237", zone="DATA_TIER")
# Returns: "db-db-237"

# Production mode with DNS
resolver = HostnameResolver(
    demo_mode=False,
    enable_dns_lookup=True,
    dc_server="dc1.company.local",
    dc_domain="company.local"
)
hostname = resolver.resolve("10.164.116.237")
# Returns actual hostname from DNS/AD

# Get formatted display name
hostname, display = resolver.resolve_with_display("10.164.116.237", zone="DATA_TIER")
# Returns: ("db-db-237", "db-db-237<br/>(10.164.116.237)")
```

### Global Configuration

```python
from utils.hostname_resolver import configure_resolver

# Configure once at startup
resolver = configure_resolver(
    demo_mode=False,
    enable_dns_lookup=True,
    dc_server="dc1.company.local",
    dc_domain="company.local"
)

# Use throughout the application
from utils.hostname_resolver import resolve_hostname
hostname = resolve_hostname("10.164.116.237", zone="DATA_TIER")
```

## Synthetic Hostname Patterns

In demo mode, hostnames follow these patterns:

| Subnet Pattern | Prefix | Example |
|----------------|--------|---------|
| `10.100.160.*` | `mgmt` | `mgmt-mgmt-101` |
| `10.100.246.*` | `app` | `app-app-42` |
| `10.164.105.*` | `web` | `web-web-248` |
| `10.164.116.*` | `db` | `db-db-237` |
| `10.164.144.*` | `cache` | `cache-cache-219` |
| `10.164.145.*` | `mq` | `mq-mq-83` |
| `10.165.116.*` | `api` | `api-api-47` |
| `2001:db8:*` | `ipv6` | `ipv6-app-504b` |

### Zone-Based Naming

If security zone is provided, hostnames reflect the zone:

```python
resolver.resolve("10.100.100.50", zone="WEB_TIER")     # → "web-server-50"
resolver.resolve("10.100.100.50", zone="APP_TIER")     # → "app-server-50"
resolver.resolve("10.100.100.50", zone="DATA_TIER")    # → "db-server-50"
resolver.resolve("10.100.100.50", zone="CACHE_TIER")   # → "cache-server-50"
```

## Production Integration

### Domain Controller Query (Windows AD)

For production environments with Active Directory:

```python
resolver = HostnameResolver(
    demo_mode=False,
    dc_server="dc1.company.local",
    dc_domain="company.local"
)

# This will:
# 1. First check cache
# 2. Try reverse DNS lookup
# 3. Query AD/LDAP for computer object
# 4. Return hostname with domain suffix
```

### LDAP Query Example

The system can query Active Directory via LDAP:

```python
# Queries AD for computer with specific IP
# LDAP filter: (&(objectClass=computer)(ipAddress=10.164.116.237))
# Returns: CN attribute (computer name)
```

### PowerShell Integration (Future)

For Windows environments without LDAP access:

```powershell
# The system can execute PowerShell commands
Resolve-DnsName -Name 10.164.116.237 -Type PTR
```

## Performance & Caching

### Caching Strategy

- All resolved hostnames are cached
- Cache persists for session duration
- Configurable TTL (default: 1 hour)
- Maximum 10,000 cached entries

### Cache Stats

```python
resolver = HostnameResolver()
stats = resolver.get_cache_stats()
print(f"Cached hostnames: {stats['cached_hostnames']}")
print(f"Provided hostnames: {stats['provided_hostnames']}")
```

### Clear Cache

```python
resolver.clear_cache()
```

## Viewing Results

### See Hostnames in Diagrams

After running the pipeline:

```bash
# Process files with complete pipeline
python run_complete_pipeline.py --max-files 1
```

Open the generated diagrams:
- `outputs_final/diagrams/ALE_diagram.html` - Interactive HTML
- `outputs_final/diagrams/ALE_diagram.mmd` - Mermaid source

### Web UI

Visit http://localhost:5000/topology to see the interactive topology with hostnames.

## Benefits

✅ **Better Visualization** - See meaningful names instead of IPs
✅ **Easier Debugging** - Quickly identify servers in diagrams
✅ **Demo-Ready** - No setup needed for presentations
✅ **Production-Ready** - Full AD/DNS integration available
✅ **Flexible** - Works with CSV data, DNS, or AD
✅ **Cached** - Fast repeated lookups
✅ **Fallback** - Always shows something useful

## Troubleshooting

### Hostnames Not Showing in Diagrams

1. Check if hostname resolver is enabled in diagram generator
2. Verify config file `config/hostname_config.yaml`
3. Check logs for DNS/AD errors

### DNS Lookups Timing Out

Increase timeout in config:
```yaml
dns_lookup:
  timeout: 5.0  # Increase to 5 seconds
```

### Domain Controller Connection Failed

Verify:
- DC server is reachable: `ping dc1.company.local`
- Credentials are correct
- Environment variable is set
- LDAP port 389 is accessible

## Next Steps

- Configure production mode for your environment
- Set up service account for AD queries
- Adjust synthetic patterns for your IP ranges
- Enable DNS caching for better performance

---

**Status:** ✅ Fully Implemented
**Version:** 1.0
**Last Updated:** 2025-10-12
