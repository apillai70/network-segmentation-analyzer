# Zone Classification System

## Overview

The Network Segmentation Analyzer uses a **hybrid classification approach** combining IP-based network topology analysis with semantic naming patterns to accurately assign applications to security zones.

## Security Zones

### Zone Hierarchy

```
MANAGEMENT_TIER    ← Infrastructure & Monitoring (Highest Security)
    ↓
WEB_TIER          ← Public-Facing Web Servers
    ↓
APP_TIER          ← Business Logic Applications
    ↓
DATA_TIER         ← Databases & Persistent Storage (Highest Protection)
    ↓
CACHE_TIER        ← In-Memory Caching Layer
    ↓
MESSAGING_TIER    ← Asynchronous Message Brokers
```

### Zone Definitions

| Zone | Purpose | Typical Components | Security Level |
|------|---------|-------------------|----------------|
| **MANAGEMENT_TIER** | Infrastructure management & monitoring | Prometheus, Grafana, Logging, Monitoring tools | HIGH |
| **WEB_TIER** | Public-facing web servers | Nginx, Apache, Frontend apps | MEDIUM-HIGH |
| **APP_TIER** | Business logic & microservices | API servers, Backend services, Workers | MEDIUM |
| **DATA_TIER** | Persistent data storage | PostgreSQL, MySQL, MongoDB | CRITICAL |
| **CACHE_TIER** | Fast-access caching | Redis, Memcache | MEDIUM |
| **MESSAGING_TIER** | Asynchronous communication | Kafka, RabbitMQ, SQS | MEDIUM |

## Classification Methods

### Method 1: IP-Based Classification (Primary)

**Priority:** Highest (overrides naming patterns)

**How it works:**
1. Analyze all Source and Destination IPs from network flows
2. Match IPs against known subnet patterns
3. Count matches for each zone (voting system)
4. Assign zone with ≥30% IP pattern confidence

**IP Subnet Mappings:**

```python
# Management Infrastructure
10.100.160.0/24    → MANAGEMENT_TIER

# Web Tier
10.164.105.0/24    → WEB_TIER

# Application Tier (Multiple Subnets)
10.100.246.0/24    → APP_TIER
10.165.116.0/24    → APP_TIER

# Data Tier
10.164.116.0/24    → DATA_TIER

# Cache Tier
10.164.144.0/24    → CACHE_TIER

# Messaging Tier
10.164.145.0/24    → MESSAGING_TIER
```

**Example:**

Application `DM_SBADJ` with flow records:
```
Source IP         Dest IP           Zone Pattern
10.164.105.74  →  10.164.116.125   WEB → DATA
10.164.105.189 →  10.164.144.111   WEB → CACHE
10.164.105.183 →  10.165.116.31    WEB → APP
```

**Result:** 60% of IPs match WEB_TIER pattern → Classified as **WEB_TIER**

### Method 2: Semantic Analysis (Fallback)

**Priority:** Secondary (used when IP-based fails)

**Based on:**
- Application naming patterns
- Metadata (if available)
- Characteristic keywords

**Naming Patterns:**

| Pattern | Zone | Examples |
|---------|------|----------|
| `web`, `frontend`, `ui`, `nginx`, `apache` | WEB_TIER | `web-server-01`, `frontend-app` |
| `api`, `service`, `backend`, `srv` | APP_TIER | `api-gateway`, `user-service` |
| `db`, `database`, `postgres`, `mysql`, `mongo` | DATA_TIER | `postgres-primary`, `mongodb-01` |
| `cache`, `redis`, `memcache` | CACHE_TIER | `redis-cluster`, `memcached-01` |
| `kafka`, `rabbitmq`, `mq`, `queue` | MESSAGING_TIER | `kafka-broker`, `rabbitmq-01` |
| `monitor`, `grafana`, `prometheus` | MANAGEMENT_TIER | `grafana-dashboard` |

**Characteristic Keywords:**

Applications with special characteristics are prioritized:

- `payment`, `billing` → Always **APP_TIER** (requires protection)
- `authentication`, `auth`, `sso` → Always **APP_TIER** (security critical)
- Default fallback → **APP_TIER** (safe default)

### Method 3: Port-Based Hints

**Used as supporting evidence:**

| Port(s) | Likely Zone | Component Type |
|---------|-------------|----------------|
| 80, 443, 8080, 8443 | WEB_TIER | HTTP/HTTPS |
| 5432, 3306, 27017, 1521 | DATA_TIER | Database |
| 6379, 11211 | CACHE_TIER | Redis, Memcache |
| 9092, 5672 | MESSAGING_TIER | Kafka, RabbitMQ |
| 9090, 3000 | MANAGEMENT_TIER | Prometheus, Grafana |

## Classification Algorithm

### Decision Flow

```
START
  ↓
1. Extract all IPs from network flows
  ↓
2. Match IPs against subnet patterns
  ↓
3. Calculate zone confidence (vote count / total IPs)
  ↓
4. IF confidence ≥ 30%
      → Use IP-based zone [HIGH CONFIDENCE]
   ELSE
      ↓
   5. Check application name patterns
      ↓
   6. Check characteristics (auth, payment, etc.)
      ↓
   7. Use semantic zone or fallback to APP_TIER [MEDIUM CONFIDENCE]
  ↓
END
```

### Confidence Scoring

| Method | Confidence | Reliability |
|--------|------------|-------------|
| IP-based with ≥50% match | 0.90-0.95 | Very High |
| IP-based with 30-49% match | 0.70-0.89 | High |
| Semantic with known pattern | 0.60-0.75 | Medium |
| Default fallback | 0.50 | Low |

