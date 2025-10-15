# Batch Processing Guide

## ⚠️ CRITICAL: PNG File Generation

**PNG files require mermaid-cli to be installed:**

```bash
npm install -g @mermaid-js/mermaid-cli
```

**Verify installation:**
```bash
mmdc --version
```

If `mmdc` is not found, only `.mmd` and `.html` files will be generated.

The batch processor will **automatically verify and regenerate** missing PNGs after each batch.

---

## Quick Start - Process All 138 Files

### Recommended Command (10 files at a time, both outputs)
```bash
python run_batch_processing.py --batch-size 10 --output-format both
```

This will:
- ✅ Process 10 files per batch (14 batches total for 138 files)
- ✅ Show status of EACH file as it's processed
- ✅ Generate Mermaid diagrams (.mmd, .html)
- ✅ **Verify and generate PNG files** (if mmdc installed)
- ✅ Generate Lucidchart CSV exports
- ✅ Generate network segmentation Word docs
- ✅ Generate architecture Word docs
- ✅ Auto-continue to next batch until all 138 files done

Expected time: **30-45 minutes**

---

## Output Format Options

### 1. Mermaid Only (Fastest)
```bash
python run_batch_processing.py --batch-size 10 --output-format mermaid
```
- ✅ Mermaid diagrams (.mmd, .html, .png)
- ❌ No Lucidchart CSVs
- ❌ No network segmentation Word docs
- ✅ Architecture docs still generated

Expected time: **15-20 minutes**

### 2. Lucidchart Only
```bash
python run_batch_processing.py --batch-size 10 --output-format lucid
```
- ❌ No Mermaid diagrams
- ✅ Lucidchart CSV exports
- ✅ Network segmentation Word docs
- ✅ Architecture docs

Expected time: **25-35 minutes**

### 3. Both (Default - Recommended)
```bash
python run_batch_processing.py --batch-size 10 --output-format both
```
- ✅ Mermaid diagrams
- ✅ Lucidchart CSV exports
- ✅ All Word documents

Expected time: **30-45 minutes**

---

## Per-File Status Display

When running, you'll see **real-time status for each file**:

```
================================================================================
BATCH 1/14
================================================================================

Processing: App_Code_ACDA.csv
  ✓ Loaded 456 flows
  ✓ Analyzing topology...
  ✓ Generated diagram: ACDA_application_diagram.png
  ✓ Saved topology data
  Time: 2.3s

Processing: App_Code_AODSVY.csv
  ✓ Loaded 924 flows
  ✓ Analyzing topology...
  ✓ Generated diagram: AODSVY_application_diagram.png
  ✓ Saved topology data
  Time: 3.1s

[... continues for all 10 files in batch ...]

✓ Batch 1 complete
  Remaining files: 128
```

---

## Batch Size Options

### Small Batches (10 files) - RECOMMENDED
```bash
python run_batch_processing.py --batch-size 10
```
- More frequent status updates
- Easier to spot/fix errors
- Can stop/resume more easily

### Medium Batches (20 files)
```bash
python run_batch_processing.py --batch-size 20
```
- Faster overall (fewer report generation cycles)
- Less frequent status updates

### Large Batches (50 files)
```bash
python run_batch_processing.py --batch-size 50
```
- Fastest overall
- Harder to diagnose errors
- Long wait between batches

---

## Common Scenarios

### First-Time Processing (All 138 Files)
```bash
python run_batch_processing.py --batch-size 10 --output-format both
```

### Reprocess Everything from Scratch
```bash
python run_batch_processing.py --batch-size 10 --clear-first --output-format both
```

### Fast Processing (Diagrams Only, Skip Docs)
```bash
python run_batch_processing.py --batch-size 20 --output-format mermaid --skip-architecture
```

### Process Only First 50 Files (5 Batches)
```bash
python run_batch_processing.py --batch-size 10 --max-batches 5 --output-format both
```

### Resume Processing (Continue from Where You Left Off)
```bash
# Just run again - it auto-detects unprocessed files
python run_batch_processing.py --batch-size 10 --output-format both
```

---

## What Gets Generated

### After Each Batch:

**Diagrams (if Mermaid enabled):**
- `outputs_final/diagrams/{AppID}_application_diagram.mmd`
- `outputs_final/diagrams/{AppID}_application_diagram.html`
- `outputs_final/diagrams/{AppID}_application_diagram.png`

**Topology Data (always):**
- `persistent_data/topology/{AppID}.json`

