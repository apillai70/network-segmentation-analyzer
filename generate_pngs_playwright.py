#!/usr/bin/env python3
"""
PNG generation using Playwright (Python)
Better Windows support than Puppeteer, pure Python

SETUP:
pip install playwright
playwright install chromium

USAGE:
python generate_pngs_playwright.py
"""
import sys
from pathlib import Path

# Check if playwright is installed
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed")
    print("\nInstall with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

print("="*80)
print("PNG GENERATION FROM MERMAID DIAGRAMS (Playwright)")
print("="*80)

diagram_dir = Path('outputs_final/diagrams')

# Find all .mmd files that need PNG conversion
print(f"\nScanning {diagram_dir} for Mermaid diagrams...")
all_mmd_files = list(diagram_dir.glob('*_diagram.mmd'))
missing_pngs = []

for mmd_file in all_mmd_files:
    png_file = mmd_file.with_suffix('.png')
    if not png_file.exists():
        missing_pngs.append(mmd_file)

print(f"Found {len(all_mmd_files)} total Mermaid diagrams")
print(f"Missing {len(missing_pngs)} PNG files")

if not missing_pngs:
    print("\n[OK] All PNG files already exist!")
    sys.exit(0)

print(f"\nGenerating {len(missing_pngs)} PNG files using Playwright...")
print("="*80)

success_count = 0
failed_count = 0

# HTML template for rendering Mermaid
html_template = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; background: white; }}
        #diagram {{ width: 4800px; }}
    </style>
</head>
<body>
    <div id="diagram" class="mermaid">
{mermaid_content}
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'neutral',
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>
"""

with sync_playwright() as p:
    # Launch browser with no sandbox (for customer environments)
    browser = p.chromium.launch(
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    )

    page = browser.new_page(viewport={'width': 4800, 'height': 3600})

    for mmd_file in missing_pngs:
        app_name = mmd_file.stem.replace('_diagram', '')
        png_path = mmd_file.with_suffix('.png')

        print(f"  {app_name}...", end=' ', flush=True)

        try:
            # Read diagram content
            with open(mmd_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove code fences if present
            if '```mermaid' in content:
                lines = content.split('\n')
                graph_lines = []
                in_graph = False

                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('```mermaid'):
                        in_graph = True
                        continue
                    elif stripped == '```':
                        in_graph = False
                        break
                    elif in_graph:
                        graph_lines.append(line)

                content = '\n'.join(graph_lines).strip()
            else:
                content = content.strip()

            # Create HTML with Mermaid content
            html = html_template.format(mermaid_content=content)

            # Load HTML and wait for Mermaid to render
            page.set_content(html)
            page.wait_for_timeout(2000)  # Wait 2 seconds for rendering

            # Take screenshot
            page.screenshot(path=str(png_path), full_page=True)

            print("[OK]")
            success_count += 1

        except Exception as e:
            print(f"[ERROR - {type(e).__name__}]")
            failed_count += 1

    browser.close()

print("\n" + "="*80)
print(f"PNG GENERATION COMPLETE")
print("="*80)
print(f"[OK] Success: {success_count}/{len(missing_pngs)} PNG files generated")
if failed_count > 0:
    print(f"[ERROR] Failed: {failed_count}/{len(missing_pngs)} PNG files")
print(f"\nOutput location: {diagram_dir}")
print("="*80)