## Customization

### Adding Custom IP Patterns

Edit `src/agentic/local_semantic_analyzer.py`:

```python
def _infer_zone_from_ips(self, observed_peers):
    """Infer security zone from IP patterns"""

    # Add your custom patterns
    if ip.startswith('192.168.10.'):
        zone_votes['CUSTOM_DMZ'] += 1
    elif ip.startswith('172.16.50.'):
        zone_votes['PARTNER_ZONE'] += 1
```

### Adjusting Confidence Threshold

Line 485 in `local_semantic_analyzer.py`:

```python
# Default: 30% of IPs must match
if zone_votes[best_zone] >= len(observed_peers) * 0.3:
    return best_zone

# Example: Increase to 50% for stricter classification
if zone_votes[best_zone] >= len(observed_peers) * 0.5:
    return best_zone
```

### Adding New Zones

1. **Define zone in knowledge graph** (`local_semantic_analyzer.py`):

```python
'custom_zone': {
    'characteristics': ['custom', 'special'],
    'common_names': ['custom', 'special'],
    'typical_ports': [9999],
    'typical_dependencies': [],
    'security_zone': 'CUSTOM_ZONE',
    'risk_level': 'HIGH',
    'protocols': ['tcp']
}
```

2. **Add IP pattern**:

```python
elif ip.startswith('10.200.0.'):
    zone_votes['CUSTOM_ZONE'] += 1
```

3. **Update web UI** (`web_app/static/js/topology.js`) for visualization

## Validation & Testing

### Verify Classification

```bash
# Check zone distribution
python -c "
import json
from pathlib import Path
from collections import Counter

zones = []
for f in Path('persistent_data/topology').glob('*.json'):
    data = json.load(open(f))
    zones.append(data['security_zone'])

counts = Counter(zones)
for zone, count in counts.most_common():
    print(f'{zone:20s}: {count:3d} apps')
"
```

### Test IP Pattern Matching

```python
# In Python shell
from src.agentic.local_semantic_analyzer import LocalSemanticAnalyzer

analyzer = LocalSemanticAnalyzer()

# Test IPs
test_ips = [
    '10.100.160.50',   # Should be MANAGEMENT_TIER
    '10.164.105.100',  # Should be WEB_TIER
    '10.164.116.200',  # Should be DATA_TIER
]

zone = analyzer._infer_zone_from_ips(test_ips)
print(f"Inferred zone: {zone}")
```

### Manual Override

If classification is incorrect, manually edit topology JSON:

```bash
# Edit specific app
vim persistent_data/topology/APP_NAME.json

# Change security_zone field
{
  "app_id": "APP_NAME",
  "security_zone": "CORRECT_ZONE",  # ← Change this
  ...
}
```

## Common Scenarios

### Scenario 1: Multi-Tier Application

App communicates with multiple zones:

```
App IPs:
- 10.165.116.50 (APP_TIER)  ← 40%
- 10.164.116.100 (DATA_TIER) ← 30%
- 10.164.144.200 (CACHE_TIER) ← 30%
```

**Result:** APP_TIER (highest vote)

### Scenario 2: Boundary Application

App spans two zones equally:

```
App IPs:
- 10.164.105.50 (WEB_TIER)  ← 50%
- 10.165.116.100 (APP_TIER)  ← 50%
```

**Result:** WEB_TIER (first in evaluation order)

**Recommendation:** Manual review needed

### Scenario 3: Unknown Subnet

App uses unlisted IP range:

```
App IPs:
- 192.168.1.100 (UNKNOWN)
- 192.168.1.200 (UNKNOWN)
```

**Result:** Falls back to semantic analysis based on app name

## Best Practices

1. **Keep IP Mappings Updated:** Document subnet-to-zone mappings
2. **Monitor Classification:** Review zone distribution periodically
3. **Manual Verification:** Audit critical apps (payment, auth, databases)
4. **Confidence Thresholds:** Adjust based on network complexity
5. **Hybrid Approach:** Don't rely solely on IPs or names
6. **Log Review:** Check logs for classification decisions

## Troubleshooting

### Issue: All Apps Classified as APP_TIER

**Possible Causes:**
- Flow data doesn't contain IPs from known subnets
- Confidence threshold too high
- IP patterns not matching network topology

**Solution:**
```bash
# Check actual IP distribution
head -100 persistent_data/applications/*/flows.csv | grep -E "10\.[0-9]+"

# Update IP patterns in local_semantic_analyzer.py
# Lower confidence threshold if needed
```

### Issue: Inconsistent Classification

**Cause:** App communicates across multiple zones without clear majority

**Solution:** Increase minimum confidence threshold or add more specific patterns

### Issue: Wrong Zone Assignment

**Cause:** IP-based inference incorrect for edge cases

**Solution:** Add name-based override for specific apps:

```python
# In analyze_application()
if app_name in ['special-app-1', 'special-app-2']:
    security_zone = 'CORRECT_ZONE'
```

## Related Documentation

- [REPROCESSING_GUIDE.md](../REPROCESSING_GUIDE.md) - How to reprocess apps with new classification
- [README.md](../README.md) - Main documentation
- Code: `src/agentic/local_semantic_analyzer.py:436-489`

## References

- **NIST SP 800-125B:** Secure Virtual Network Configuration for IaaS
- **Zero Trust Architecture:** Micro-segmentation principles
- **Defense in Depth:** Multi-layer security design

---

Last Updated: October 2025 | Version: 3.1
