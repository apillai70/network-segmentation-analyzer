#!/usr/bin/env python3
"""
Clean up corrupted PNG files and regenerate them
"""
import os
from pathlib import Path

diagram_dir = Path('outputs_final/diagrams')

print("="*80)
print("CLEANING UP CORRUPTED PNG FILES")
print("="*80)

# Find all corrupted PNG files
corrupted = []
for png_file in diagram_dir.glob('*_diagram.png'):
    size_kb = png_file.stat().st_size / 1024

    # Check if file is too small OR not a valid PNG
    is_corrupted = False

    # Check 1: File size < 10KB is likely corrupted
    if size_kb < 10:
        is_corrupted = True
        reason = f"too small ({size_kb:.1f} KB)"
    else:
        # Check 2: Verify PNG file signature
        try:
            with open(png_file, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'\x89PNG'):
                    is_corrupted = True
                    reason = "not a valid PNG file (HTML error page?)"
        except Exception as e:
            is_corrupted = True
            reason = f"read error: {e}"

    if is_corrupted:
        corrupted.append(png_file)
        print(f"  Deleting: {png_file.name} - {reason}")
        png_file.unlink()

print(f"\n[OK] Deleted {len(corrupted)} corrupted PNG files")
print("\nNow run: python generate_pngs_python.py")
print("="*80)
