# 🚀 Deployment Guide

Complete guide for deploying the Network Segmentation Analyzer v3.0

---

## Prerequisites

### Required
- Python 3.8+
- pip (Python package manager)
- 4GB RAM minimum
- 10GB disk space

### Optional
- PostgreSQL 12+ (recommended for production)
- CUDA-capable GPU (for deep learning acceleration)

---

## Installation

### Step 1: Install Dependencies

```bash
# Basic installation (without deep learning)
pip install -r requirements.txt

# Full installation (with deep learning)
# Edit requirements.txt first: uncomment torch line
pip install -r requirements.txt

# Or use the automated installer
python install.py
```

### Step 2: Configure Database (Optional)

**Option A: PostgreSQL (Recommended for Production)**

```bash
# Install PostgreSQL
# Windows: Download from https://www.postgresql.org/download/windows/
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
CREATE DATABASE network_analysis;
\q

# Update config.yaml with your PostgreSQL credentials
```

**Option B: JSON Files (Automatic Fallback)**

If PostgreSQL is not available, the system automatically uses JSON file-based persistence. No configuration needed!

### Step 3: Initialize System

```bash
# Check dependencies and initialize directories
python start_system.py --skip-checks
```

---

## Quick Start Scenarios

### Scenario 1: Complete System with Web UI

**For immediate visualization and monitoring:**

```bash
# Start web UI with automatic data generation
python start_system.py --web --generate-data 140 --incremental

# Then open browser:
# http://localhost:5000
```

**What this does:**
- ✅ Generates 140 synthetic flow files
- ✅ Starts continuous learning (processes files as they arrive)
- ✅ Launches web UI on port 5000
- ✅ Real-time topology visualization
- ✅ Live statistics dashboard

### Scenario 2: Batch Analysis Only

**For one-time analysis without web UI:**

```bash
# Generate data and analyze
python start_system.py --generate-data 140 --batch

# Results saved to outputs_final/
```

### Scenario 3: Incremental Learning + Web UI

**For continuous monitoring of new applications:**

```bash
# Terminal 1: Start system
python start_system.py --web --incremental

# Terminal 2: Add files gradually (simulates real deployment)
python scripts/generate_synthetic_flows.py --num-apps 10 --start-index 0
# Wait 30 seconds...
python scripts/generate_synthetic_flows.py --num-apps 10 --start-index 10
# System automatically processes new files!
```

### Scenario 4: Production Deployment

**For customer environment with PostgreSQL:**

```bash
# 1. Configure PostgreSQL in config.yaml
nano config.yaml

# 2. Start with all optimizations
python start_system.py \
  --web \
  --incremental \
  --host 0.0.0.0 \
  --port 5000

# 3. Access from any machine on network:
# http://<server-ip>:5000
```

---

## Configuration

### Database Configuration

Edit `config.yaml`:

```yaml
database:
  postgresql:
    enabled: true  # Set to false to force JSON mode
    host: localhost
    port: 5432
    database: network_analysis
    user: postgres
    password: YOUR_PASSWORD_HERE  # CHANGE THIS!
```

### Web UI Configuration

```yaml
web:
  host: 0.0.0.0  # Listen on all interfaces
  port: 5000     # Change if port conflict
  debug: false   # Enable for development
```

### Model Configuration

```yaml
models:
  deep_learning:
    enabled: false  # Set true if PyTorch installed
    device: cpu     # Change to 'cuda' for GPU
```

---

## Usage

### Command-Line Options

```bash
# Start web UI
python start_system.py --web

# Generate synthetic data
python start_system.py --generate-data 140

# Run batch analysis
python start_system.py --batch

# Start incremental learning
python start_system.py --incremental

# Enable deep learning features
python start_system.py --web --incremental --enable-all

# Custom port
python start_system.py --web --port 8080

# Combine multiple options
python start_system.py --web --incremental --generate-data 140 --enable-all
```

### Web UI Features

Once web UI is running, access these pages:

1. **Dashboard** (`/`)
   - Total applications
   - Zone distribution chart
   - Confidence scores
   - Recent activity

2. **Topology View** (`/topology`)
   - Interactive D3.js force-directed graph
   - Zoom, pan, drag nodes
   - Filter by zone
   - Search applications
   - Export visualization

3. **Applications** (`/applications`)
   - List all applications
   - Security zones
   - Dependencies
   - Risk scores

4. **Zones** (`/zones`)
   - Security zone details
   - Applications per zone
   - Compliance requirements

5. **Incremental** (`/incremental`)
   - Real-time learning statistics
   - Files processed
   - Model updates

### API Endpoints

REST API available at `/api/*`:

```bash
# Get all applications
curl http://localhost:5000/api/applications

# Get topology
curl http://localhost:5000/api/topology

# Get statistics
curl http://localhost:5000/api/stats

# Get specific zone
curl http://localhost:5000/api/zones/APP_TIER

# Export topology (JSON)
curl http://localhost:5000/api/export/topology > topology.json
```

