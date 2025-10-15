"""
Test new upstream/downstream diagram generation for DNMET
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Now we need to load the actual flow records for DNMET
import pandas as pd
from collections import namedtuple
from diagrams import MermaidDiagramGenerator
from utils.hostname_resolver import HostnameResolver

print("="*60)
print("Testing Upstream/Downstream Diagram for DNMET")
print("="*60)

# Load DNMET flow records from CSV
csv_path = Path("data/input/processed/App_Code_DNMET.csv")

if not csv_path.exists():
    # Try duplicates folder
    csv_path = Path("data/input/duplicates/App_Code_DNMET.csv")

if not csv_path.exists():
    print(f"ERROR: Cannot find DNMET CSV file")
    sys.exit(1)

print(f"\nLoading flow records from: {csv_path}")
df = pd.read_csv(csv_path, encoding='utf-8')

print(f"Loaded {len(df)} flow records")
print(f"Columns: {list(df.columns)}")

# Create FlowRecord objects
FlowRecord = namedtuple('FlowRecord', ['src_ip', 'dst_ip', 'port', 'protocol', 'bytes', 'app_name'])

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
        app_name='DNMET'
    )
    records.append(record)

print(f"\nCreated {len(records)} flow records")

# Create hostname resolver
hostname_resolver = HostnameResolver(demo_mode=True)  # Use demo mode for faster testing

# Create diagram generator
generator = MermaidDiagramGenerator(records, {}, hostname_resolver=hostname_resolver)

# Generate the new diagram
output_mmd = Path("outputs_final/diagrams/DNMET_diagram_v2.mmd")
output_html = Path("outputs_final/diagrams/DNMET_diagram_v2.html")

print(f"\nGenerating diagram to {output_mmd}")
generator.generate_app_diagram('DNMET', str(output_mmd))

print("\nDone! Open the HTML file in your browser:")
print(f"  file:///{output_html.absolute()}")
print(f"\nCompare with old version:")
print(f"  file:///{Path('outputs_final/diagrams/DNMET_diagram.html').absolute()}")
