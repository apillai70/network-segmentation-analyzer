#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate PNGs using local mmdc (strips markdown fences)
"""
import sys
import subprocess
import tempfile
from pathlib import Path

def generate_png_with_mmdc(mmd_file: Path, png_file: Path) -> bool:
    """Generate PNG using mmdc after stripping markdown fences"""

    # Read .mmd file
    with open(mmd_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip markdown code fences if present
    if content.strip().startswith('```mermaid'):
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

    # Write to temporary file without fences
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Run mmdc
        result = subprocess.run(
            ['mmdc', '-i', tmp_path, '-o', str(png_file), '-w', '4800', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Clean up temp file
        Path(tmp_path).unlink()

        if result.returncode == 0:
            return True
        else:
            print(f"  Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"  Error: {e}")
        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except:
            pass
        return False


def main():
    """Generate PNGs for the 3 failing apps"""
    diagram_dir = Path('outputs_final/diagrams')

    failing_apps = ['BLZE', 'BW', 'CACS']

    print("="*80)
    print("PNG GENERATION USING LOCAL MMDC")
    print("="*80)
    print(f"\nGenerating PNGs for {len(failing_apps)} apps that failed with Mermaid.ink API...")
    print()

    success = 0
    failed = 0

    for app in failing_apps:
        mmd_file = diagram_dir / f'{app}_diagram.mmd'
        png_file = diagram_dir / f'{app}_diagram.png'

        if not mmd_file.exists():
            print(f"  {app}... [SKIP - .mmd not found]")
            continue

        print(f"  {app}...", end=' ', flush=True)

        if generate_png_with_mmdc(mmd_file, png_file):
            print("[OK]")
            success += 1
        else:
            print("[FAILED]")
            failed += 1

    print()
    print("="*80)
    print(f"Success: {success}/{len(failing_apps)}")
    print(f"Failed: {failed}/{len(failing_apps)}")
    print("="*80)


if __name__ == '__main__':
    main()