**Network Segmentation Reports (if not mermaid-only):**
- `outputs_final/word_reports/netseg/{AppID}_report.docx`

**Lucidchart Exports (if lucid/both):**
- `outputs_final/diagrams/lucidchart_export_*.csv`
- `outputs_final/diagrams/lucidchart_zones_*.csv`

**Architecture Documents (if not skipped):**
- `outputs_final/word_reports/architecture/{AppID}_architecture.docx`
- `outputs_final/word_reports/architecture/Solution_Design-{AppID}.docx`

---

## Progress Tracking

The script shows:
- ✅ Current batch number (e.g., "BATCH 3/14")
- ✅ Files remaining
- ✅ Per-file status (name, flows, time)
- ✅ PNG verification status
- ✅ Success/failure for each step
- ✅ Overall statistics at end

---

## PNG File Troubleshooting

### Missing PNG Files

If PNGs are not generated, you'll see:
```
⚠ mmdc (mermaid-cli) not found - cannot generate PNGs
Install with: npm install -g @mermaid-js/mermaid-cli
```

**Solution:**
1. Install mermaid-cli:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. Verify installation:
   ```bash
   mmdc --version
   ```

3. Re-run batch processing - it will regenerate missing PNGs

### Manual PNG Generation

If some PNGs are missing after batch processing:

```bash
python generate_missing_pngs.py
```

This will scan for `.mmd` files and generate missing `.png` files.

### PNG Verification Output

After each batch, you'll see:
```
STEP 2B: VERIFYING PNG FILES
================================================================================
Found 10 Mermaid diagrams
Missing 0 PNG files
✓ All PNG files present
```

Or if missing:
```
Found 10 Mermaid diagrams
Missing 3 PNG files
Regenerating missing PNGs...
  ✓ ACDA_application_diagram.png
  ✓ AODSVY_application_diagram.png
  ✓ BKO_application_diagram.png
PNG generation: 3/3 successful
```

---

## Error Handling

If a batch fails:
1. Script logs the error
2. Asks: "Continue to next batch? (y/n)"
3. Type `y` to skip and continue
4. Type `n` to stop processing

---

## Logs

Detailed logs saved to:
```
logs/batch_processing_YYYYMMDD_HHMMSS.log
```

Check logs for:
- Detailed error messages
- Per-file processing details
- Timing information
- Debug output

---

## Quick Command Reference

| Command | Description |
|---------|-------------|
| `--batch-size 10` | Process 10 files per batch |
| `--output-format mermaid` | Mermaid diagrams only |
| `--output-format lucid` | Lucidchart CSVs only |
| `--output-format both` | Both Mermaid + Lucidchart (default) |
| `--max-batches 5` | Stop after 5 batches |
| `--clear-first` | Clear tracking, reprocess all |
| `--skip-architecture` | Skip architecture docs |
| `--skip-reports` | Skip all reports (analysis only) |

---

## Full Example Output

```bash
$ python run_batch_processing.py --batch-size 10 --output-format both

================================================================================
BATCH PROCESSING ORCHESTRATOR
================================================================================
Batch size: 10 files per batch
Max batches: unlimited
Clear tracking first: No
Output format: BOTH
  - Mermaid diagrams: Yes
  - Lucidchart CSVs: Yes
Generate reports: Yes
Generate architecture: Yes
================================================================================

Total files to process: 138
Total batches planned: 14

================================================================================
BATCH 1/14
================================================================================

[Processing files with real-time status...]

✓ Batch 1 complete
  Remaining files: 128

[Repeats for batches 2-14...]

================================================================================
BATCH PROCESSING COMPLETE
================================================================================

Start time: 2025-10-13 14:30:00
End time: 2025-10-13 15:12:00
Elapsed: 42.0 minutes (2520 seconds)

Statistics:
  Batches processed: 14/14
  Batches failed: 0
  Reports generated: 14
  Reports failed: 0
  Architecture docs generated: 14
  Architecture docs failed: 0

Output locations:
  Diagrams: outputs_final/diagrams/
  Network segmentation reports: outputs_final/word_reports/netseg/
  Architecture documents: outputs_final/word_reports/architecture/
  Topology data: persistent_data/topology/

Log file: logs/batch_processing_20251013_143000.log
================================================================================
```

---

## Need Help?

- Check logs: `logs/batch_processing_*.log`
- Review individual file processing: Look for ERROR messages
- Resume processing: Just run the command again (auto-detects remaining files)
