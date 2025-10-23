#!/usr/bin/env python3
"""Debug parser to see why 0 records are parsed"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import parse_network_logs
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 80)
print("TESTING PARSER - Looking in data/input/processed/")
print("=" * 80)

# Check if directory exists
processed_dir = Path('data/input/processed')
if not processed_dir.exists():
    print(f"ERROR: Directory does not exist: {processed_dir}")
    sys.exit(1)

# Count CSV files
csv_files = list(processed_dir.glob('*.csv'))
print(f"\nFound {len(csv_files)} CSV files")

if not csv_files:
    print("ERROR: No CSV files found!")
    sys.exit(1)

# List first 5 files
print("\nFirst 5 files:")
for f in csv_files[:5]:
    print(f"  - {f.name}")

print("\n" + "=" * 80)
print("PARSING ALL FILES...")
print("=" * 80)

# Use the same function as generate_threat_surface_docs.py
parser = parse_network_logs('data/input/processed')

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Total records parsed: {len(parser.records)}")
print(f"Total errors: {len(parser.parse_errors)}")

if parser.records:
    print(f"\nFirst 3 records:")
    for i, rec in enumerate(parser.records[:3], 1):
        print(f"  {i}. {rec.app_name}: {rec.src_ip} -> {rec.dst_ip} ({rec.protocol}:{rec.port})")
else:
    print("\nNO RECORDS PARSED!")
    print("\nChecking for errors...")
    if parser.parse_errors:
        print(f"\nFirst 5 errors:")
        for err in parser.parse_errors[:5]:
            print(f"  File: {err['file']}, Row: {err['row']}")
            print(f"  Error: {err['error']}")
            print(f"  Data: {err.get('data', {})}")
            print()

print("=" * 80)
