# PostgreSQL Database Setup Guide

## Overview

This application uses PostgreSQL to persist all network flow data for analysis, querying, and visualization.

## Configuration

### Environment Files

The application uses environment-specific `.env` files for database credentials:

- **`.env.production`** - Production database (NEVER commit to git!)
- **`.env.development`** - Local development database
- **`.env.example`** - Template for creating your own `.env` files

### Production Configuration

Production credentials are in `.env.production`:

```bash
ENVIRONMENT=production
DB_HOST=udideapdb01.unix.rgbk.com
DB_PORT=5432
DB_NAME=prutech_bais
DB_SCHEMA=activenet
DB_USER=activenet_admin
DB_PASSWORD=Xm9Kp2Nq7Rt4Wv8Yz3Lh6Jc5
```

### Development Configuration

For local development, use `.env.development`:

```bash
ENVIRONMENT=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=network_analysis_dev
DB_SCHEMA=public
DB_USER=postgres
DB_PASSWORD=postgres
```

## Local PostgreSQL Setup

### Option 1: Docker (Recommended)

```bash
# Start PostgreSQL container
docker run --name network-analysis-db \
  -e POSTGRES_DB=network_analysis_dev \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:15

# Verify connection
docker exec -it network-analysis-db psql -U postgres -d network_analysis_dev
```

### Option 2: Native Installation

#### Windows

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Set password for `postgres` user
4. Ensure PostgreSQL service is running

#### macOS

```bash
brew install postgresql@15
brew services start postgresql@15
createdb network_analysis_dev
```

#### Linux

```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb network_analysis_dev
```

## Database Schema

The application automatically creates the following tables:

### 1. `enriched_flows`

Main table storing all network flow data:

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| created_at | TIMESTAMP | Insertion timestamp |
| source_app_code | VARCHAR(50) | Source application code |
| source_ip | INET | Source IP address |
| source_hostname | VARCHAR(255) | Source hostname (DNS resolved) |
| source_device_type | VARCHAR(50) | Device type (web/app/database/cache/queue) |
| dest_ip | INET | Destination IP address |
| dest_hostname | VARCHAR(255) | Destination hostname |
| dest_device_type | VARCHAR(50) | Destination device type |
| dest_app_code | VARCHAR(50) | Destination application code |
| protocol | VARCHAR(20) | Protocol (TCP/UDP/HTTPS) |
| port | INTEGER | Port number |
| bytes_in | BIGINT | Bytes received |
| bytes_out | BIGINT | Bytes sent |
| flow_direction | VARCHAR(20) | intra-app/inter-app/ingress/egress |
| flow_count | INTEGER | Number of flows |
| has_missing_data | BOOLEAN | Flag for incomplete data |
| missing_fields | TEXT[] | List of missing field names |
| batch_id | VARCHAR(100) | Batch identifier |
| file_source | VARCHAR(255) | Source CSV filename |

**Indexes:**
- `idx_enriched_flows_src_app` on `source_app_code`
- `idx_enriched_flows_dst_app` on `dest_app_code`
- `idx_enriched_flows_src_ip` on `source_ip`
- `idx_enriched_flows_dst_ip` on `dest_ip`
- `idx_enriched_flows_flow_direction` on `flow_direction`
- `idx_enriched_flows_created_at` on `created_at`

### 2. `dns_cache`

DNS lookup cache:

| Column | Type | Description |
|--------|------|-------------|
| ip | INET | IP address (primary key) |
| hostname | VARCHAR(255) | Resolved hostname |
| resolved_at | TIMESTAMP | Resolution timestamp |
| ttl | INTEGER | Time to live (seconds) |

### 3. `flow_aggregates`

Pre-computed aggregations for performance:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| source_app_code | VARCHAR(50) | Source app |
| dest_app_code | VARCHAR(50) | Destination app |
| flow_direction | VARCHAR(20) | Flow direction |
| total_flows | INTEGER | Total flow count |
| total_bytes_in | BIGINT | Total bytes in |
| total_bytes_out | BIGINT | Total bytes out |
| unique_source_ips | INTEGER | Unique source IPs |
| unique_dest_ips | INTEGER | Unique destination IPs |
| last_updated | TIMESTAMP | Last update time |

## Usage

### Initialize Database Connection

```python
from src.database import FlowRepository

# Auto-loads config from .env files
repo = FlowRepository()
```

### Insert Flows from DataFrame

