#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python-based PNG generation using Mermaid.ink API
NO Node.js or Chromium required - pure Python!
"""
import os
import sys

# Force UTF-8 encoding (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
import base64
import urllib.request
import urllib.parse
from pathlib import Path
import time
import subprocess
import tempfile

def generate_png_with_mmdc(content: str, png_path: Path) -> bool:
    """
    Fallback: Generate PNG using local mmdc when API fails

    Args:
        content: Raw Mermaid content (already stripped of fences)
        png_path: Output PNG file path

    Returns:
        True if successful, False otherwise
    """
    # Write content to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Run mmdc
        result = subprocess.run(
            ['mmdc', '-i', tmp_path, '-o', str(png_path), '-w', '4800', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Clean up temp file
        Path(tmp_path).unlink()

        return result.returncode == 0

    except FileNotFoundError:
        # mmdc not found
        Path(tmp_path).unlink()
        return False
    except Exception:
        # Any other error
        try:
            Path(tmp_path).unlink()
        except:
            pass
        return False

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate PNG files from Mermaid diagrams using Mermaid.ink API')
    parser.add_argument(
        '--apps',
        type=str,
        nargs='+',
        help='List of app codes to process (e.g., DNMET XECHK). If not specified, processes all apps.'
    )
    args = parser.parse_args()

    print("="*80)
    if args.apps:
        print(f"PNG GENERATION FOR {len(args.apps)} APPS (Python Method)")
    else:
        print("PNG GENERATION FROM MERMAID DIAGRAMS (Python Method)")
    print("="*80)

    diagram_dir = Path('outputs_final/diagrams')

    # Find all .mmd files that need PNG conversion
    print(f"\nScanning {diagram_dir} for Mermaid diagrams...")

    if args.apps:
        # Only process specified apps - both diagram types
        all_mmd_files = []
        for app_code in args.apps:
            # Check for regular diagram
            mmd_path = diagram_dir / f'{app_code}_diagram.mmd'
            if mmd_path.exists():
                all_mmd_files.append(mmd_path)
            else:
                print(f"⚠ Warning: {mmd_path.name} not found")

            # Check for application diagram
            app_mmd_path = diagram_dir / f'{app_code}_application_diagram.mmd'
            if app_mmd_path.exists():
                all_mmd_files.append(app_mmd_path)
    else:
        # Process all diagrams - both regular and application diagrams
        all_mmd_files = list(diagram_dir.glob('*_diagram.mmd'))
        all_mmd_files.extend(list(diagram_dir.glob('*_application_diagram.mmd')))

    missing_pngs = []

    for mmd_file in all_mmd_files:
        png_file = mmd_file.with_suffix('.png')
        if not png_file.exists():
            missing_pngs.append(mmd_file)

    print(f"Found {len(all_mmd_files)} total Mermaid diagrams")
    print(f"Missing {len(missing_pngs)} PNG files")

    if not missing_pngs:
        print("\n[OK] All PNG files already exist!")
        return

    print(f"\nGenerating {len(missing_pngs)} PNG files using Mermaid.ink API...")
    print("="*80)

    success_count = 0
    failed_count = 0

    for mmd_file in missing_pngs:
        app_name = mmd_file.stem.replace('_diagram', '')
        png_path = mmd_file.with_suffix('.png')

        print(f"  {app_name}...", end=' ', flush=True)

        # Read diagram content once (for both API and mmdc fallback)
        with open(mmd_file, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Strip markdown fences if present
        if '```mermaid' in file_content:
            lines = file_content.split('\n')
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
            content = file_content.strip()

        # Retry logic for 503 errors
        max_retries = 3
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
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

                        # Validate it's actually a PNG file (PNG files start with \x89PNG)
                        is_png = png_data.startswith(b'\x89PNG')

                        # Save PNG only if data is valid PNG and > 10KB (real diagrams are larger)
                        if is_png and len(png_data) > 10240:
                            with open(png_path, 'wb') as f:
                                f.write(png_data)

                            print("[OK]")
                            success_count += 1
                            success = True
                        else:
                            if not is_png:
                                print(f"[WARN - Not PNG, retry {retry_count+1}]", end=' ')
                            else:
                                print(f"[WARN - Too small {len(png_data)} bytes, retry {retry_count+1}]", end=' ')
                            retry_count += 1
                            time.sleep(3)  # Longer delay before retry
                    else:
                        print(f"[ERROR - HTTP {response.status}, retry {retry_count+1}]", end=' ')
                        retry_count += 1
                        time.sleep(2)

                # Be nice to the API - delay to avoid rate limiting
                if success:
                    time.sleep(1.5)  # Increased delay to avoid rate limiting after 10 requests

            except Exception as e:
                error_msg = str(e)
                if '503' in error_msg or 'Service Unavailable' in error_msg:
                    print(f"[503 - retry {retry_count+1}]", end=' ')
                    retry_count += 1
                    time.sleep(3)  # Longer delay for 503
                else:
                    print(f"[ERROR - {type(e).__name__}]", end=' ')
                    retry_count = max_retries  # Force fallback to mmdc
                    break

        # If API failed, try local mmdc as fallback
        if not success:
            print(f"[API FAILED - trying mmdc]", end=' ')

            # Try mmdc fallback (content already stripped of fences)
            if generate_png_with_mmdc(content, png_path):
                print("[OK via mmdc]")
                success_count += 1
            else:
                print("[FAILED - mmdc unavailable]")
                failed_count += 1

    print("\n" + "="*80)
    print(f"PNG GENERATION COMPLETE")
    print("="*80)
    print(f"[OK] Success: {success_count}/{len(missing_pngs)} PNG files generated")
    if failed_count > 0:
        print(f"[ERROR] Failed: {failed_count}/{len(missing_pngs)} PNG files")
    print(f"\nOutput location: {diagram_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
