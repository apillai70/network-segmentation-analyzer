"""
Regenerate ALL application diagrams with new upstream/downstream layout
"""
import sys
from pathlib import Path
import pandas as pd
from collections import namedtuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from diagrams import MermaidDiagramGenerator
from utils.hostname_resolver import HostnameResolver

print("="*70)
print("REGENERATING ALL APPLICATION DIAGRAMS")
print("="*70)

# Find all CSV files
csv_dir = Path("data/input/duplicates")
if not csv_dir.exists():
    csv_dir = Path("data/input/processed")

csv_files = list(csv_dir.glob("App_Code_*.csv"))
print(f"\nFound {len(csv_files)} application CSV files")

# Create output directory
output_dir = Path("outputs_final/diagrams")
output_dir.mkdir(parents=True, exist_ok=True)

# Create hostname resolver (demo mode for speed)
hostname_resolver = HostnameResolver(demo_mode=True)

# FlowRecord structure
FlowRecord = namedtuple('FlowRecord', ['src_ip', 'dst_ip', 'port', 'protocol', 'bytes', 'app_name'])

successful = 0
failed = 0
skipped = 0

for csv_file in sorted(csv_files):
    app_code = csv_file.stem.replace('App_Code_', '')

    print(f"\n[{successful + failed + skipped + 1}/{len(csv_files)}] Processing {app_code}...")

    try:
        # Load CSV
        df = pd.read_csv(csv_file, encoding='utf-8')

        if len(df) == 0:
            print(f"  [SKIP] Empty CSV file")
            skipped += 1
            continue

        # Create flow records
        records = []
        for _, row in df.iterrows():
            src_ip = row.get('Source IP', row.get('src_ip'))
            dst_ip = row.get('Dest IP', row.get('dst_ip'))

            # Skip if either IP is missing
            if pd.isna(src_ip) or pd.isna(dst_ip):
                continue

            port_val = row.get('Port', row.get('port', 0))
            bytes_val = row.get('Bytes In', row.get('bytes', 0))

            record = FlowRecord(
                src_ip=src_ip,
                dst_ip=dst_ip,
                port=int(port_val) if pd.notna(port_val) else None,
                protocol=row.get('Protocol', row.get('protocol', 'TCP')),
                bytes=int(bytes_val) if pd.notna(bytes_val) else 0,
                app_name=app_code
            )
            records.append(record)

        if len(records) == 0:
            print(f"  [SKIP] No valid flow records")
            skipped += 1
            continue

        print(f"  -> {len(records)} flow records loaded")

        # Generate diagram
        generator = MermaidDiagramGenerator(records, {}, hostname_resolver=hostname_resolver)

        output_mmd = output_dir / f"{app_code}_diagram.mmd"
        generator.generate_app_diagram(app_code, str(output_mmd))

        print(f"  [OK] Generated: {app_code}_diagram.html")
        successful += 1

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        failed += 1

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total applications: {len(csv_files)}")
print(f"  [OK] Successfully generated: {successful}")
print(f"  [SKIP] Skipped (empty/invalid): {skipped}")
print(f"  [ERROR] Failed: {failed}")
print(f"\nDiagrams saved to: {output_dir.absolute()}")
print("="*70)
