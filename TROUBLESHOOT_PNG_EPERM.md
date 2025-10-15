# PNG Generation EPERM Error - Troubleshooting Guide

## Problem
Getting `spawn EPERM` error when generating PNG diagrams at customer site:
```
Error: spawn EPERM at ChildProcess.spawn (node:internal/child_process:421:11)
```

## Root Cause
Windows is blocking Chromium (used by mermaid-cli) from executing due to:
- Antivirus/security software
- Windows Defender SmartScreen
- Missing execute permissions
- Corporate security policies

## Solutions (Try in Order)

### Solution 1: Use Puppeteer Config (Already Applied)
The `puppeteer-config.json` file disables Chrome sandboxing:
```json
{
  "args": [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions"
  ]
}
```

**Status:** If still getting EPERM, try Solution 2.

### Solution 2: Reinstall Chromium in Nodeenv
Chromium may not have been installed or has incorrect permissions.

```bash
# Navigate to project directory
cd C:\Users\AjayPillai\project\network-segmentation-analyzer

# Reinstall Chromium for Puppeteer
nodeenv\Scripts\node nodeenv\Scripts\node_modules\puppeteer\install.js
```

### Solution 3: Add Antivirus Exclusion
Add these paths to antivirus exclusions:
- `C:\Users\AjayPillai\project\network-segmentation-analyzer\nodeenv\`
- Specifically: `nodeenv\Scripts\node_modules\@mermaid-js\mermaid-cli\`

**Windows Defender:**
1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Exclusions → Add or remove exclusions
4. Add folder → Select `nodeenv` folder

### Solution 4: Check Chromium Executable Permissions
```bash
# Check if Chromium exists
dir nodeenv\Scripts\node_modules\@mermaid-js\mermaid-cli\node_modules\puppeteer\.local-chromium /s

# If found, check permissions
icacls "path\to\chrome.exe"

# Add execute permissions if needed
icacls "path\to\chrome.exe" /grant Users:(RX)
```

### Solution 5: Use System Chrome Instead
Set environment variable to use system Chrome:

```bash
# Find your Chrome installation
where chrome

# Set environment variable (PowerShell)
$env:PUPPETEER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Then run generation
python generate_missing_pngs.py
```

### Solution 6: Disable Windows Defender SmartScreen (Temporary)
**WARNING:** Only do this temporarily for testing.

1. Open Windows Security
2. App & browser control
3. Reputation-based protection settings
4. Turn off "Check apps and files"
5. Run PNG generation
6. **Turn it back on after testing**

### Solution 7: Manual PNG Generation (Fallback)
If all else fails, generate PNGs on a different machine:

1. Copy `outputs_final/diagrams/*.mmd` files to working machine
2. Run `generate_missing_pngs.py` there
3. Copy generated `*.png` files back to customer site

## Verification Commands

### Check mmdc is found:
```bash
where mmdc
# Should output: C:\Users\...\nodeenv\Scripts\mmdc.CMD
```

### Test mmdc directly:
```bash
mmdc --version
# Should output version number
```

### Test with single file:
```bash
mmdc -i outputs_final\diagrams\DNMET_diagram.mmd -o test.png -p puppeteer-config.json
```

### Check if config is being used:
```bash
python -c "from pathlib import Path; print(Path('puppeteer-config.json').exists())"
# Should output: True
```

## Still Having Issues?

### Get Full Error Details:
Run with verbose output:
```bash
python generate_missing_pngs.py 2>&1 | tee png_errors.log
```

Send `png_errors.log` for further diagnosis.

### Quick Workaround:
Skip PNG generation and use HTML diagrams instead:
```bash
python generate_all_reports.py --skip-diagrams
```

HTML diagrams in `outputs_final/diagrams/*.html` are fully interactive and don't require PNG files.

## Contact
If none of these solutions work, the issue is likely:
- Corporate security policy blocking process spawning
- Need IT admin rights to whitelist Chromium
- Need to use Solution 7 (generate on different machine)