---

## Monitoring

### Logs

All logs saved to `logs/` directory:

```bash
# System startup logs
tail -f logs/system_startup_*.log

# Incremental learning logs
tail -f logs/incremental_*.log

# Web application logs
tail -f logs/web_app_*.log
```

### Database Inspection

**PostgreSQL:**
```bash
psql -U postgres -d network_analysis

# Query applications
SELECT app_id, security_zone FROM applications LIMIT 10;

# Query flows
SELECT COUNT(*) FROM flows;
```

**JSON Files:**
```bash
# View applications
cat outputs_final/persistent_data/applications.json | jq '.ACDA'

# View topology
cat outputs_final/incremental_topology.json | jq '.topology'
```

---

## Troubleshooting

### Issue: Port Already in Use

```bash
# Change port
python start_system.py --web --port 8080
```

### Issue: PostgreSQL Connection Failed

```bash
# Check PostgreSQL status
# Windows: Check Services
# Linux: sudo systemctl status postgresql

# Or force JSON mode
# Edit config.yaml: postgresql.enabled = false
```

### Issue: Missing Dependencies

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Or use installer
python install.py
```

### Issue: Incremental Learning Not Detecting Files

```bash
# Check watch directory
ls data/input/App_Code_*.csv

# Reset processed files
rm models/incremental/processed_files.json

# Restart
python start_system.py --incremental --batch
```

### Issue: Deep Learning Features Not Working

```bash
# Check if PyTorch installed
python -c "import torch; print(torch.__version__)"

# If not installed:
pip install torch

# Or edit config.yaml:
models:
  deep_learning:
    enabled: false
```

---

## Performance Tuning

### For Large Datasets (500+ apps)

```yaml
# config.yaml
incremental:
  check_interval: 60  # Check less frequently
  max_files_per_batch: 20  # Process fewer files at once

models:
  deep_learning:
    enabled: false  # Disable for speed
```

### For GPU Acceleration

```yaml
# config.yaml
models:
  deep_learning:
    enabled: true
    device: cuda  # Use GPU
```

```bash
# Start with GPU
python start_system.py --web --incremental --enable-all
```

### For Memory-Constrained Environments

```bash
# Disable deep learning
python start_system.py --web --incremental

# Or edit config.yaml:
models:
  deep_learning:
    enabled: false
  reinforcement_learning:
    enabled: false
```

---

## Production Checklist

- [ ] Change default passwords in `config.yaml`
- [ ] Set `web.debug: false` in config
- [ ] Configure PostgreSQL with production credentials
- [ ] Set up log rotation
- [ ] Configure firewall rules for port 5000
- [ ] Set up SSL/TLS (use nginx reverse proxy)
- [ ] Back up database regularly
- [ ] Monitor disk space for logs
- [ ] Test incremental learning with sample files
- [ ] Verify web UI accessible from client machines

---

## Security Considerations

1. **Data Privacy**: All processing is 100% local - no external APIs
2. **Database**: Change default PostgreSQL password
3. **Web UI**: Use HTTPS in production (nginx reverse proxy)
4. **Network**: Restrict port 5000 to trusted networks
5. **Secrets**: Store passwords in environment variables, not config files

---

## Backup and Recovery

### Database Backup (PostgreSQL)

```bash
# Backup
pg_dump -U postgres network_analysis > backup.sql

# Restore
psql -U postgres -d network_analysis < backup.sql
```

### JSON Backup (Automatic)

```yaml
# config.yaml
database:
  json:
    backup_enabled: true
    backup_dir: ./outputs_final/backups
```

Backups created automatically every 24 hours.

### Model Checkpoints

```bash
# Models saved to:
models/incremental/

# Copy to backup location:
cp -r models/incremental/ backups/models_$(date +%Y%m%d)/
```

---

## Upgrading

```bash
# 1. Backup current system
cp -r outputs_final/ backups/
cp -r models/ backups/

# 2. Pull latest changes
git pull

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Restart system
python start_system.py --web --incremental
```

---

## Support

### Logs Location
- System: `logs/system_startup_*.log`
- Incremental: `logs/incremental_*.log`
- Web App: `logs/web_app_*.log`

### Common Files
- Configuration: `config.yaml`
- Database: `outputs_final/network_analysis.db` (SQLite) or PostgreSQL
- Topology: `outputs_final/incremental_topology.json`
- Processed Files: `models/incremental/processed_files.json`

### Documentation
- Quick Start: `QUICKSTART_INCREMENTAL.md`
- Incremental Learning: `INCREMENTAL_LEARNING_GUIDE.md`
- What's New: `WHATS_NEW_V3.md`
- Web App: `WEB_APP_README.md`

---

**Ready to deploy!** 🚀

For quick start: `python start_system.py --web --generate-data 140 --incremental`
