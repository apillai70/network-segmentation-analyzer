# Quick Reference Card
## Network Segmentation Analyzer v3.0

**Print this page for quick reference**

---

## Initial Setup (First Time Only)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Edit config.yaml
# Set: postgresql.enabled = false (for JSON mode)

# 3. Verify installation
python scripts/verify_installation.py
```

---

## File Requirements

### Application List
**Location:** `data/input/applicationList.csv`
```csv
app_id,app_name
MYAPP,My Application Name
```

### Flow Files
**Naming:** `data/input/App_Code_{APP_ID}.csv`
```csv
App,Source IP,Source Hostname,Dest IP,Dest Hostname,Port,Protocol,Bytes In,Bytes Out
MYAPP,10.1.2.3,host1,10.4.5.6,host2,443,HTTPS,12345,67890
```

---

## Daily Operations

### Add and Process Files

```bash
# Copy file to input directory
cp /path/to/App_Code_MYAPP.csv data/input/

# Process new files
python run_incremental_learning.py --batch

# Check results
tail -f logs/incremental_*.log
```

### Generate Reports

```bash
# Generate all diagrams
python generate_application_reports.py

# Generate architecture documents
python generate_solution_design_docs.py

# Generate simple netseg documents
python generate_application_word_docs.py
```

---

## Common Commands

| Task | Command |
|------|---------|
| Process one file | `python run_incremental_learning.py --batch --max-files 1` |
| Process all new files | `python run_incremental_learning.py --batch` |
| Start continuous mode | `python run_incremental_learning.py --continuous` |
| **Generate diagrams (FIRST!)** | `python generate_application_reports.py` |
| **Generate docs (SECOND!)** | `python generate_solution_design_docs.py` |
| Launch web UI | `python start_system.py --web --skip-cleanup` |
| Check logs | `tail -f logs/incremental_*.log` |
| List processed files | `python scripts/manage_file_tracking.py --list` |
| Reprocess file | `python scripts/manage_file_tracking.py --forget App_Code_X.csv` |

**⚠️ WARNING:** Do NOT use `start_system.py` without `--skip-cleanup` flag - it will delete your real data!

---

## Output Locations

| Output Type | Location |
|-------------|----------|
| Topology | `outputs_final/incremental_topology.json` |
| PNG Diagrams | `outputs_final/diagrams/*.png` |
| Mermaid Code | `outputs_final/diagrams/*.mmd` |
| HTML Diagrams | `outputs_final/diagrams/*.html` |
| Architecture Docs | `outputs_final/word_reports/architecture/` |
| NetSeg Docs | `outputs_final/word_reports/netseg/` |
| JSON Storage | `outputs_final/persistent_data/` |
| Logs | `logs/` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Missing dependencies | `pip install -r requirements.txt` |
| Encoding errors | Files auto-handled (UTF-8/Latin-1) |
| No apps in topology | `python reprocess_all_apps.py` |
| Port in use | `python start_system.py --web --port 5001` |
| Out of memory | Process fewer files: `--max-files 5` |
| Slow performance | Disable deep learning in `config.yaml` |

---

## File Processing Workflow

```
1. Copy flow file → data/input/App_Code_MYAPP.csv
2. Run processing → python run_incremental_learning.py --batch
3. Check topology → cat outputs_final/incremental_topology.json
4. Generate diagrams → python generate_application_reports.py (REQUIRED FIRST!)
5. Generate docs → python generate_solution_design_docs.py (SECOND!)
6. Review output → outputs_final/word_reports/architecture/
```

**IMPORTANT ORDER:**
- Diagrams MUST be generated BEFORE documents
- Documents embed the PNG diagrams created in diagram generation step

---

## Log Files

| Log File | Purpose |
|----------|---------|
| `logs/incremental_*.log` | Processing logs |
| `logs/system_startup_*.log` | System logs |
| `solution_docs_generation.log` | Doc generation |

**View logs:**
```bash
tail -100 logs/incremental_*.log
tail -f logs/incremental_*.log  # Follow
```

---

## Status Checks

```bash
# Check processed files
python scripts/manage_file_tracking.py --list

# Check topology
python -c "
import json
with open('outputs_final/incremental_topology.json') as f:
    data = json.load(f)
    print(f'Apps: {data[\"total_apps\"]}')
"

# Check disk space
df -h outputs_final/

# Check memory
free -h
```

---

## Emergency Commands

```bash
# Reset all tracking (start over)
python scripts/manage_file_tracking.py --reset

# Reprocess everything
python reprocess_all_apps.py

# Clear old logs
find logs/ -name "*.log" -mtime +30 -delete

# Backup everything
tar -czf backup_$(date +%Y%m%d).tar.gz outputs_final/
```

---

## Support

**Full Documentation:** `CUSTOMER_DEPLOYMENT_GUIDE.md`

**Quick Help:**
```bash
python run_incremental_learning.py --help
python generate_solution_design_docs.py --help
```

---

**End of Quick Reference**
