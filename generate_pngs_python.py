#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python-based PNG and SVG generation using Mermaid.ink API
NO Node.js or Chromium required - pure Python!
Generates both PNG (for compatibility) and SVG (for scalable, zoom-friendly diagrams)
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

def generate_with_mmdc(content: str, output_path: Path, format_type: str) -> bool:
    """
    Fallback: Generate PNG or SVG using local mmdc when API fails

    Args:
        content: Raw Mermaid content (already stripped of fences)
        output_path: Output file path (PNG or SVG)
        format_type: 'png' or 'svg'

    Returns:
        True if successful, False otherwise
    """
    # Write content to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Run mmdc
        cmd = ['mmdc', '-i', tmp_path, '-o', str(output_path)]
        if format_type == 'png':
            cmd.extend(['-w', '4800', '-b', 'transparent'])
        
        result = subprocess.run(
            cmd,
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

def generate_diagram(mmd_file: Path, content: str, format_type: str) -> bool:
    """
    Generate a diagram in specified format (PNG or SVG)
    
    Args:
        mmd_file: Source Mermaid file path
        content: Mermaid diagram content (already stripped)
        format_type: 'png' or 'svg'
    
    Returns:
        True if successful, False otherwise
    """
    output_path = mmd_file.with_suffix(f'.{format_type}')
    
    # Retry logic for 503 errors
    max_retries = 3
    retry_count = 0
    success = False

    while retry_count < max_retries and not success:
        try:
            # Encode diagram for URL (base64)
            encoded = base64.urlsafe_b64encode(content.encode('utf-8')).decode('ascii')

            # Use Mermaid.ink API
            if format_type == 'png':
                url = f"https://mermaid.ink/img/{encoded}?type=png&width=4800"
            else:  # svg
                url = f"https://mermaid.ink/svg/{encoded}"

            # Download file
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'NetworkSegmentationAnalyzer/1.0')

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = response.read()

                    # Validate content
                    if format_type == 'png':
                        is_valid = data.startswith(b'\x89PNG') and len(data) > 10240
                        min_size = 10240
                    else:  # svg
                        is_valid = b'<svg' in data and len(data) > 100
                        min_size = 100

                    if is_valid:
                        with open(output_path, 'wb') as f:
                            f.write(data)
                        success = True
                    else:
                        retry_count += 1
                        time.sleep(3)
                else:
                    retry_count += 1
                    time.sleep(2)

            # Be nice to the API
            if success:
                time.sleep(1.5)

        except Exception as e:
            error_msg = str(e)
            if '503' in error_msg or 'Service Unavailable' in error_msg:
                retry_count += 1
                time.sleep(3)
            else:
                retry_count = max_retries
                break

    # If API failed, try local mmdc as fallback
    if not success:
        if generate_with_mmdc(content, output_path, format_type):
            success = True

    return success

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Generate PNG and SVG files from Mermaid diagrams')
    parser.add_argument(
        '--apps',
        type=str,
        nargs='+',
        help='List of app codes to process (e.g., DNMET XECHK). If not specified, processes all apps.'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['png', 'svg', 'both'],
        default='both',
        help='Output format: png, svg, or both (default: both)'
    )
    args = parser.parse_args()

    print("="*80)
    if args.apps:
        print(f"DIAGRAM GENERATION FOR {len(args.apps)} APPS (Python Method)")
    else:
        print("DIAGRAM GENERATION FROM MERMAID FILES (Python Method)")
    print(f"Format: {args.format.upper()}")
    print("="*80)

    diagram_dir = Path('outputs_final/diagrams')

    # Find all .mmd files that need conversion
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
                print(f"[WARNING] Warning: {mmd_path.name} not found")

            # Check for application diagram
            app_mmd_path = diagram_dir / f'{app_code}_application_diagram.mmd'
            if app_mmd_path.exists():
                all_mmd_files.append(app_mmd_path)
    else:
        # Process all diagrams - both regular and application diagrams
        all_mmd_files = list(diagram_dir.glob('*_diagram.mmd'))
        all_mmd_files.extend(list(diagram_dir.glob('*_application_diagram.mmd')))

    # Determine which files need generation
    missing_files = []
    formats_to_generate = []
    
    if args.format in ['png', 'both']:
        formats_to_generate.append('png')
    if args.format in ['svg', 'both']:
        formats_to_generate.append('svg')

    for mmd_file in all_mmd_files:
        needs_generation = False
        for fmt in formats_to_generate:
            output_file = mmd_file.with_suffix(f'.{fmt}')
            if not output_file.exists():
                needs_generation = True
                break
        if needs_generation:
            missing_files.append(mmd_file)

    print(f"Found {len(all_mmd_files)} total Mermaid diagrams")
    print(f"Need to process {len(missing_files)} diagrams")

    if not missing_files:
        print("\n[OK] All output files already exist!")
        return

    print(f"\nGenerating diagrams using Mermaid.ink API...")
    print("="*80)

    png_success = 0
    png_failed = 0
    svg_success = 0
    svg_failed = 0

    for mmd_file in missing_files:
        app_name = mmd_file.stem.replace('_diagram', '')
        print(f"\n{app_name}:")

        # Read diagram content once
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

        # Generate PNG if needed
        if 'png' in formats_to_generate:
            png_path = mmd_file.with_suffix('.png')
            if not png_path.exists():
                print(f"  PNG...", end=' ', flush=True)
                if generate_diagram(mmd_file, content, 'png'):
                    print("[OK]")
                    png_success += 1
                else:
                    print("[FAILED]")
                    png_failed += 1
            else:
                print(f"  PNG... [EXISTS]")

        # Generate SVG if needed
        if 'svg' in formats_to_generate:
            svg_path = mmd_file.with_suffix('.svg')
            if not svg_path.exists():
                print(f"  SVG...", end=' ', flush=True)
                if generate_diagram(mmd_file, content, 'svg'):
                    print("[OK]")
                    svg_success += 1
                else:
                    print("[FAILED]")
                    svg_failed += 1
            else:
                print(f"  SVG... [EXISTS]")

    print("\n" + "="*80)
    print(f"DIAGRAM GENERATION COMPLETE")
    print("="*80)
    
    if 'png' in formats_to_generate:
        total_png = png_success + png_failed
        if total_png > 0:
            print(f"PNG: {png_success}/{total_png} successful")
            if png_failed > 0:
                print(f"     {png_failed}/{total_png} failed")
    
    if 'svg' in formats_to_generate:
        total_svg = svg_success + svg_failed
        if total_svg > 0:
            print(f"SVG: {svg_success}/{total_svg} successful")
            if svg_failed > 0:
                print(f"     {svg_failed}/{total_svg} failed")
    
    print(f"\nOutput location: {diagram_dir}")
    
    if 'svg' in formats_to_generate:
        print("\n✓ SVG files support infinite zoom without blur!")
    
    print("="*80)


if __name__ == '__main__':
    main()
