# PNG Generation Options - Comparison Guide

## Overview
Three methods to generate PNG diagrams from Mermaid files, ranked by ease of use:

| Method | Installation | Internet Required | EPERM Issues | Quality |
|--------|-------------|-------------------|--------------|---------|
| **1. Mermaid.ink API** | ✅ None (built-in Python) | ✅ Yes | ❌ No | ⭐⭐⭐⭐ Good |
| **2. Playwright** | `pip install playwright` | ✅ Yes (first time) | ⚠️ Rare | ⭐⭐⭐⭐⭐ Excellent |
| **3. mmdc (Node.js)** | `npm install -g @mermaid-js/mermaid-cli` | ⚠️ Sometimes | ❌ Yes (EPERM) | ⭐⭐⭐⭐⭐ Excellent |

---

## Option 1: Mermaid.ink API (Recommended for Customer Sites)

### ✅ Pros
- **No installation required** - uses Python standard library only
- **No EPERM errors** - no local browser execution
- **Works anywhere** - even in restricted corporate environments
- **Fast setup** - works immediately

### ❌ Cons
- Requires internet connection
- Depends on external service (mermaid.ink)
- Might have rate limits for large batches

### Setup
```bash
# No setup needed! Just run:
python generate_pngs_python.py
```

### Use When
- Customer site has strict security policies
- Getting EPERM errors with other methods
- Need quick results without installation
- Internet connection is available

---

## Option 2: Playwright (Python)

### ✅ Pros
- **Pure Python** - install with `pip`
- **Better Windows support** than Puppeteer
- **More reliable** than Node.js mmdc
- **Same quality** as mmdc
- **Better error messages**

### ❌ Cons
- Requires pip installation
- Downloads Chromium (~300MB) on first run
- Still might have EPERM (but rarer than mmdc)

### Setup
```bash
# Install Playwright
pip install playwright

# Download Chromium browser
playwright install chromium
```

### Run
```bash
python generate_pngs_playwright.py
```

### Use When
- Want Python-only solution
- Have pip/internet access
- mmdc giving EPERM errors
- Need local generation without API

---

## Option 3: mmdc (Node.js) - Original Method

### ✅ Pros
- Industry standard tool
- Highest quality output
- Most features (scale, themes, etc.)

### ❌ Cons
- **EPERM errors** on Windows with security software
- Requires Node.js/npm
- Chromium permission issues
- More complex troubleshooting

### Setup
```bash
# Global install
npm install -g @mermaid-js/mermaid-cli

# OR in nodeenv
nodeenv\Scripts\npm install -g @mermaid-js/mermaid-cli
```

### Run
```bash
python generate_missing_pngs.py
```

### Troubleshooting
See `TROUBLESHOOT_PNG_EPERM.md` for EPERM error solutions.

---

## Quick Decision Guide

### At Customer Site with EPERM Errors?
→ **Use Option 1** (Mermaid.ink API)
```bash
python generate_pngs_python.py
```

### Want Best Quality + Control?
→ **Use Option 2** (Playwright)
```bash
pip install playwright
playwright install chromium
python generate_pngs_playwright.py
```

### Already Have Node.js Working?
→ **Use Option 3** (mmdc)
```bash
python generate_missing_pngs.py
```

---

## Performance Comparison

Generating 140 diagrams:

| Method | Time | Notes |
|--------|------|-------|
| mmdc | ~3-5 min | Fastest (parallel capable) |
| Playwright | ~5-8 min | Moderate (reuses browser) |
| Mermaid.ink | ~2-3 min | Fast but has 0.5s delay per diagram (be nice to API) |

---

## Integrated into Main Scripts

The main script `generate_all_reports.py` will auto-detect which method to use:

1. Check if `playwright` installed → use it
2. Check if `mmdc` found → use it
3. Fallback → show instructions for manual generation

---

## Example Usage

### Generate All PNGs (Auto-detect method)
```bash
python generate_all_reports.py
```

### Force Specific Method
```bash
# Force Mermaid.ink API
python generate_pngs_python.py

# Force Playwright
python generate_pngs_playwright.py

# Force mmdc
python generate_missing_pngs.py
```

---

## Installation Commands Summary

```bash
# Option 1: No installation needed
# (Already works!)

# Option 2: Playwright
pip install playwright
playwright install chromium

# Option 3: mmdc (if you want to fix EPERM)
npm install -g @mermaid-js/mermaid-cli
npx puppeteer browsers install chrome
```

---

## Recommendation

**For customer deployments:**
1. Try **Option 1** (Mermaid.ink) first - zero setup
2. If offline environment, install **Option 2** (Playwright)
3. Avoid **Option 3** (mmdc) unless already working

**For development:**
- Use **Option 2** (Playwright) - best balance of quality and reliability
