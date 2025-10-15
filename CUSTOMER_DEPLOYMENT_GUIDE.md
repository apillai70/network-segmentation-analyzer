# Customer Deployment Guide
## Network Segmentation Analyzer v3.0

**Purpose:** Complete guide for setting up and deploying the Network Segmentation Analyzer at customer sites with real network flow data.

**Last Updated:** October 2025
**Author:** Enterprise Architecture Team

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Project Structure](#project-structure)
5. [Configuration](#configuration)
6. [File Format Requirements](#file-format-requirements)
7. [Incremental Processing Workflow](#incremental-processing-workflow)
8. [Running the Analysis](#running-the-analysis)
9. [Generating Reports](#generating-reports)
10. [Monitoring Progress](#monitoring-progress)
11. [Troubleshooting](#troubleshooting)
12. [Production Checklist](#production-checklist)

---

## Quick Start (5 Minutes)

```bash
# 1. Extract project files
cd /path/to/deployment

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure for JSON mode (no database)
# Edit config.yaml: set postgresql.enabled = false

# 4. Verify installation
python -c "import pandas, numpy, networkx, sklearn; print('✓ Ready')"

# 5. Add first flow file
cp /path/to/App_Code_MYAPP.csv data/input/

# 6. Run incremental processing (NOT start_system.py!)
python run_incremental_learning.py --batch

# 7. Generate diagrams
python generate_application_reports.py

# 8. Generate documents
python generate_solution_design_docs.py
```

**IMPORTANT:** Do NOT use `start_system.py` for customer deployments - it's designed for demos with synthetic data and will delete your real data!

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk Space | 10 GB | 50+ GB |
| Network | - | Internet (for package install only) |

### Software Requirements

| Software | Version | Required |
|----------|---------|----------|
| Python | 3.8+ | ✓ Yes |
| pip | Latest | ✓ Yes |
| Git | Any | ⚠ Optional |
| PostgreSQL | 12+ | ⚠ Optional (can use JSON) |

### Python Packages

**Required (Core):**
- pandas >= 2.1.4
- numpy >= 1.26.2
- networkx >= 3.2.1
- scikit-learn >= 1.3.2
- python-docx >= 1.1.0
- pyyaml >= 6.0.1
- flask >= 3.0.0

**Optional (Advanced Features):**
- torch >= 2.1.2 (Deep learning)
- plotly >= 5.18.0 (Interactive visualizations)
- psycopg2-binary >= 2.9.9 (PostgreSQL support)

---

## Installation Steps

### Step 1: Extract Project Files

```bash
# On Linux/Mac
cd /opt/network-analyzer
unzip network-segmentation-analyzer.zip

# On Windows
cd C:\Projects
# Extract ZIP using Windows Explorer or:
# powershell -command "Expand-Archive network-segmentation-analyzer.zip ."
```

### Step 2: Install Python Dependencies

```bash
# Navigate to project directory
cd network-segmentation-analyzer

# Install required packages
pip install -r requirements.txt

# Verify installation
python scripts/verify_installation.py
```

**If you see errors:**
```bash
# On Linux, you may need development headers
sudo apt-get install python3-dev build-essential

# On Windows, ensure Visual C++ is installed
# Download from: https://visualstudio.microsoft.com/downloads/
```

### Step 3: Create Directory Structure

```bash
# Create all necessary directories
mkdir -p data/input
mkdir -p outputs_final
mkdir -p logs
mkdir -p models/incremental
mkdir -p models/ensemble

# Verify structure
ls -la data/input
```

### Step 4: Configure for JSON Mode

Edit `config.yaml`:

```yaml
database:
  postgresql:
    enabled: false  # <-- Set to false for JSON-only mode

  json:
    data_dir: ./outputs_final/persistent_data
    backup_enabled: true
    backup_dir: ./outputs_final/backups
```

**No other configuration changes are required!**

---

## Project Structure

```
network-segmentation-analyzer/
├── data/
│   └── input/                          # Place flow files here
│       ├── applicationList.csv         # Application catalog (required)
│       ├── App_Code_APP1.csv          # Flow data files
│       ├── App_Code_APP2.csv          # Add files one by one
│       └── ...
├── outputs_final/
│   ├── persistent_data/                # JSON storage (auto-created)
│   │   ├── topology/                   # Application topology
│   │   └── flows/                      # Flow records
│   ├── diagrams/                       # Generated diagrams
│   │   ├── *_application_diagram.png   # PNG diagrams
│   │   ├── *_application_diagram.mmd   # Mermaid source
│   │   └── *_application_diagram.html  # Interactive HTML
│   ├── word_reports/                   # Word documents
│   │   ├── architecture/               # Solution Design docs
│   │   │   └── Solution_Design-*.docx
│   │   └── netseg/                     # NetSeg docs
│   │       └── *_architecture.docx
│   ├── incremental_topology.json       # Master topology file
│   └── backups/                        # JSON backups
├── logs/                               # All log files
│   ├── incremental_*.log
│   ├── system_startup_*.log
│   └── ...
├── models/                             # ML models (auto-created)
│   ├── incremental/
│   └── ensemble/
├── config.yaml                         # Configuration file
├── requirements.txt                    # Python dependencies
├── run_incremental_learning.py         # Main processing script
├── generate_solution_design_docs.py    # Doc generator
└── start_system.py                     # Web UI launcher
```

---

## Configuration

### JSON-Only Mode (Recommended for Initial Deployment)

**File:** `config.yaml`

```yaml
# Database Configuration
database:
  postgresql:
    enabled: false  # ✓ Use JSON instead of PostgreSQL

  json:
    data_dir: ./outputs_final/persistent_data
    backup_enabled: true
    backup_dir: ./outputs_final/backups

# Incremental Learning
incremental:
  watch_dir: ./data/input
  check_interval: 30  # seconds
  checkpoint_interval: 10
  max_files_per_batch: 50

# Model Configuration
models:
  deep_learning:
    enabled: false  # Set true if PyTorch installed
    device: cpu

  graph_algorithms:
    enabled: true  # Always keep enabled

  reinforcement_learning:
    enabled: false  # Disable for production

# Logging
logging:
  level: INFO  # INFO or DEBUG
  dir: ./logs
  max_size_mb: 100
  backup_count: 10
```

### Optional: Enable PostgreSQL Later

```yaml
database:
  postgresql:
    enabled: true
    host: your-db-server.com
    port: 5432
    database: network_analysis
    user: dbuser
    password: secure_password
```

---

## File Format Requirements

### 1. Application List File

**File:** `data/input/applicationList.csv`

**Format:**
```csv
app_id,app_name
XECHK,Financial Transaction Manager for Check
ACDA,Account Data Aggregator
DPAPI,Digital Process API
```

**Requirements:**
- Must exist before processing flow files
- Two columns: `app_id` and `app_name`
- UTF-8 or Latin-1 encoding
- No blank lines

### 2. Flow Data Files

**File Naming:** `App_Code_{APP_ID}.csv`

**Examples:**
- `App_Code_XECHK.csv`
- `App_Code_ACDA.csv`
- `App_Code_DPAPI.csv`

**Format:**
```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
XECHK,10.164.145.23,,10.164.105.45,,1521,ORACLE,1245678,987654
XECHK,10.164.145.23,,10.100.246.12,,443,HTTPS,45678,123456
XECHK,2001:db8:2bda::1,,2001:db8:548b::2,,5432,POSTGRESQL,2345678,1234567
```

**Column Specifications:**

| Column | Description | Required | Example |
|--------|-------------|----------|---------|
| `App` | Application ID | ✓ Yes | XECHK |
| `Source IP` | Source IP (IPv4/IPv6) | ✓ Yes | 10.164.145.23 |
| `Source Hostname` | Source hostname | Optional | web-srv-01 |
| `Dest IP` | Destination IP | ✓ Yes | 10.164.105.45 |
| `Dest Hostname` | Destination hostname | Optional | db-srv-02 |
| `Port` | Destination port | Optional | 1521 |
| `Protocol` | Protocol name | ✓ Yes | HTTPS, TCP, ORACLE |
| `Bytes In` | Bytes received | ✓ Yes | 1245678 |
| `Bytes Out` | Bytes sent | ✓ Yes | 987654 |

**Important Notes:**
- App ID in filename must match `App` column
- IPv4 and IPv6 are both supported
- Hostnames are optional but helpful
- Port can be empty for some flows
- Bytes can be 0 for connection setup flows
- One file per application

**Example Real Flow:**
```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
ACDA,10.164.145.100,acda-app-01,10.164.105.50,acda-db-01,3306,MYSQL,5234567,2345678
ACDA,10.164.145.100,acda-app-01,10.164.116.25,redis-cache-01,6379,REDIS,123456,234567
ACDA,10.164.145.100,acda-app-01,10.165.116.30,kafka-01,9092,KAFKA,456789,567890
ACDA,10.164.144.80,acda-web-01,10.164.145.100,acda-app-01,8443,HTTPS,987654,1234567
```

---

## Incremental Processing Workflow

### Option 1: Process Files One by One (Recommended for Initial Setup)

**Workflow:**
1. Add one flow file to `data/input/`
2. Run batch processing
3. Verify results
4. Repeat

```bash
# Step 1: Add first file
cp /path/to/customer/App_Code_APP1.csv data/input/

# Step 2: Process it
python run_incremental_learning.py --batch

# Step 3: Check results
cat outputs_final/incremental_topology.json | grep APP1

# Step 4: Add next file
cp /path/to/customer/App_Code_APP2.csv data/input/

# Step 5: Process again
python run_incremental_learning.py --batch
```

### Option 2: Process Multiple Files in Batch

```bash
# Copy multiple files
cp /path/to/customer/App_Code_*.csv data/input/

# Process all new files at once
python run_incremental_learning.py --batch --max-files 10

# Process all new files
python run_incremental_learning.py --batch
```

### Option 3: Continuous Monitoring (Production)

```bash
# Start continuous monitoring
python run_incremental_learning.py --continuous

# The system will:
# - Check data/input/ every 30 seconds
# - Automatically process new files
# - Update topology incrementally
# - Save progress continuously
```

**Press Ctrl+C to stop**

### File Processing Tracking

The system automatically tracks processed files:

```bash
# Check which files have been processed
python scripts/manage_file_tracking.py --list

# Reprocess a specific file
python scripts/manage_file_tracking.py --forget App_Code_XECHK.csv
cp App_Code_XECHK.csv data/input/
python run_incremental_learning.py --batch

# Clear all tracking (reprocess everything)
python scripts/manage_file_tracking.py --reset
```

---

## Running the Analysis

### ⚠️ IMPORTANT: Do NOT Use start_system.py

**`start_system.py` is NOT for customer deployments!**

❌ **DO NOT RUN:**
```bash
python start_system.py  # This will DELETE your data!
```

**Why?**
- Designed for demos with synthetic/fake data
- Cleans up and deletes existing data by default
- Generates synthetic flows (not real customer data)
- Includes unnecessary features for production

✅ **INSTEAD USE:**
```bash
python run_incremental_learning.py --batch
```

---

### Basic Commands

#### 1. Process New Flow Files

```bash
# Process all new files once
python run_incremental_learning.py --batch

# Process up to 10 files
python run_incremental_learning.py --batch --max-files 10

# Start continuous processing
python run_incremental_learning.py --continuous
```

#### 2. Generate Diagrams (REQUIRED before documents)

```bash
# Generate all diagrams (PNG, Mermaid, HTML)
python generate_application_reports.py

# Diagrams saved to: outputs_final/diagrams/
```

**Note:** You MUST generate diagrams before generating Word documents, otherwise documents will show "diagram not found" placeholders.

#### 3. Generate Word Documents

```bash
# Generate comprehensive architecture documents
python generate_solution_design_docs.py
# Output: outputs_final/word_reports/architecture/

# Generate simple netseg documents
python generate_application_word_docs.py
# Output: outputs_final/word_reports/netseg/
```

**Prerequisites:** Diagrams must exist (Step 2 above). Documents embed the PNG diagrams and Mermaid source code.

#### 4. Launch Web UI (Optional)

```bash
# Start web interface (only if you want the UI)
python start_system.py --web --skip-cleanup

# IMPORTANT: Use --skip-cleanup to prevent data deletion!

# Open browser: http://localhost:5000
```

**Alternative (safer):**
```bash
# Use Flask directly
export FLASK_APP=web_app.py
flask run --host=0.0.0.0 --port=5000
```

### Advanced Commands

#### Enable Deep Learning (Optional)

```bash
# Requires PyTorch installation
pip install torch==2.1.2+cpu

# Edit config.yaml: models.deep_learning.enabled = true

# Run with deep learning
python run_incremental_learning.py --batch --enable-all
```

#### Custom Configuration

```bash
# Use custom directories
python run_incremental_learning.py \
  --batch \
  --watch-dir /custom/path/input \
  --output-dir /custom/path/output

# Verbose logging
python run_incremental_learning.py --batch --verbose
```

---

## Generating Reports

### 1. Architecture Documents (Comprehensive)

```bash
python generate_solution_design_docs.py
```

**Output:** `outputs_final/word_reports/architecture/Solution_Design-{AppID}.docx`

**Contains:**
- Cover page with branding
- Executive summary
- Application overview
- Architecture diagram (embedded PNG)
- Network segmentation details
- Data flows and dependencies
- Security considerations
- Compliance and risk assessment
- Recommendations
- Appendix with Mermaid code

### 2. Application Architecture Documents (Simple)

```bash
python generate_application_word_docs.py
```

**Output:** `outputs_final/word_reports/architecture/{AppID}_architecture.docx`

**Contains:**
- Title page
- Application diagram
- Architecture overview
- Security considerations

### 3. Diagrams

```bash
python generate_application_reports.py
```

**Generates for each application:**
- `{AppID}_application_diagram.png` - High-resolution diagram
- `{AppID}_application_diagram.mmd` - Mermaid source code
- `{AppID}_application_diagram.html` - Interactive HTML

### 4. Export Lucidchart Format

```bash
python generate_application_reports.py --lucidchart
```

**Generates:**
- `lucidchart_applications_*.csv` - Applications for import
- `lucidchart_zones_*.csv` - Zone information
- Ready for Lucidchart import

---

## Monitoring Progress

### Check Logs

```bash
# Tail incremental learning log
tail -f logs/incremental_*.log

# Check system startup log
tail -f logs/system_startup_*.log

# View all logs
ls -lh logs/
```

### Check Topology Status

```bash
# View topology summary
python -c "
import json
with open('outputs_final/incremental_topology.json', 'r') as f:
    data = json.load(f)
    print(f'Total Apps: {data[\"total_apps\"]}')
    print(f'Apps: {data[\"apps_observed\"]}')
"

# Check specific application
python -c "
import json
with open('outputs_final/incremental_topology.json', 'r') as f:
    data = json.load(f)
    app = data['topology'].get('XECHK', {})
    print(json.dumps(app, indent=2))
"
```

### Check Processed Files

```bash
# List processed files
python scripts/manage_file_tracking.py --list

# Check statistics
python scripts/manage_file_tracking.py --stats
```

### Monitor JSON Storage

```bash
# Check persistent data
ls -lh outputs_final/persistent_data/topology/
ls -lh outputs_final/persistent_data/flows/

# Check backups
ls -lh outputs_final/backups/
```

---

## Troubleshooting

### Issue 0: PNG Generation Fails - mmdc Not Found (FIXED)

**Problem:** Batch processing completes but no PNG files are generated. You see:
```
⚠ Cannot generate architecture docs - No PNG files found
Solutions:
  1. Install mmdc: npm install -g @mermaid-js/mermaid-cli
```

**Root Cause:**
Scripts were looking for `mmdc` at hardcoded paths that only worked on development machine. On customer machines with **nodeenv**, mmdc couldn't be found even though it was installed.

**Fix Applied (Version 1.1):**
The scripts now automatically detect mmdc in **4 locations**:
1. **PATH** (if nodeenv activated or globally installed)
2. **`nodeenv/Scripts/mmdc`** (project nodeenv - **YOUR SETUP**)
3. **Windows npm global** (`%USERPROFILE%\AppData\Roaming\npm\mmdc.cmd`)
4. **Direct command** (last resort)

**Files Updated:**
- `run_batch_processing.py` - Smart mmdc detection (lines 263-321)
- `generate_missing_pngs.py` - Auto-finds mmdc + processes all diagrams

**Verification:**
```bash
# Check if mmdc is accessible
nodeenv\Scripts\mmdc --version
# Should show: 11.12.0

# Test the detection
python -c "import shutil; print(shutil.which('mmdc') or 'Will check nodeenv/')"
```

**Solution - Run Batch Processing:**
```bash
# On customer machine - mmdc detection now automatic
python run_batch_processing.py --batch-size 10 --clear-first
```

**Expected Output:**
```
================================================================================
STEP 2B: VERIFYING PNG FILES
================================================================================
Found 139 Mermaid diagrams
Missing 139 PNG files
Regenerating missing PNGs...
✓ Found mmdc in nodeenv: C:\Users\RC34361\network-segmentation-analyzer\nodeenv\Scripts\mmdc
  ✓ ACDA.png
  ✓ ALE.png
  ...
PNG generation: 139/139 successful
```

**Alternative - Generate PNGs Only:**
```bash
# If you already have .mmd files, just generate PNGs
python generate_missing_pngs.py
```

**This Now Works:**
- ✅ Automatic mmdc detection in nodeenv
- ✅ No manual path configuration needed
- ✅ Works on customer and development machines
- ✅ Clear error messages if mmdc truly missing

### Issue 1: Missing Dependencies

**Error:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:**
```bash
pip install -r requirements.txt

# If still failing, upgrade pip
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue 2: Encoding Errors

**Error:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solution:**
The system handles this automatically, but if you see errors:

```bash
# Convert file to UTF-8
iconv -f WINDOWS-1252 -t UTF-8 input.csv > output.csv

# Or use Python
python -c "
import pandas as pd
df = pd.read_csv('input.csv', encoding='latin-1')
df.to_csv('output.csv', index=False, encoding='utf-8')
"
```

### Issue 3: No Applications Appearing in Topology

**Problem:** Topology file is empty or missing applications

**Solution:**
```bash
# Check if files are being processed
python scripts/manage_file_tracking.py --list

# Reprocess specific application
python scripts/manage_file_tracking.py --forget App_Code_MYAPP.csv
python run_incremental_learning.py --batch

# Reprocess all applications
python reprocess_all_apps.py
```

### Issue 4: Diagrams Not Generating

**Problem:** No PNG files in outputs_final/diagrams/

**Solution:**
```bash
# Ensure topology exists
cat outputs_final/incremental_topology.json

# Regenerate diagrams
python generate_application_reports.py

# Check for errors
tail -f logs/diagram_generation_*.log
```

### Issue 5: Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```bash
# Process fewer files at once
python run_incremental_learning.py --batch --max-files 5

# Disable deep learning
# Edit config.yaml: models.deep_learning.enabled = false

# Increase system swap space (Linux)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue 6: Slow Performance

**Problem:** Processing taking too long

**Solution:**
```bash
# Disable optional features in config.yaml:
models:
  deep_learning:
    enabled: false
  reinforcement_learning:
    enabled: false

# Process in smaller batches
python run_incremental_learning.py --batch --max-files 10

# Check system resources
top
df -h
```

### Issue 7: Port Already in Use (Web UI)

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Use different port
python start_system.py --web --port 5001

# Or kill existing process
lsof -ti:5000 | xargs kill -9
```

---

## Production Checklist

### Pre-Deployment

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `config.yaml` configured for JSON mode
- [ ] `data/input/applicationList.csv` exists
- [ ] Directory structure created
- [ ] Test file processed successfully

### Initial Setup

- [ ] First flow file added to `data/input/`
- [ ] Initial processing completed
- [ ] `outputs_final/incremental_topology.json` created
- [ ] Logs reviewed for errors
- [ ] Test diagram generated

### Production Operations

- [ ] Backup strategy defined for `outputs_final/`
- [ ] Log rotation configured
- [ ] Monitoring alerts set up
- [ ] Documentation provided to operations team
- [ ] Escalation procedures defined

### Security

- [ ] File permissions reviewed
- [ ] Network flow data classified appropriately
- [ ] Access controls implemented
- [ ] Audit logging enabled
- [ ] Sensitive data handling procedures followed

### Documentation

- [ ] Application catalog (`applicationList.csv`) updated
- [ ] File naming conventions documented
- [ ] Operations runbook created
- [ ] Contact information for support provided

---

## Common Workflows

### Workflow 1: Initial Deployment with First 10 Apps

```bash
# Day 1: Setup
cd /opt/network-analyzer
pip install -r requirements.txt
vi config.yaml  # Set postgresql.enabled = false

# Day 1: First batch (10 apps)
cp customer_data/App_Code_APP_{1..10}.csv data/input/

# Day 1: Process files
python run_incremental_learning.py --batch

# Day 1: Generate diagrams (REQUIRED FIRST!)
python generate_application_reports.py

# Day 1: Generate documents (embeds diagrams)
python generate_solution_design_docs.py
python generate_application_word_docs.py

# Day 1: Review
ls -lh outputs_final/word_reports/architecture/
tail -100 logs/incremental_*.log
```

### Workflow 2: Weekly Incremental Updates

```bash
# Week 2: Add 10 more apps
cp customer_data/App_Code_APP_{11..20}.csv data/input/
python run_incremental_learning.py --batch

# Week 2: Generate new docs
python generate_solution_design_docs.py

# Week 2: Backup
tar -czf backup_week2_$(date +%Y%m%d).tar.gz outputs_final/
```

### Workflow 3: Continuous Processing (Production)

```bash
# Terminal 1: Start continuous processing
python run_incremental_learning.py --continuous

# Terminal 2: Monitor logs
tail -f logs/incremental_*.log

# Terminal 3: Copy files as they're ready
while true; do
  cp /incoming/*.csv data/input/ 2>/dev/null
  sleep 300  # Check every 5 minutes
done
```

### Workflow 4: Report Generation Cycle

```bash
# Monthly report generation
cd /opt/network-analyzer

# 1. Process any new files first (if applicable)
python run_incremental_learning.py --batch

# 2. Generate/update all diagrams (REQUIRED FIRST!)
python generate_application_reports.py

# 3. Generate architecture docs (embeds diagrams from step 2)
python generate_solution_design_docs.py

# 4. Generate netseg docs (embeds diagrams from step 2)
python generate_application_word_docs.py

# 5. Package for distribution
timestamp=$(date +%Y%m%d)
mkdir -p reports_${timestamp}
cp -r outputs_final/word_reports/* reports_${timestamp}/
cp -r outputs_final/diagrams/*.png reports_${timestamp}/diagrams/
tar -czf network_analysis_reports_${timestamp}.tar.gz reports_${timestamp}/
```

**Order Matters:**
1. Process data (if new files added)
2. Generate diagrams (creates PNG/MMD files)
3. Generate documents (embeds diagrams from step 2)

---

## Contact and Support

### Documentation
- **This Guide:** `CUSTOMER_DEPLOYMENT_GUIDE.md`
- **Incremental Learning:** `INCREMENTAL_LEARNING_GUIDE.md`
- **Word Documents:** `README_WORD_DOCS.md`
- **Architecture Docs:** `SOLUTION_DESIGN_DOCS_GUIDE.md`

### Getting Help

**Check logs first:**
```bash
tail -100 logs/incremental_*.log
tail -100 logs/system_startup_*.log
```

**Common log locations:**
- `logs/incremental_*.log` - Processing logs
- `logs/system_startup_*.log` - System startup logs
- `logs/diagram_generation_*.log` - Diagram generation
- `solution_docs_generation.log` - Document generation

---

## Appendix

### A. Example Application List

**File:** `data/input/applicationList.csv`

```csv
app_id,app_name
XECHK,Financial Transaction Manager for Check
ACDA,Account Data Aggregator
DPAPI,Digital Process API
XEFTM,Financial Transaction Manager - Base
DM_CMRDB,Commercial Reporting Database
DNCCW,Call Center Wrap
RCSS,Regions Connects Sales and Service
```

### B. Example Flow File

**File:** `data/input/App_Code_XECHK.csv`

```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
XECHK,10.164.145.23,xechk-app-01,10.164.105.45,xechk-db-01,1521,ORACLE,1245678,987654
XECHK,10.164.145.23,xechk-app-01,10.100.246.12,external-gw,443,HTTPS,45678,123456
XECHK,10.164.145.24,xechk-app-02,10.164.105.45,xechk-db-01,1521,ORACLE,2345678,1234567
XECHK,10.164.145.23,xechk-app-01,10.164.116.25,redis-cache,6379,REDIS,123456,234567
XECHK,10.164.144.80,xechk-web-01,10.164.145.23,xechk-app-01,8443,HTTPS,987654,1234567
XECHK,2001:db8:2bda::1,xechk-app-03,2001:db8:548b::2,xechk-db-02,5432,POSTGRESQL,3456789,2345678
```

### C. Quick Reference Commands

```bash
# PROCESSING (Real customer data)
python run_incremental_learning.py --batch                # Process once
python run_incremental_learning.py --continuous           # Monitor continuously
python run_incremental_learning.py --batch --max-files 10 # Process 10 files

# ⚠️ DO NOT USE for customer data:
# python start_system.py  # This deletes data and generates synthetic flows!

# REPORTS (Must run in this order!)
# Step 1: Generate diagrams FIRST
python generate_application_reports.py                    # Creates PNG/MMD/HTML

# Step 2: Generate documents SECOND (embeds diagrams from step 1)
python generate_solution_design_docs.py                   # Architecture docs
python generate_application_word_docs.py                  # NetSeg docs

# MONITORING
tail -f logs/incremental_*.log                            # Watch processing
python scripts/manage_file_tracking.py --list             # List processed files
cat outputs_final/incremental_topology.json | jq .        # View topology

# TROUBLESHOOTING
python scripts/manage_file_tracking.py --reset            # Clear tracking
python reprocess_all_apps.py                              # Reprocess all
python scripts/verify_installation.py                     # Check setup

# WEB UI (Optional - use carefully!)
python start_system.py --web --skip-cleanup              # With --skip-cleanup flag!
# Or use Flask directly:
export FLASK_APP=web_app.py && flask run
```

### D. Directory Size Estimates

| Directory | Initial | 100 Apps | 1000 Apps |
|-----------|---------|----------|-----------|
| `data/input/` | 1 MB | 100 MB | 1 GB |
| `outputs_final/persistent_data/` | <1 MB | 50 MB | 500 MB |
| `outputs_final/diagrams/` | <1 MB | 30 MB | 300 MB |
| `outputs_final/word_reports/` | <1 MB | 200 MB | 2 GB |
| `logs/` | <1 MB | 10 MB | 100 MB |
| `models/` | <1 MB | 20 MB | 100 MB |

**Total estimated:** 500 MB - 4 GB for 1000 applications

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-12 | Initial deployment guide |

---

**End of Customer Deployment Guide**
