#!/usr/bin/env python3
"""Quick test to verify CSV parsing is working"""

import pandas as pd
from pathlib import Path

# Find a test CSV file
csv_file = Path('data/input/processed/App_Code_AODSVY.csv')

if not csv_file.exists():
    # Try to find any App_Code CSV
    csv_files = list(Path('data/input').glob('App_Code_*.csv'))
    if csv_files:
        csv_file = csv_files[0]
    else:
        print("ERROR: No CSV files found!")
        exit(1)

print(f"Testing CSV file: {csv_file}")
print("=" * 80)

# Load the CSV
df = pd.read_csv(csv_file)

print(f"\nColumn names in CSV:")
print(df.columns.tolist())

print(f"\nFirst row of data:")
for col in df.columns:
    print(f"  {col}: {df.iloc[0][col]}")

print(f"\n{'='*80}")
print(f"Testing row.get() method:")
row = df.iloc[0]

src_ip = row.get('Source IP', 'NOT_FOUND')
dst_ip = row.get('Dest IP', 'NOT_FOUND')
src_hostname = row.get('Source Hostname', 'NOT_FOUND')
dst_hostname = row.get('Dest Hostname', 'NOT_FOUND')

print(f"  row.get('Source IP'): '{src_ip}'")
print(f"  row.get('Dest IP'): '{dst_ip}'")
print(f"  row.get('Source Hostname'): '{src_hostname}'")
print(f"  row.get('Dest Hostname'): '{dst_hostname}'")

print(f"\n{'='*80}")
if src_ip == 'NOT_FOUND':
    print("❌ PROBLEM: 'Source IP' column not found!")
    print("\nTrying case-insensitive search...")
    for col in df.columns:
        if 'source' in col.lower() and 'ip' in col.lower():
            print(f"  Found similar column: '{col}' = {df.iloc[0][col]}")
else:
    print("✅ SUCCESS: CSV parsing is working correctly!")
