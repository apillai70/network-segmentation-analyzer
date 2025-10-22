# Network Segmentation Analyzer - Setup and Run Guide

## Quick Answer: How to Start the Application

**Main entry point to process your data:**

```bash
python enterprise_network_analyzer.py
```

That's it! This is the PRIMARY script that initiates everything.

---

## What Does Each Script Do?

### 1. **enterprise_network_analyzer.py** - MAIN ENTRY POINT
**Purpose**: Parse CSV files, analyze flows, generate basic reports

**Usage:**
```bash
python enterprise_network_analyzer.py
```

**What it does:**
- Reads all CSV files from `data/input/`
- Parses network flow records (src_ip, dst_ip, port, protocol, bytes, etc.)
- Analyzes traffic patterns
- Generates network topology diagrams
- Creates tier-to-tier communication matrix

**Output:**
- `outputs/network_analysis/flow_summary.json` - Summary statistics
- `outputs/network_analysis/tier_matrix.json` - Tier communication matrix
- `outputs/diagrams/*.html` - Interactive network diagrams

**Requirements:**
- CSV files in `data/input/`
- NO database required
- NO configuration needed

---

### 2. **run_graph_analysis.py** - Graph Analysis
**Purpose**: Find shortest paths, detect topology gaps, identify chokepoints

**Usage:**
```bash
python run_graph_analysis.py
```

