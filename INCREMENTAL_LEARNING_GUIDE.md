# 🔄 Incremental Learning - Quick Reference

## ⚡ **Quick Commands**

### **Process One File:**
```bash
python run_incremental_learning.py --batch --max-files 1
```

### **With Deep Learning (Features + Embeddings):**
```bash
python run_incremental_learning.py --batch --max-files 1 --enable-deep-learning
```

### **Continuous Mode (Watch for Files):**
```bash
python run_incremental_learning.py --continuous --check-interval 10
```

### **Complete Pipeline (Everything):**
```bash
python run_complete_pipeline.py --max-files 1
```

---

## 📁 **Where Files Go:**

**Input:** `data/input/App_Code_YOURAPP.csv`

**After Processing:**
- Moved to: `data/input/processed/App_Code_YOURAPP.csv`
- Features: `data/input/processed/features/YOURAPP_features.csv`
- Embeddings: `data/input/processed/embeddings/YOURAPP_embedding.npy`
- Database: `data/output/network_data.json`
- Topology: `outputs_final/incremental_topology.json`

---

## 🌐 **View Results:**

- **Dashboard:** http://localhost:5000/
- **Incremental:** http://localhost:5000/incremental
- **Topology:** http://localhost:5000/topology
- **Apps:** http://localhost:5000/applications

---

## 🎯 **Example Workflow:**

```bash
# 1. Add your CSV file
cp my_app.csv data/input/App_Code_MYAPP.csv

# 2. Process it
python run_incremental_learning.py --batch --max-files 1 --enable-deep-learning

# 3. View in browser
open http://localhost:5000/incremental
```

Done! Takes ~2 seconds per file.

---

**Last Updated:** 2025-10-12
