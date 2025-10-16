#!/usr/bin/env python3
"""
Debug: Check CSV column names and first row
"""
import pandas as pd
from pathlib import Path

# Find first CSV file
csv_file = list(Path('data/input').glob('App_Code_*.csv'))[0]

print(f"Checking: {csv_file.name}")
print("="*80)

df = pd.read_csv(csv_file)

print(f"\nColumns found: {list(df.columns)}")
print(f"Total rows: {len(df)}")
print("\nFirst row:")
print(df.iloc[0].to_dict())
print("="*80)
