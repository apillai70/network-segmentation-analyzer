# Getting Started Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install PostgreSQL driver
pip install psycopg2-binary>=2.9.0

# Or install all requirements
pip install -r requirements.txt
```

### 2. Configure Environment

**For Development (Local):**
```bash
# Copy example to development
cp .env.example .env.development

# Edit .env.development with your local PostgreSQL settings
# Default: localhost:5432, database=network_analysis_dev
```

**For Production:**
```bash
# .env.production already configured with production credentials
# Host: udideapdb01.unix.rgbk.com
# Schema: activenet
```

### 3. Test Database Connection

```bash
# Test PostgreSQL connection
python -c "from src.database import FlowRepository; repo = FlowRepository(); print('✓ Database connected!')"
```

Expected output:
```
✓ Connected to PostgreSQL: localhost:5432/network_analysis_dev
✓ Schema 'public' ready
✓ Database tables created in schema 'public'
✓ Database connected!
```

### 4. Run Complete Pipeline

```bash
# Process all CSV files and generate diagrams
python run_complete_pipeline.py
```

---

## 📊 Processing Flow Data

### Step-by-Step Workflow

**1. Prepare CSV Files**
- Place CSV files in `data/input/` directory
- Format: `App_Code_XXXX.csv`
- Columns: `App, Source IP, Source Hostname, Dest IP, Dest Hostname, Port, Protocol, Bytes In, Bytes Out`

**2. Build Master DataFrame**
```python
from src.data_enrichment.master_df_builder import MasterDataFrameBuilder

# Initialize builder
builder = MasterDataFrameBuilder(
    input_dir='data/input',
    output_dir='outputs_final'
)

# Build enriched master DataFrame
master_df = builder.build_master_dataframe()

# Output:
# - outputs_final/master_enriched_flows.csv
# - outputs_final/master_enriched_flows.parquet
```

**3. Persist to PostgreSQL**
```python
from src.database import FlowRepository

# Initialize repository
repo = FlowRepository()

# Insert flows (automatically done by builder, but can be manual)
repo.insert_flows_batch(
    master_df,
    batch_id='20250122_120000',
    file_source='manual_import'
)

# Update aggregates for fast queries
repo.update_flow_aggregates()

# Check statistics
stats = repo.get_statistics()
print(f"Total flows: {stats['total_flows']}")
```

**4. Generate Diagrams**
```python
from src.diagrams import MermaidDiagramGenerator

# Load flows from database
flows_df = repo.get_all_flows()

# Generate diagrams
generator = MermaidDiagramGenerator(
    flow_records=flows_df.to_dict('records'),
    zones={}  # Auto-detected from flows
)

# Generate overall network diagram
generator.generate_overall_network_diagram('outputs_final/diagrams/overall_network.mmd')

# Generate per-app diagrams
generator.generate_all_app_diagrams('outputs_final/diagrams/')
```

**5. Generate PNG/SVG**
```bash
# Generate both PNG and SVG
python generate_pngs_and_svgs_python.py --format both

# Or just SVG for better quality
python generate_pngs_and_svgs_python.py --format svg

# Or specific apps only
python generate_pngs_and_svgs_python.py --apps BLZE CNET --format both
```

---

## 🔍 Querying Data

### Query Flows by Application

```python
from src.database import FlowRepository

repo = FlowRepository()

# Get all flows for BLZE application
blze_flows = repo.get_flows_by_app('BLZE')

print(f"Total flows: {len(blze_flows)}")
print(f"Unique destinations: {blze_flows['dest_ip'].nunique()}")

# Analyze flow directions
print(blze_flows['flow_direction'].value_counts())
```

### Find Inter-App Communications

```python
# Get all flows from database
all_flows = repo.get_all_flows()

# Filter inter-app flows
inter_app = all_flows[all_flows['flow_direction'] == 'inter-app']

# Group by source and destination app
app_matrix = inter_app.groupby(['source_app_code', 'dest_app_code']).agg({
    'flow_count': 'sum',
    'bytes_in': 'sum',
    'bytes_out': 'sum'
}).reset_index()

print(app_matrix.head(10))
```

### Identify Missing Data

```python
# Find flows with missing hostnames
missing_hostname = all_flows[all_flows['has_missing_data'] == True]

# Group by app
missing_by_app = missing_hostname.groupby('source_app_code').size().sort_values(ascending=False)

print("Apps with most missing data:")
print(missing_by_app.head(10))

# Get specific missing fields
missing_fields_summary = missing_hostname.explode('missing_fields')['missing_fields'].value_counts()
print("\nMost common missing fields:")
print(missing_fields_summary)
```

---

## 🎨 Visualization Examples

### 1. Overall Network Diagram

```bash
# Generate Mermaid diagram
python -c "
from src.diagrams import MermaidDiagramGenerator
from src.database import FlowRepository

repo = FlowRepository()
flows = repo.get_all_flows(limit=1000)  # Limit for performance

generator = MermaidDiagramGenerator(flows.to_dict('records'), {})
generator.generate_overall_network_diagram('outputs_final/diagrams/overall_network.mmd')
"