**What it does:**
- Runs enterprise_network_analyzer internally (you don't need to run it separately)
- Builds in-memory NetworkX graph
- Finds shortest paths between nodes
- Detects expected connections that don't exist (gap analysis)
- Calculates centrality metrics (identifies critical nodes)

**Output:**
- `outputs/graph_analysis/network_graph.json` - Complete graph structure
- `outputs/visualizations/shortest_path.html` - Interactive path visualization
- `outputs/visualizations/all_paths.html` - All paths between two nodes
- `outputs/visualizations/gap_analysis.html` - Missing connections report

**Requirements:**
- CSV files in `data/input/`
- NetworkX installed (`pip install networkx`)
- NO database required

---

### 3. **run_threat_analysis.py** - Threat Surface Analysis
**Purpose**: Discover attack paths, calculate threat scores, generate mitigation recommendations

**Usage:**
```bash
python run_threat_analysis.py
```

**What it does:**
- Runs enterprise_network_analyzer internally
- Discovers all attack paths from external nodes to critical assets
- Calculates exposure scores for each node
- Identifies critical chokepoints (nodes whose removal blocks many attacks)
- Generates prioritized mitigation recommendations

**Output:**
- `outputs/threat_analysis/threat_surface_analysis.json` - Complete threat analysis
- Console report with:
  - Top 5 critical attack paths
  - High-exposure nodes
  - Critical chokepoints
  - Mitigation recommendations

**Requirements:**
- CSV files in `data/input/`
- NetworkX installed (`pip install networkx`)
- NO database required

---

## Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Core dependencies:**
- networkx - Graph analysis
- matplotlib - Visualization
- sqlalchemy - Database ORM (optional, only if using PostgreSQL)
- reportlab - PDF generation
- svgwrite - SVG diagram generation

### Step 2: Place Your CSV Files

```bash
# Your CSV files should be in data/input/
# Example: App_Code_WEBAPP.csv, App_Code_DATABASE.csv, etc.

# Copy your files:
cp /path/to/your/flows/*.csv data/input/
```

**Expected CSV format:**
```csv
src_ip,dst_ip,port,transport,bytes,timestamp,src_hostname,dst_hostname,app_name
10.164.105.23,10.100.246.49,443,TCP,1024,2024-01-15 10:30:00,web01,app02,ACME-APP
```

**Required columns:**
- `src_ip` - Source IP address
- `dst_ip` - Destination IP address
- `port` - Destination port
- `transport` - Protocol (TCP/UDP)

**Optional columns:**
- `bytes` - Bytes transferred
- `timestamp` - Flow timestamp
- `src_hostname` - Source hostname
- `dst_hostname` - Destination hostname
- `app_name` - Application name

### Step 3: Run Analysis

```bash
# Option 1: Basic analysis only
python enterprise_network_analyzer.py

# Option 2: Full analysis (basic + graph + threat)
python enterprise_network_analyzer.py
python run_graph_analysis.py
python run_threat_analysis.py

# Option 3: Just threat analysis (includes everything)
python run_threat_analysis.py
```

---

## Database Setup (OPTIONAL - NOT REQUIRED)

**By default, the application works ENTIRELY IN-MEMORY with NO database.**

If you want to use PostgreSQL for persistent storage:

### Option A: Using setup script

```bash
python setup_dev_database.py
```

This will:
1. Create PostgreSQL database `network_analysis`
2. Create user `netadmin`
3. Create schema `netflow`
4. Set up tables

### Option B: Manual setup

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE network_analysis;

-- Create user
CREATE USER netadmin WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE network_analysis TO netadmin;

-- Connect to new database
\c network_analysis

-- Create schema (NOT 'public')
CREATE SCHEMA netflow;
GRANT ALL ON SCHEMA netflow TO netadmin;
```

### Configure database connection

Create `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=network_analysis
DB_USER=netadmin
DB_PASSWORD=your_secure_password
DB_SCHEMA=netflow
```

---

## Output Files

All analysis results are saved to `outputs/` directory:

```
outputs/
├── network_analysis/       # Basic flow analysis
│   ├── flow_summary.json
│   └── tier_matrix.json
├── diagrams/               # Network topology diagrams
│   ├── network_topology_APPNAME.html
│   └── network_topology_APPNAME.mmd
├── graph_analysis/         # Path and gap analysis
│   └── network_graph.json
├── visualizations/         # Interactive HTML charts
│   ├── shortest_path.html
│   ├── all_paths.html
│   └── gap_analysis.html
└── threat_analysis/        # Security assessment
    └── threat_surface_analysis.json
```

---

## Configuration (Optional)

### Customize tier classification

Edit tier ranges to match your network:

Create `config/tier_classification.json`:

```json
{
  "tiers": {
    "WEB": ["10.164.105.0/24"],
    "APP": ["10.100.246.0/24", "10.165.116.0/24"],
    "DATABASE": ["10.164.116.0/24"],
    "CACHE": ["10.164.144.0/24"],
    "QUEUE": ["10.164.145.0/24"],
    "MANAGEMENT": ["10.164.150.0/24"]
  }
}
```

### Customize threat scores

Edit risk levels for different tiers:

In `src/threat_surface_analyzer.py`, modify:

```python
TIER_RISK_SCORES = {
    'WEB': 8,              # High risk (internet-facing)
    'LOADBALANCER': 9,     # Very high (entry point)
    'DATABASE': 10,        # Critical (data at rest)
    'APP': 6,              # Medium risk
    'CACHE': 5,
    'QUEUE': 7,
    'MANAGEMENT': 10       # Critical
}
```

---

## Complete Workflow Example

```bash
# 1. Install dependencies
pip install networkx matplotlib sqlalchemy reportlab svgwrite

# 2. Check your CSV files are present
ls -lh data/input/*.csv

# 3. Run threat analysis (this includes all other analysis)
python run_threat_analysis.py

# 4. View results
# - Console output shows critical attack paths
# - JSON file: outputs/threat_analysis/threat_surface_analysis.json

# 5. Optional: View graph visualizations
start outputs/visualizations/shortest_path.html        # Windows
open outputs/visualizations/shortest_path.html         # macOS
xdg-open outputs/visualizations/shortest_path.html     # Linux
```

---

## Troubleshooting

### Error: "No CSV files found"

**Solution:**
```bash
# Check files are in correct location
ls data/input/*.csv

# If empty, copy your files
cp /path/to/flows/*.csv data/input/
```

### Error: "No module named 'networkx'"

**Solution:**
```bash
pip install networkx
```

### Error: "UnicodeEncodeError" (Windows)

**Cause:** Console encoding issue

**Solution:** Already fixed in code. If it still occurs:
```bash
chcp 65001
python run_threat_analysis.py
```

### Error: "Permission denied"

**Solution:**
```bash
# Windows
icacls data\input /grant Users:F

# Linux/macOS
chmod -R 755 data/input
```

---

## Performance Notes

**Typical performance (Intel i5, 8GB RAM):**

| Dataset Size | Parse Time | Graph Build | Threat Analysis |
|-------------|-----------|-------------|-----------------|
| <10K flows  | <1 second | <1 second   | 10-20 seconds   |
| 10-50K flows| 2-5 seconds | 2-3 seconds | 30-60 seconds  |
| 50-100K flows| 10-20 seconds | 5-10 seconds | 2-5 minutes  |

**Memory usage:**
- Small dataset (<10K): ~50MB
- Medium dataset (10-50K): ~200MB
- Large dataset (50-100K): ~500MB

---

## Summary

**To process your data:**
1. Put CSV files in `data/input/`
2. Run: `python enterprise_network_analyzer.py`
3. View results in `outputs/`

**For threat analysis:**
1. Run: `python run_threat_analysis.py`
2. Review attack paths and recommendations

**No database, no configuration, no setup required - just run the script!**

---

## Quick Reference

```bash
# Main entry point (processes all data)
python enterprise_network_analyzer.py

# Graph analysis (shortest path, gaps)
python run_graph_analysis.py

# Threat analysis (attack paths, security)
python run_threat_analysis.py

# View output
ls outputs/network_analysis/
ls outputs/visualizations/
ls outputs/threat_analysis/
```
