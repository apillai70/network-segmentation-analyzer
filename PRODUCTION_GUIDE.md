# 🚀 PRODUCTION GUIDE - Real Data Processing

## 📋 **Quick Start for Real Network Flow Data**

### **Step 1: Prepare Your Real Data Files**

Place your real network flow CSV files in `data/input/` directory:

```bash
# Your files should follow this format:
data/input/App_Code_WEBAPP1.csv
data/input/App_Code_DATABASE1.csv
data/input/App_Code_API_GATEWAY.csv
# etc...
```

**Required CSV Format:**
```csv
App,Source IP,Dest IP,Protocol,Bytes,Packets,Source Port,Dest Port
WEBAPP1,10.1.1.5,10.1.2.10,TCP,1500,10,443,80
WEBAPP1,10.1.1.5,10.1.3.20,TCP,2500,15,443,5432
```

### **Step 2: Run Complete Pipeline (Single Command)**

```bash
# Process ALL real files with training, visualization, and reports
python run_complete_pipeline.py
```

This will:
- ✅ Process each file one by one
- ✅ Train ML models (Random Forest + SVM)
- ✅ Generate zone predictions
- ✅ Create visualizations
- ✅ Export results (CSV, JSON, reports)

---

## 📊 **Alternative Commands**

### **Option 1: Process Specific Number of Files**
```bash
# Test with first 10 files
python run_complete_pipeline.py --max-files 10

# Process first 50 files
python run_complete_pipeline.py --max-files 50
```

### **Option 2: Fast Processing (Skip Visualizations)**
```bash
# Faster - skip visualization generation
python run_complete_pipeline.py --no-viz

# Even faster - skip training too
python run_complete_pipeline.py --no-viz --no-training
```

### **Option 3: Incremental Learning (Advanced)**
```bash
# Process files with incremental model updates
python run_incremental_learning.py --batch

# Continuous mode - watches for new files
python run_incremental_learning.py --continuous --check-interval 60
```

### **Option 4: Full System with Web UI**
```bash
# Start complete system with web interface
python start_system.py --web --incremental
```

Then open browser: http://localhost:5000

---

## 📁 **Output Files Location**

All results saved in `outputs_final/`:

```
outputs_final/
├── ANALYSIS_REPORT.txt          # Human-readable summary
├── application_zones.csv         # Zone assignments for all apps
├── complete_results.json         # Raw data in JSON
└── visualizations/
    ├── zone_distribution.png     # Zone distribution chart
    ├── processing_timeline.png   # Processing progress
    └── flow_distribution.png     # Flow statistics
```

---

## 🔄 **Production Workflow**

### **Daily/Weekly Processing:**

1. **Export flow data** from your network monitoring tool (NetFlow, sFlow, etc.)
2. **Save as CSV** with naming pattern: `App_Code_<APPNAME>.csv`
3. **Copy to** `data/input/` directory
4. **Run pipeline:**
   ```bash
   python run_complete_pipeline.py
   ```
5. **Review results** in `outputs_final/`
6. **Processed files** automatically moved to `data/input/processed/`

### **Continuous Monitoring:**

```bash
# Run in background - processes new files as they arrive
python run_incremental_learning.py --continuous --check-interval 300
```

This will check every 5 minutes for new files.

---

## ⚙️ **Advanced Configuration**

### **Enable Deep Learning (Requires PyTorch):**

```bash
# Install PyTorch first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Run with deep learning
python run_incremental_learning.py --batch --enable-deep-learning
```

### **Use PostgreSQL Instead of JSON:**

1. Set up PostgreSQL database
2. Update credentials in `config.yml` or environment variables
3. System will auto-detect and use PostgreSQL

### **Custom Input/Output Directories:**

```bash
# Specify custom directories
python run_complete_pipeline.py \
  --watch-dir /path/to/real/data \
  --output-dir /path/to/results
```

---

## 📈 **Expected Performance**

| Files | Processing Time | Speed |
|-------|----------------|-------|
| 10    | ~1 second      | 10 files/sec |
| 100   | ~2 seconds     | 50 files/sec |
| 1000  | ~20 seconds    | 50 files/sec |

Performance depends on:
- File size (number of flows)
- CPU speed
- Disk I/O
- Deep learning enabled/disabled

---

## ✅ **Validation Checklist**

Before production use:

- [ ] Test with sample real data (10-20 files)
- [ ] Verify CSV format matches requirements
- [ ] Check zone predictions are reasonable
- [ ] Review confidence scores
- [ ] Validate output files are created
- [ ] Test duplicate detection works
- [ ] Ensure processed files are moved correctly

---

## 🆘 **Troubleshooting**

### **Issue: Files not processed**
```bash
# Check file format
head -5 data/input/App_Code_YOURAPP.csv

# Check file tracker status
python -c "from src.utils.file_tracker import FileTracker; ft = FileTracker('./data/input'); print(f'Tracked: {len(ft.processed_files)}')"
```

### **Issue: Low confidence scores**
- Normal for initial run (0.5-0.6)
- Improves with more training data
- Use `--enable-deep-learning` for better accuracy

### **Issue: Wrong zone predictions**
- Check application naming patterns
- Review heuristic rules in `ensemble_model.py`
- Train with labeled data for better results

---

## 🔐 **Security Notes**

- ✅ **100% LOCAL** - No external API calls
- ✅ All data stays on your machine
- ✅ No internet connection required
- ✅ Safe for sensitive network data

---

## 📞 **Support**

For issues or questions:
1. Check `logs/` directory for error details
2. Review `pipeline_run.log` for processing logs
3. See `ANALYSIS_REPORT.txt` for results summary

---

## 🎯 **Next Steps**

1. **Delete synthetic data** (see CLEANUP_GUIDE.md)
2. **Copy real network flow files** to `data/input/`
3. **Run:** `python run_complete_pipeline.py`
4. **Review results** in `outputs_final/`
5. **Schedule regular runs** (cron/Task Scheduler)

---

**Version:** 3.0
**Last Updated:** 2025-10-12
**Status:** Production Ready ✅
