# Client Deployment - Enhanced Diagram Generator

## Files to Copy (4 Core Files)

### 1. Enhanced Diagram Generator
```
Source: src/enhanced_application_diagram_generator.py
Destination: <client-project>/src/enhanced_application_diagram_generator.py
Size: 865 lines
```

**What it does:**
- Generates enhanced diagrams with 6 views
- Zero Trust analysis
- Executive deliverables
- Fixed Mermaid rendering (all tabs work)

### 2. Regular Diagram Generator (MODIFIED)
```
Source: src/application_diagram_generator.py
Destination: <client-project>/src/application_diagram_generator.py
```

**What changed:**
- Added "View Enhanced Analysis" button in header
- Button positioned with 180px margin-right (no overlap)
- Links to ../enhanced_diagrams/{app_code}_enhanced_application_diagram.html

### 3. Enhanced Diagram Generation Script
```
Source: generate_enhanced_diagrams.py
Destination: <client-project>/generate_enhanced_diagrams.py
```

**What it does:**
- Reads flow data from PostgreSQL database
- Generates enhanced diagrams for all apps
- Outputs to outputs_final/enhanced_diagrams/

**Usage:**
```bash
python generate_enhanced_diagrams.py --max-batch 140
python generate_enhanced_diagrams.py --app-codes AODSVY ALE APSE
```

### 4. HTML Regeneration Script (FIXED)
```
Source: regenerate_all_html.py
Destination: <client-project>/regenerate_all_html.py
```

**What changed:**
- Fixed code fence handling for different diagram types
- Application diagrams: keeps code fences
- Network diagrams: strips code fences

**Usage:**
```bash
python regenerate_all_html.py
```

---

## Deployment Steps on Client Site

### Step 1: Copy Files

**Option A - Manual Copy:**
1. Copy the 4 files listed above
2. Maintain directory structure (src/ files go in src/)

**Option B - SCP (Linux/Mac):**
```bash
scp src/enhanced_application_diagram_generator.py user@client:/path/to/project/src/
scp src/application_diagram_generator.py user@client:/path/to/project/src/
scp generate_enhanced_diagrams.py user@client:/path/to/project/
scp regenerate_all_html.py user@client:/path/to/project/
```

**Option C - PowerShell (Windows):**
```powershell
Copy-Item src\enhanced_application_diagram_generator.py \client-server\project\src\
Copy-Item src\application_diagram_generator.py \client-server\project\src\
Copy-Item generate_enhanced_diagrams.py \client-server\project\
Copy-Item regenerate_all_html.py \client-server\project\
```

### Step 2: ONE COMMAND - Regenerate Everything

**NEW! Unified command with `--enhanced` flag:**

On client machine:
```bash
cd /path/to/project

# Option A: Regenerate everything in one command
python regenerate_all_html.py --enhanced --max-batch 140

# Option B: Regenerate regular diagrams only (without enhanced)
python regenerate_all_html.py
```

**Expected output (with --enhanced):**
```
Application Diagrams: 10 successful, 0 failed
Network Diagrams: 140 successful, 0 failed
Enhanced Diagrams: 140 successful, 0 failed
Total Success: 290
```

**What this does:**
- Adds "View Enhanced Analysis" button to all application diagrams
- Regenerates all network diagrams
- **[NEW]** Generates enhanced diagrams from database (if --enhanced flag used)
- All in one command!

### Step 3: Alternative - Use Separate Script (Optional)

If you prefer to generate enhanced diagrams separately:

```bash
# Generate enhanced diagrams only
python generate_enhanced_diagrams.py --max-batch 140
```

**Note:** The `regenerate_all_html.py --enhanced` approach is now recommended as it does everything in one step.

### Step 4: Verify Output

Check folder structure:
```
outputs_final/
├── diagrams/
│   ├── AODSVY_application_diagram.html  (updated - has button)
│   ├── AODSVY_diagram.html              (unchanged)
│   ├── ALE_application_diagram.html     (updated - has button)
│   └── ... (140 apps)
│
└── enhanced_diagrams/                   (NEW)
    ├── AODSVY_enhanced_application_diagram.html
    ├── ALE_enhanced_application_diagram.html
    └── ... (140 apps)
```

### Step 5: Test in Browser

```bash
# Open regular diagram
start outputs_final/diagrams/AODSVY_application_diagram.html

# Verify:
# 1. Button appears on right side of header
# 2. Button doesn't overlap controls
# 3. Click button -> opens enhanced version
# 4. Enhanced version shows 6 tabs
# 5. All tabs switch correctly
# 6. All diagrams render (no empty canvas)
```

---

## File Checksums (for verification)

After copying, verify file sizes:
```bash
wc -l src/enhanced_application_diagram_generator.py  # Should be ~865 lines
wc -l generate_enhanced_diagrams.py                  # Should be ~115 lines
wc -l regenerate_all_html.py                         # Should be ~175 lines
```

---

## Quick Reference Commands

### **RECOMMENDED: ONE COMMAND DEPLOYMENT**
```bash
# Regenerate everything (regular + enhanced) in one command
python regenerate_all_html.py --enhanced --max-batch 140

# Verify
ls -lh outputs_final/diagrams/ | wc -l          # Should show 280+ files (regular)
ls -lh outputs_final/enhanced_diagrams/ | wc -l  # Should show 140+ files (enhanced)
```

### Test Before Full Rollout
```bash
# Generate just 5 apps first to test
python regenerate_all_html.py --enhanced --max-batch 5

# Verify they work, then run full batch
python regenerate_all_html.py --enhanced --max-batch 140
```

### Regenerate Regular Diagrams Only (No Enhanced)
```bash
# Just add buttons to existing diagrams, no enhanced generation
python regenerate_all_html.py
```

### Alternative: Separate Commands (Old Method)
```bash
# Step 1: Regular diagrams
python regenerate_all_html.py

# Step 2: Enhanced diagrams
python generate_enhanced_diagrams.py --max-batch 140
```

### Generate Specific Apps Only (Enhanced)
```bash
# If you only need specific apps
python generate_enhanced_diagrams.py --app-codes AODSVY ALE APSE BCA
```

---

## Troubleshooting

### Issue: Button not showing
**Solution:** Run `python regenerate_all_html.py` again

### Issue: 404 error when clicking button
**Solution:** Run `python generate_enhanced_diagrams.py --max-batch 140`

### Issue: Empty diagrams in tabs
**Solution:** Regenerate with latest enhanced_application_diagram_generator.py (has Mermaid fix)

### Issue: Database connection error
**Solution:** Check .env.production has correct credentials

---

## Summary

**4 Files to Copy:**
1. ✅ src/enhanced_application_diagram_generator.py
2. ✅ src/application_diagram_generator.py
3. ✅ generate_enhanced_diagrams.py (optional - can use regenerate_all_html.py instead)
4. ✅ regenerate_all_html.py (updated with --enhanced flag)

**RECOMMENDED: ONE Command to Run:**
```bash
python regenerate_all_html.py --enhanced --max-batch 140
```

**Alternative: Two Separate Commands:**
1. ✅ python regenerate_all_html.py
2. ✅ python generate_enhanced_diagrams.py --max-batch 140

**Result:**
- 140 regular diagrams with "View Enhanced Analysis" button
- 140 enhanced diagrams with 6 interactive views
- Zero Trust analysis for each app
- Executive deliverables with recommendations
- All Mermaid rendering issues fixed

**Time Required:** ~15 minutes (10 min for generation + 5 min verification)

