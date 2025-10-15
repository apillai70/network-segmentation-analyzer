#!/usr/bin/env python3
"""
Python-based PNG generation using Mermaid.ink API
NO Node.js or Chromium required - pure Python!
"""
import os
import base64
import urllib.request
import urllib.parse
from pathlib import Path
import time

print("="*80)
print("PNG GENERATION FROM MERMAID DIAGRAMS (Python Method)")
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
    exit(0)

print(f"\nGenerating {len(missing_pngs)} PNG files using Mermaid.ink API...")
print("="*80)

success_count = 0
failed_count = 0

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

        # Encode diagram for URL (base64)
        encoded = base64.urlsafe_b64encode(content.encode('utf-8')).decode('ascii')

        # Use Mermaid.ink API (free service)
        # Format: https://mermaid.ink/img/{base64_encoded_diagram}?type=png&width=4800
        url = f"https://mermaid.ink/img/{encoded}?type=png&width=4800"

        # Download PNG
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'NetworkSegmentationAnalyzer/1.0')

        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                png_data = response.read()

                # Save PNG
                with open(png_path, 'wb') as f:
                    f.write(png_data)

                print("[OK]")
                success_count += 1
            else:
                print(f"[ERROR - HTTP {response.status}]")
                failed_count += 1

        # Be nice to the API - small delay
        time.sleep(0.5)

    except Exception as e:
        print(f"[ERROR - {type(e).__name__}: {str(e)[:50]}]")
        failed_count += 1

print("\n" + "="*80)
print(f"PNG GENERATION COMPLETE")
print("="*80)
print(f"[OK] Success: {success_count}/{len(missing_pngs)} PNG files generated")
if failed_count > 0:
    print(f"[ERROR] Failed: {failed_count}/{len(missing_pngs)} PNG files")
print(f"\nOutput location: {diagram_dir}")
print("="*80)
