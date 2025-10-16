#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manually generate PNGs for all .mmd files
"""
import sys
import base64
import urllib.request
from pathlib import Path
import time

# Force UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def generate_png(mmd_file):
    """Generate PNG from .mmd file using Mermaid.ink API"""
    png_path = mmd_file.with_suffix('.png')

    # Read content
    with open(mmd_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove code fences
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

    # Encode for URL
    encoded = base64.urlsafe_b64encode(content.encode('utf-8')).decode('ascii')

    # Call API
    url = f"https://mermaid.ink/img/{encoded}?type=png&width=4800"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'NetworkSegmentationAnalyzer/1.0')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                png_data = response.read()

                # Validate PNG
                is_png = png_data.startswith(b'\x89PNG')

                if is_png and len(png_data) > 5000:
                    with open(png_path, 'wb') as f:
                        f.write(png_data)
                    return True, f"OK ({len(png_data)} bytes)"
                else:
                    return False, f"Invalid PNG (size={len(png_data)})"
            else:
                return False, f"HTTP {response.status}"
    except Exception as e:
        return False, str(e)

def main():
    diagram_dir = Path('outputs_final/diagrams')
    mmd_files = sorted(diagram_dir.glob('*.mmd'))

    print(f"Found {len(mmd_files)} .mmd files\n")

    success = 0
    failed = 0

    for mmd_file in mmd_files:
        print(f"{mmd_file.name}...", end=' ', flush=True)

        ok, msg = generate_png(mmd_file)

        if ok:
            print(f"[OK] {msg}")
            success += 1
        else:
            print(f"[FAILED] {msg}")
            failed += 1

        # Rate limiting delay
        time.sleep(2)

    print(f"\nComplete: {success} success, {failed} failed")

if __name__ == '__main__':
    main()
