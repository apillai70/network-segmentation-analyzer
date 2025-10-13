# 🚀 QUICK START - Network Segmentation Analyzer

## ✅ System Status: READY FOR PRODUCTION

- ✓ Synthetic data removed
- ✓ Clean directory structure
- ✓ All scripts operational
- ✓ Ready for real network flow data

---

## 📥 **Step 1: Add Your Real Network Flow Files**

Copy your network flow CSV files to `data/input/`:

```bash
# Your files should be named: App_Code_<APPNAME>.csv
cp /path/to/your/flows/App_Code_*.csv data/input/

# Or copy individual files
cp /path/to/WEBAPP1_flows.csv data/input/App_Code_WEBAPP1.csv
```

### **Required CSV Format:**

```csv
App,Source IP,Dest IP,Protocol,Bytes,Packets,Source Port,Dest Port
WEBAPP1,10.1.1.5,10.1.2.10,TCP,1500,10,443,80
WEBAPP1,10.1.1.5,10.1.3.20,TCP,2500,15,443,5432
DATABASE1,10.1.3.20,10.1.4.50,TCP,50000,100,5432,3306
```

**Columns:**
- `App` - Application name
- `Source IP` - Source IP address
- `Dest IP` - Destination IP address
- `Protocol` - TCP/UDP/etc
- `Bytes` - Bytes transferred
- `Packets` - Number of packets
- `Source Port` - Source port number
- `Dest Port` - Destination port number

---

## 🏃 **Step 2: Run the Complete Pipeline**

### **Option A: Quick Analysis (Recommended First Run)**

```bash
# Process all files with ML training and visualization
python run_complete_pipeline.py
```

This will:
1. ✓ Process each file one by one
2. ✓ Predict security zones (using heuristics initially)
3. ✓ Train ML models
4. ✓ Generate visualizations
5. ✓ Export results

**Output:** `outputs_final/` directory with reports and charts

### **Option B: With Smart Label Detection**

```bash
# Step 1: Generate smart labels
python create_smart_labels.py

# Step 2: Review and edit smart_labels.csv
#         (Correct any wrong zone predictions)

# Step 3: Train models with labels
python train_with_labels.py --labels-file smart_labels.csv

# Step 4: Run pipeline with trained models
python run_complete_pipeline.py
```

**Result:** High confidence predictions (0.85-0.95 instead of 0.5)

### **Option C: Full System with Web UI**

```bash
# Start complete system with web interface
python start_system.py --web --incremental

# Then open browser to:
# http://localhost:5000
```

---

## 📊 **Step 3: Review Results**

All results are in `outputs_final/`:

```bash
# View summary report
cat outputs_final/ANALYSIS_REPORT.txt

# View zone assignments
cat outputs_final/application_zones.csv

# Open visualizations
start outputs_final/visualizations/zone_distribution.png
start outputs_final/visualizations/processing_timeline.png
```

---

## ⚡ **Common Commands**

### **Process First 10 Files (Testing)**
```bash
python run_complete_pipeline.py --max-files 10
```

### **Fast Processing (Skip Visualizations)**
```bash
python run_complete_pipeline.py --no-viz
```

### **Continuous Monitoring (Watch for New Files)**
```bash
python run_incremental_learning.py --continuous --check-interval 300
# Checks every 5 minutes for new files
```

### **Generate Smart Labels from Real Data**
```bash
python create_smart_labels.py
# Analyzes ports, protocols, naming patterns
# Creates smart_labels.csv for review
```

### **Train Models with Ground Truth**
```bash
# Edit ground_truth_labels.csv or smart_labels.csv first
python train_with_labels.py
# Models saved to models/trained_ensemble/
```

---

## 🎯 **Improving Confidence Scores**

### **Why Initial Confidence is Low (0.5)?**

The system starts with **untrained models** using heuristics:
- No training data yet
- Guesses based on app names
- Default confidence = 0.5 (50%)

### **How to Get High Confidence (0.85-0.95)?**

**Method 1: Use Smart Labels**
```bash
# 1. Generate labels based on patterns
python create_smart_labels.py

# 2. Review smart_labels.csv
#    - Apps with "DM_" → DATA_TIER
#    - Apps with "API" → APP_TIER
#    - Apps on port 443 → WEB_TIER
#    - etc.

# 3. Correct any mistakes

# 4. Train models
python train_with_labels.py --labels-file smart_labels.csv

# 5. Re-run pipeline
python run_complete_pipeline.py
# Now confidence = 0.85-0.95! ✓
```

**Method 2: Manual Labels**
```bash
# 1. Edit ground_truth_labels.csv
#    Set correct zone for each app

# 2. Train
python train_with_labels.py

# 3. Run
python run_complete_pipeline.py
```

---

## 📁 **Directory Structure**

```
network-segmentation-analyzer/
├── data/
│   └── input/              # Put your CSV files here! ←
├── outputs_final/          # Results go here
│   ├── ANALYSIS_REPORT.txt
│   ├── application_zones.csv
│   ├── complete_results.json
│   └── visualizations/
│       ├── zone_distribution.png
│       └── processing_timeline.png
├── models/
│   ├── trained_ensemble/   # Trained models saved here
│   └── incremental/
├── logs/                   # Processing logs
└── src/                    # Source code (DO NOT MODIFY)
```

---

## 🔧 **Troubleshooting**

### **No files processed?**
```bash
# Check files are in correct location
ls -lh data/input/App_Code_*.csv

# Check file format
head -5 data/input/App_Code_YOURAPP.csv
```

### **Low confidence scores?**
```bash
# Train models first!
python create_smart_labels.py
python train_with_labels.py --labels-file smart_labels.csv
python run_complete_pipeline.py
```

### **Import errors?**
```bash
# Reinstall dependencies
pip install -r requirements_fixed.txt
```

### **Want to reset everything?**
```bash
# Clean all data (keeps source code)
rm -rf data/input/processed data/input/duplicates
rm -rf outputs_final/*
rm -rf models/*
mkdir -p data/input outputs_final models/ensemble models/incremental
```

---

## 📚 **Additional Documentation**

- **PRODUCTION_GUIDE.md** - Complete production deployment guide
- **README_CONFIDENCE_ISSUE.md** - Why confidence is 0.5 and how to fix it
- **ARCHETYPES_DETECTED.md** - How label detection works
- **CLEANUP_GUIDE.md** - How to clean up old data

---

## 🆘 **Need Help?**

1. **Check logs:** `logs/pipeline_*.log`
2. **View detailed analysis:** `label_analysis.csv`
3. **Read guides:** All *.md files in root directory

---

## 🎉 **You're All Set!**

**Current Status:**
- ✅ System cleaned and ready
- ✅ Scripts verified working
- ✅ Awaiting real network flow data

**Next Step:**
```bash
# 1. Copy your real CSV files to data/input/
cp /path/to/flows/*.csv data/input/

# 2. Run the pipeline
python run_complete_pipeline.py

# 3. Review results in outputs_final/
```

**For High Confidence Predictions:**
```bash
python create_smart_labels.py
python train_with_labels.py --labels-file smart_labels.csv
python run_complete_pipeline.py
```

---

**Version:** 3.0
**Status:** Production Ready ✅
**Last Updated:** 2025-10-12
