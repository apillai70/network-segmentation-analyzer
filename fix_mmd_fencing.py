#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add markdown fencing to existing .mmd files
"""
import sys
from pathlib import Path

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def main():
    diagrams_dir = Path('outputs_final/diagrams')
    mmd_files = list(diagrams_dir.glob('*.mmd'))  # Get ALL .mmd files

    print(f"Found {len(mmd_files)} .mmd files to fix")
    print()

    success = 0
    skipped = 0

    for mmd_file in mmd_files:
        # Read content
        with open(mmd_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # Check if already has markdown fencing
        if content.startswith('```mermaid'):
            print(f"[SKIP] {mmd_file.name} - Already has fencing")
            skipped += 1
            continue

        # Add markdown fencing
        new_content = f"```mermaid\n{content}\n```"

        # Write back
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[FIXED] {mmd_file.name}")
        success += 1

    print()
    print(f"Complete: {success} fixed, {skipped} skipped")

if __name__ == '__main__':
    main()