# Generate SVG
python generate_pngs_and_svgs_python.py --format svg
```

### 2. Application-Specific Diagram

```python
from src.diagrams import MermaidDiagramGenerator
from src.database import FlowRepository

repo = FlowRepository()
blze_flows = repo.get_flows_by_app('BLZE')

generator = MermaidDiagramGenerator(blze_flows.to_dict('records'), {})
generator.generate_app_diagram('BLZE', 'outputs_final/diagrams/BLZE_diagram.mmd')
```

### 3. Embed in Word Document

```python
from src.docx_generator import SolutionArchitectureGenerator
from pathlib import Path

# Assuming SVG file exists
svg_path = 'outputs_final/diagrams/BLZE_diagram.svg'

doc_gen = SolutionArchitectureGenerator(
    app_name='BLZE',
    flows=blze_flows.to_dict('records'),
    zones={},
    rules=[],
    svg_path=svg_path  # Use SVG for infinite zoom!
)

doc_gen.save('outputs_final/BLZE_solution_architecture.docx')
```

---

## 🛠️ Advanced Usage

### Custom Device Type Classification

```python
from src.data_enrichment.master_df_builder import MasterDataFrameBuilder

builder = MasterDataFrameBuilder()

# Override device type classification
def custom_classifier(ip, port, protocol, hostname, app_code):
    # Custom logic
    if 'special-server' in hostname.lower():
        return 'special_type'
    return builder.classify_device_type(ip, port, protocol, hostname, app_code)

# Apply to DataFrame
df['source_device_type'] = df.apply(
    lambda row: custom_classifier(
        row['source_ip'],
        row['port'],
        row['protocol'],
        row['source_hostname'],
        row['source_app_code']
    ),
    axis=1
)
```

### Bulk DNS Lookup from External Source

```python
from src.database import FlowRepository

repo = FlowRepository()

# Bulk cache DNS results
dns_mappings = {
    '10.164.144.23': 'blze-cache-01.company.com',
    '10.164.116.124': 'blze-db-primary.company.com',
    # ... more mappings
}

for ip, hostname in dns_mappings.items():
    repo.cache_dns_lookup(ip, hostname, ttl=86400)  # 24 hour TTL

print(f"✓ Cached {len(dns_mappings)} DNS entries")
```

### Export to Different Formats

```python
import pandas as pd

# Load from database
repo = FlowRepository()
df = repo.get_all_flows()

# Export to Excel
df.to_excel('outputs_final/all_flows.xlsx', index=False)

# Export to JSON
df.to_json('outputs_final/all_flows.json', orient='records', indent=2)

# Export to Parquet (compressed, fast)
df.to_parquet('outputs_final/all_flows.parquet', compression='snappy')

# Export summary statistics
summary = df.groupby(['source_app_code', 'dest_app_code']).agg({
    'flow_count': 'sum',
    'bytes_in': 'sum',
    'bytes_out': 'sum'
}).reset_index()

summary.to_csv('outputs_final/app_to_app_summary.csv', index=False)
```

---

## 🐛 Troubleshooting

### Database Connection Failed

**Problem:**
```
Failed to connect to PostgreSQL: FATAL: password authentication failed
```

**Solution:**
1. Check `.env.development` or `.env.production` file
2. Verify credentials: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
3. Test connection manually:
   ```bash
   psql -h localhost -U postgres -d network_analysis_dev
   ```

### DNS Lookups Timing Out

**Problem:**
DNS lookups take too long or fail

**Solution:**
1. Reduce DNS timeout in config
2. Use cached results from database
3. Skip DNS for known internal IPs
4. Use parallel DNS lookups (future enhancement)

### Out of Memory

**Problem:**
```
MemoryError: Unable to allocate array
```

**Solution:**
1. Process files in batches instead of all at once
2. Use `limit` parameter when querying database
3. Increase system memory
4. Use Parquet format instead of CSV (more efficient)

### Diagram Generation Slow

**Problem:**
Mermaid diagram generation takes too long

**Solution:**
1. Limit number of flows in diagram
2. Aggregate similar flows
3. Use `--apps` parameter to generate specific apps only
4. Pre-compute aggregates in database

---

## 📖 Additional Resources

- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Detailed PostgreSQL setup
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[.env.example](.env.example)** - Configuration template
- **Code Documentation** - Inline comments in source files

---

## 🤝 Support

For issues or questions:
1. Check troubleshooting section above
2. Review implementation summary
3. Check code comments in relevant modules
4. Consult database setup guide for PostgreSQL issues

---

## 🎓 Best Practices

1. **Always use `.env` files** - Never hardcode credentials
2. **Validate app codes** - Check against `applicationList.csv`
3. **Cache DNS results** - Use PostgreSQL cache to avoid duplicate lookups
4. **Use SVG for documents** - Better quality than PNG
5. **Update aggregates regularly** - Keep statistics tables current
6. **Backup database** - Regular PostgreSQL backups
7. **Monitor performance** - Check query execution times
8. **Index wisely** - Add indexes for frequent queries

---

**Happy Analyzing! 🚀**
