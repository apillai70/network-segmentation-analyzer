# PNG Generation Setup Guide

## ⚠️ CRITICAL: PNG Files Are Required

PNG diagram files are **essential** for:
- Word document reports (embedded diagrams)
- Presentations and documentation
- Visual review and approval

Without PNG files, your Word documents will be **incomplete**.

---

## Quick Setup

### Step 1: Check if Node.js is Installed

```bash
node --version
```

If not installed:
- **Windows**: Download from https://nodejs.org/
- **Linux**: `sudo apt install nodejs npm` or `sudo yum install nodejs npm`

### Step 2: Install Mermaid CLI

```bash
npm install -g @mermaid-js/mermaid-cli
```

This installs the `mmdc` command globally.

### Step 3: Verify Installation

```bash
mmdc --version
```

You should see version information like:
```
@mermaid-js/mermaid-cli: 10.x.x
```

---

## Troubleshooting

### "mmdc is not recognized"

**Windows:**
1. Check installation path:
   ```bash
   npm config get prefix
   ```

2. Add to PATH (typical location):
   ```
   C:\Users\<YourUsername>\AppData\Roaming\npm
   ```

3. Restart your terminal/Command Prompt

**Linux/Mac:**
```bash
export PATH="$(npm bin -g):$PATH"
echo 'export PATH="$(npm bin -g):$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "Cannot find module 'puppeteer'"

This is normal - mermaid-cli installs its own Chromium.

If it fails, install puppeteer separately:
```bash
npm install -g puppeteer
```

### Slow PNG Generation

Each PNG takes 2-5 seconds to generate. This is normal.

For 138 applications:
- PNG generation time: ~7-12 minutes total
- The batch processor generates PNGs automatically after each batch

### PNG Generation Fails for Some Diagrams

Check the Mermaid syntax in the `.mmd` file:
```bash
mmdc -i diagram.mmd -o diagram.png
```

Common issues:
- Special characters in node names
- Missing quotes around labels
- Syntax errors in Mermaid code

The batch processor automatically handles these issues by cleaning the Mermaid code.

---

## How PNG Generation Works in Batch Processing

### Automatic Generation

When you run:
```bash
python run_batch_processing.py --batch-size 10
```

The script automatically:

1. **During file processing:**
   - Generates `.mmd` (Mermaid source)
   - Generates `.html` (interactive HTML)
   - **Attempts** to generate `.png` (if mmdc available)

2. **After each batch:**
   - Verifies all `.png` files exist
   - Regenerates any missing `.png` files
   - Logs success/failure for each

3. **Output:**
   ```
   STEP 2B: VERIFYING PNG FILES
   ================================================================================
   Found 10 Mermaid diagrams
   Missing 0 PNG files
   ✓ All PNG files present
   ```

### Manual Verification

Check if PNGs are present:
```bash
dir outputs_final\diagrams\*.png   # Windows
ls outputs_final/diagrams/*.png    # Linux/Mac
```

Expected files per application:
- `{AppID}_application_diagram.mmd` ✓
- `{AppID}_application_diagram.html` ✓
- `{AppID}_application_diagram.png` ✓ **CRITICAL**

### Manual PNG Generation

If you need to regenerate PNGs after processing:

```bash
python generate_missing_pngs.py
```

This will:
1. Scan for all `.mmd` files
2. Check if corresponding `.png` exists
3. Regenerate missing PNGs
4. Show progress for each file

---

## PNG File Locations

All PNG files are saved to:
```
outputs_final/diagrams/{AppID}_application_diagram.png
```

Used by:
- `generate_application_word_docs.py` → Embeds in architecture docs
- `generate_solution_design_docs.py` → Embeds in solution design docs
- `generate_all_reports.py` → Embeds in network segmentation reports

---

## Alternative: Use HTML Instead

If you **cannot** install mmdc, you can use HTML diagrams instead:

1. Open `.html` files in browser
2. Take screenshot
3. Manually embed in Word documents

**Not recommended** - this is tedious for 138 applications.

---

## Quick Commands Reference

| Task | Command |
|------|---------|
| Check Node.js | `node --version` |
| Install mmdc | `npm install -g @mermaid-js/mermaid-cli` |
| Verify mmdc | `mmdc --version` |
| Generate single PNG | `mmdc -i diagram.mmd -o diagram.png` |
| Regenerate all missing PNGs | `python generate_missing_pngs.py` |
| Check PNG count | `dir outputs_final\diagrams\*.png` (Win) or `ls outputs_final/diagrams/*.png | wc -l` (Linux) |

---

## What Happens If mmdc Is Not Installed?

**During batch processing:**
- `.mmd` files are created ✓
- `.html` files are created ✓
- `.png` files are **skipped** ❌
- You'll see: `⚠ mmdc not found - PNG generation skipped`

**Result:**
- Word documents will be **incomplete** (no diagram images)
- You'll need to manually add screenshots
- **138 applications × manual screenshots = NOT RECOMMENDED**

---

## Installation at Customer Site

If the customer site has restricted internet access:

### Option 1: Offline NPM Install
1. Download mermaid-cli on a machine with internet:
   ```bash
   npm pack @mermaid-js/mermaid-cli
   ```

2. Copy `.tgz` file to customer site

3. Install from file:
   ```bash
   npm install -g mermaid-js-mermaid-cli-*.tgz
   ```

### Option 2: Use Docker
```bash
docker pull minlag/mermaid-cli
docker run --rm -v $(pwd):/data minlag/mermaid-cli -i diagram.mmd -o diagram.png
```

### Option 3: Pre-generate PNGs
Generate all PNGs on your development machine, then copy:
```
outputs_final/diagrams/*.png
```
to the customer site.

---

## Summary Checklist

Before running batch processing:

- [ ] Node.js installed (`node --version`)
- [ ] NPM installed (`npm --version`)
- [ ] Mermaid-cli installed (`mmdc --version`)
- [ ] mmdc accessible from command line
- [ ] Test PNG generation on one diagram

If all checked, run:
```bash
python run_batch_processing.py --batch-size 10 --output-format both
```

PNGs will be automatically generated and verified!
