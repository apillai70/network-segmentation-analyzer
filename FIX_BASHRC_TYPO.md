# Fix .bashrc Typo - mmdc Not Found

## The Problem

Your `.bashrc` has a typo:

```bash
export PATH="$HOME/network-segmentation-analyzer/nodevenv/Scripts:$PATH"
                                                    ^^^^^^^^
                                                    TYPO: should be "nodeenv"
```

This is why mmdc cannot be found even though it's installed!

---

## Quick Fix (2 minutes)

### Step 1: Check Your Directory Name

```bash
cd $HOME/network-segmentation-analyzer
ls -la | grep env
```

**You'll see either:**
- `nodeenv/` ✓ Correct name
- `nodevenv/` ✗ Typo in directory name

### Step 2: Fix the Issue

**If directory is named "nodeenv"** (correct):

Edit `~/.bashrc`:
```bash
nano ~/.bashrc
# or
vi ~/.bashrc
```

Change this line:
```bash
# FROM (wrong):
export PATH="$HOME/network-segmentation-analyzer/nodevenv/Scripts:$PATH"

# TO (correct):
export PATH="$HOME/network-segmentation-analyzer/nodeenv/Scripts:$PATH"
```

Save and reload:
```bash
source ~/.bashrc
```

**If directory is named "nodevenv"** (typo in directory):

Rename the directory:
```bash
cd $HOME/network-segmentation-analyzer
mv nodevenv nodeenv
```

Then reload .bashrc:
```bash
source ~/.bashrc
```

### Step 3: Verify Fix

```bash
# Check if mmdc is now in PATH
which mmdc
# Should show: /home/RC34361/network-segmentation-analyzer/nodeenv/Scripts/mmdc

# Check version
mmdc --version
# Should show: 11.12.0
```

---

## Then Run Batch Processing

```bash
cd $HOME/network-segmentation-analyzer

# Now this will work!
./run_batch_with_nodeenv.sh --batch-size 10 --clear-first
```

---

## Expected Result

```
================================================================================
BATCH PROCESSING WITH NODEENV
================================================================================

1. Setting up environment...
   Sourcing ~/.bashrc...
   ✓ Environment loaded
   Activating nodeenv...
   ✓ Nodeenv activated

2. Checking for mmdc (mermaid-cli)...
   ✓ Found: mmdc 11.12.0
   ✓ Location: /home/RC34361/network-segmentation-analyzer/nodeenv/Scripts/mmdc

4. Starting batch processing...
   Command: python run_batch_processing.py --batch-size 10 --clear-first

================================================================================
STEP 2B: VERIFYING PNG FILES
================================================================================
Found 139 Mermaid diagrams
Missing 139 PNG files
Regenerating missing PNGs...
✓ Found mmdc in nodeenv: /home/RC34361/.../nodeenv/Scripts/mmdc
  ✓ ACDA.png
  ✓ ALE.png
  ...
PNG generation: 139/139 successful

✅ Architecture docs generated: 139
```

---

## Verification After Fix

```bash
# Check outputs
find outputs_final/diagrams -name "*.mmd" | wc -l    # Should be 139
find outputs_final/diagrams -name "*.png" | wc -l    # Should be 139
find outputs_final/word_reports -name "*.docx" | wc -l  # Should be 278+
```

---

## If Still Not Working

Run the diagnostic:

```bash
python test_mmdc_detection.py
```

This will show exactly where mmdc is (or isn't) and give specific recommendations.

---

## Summary

**The Issue:** Typo in .bashrc: `nodevenv` → `nodeenv`

**The Fix:**
1. Edit `~/.bashrc`
2. Change `nodevenv` to `nodeenv`
3. Run `source ~/.bashrc`
4. Run `./run_batch_with_nodeenv.sh --batch-size 10 --clear-first`
5. ✅ Everything works!

**Time to fix:** ~2 minutes