```python
import pandas as pd

# Your enriched DataFrame
df = pd.DataFrame({
    'source_app_code': ['BLZE'],
    'source_ip': ['10.164.144.23'],
    'dest_ip': ['10.164.116.124'],
    # ... other columns
})

# Insert batch
repo.insert_flows_batch(
    df,
    batch_id='20250122_120000',
    file_source='App_Code_BLZE.csv'
)
```

### Query Flows

```python
# Get all flows for a specific app
blze_flows = repo.get_flows_by_app('BLZE')

# Get all flows (with limit)
all_flows = repo.get_all_flows(limit=1000)

# Get statistics
stats = repo.get_statistics()
print(f"Total flows: {stats['total_flows']}")
print(f"Unique apps: {stats['unique_source_apps']}")
```

### DNS Caching

```python
# Cache DNS result
repo.cache_dns_lookup('10.164.144.23', 'blze-server-01.company.com')

# Retrieve cached result
hostname = repo.get_cached_dns('10.164.144.23')
```

### Update Aggregates

```python
# Refresh aggregated statistics
repo.update_flow_aggregates()
```

## Environment Selection

The application automatically detects the environment based on:

1. `ENVIRONMENT` variable in `.env` file
2. Presence of `.env.production` vs `.env.development`

### Force Specific Environment

```python
from src.config import get_config

# Force production
config = get_config(environment='production')

# Force development
config = get_config(environment='development')
```

## Troubleshooting

### Connection Failed

```
Failed to connect to PostgreSQL: FATAL: password authentication failed
```

**Solution:** Check credentials in `.env` file

### Schema Not Found

```
ERROR: schema "activenet" does not exist
```

**Solution:** The application will create the schema automatically. If it fails, create manually:

```sql
CREATE SCHEMA activenet;
GRANT ALL ON SCHEMA activenet TO activenet_admin;
```

### Permission Denied

```
ERROR: permission denied for schema activenet
```

**Solution:** Grant permissions:

```sql
GRANT ALL ON SCHEMA activenet TO activenet_admin;
GRANT ALL ON ALL TABLES IN SCHEMA activenet TO activenet_admin;
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] `.env.production` exists with correct credentials
- [ ] `.env.production` is in `.gitignore` (NEVER commit!)
- [ ] PostgreSQL instance is accessible from application server
- [ ] Database user has necessary permissions
- [ ] Schema `activenet` exists
- [ ] Firewall allows connection to port 5432

### Test Connection

```python
python -c "from src.database import FlowRepository; repo = FlowRepository(); print(repo.get_statistics())"
```

Expected output:
```
✓ Connected to PostgreSQL: udideapdb01.unix.rgbk.com:5432/prutech_bais
✓ Schema 'activenet' ready
✓ Database tables created in schema 'activenet'
{'total_flows': 0, 'unique_source_apps': 0, ...}
```

## Security Best Practices

1. **Never commit credentials** - `.env` files are in `.gitignore`
2. **Use strong passwords** - Change default passwords in production
3. **Limit database user permissions** - Grant only necessary privileges
4. **Enable SSL** - Set `DB_SSL_MODE=require` in production
5. **Rotate credentials** - Update passwords periodically
6. **Monitor access** - Enable PostgreSQL logging

## Backup & Recovery

### Manual Backup

```bash
# Backup entire database
pg_dump -h udideapdb01.unix.rgbk.com -U activenet_admin -d prutech_bais > backup.sql

# Backup specific schema
pg_dump -h udideapdb01.unix.rgbk.com -U activenet_admin -d prutech_bais -n activenet > activenet_backup.sql
```

### Restore

```bash
psql -h udideapdb01.unix.rgbk.com -U activenet_admin -d prutech_bais < backup.sql
```

## Performance Optimization

### Vacuum and Analyze

```sql
-- Run periodically to optimize queries
VACUUM ANALYZE activenet.enriched_flows;
VACUUM ANALYZE activenet.flow_aggregates;
```

### Check Index Usage

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'activenet'
ORDER BY idx_scan DESC;
```

## Disabling PostgreSQL

To disable PostgreSQL and use JSON fallback:

1. Edit `.env.{environment}`:
   ```bash
   DB_ENABLED=false
   ```

2. Or edit `config.yaml`:
   ```yaml
   database:
     postgresql:
       enabled: false
   ```

The application will automatically fall back to JSON file storage.
