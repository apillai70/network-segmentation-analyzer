# Network Segmentation Analyzer - Installation Guide

**Version**: 2.0 - FastAPI Edition
**Python Compatibility**: 3.11, 3.13, 3.14+
**Last Updated**: October 2025

---

## Quick Install (60 seconds)

```bash
# 1. Clone or extract the repository
cd network-segmentation-analyzer

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Start the web dashboard
./start_web_app.sh    # GitBash/Linux/Mac
# OR
start_web_app.bat     # Windows CMD

# 4. Open browser
# http://localhost:8000
```

---

## What's Included in requirements.txt

Our **consolidated** `requirements.txt` includes everything needed:

### Core Dependencies (Always Installed)
- **Data Processing**: pandas, numpy, networkx
- **Machine Learning**: scikit-learn
- **Visualization**: matplotlib, seaborn, plotly
- **Document Generation**: python-docx, Pillow, reportlab
- **Web Application**: FastAPI, uvicorn, pydantic V2 (Python 3.13+ compatible!)
- **HTTP Client**: requests, certifi, urllib3
- **Utilities**: tqdm, pyyaml, lxml, python-dotenv

### Optional Components (Commented Out by Default)
- **Deep Learning**: torch (for advanced AI features)
- **Database**: PostgreSQL adapter
- **Development Tools**: pytest, black, mypy, ipython, jupyterlab
- **Diagram Generation**: nodeenv or playwright

---

## Installation for Your Client (Python 3.13)

Your client has **Python 3.13** - Perfect! Here's the exact process:

### Step 1: Install Core Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages including:
- FastAPI 0.115+ (Python 3.13/3.14 compatible)
- Pydantic V2 (full Python 3.13 support)
- All data processing and visualization libraries

### Step 2: Test the Web Dashboard

```bash
# Option 1: GitBash (RECOMMENDED)
./start_web_app.sh

# Option 2: Windows CMD
start_web_app.bat

# Option 3: Direct Python
python fastapi_app.py
```

Visit: **http://localhost:8000**

### Step 3: Verify Installation

The web dashboard will show:
- 139 applications loaded
- Security zones distribution chart
- DNS validation statistics
- Interactive API docs at /docs

---

## Optional Features

### Option A: Deep Learning Features (Advanced AI)

If you want GAT, VAE, Transformer, or RL features:

```bash
# CPU-only installation (recommended for most users)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# GPU installation (if you have NVIDIA GPU with CUDA)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Option B: Diagram Generation (PNG from Mermaid)

**Choose ONE method:**

#### Method 1: Mermaid CLI via nodeenv (RECOMMENDED)

```bash
# Install nodeenv Python package
pip install nodeenv

# Create isolated Node.js environment
nodeenv nodeenv

# Activate nodeenv
nodeenv\Scripts\activate      # Windows
source nodeenv/bin/activate   # Linux/Mac

# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Test
mmdc --version
```

#### Method 2: Playwright (Python-only alternative)

```bash
pip install playwright
playwright install chromium
```

### Option C: Development Tools

Uncomment in `requirements.txt` and install:

```bash
# Uncomment these lines in requirements.txt:
# black>=23.0.0
# flake8>=7.0.0
# mypy>=1.7.0
# pytest>=7.4.0
# ipython>=8.18.0

# Then install
pip install -r requirements.txt
```

---

## Package Management

### What We Consolidated

We merged these files into ONE `requirements.txt`:
- ~~requirements_fixed.txt~~ (removed)
- ~~requirements_fastapi.txt~~ (removed)
- **requirements.txt** (consolidated, Python 3.13+ compatible)

### Packages Added from Ad-hoc Installations

During development, we installed these packages ad-hoc. They're now in `requirements.txt`:
- `requests` - HTTP client for API testing
- `lxml` - XML/HTML processing
- `python-dotenv` - Environment variable management
- `certifi`, `urllib3` - SSL/TLS support

### Optional Packages (nodeenv)

**nodeenv** is NOT in `requirements.txt` by default because:
1. It's only needed for PNG diagram generation
2. Some clients don't need diagrams (web dashboard only)
3. There's a Python alternative (playwright)

**To install if needed:**
```bash
pip install nodeenv
```

---

## Python Version Compatibility

| Python Version | Status | Notes |
|----------------|--------|-------|
| **3.11** | ✅ Fully tested | Recommended for production |
| **3.13** | ✅ Client environment | FastAPI 0.115+ compatible |
| **3.14** | ✅ Latest | Modern lifespan events |
| 3.10 | ⚠️ Should work | Not tested |
| 3.9 and below | ❌ Not supported | Use Python 3.11+ |

---

## Troubleshooting

### Issue: "Module not found" errors

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: FastAPI import errors on Python 3.13

Our `requirements.txt` already has the fix:
- FastAPI >= 0.115.0 (with Pydantic V2)
- This resolves all Python 3.13/3.14 compatibility issues

### Issue: Port 8000 already in use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Issue: mmdc not found (diagram generation)

**Option 1: Check if installed**
```bash
mmdc --version
which mmdc  # Linux/Mac
where mmdc  # Windows
```

**Option 2: Install nodeenv** (see Optional Features above)

**Option 3: Use Python alternative**
```bash
pip install playwright
playwright install chromium
python generate_pngs_playwright.py
```

---

## For Client Deployment

### Recommended Installation Commands

```bash
# 1. Update pip
pip install --upgrade pip

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "import fastapi, uvicorn, pandas, numpy; print('✅ All core packages installed')"

# 4. Start web dashboard
./start_web_app.sh

# 5. Open browser
# http://localhost:8000
```

### Production Deployment

```bash
# For production (Linux server)
uvicorn fastapi_app:app --host 127.0.0.1 --port 8000 --workers 4

# With systemd (auto-restart)
# See FASTAPI_GUIDE.md for systemd configuration

# With nginx reverse proxy
# See FASTAPI_GUIDE.md for nginx configuration
```

---

## Security Notes

### Localhost-Only Configuration

The web dashboard is configured for **localhost access only**:
- Binds to `127.0.0.1` (NOT `0.0.0.0`)
- CORS restricted to localhost origins
- **NOT accessible from internet or network**
- Safe for sensitive data analysis

### If You Need Network Access

Edit `fastapi_app.py`:
```python
# Change this line:
host="127.0.0.1",  # Localhost only

# To this:
host="0.0.0.0",    # Network accessible
```

**⚠️ Warning**: Only do this in secure networks. Add authentication if exposing to network.

---

## Files Structure

```
network-segmentation-analyzer/
├── requirements.txt              ✅ CONSOLIDATED (Python 3.13+ compatible)
├── start_web_app.sh              ✅ GitBash launcher
├── start_web_app.bat             ✅ Windows launcher
├── fastapi_app.py                ✅ Web application (Python 3.13+ compatible)
├── INSTALLATION_GUIDE.md         ✅ This file
├── FASTAPI_GUIDE.md              ✅ Web app documentation
│
├── web_static/                   ✅ Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── applications.html
│   ├── dns.html
│   ├── css/main.css
│   └── js/main.js
│
├── src/                          ✅ Analysis modules
│   ├── dns_validation_reporter.py
│   ├── enterprise_report_generator.py
│   └── topology_network_analysis_generator.py
│
└── persistent_data/
    └── topology/                 ✅ 139 application JSON files
```

---

## Comparison: Old vs New

| Feature | Before | After |
|---------|--------|-------|
| **Requirements Files** | 3 separate files | ✅ 1 consolidated file |
| **Python 3.13** | ⚠️ Compatibility issues | ✅ Fully compatible |
| **Python 3.14** | ❌ Broken | ✅ Fully compatible |
| **FastAPI** | 0.104.1 (old) | ✅ 0.115+ (modern) |
| **Pydantic** | V1 (deprecated) | ✅ V2 (current) |
| **Ad-hoc packages** | Not documented | ✅ All in requirements.txt |
| **nodeenv** | Unclear status | ✅ Documented as optional |

---

## Quick Reference

### Essential Commands

```bash
# Install
pip install -r requirements.txt

# Start (GitBash)
./start_web_app.sh

# Start (Windows)
start_web_app.bat

# Start (Direct)
python fastapi_app.py

# Access
http://localhost:8000           # Dashboard
http://localhost:8000/docs      # API docs
```

### Test Installation

```python
# Quick test script
python -c "
import fastapi
import uvicorn
import pandas
import numpy
import networkx
print('✅ All core packages installed successfully!')
print(f'FastAPI version: {fastapi.__version__}')
print(f'Python compatible: 3.13+')
"
```

---

## Support

- **Web Dashboard Issues**: See `FASTAPI_GUIDE.md`
- **Installation Issues**: This file (INSTALLATION_GUIDE.md)
- **Deployment Guide**: See `PROJECT_STATUS_REPORT.md`
- **API Documentation**: http://localhost:8000/docs (when running)

---

**✅ Installation is now streamlined and Python 3.13+ compatible!**

Last updated: October 2025
