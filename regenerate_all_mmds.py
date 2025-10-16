#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate MMD and HTML diagram files for specified applications
"""
import sys

# Force UTF-8 encoding (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser import FlowRecord
from diagrams import MermaidDiagramGenerator
from utils.hostname_resolver import HostnameResolver

def load_flow_records(csv_path):
    """Load flow records from CSV"""
    df = pd.read_csv(csv_path)

    # Debug: Print columns for first file
    if not hasattr(load_flow_records, '_printed_columns'):
        print(f"\nCSV Columns: {list(df.columns)}")
        load_flow_records._printed_columns = True

    # Extract app name from filename
    app_code = Path(csv_path).stem.replace('App_Code_', '')

    records = []
    for _, row in df.iterrows():
        # CORRECT column names for your CSV format:
        src_ip = row.get('IP')  # Source IP
        dst_ip = row.get('Peer')  # Destination IP (Peer)
        src_hostname = row.get('Name', '')  # Hostname

        # Skip if no IPs found
        if not src_ip or not dst_ip or pd.isna(src_ip) or pd.isna(dst_ip):
            continue

        protocol = row.get('Protocol', 'TCP')

        # Extract port from protocol if it's in "TCP:443" format
        port = 0
        if protocol and ':' in str(protocol):
            try:
                proto_parts = str(protocol).split(':')
                port = int(proto_parts[1])
            except (ValueError, IndexError):
                pass

        record = FlowRecord(
            src_ip=str(src_ip).strip(),
            dst_ip=str(dst_ip).strip(),
            src_hostname=str(src_hostname).strip() if src_hostname else '',
            src_port=0,
            dst_port=port,
            protocol=str(protocol) if protocol else 'TCP',
            app_name=app_code
        )
        records.append(record)

    return records

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Regenerate MMD and HTML diagrams for applications')
    parser.add_argument(
        '--apps',
        type=str,
        nargs='+',
        help='List of app codes to process (e.g., DNMET XECHK). If not specified, processes all apps.'
    )
    args = parser.parse_args()

    print("="*80)
    if args.apps:
        print(f"REGENERATING MMD AND HTML DIAGRAMS FOR {len(args.apps)} APPS")
    else:
        print("REGENERATING ALL MMD AND HTML DIAGRAMS")
    print("="*80)

    # Find CSV files based on filter
    input_dir = Path('data/input')
    processed_dir = input_dir / 'processed'

    if args.apps:
        # Only process specified apps
        csv_files = []
        for app_code in args.apps:
            # Try data/input first (unprocessed files)
            csv_path = input_dir / f'App_Code_{app_code}.csv'

            # If not found, try data/input/processed (already processed files)
            if not csv_path.exists():
                csv_path = processed_dir / f'App_Code_{app_code}.csv'

            if csv_path.exists():
                csv_files.append(csv_path)
            else:
                print(f"⚠ Warning: App_Code_{app_code}.csv not found in {input_dir} or {processed_dir}")
    else:
        # Process all apps (check both directories)
        csv_files = list(input_dir.glob('App_Code_*.csv'))
        if processed_dir.exists():
            csv_files.extend(processed_dir.glob('App_Code_*.csv'))

    print(f"\nFound {len(csv_files)} application CSV files to process")
    if args.apps:
        print(f"  Requested apps: {', '.join(args.apps[:5])}" + (f" ... and {len(args.apps)-5} more" if len(args.apps) > 5 else ""))
        if len(csv_files) < len(args.apps):
            print(f"  {len(args.apps) - len(csv_files)} apps not found")
    print("="*80)

    # Mock zones for diagram generation
    class MockZone:
        def __init__(self, name, tier):
            self.name = name
            self.tier = tier
            self.zone_type = 'micro'
            self.security_level = tier
            self.description = f"{name.replace('_', ' ').title()}"
            self.members = set()

    zones = {
        'MANAGEMENT_TIER': MockZone('MANAGEMENT_TIER', 1),
        'WEB_TIER': MockZone('WEB_TIER', 2),
        'APP_TIER': MockZone('APP_TIER', 3),
        'DATA_TIER': MockZone('DATA_TIER', 4),
        'CACHE_TIER': MockZone('CACHE_TIER', 5),
        'MESSAGING_TIER': MockZone('MESSAGING_TIER', 6),
    }

    # Initialize hostname resolver once
    hostname_resolver = HostnameResolver(
        demo_mode=True,
        filter_nonexistent=True,
        mark_nonexistent=True
    )

    output_dir = Path('outputs_final/diagrams')
    output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0

    for i, csv_file in enumerate(csv_files, 1):
        app_code = csv_file.stem.replace('App_Code_', '')

        print(f"\n[{i}/{len(csv_files)}] {app_code}...", end=' ', flush=True)

        try:
            # Load flow records
            records = load_flow_records(str(csv_file))

            print(f"({len(records)} records)", end=' ', flush=True)

            if not records:
                print("[SKIP - No records]")
                continue

            # Infer zones from IPs in this app's records
            for record in records:
                for ip in [record.src_ip, record.dst_ip]:
                    if not ip or not isinstance(ip, str):
                        continue
                    if ip.startswith('10.100.160.'):
                        zones['MANAGEMENT_TIER'].members.add(ip)
                    elif ip.startswith('10.164.105.'):
                        zones['WEB_TIER'].members.add(ip)
                    elif ip.startswith('10.100.246.') or ip.startswith('10.165.116.'):
                        zones['APP_TIER'].members.add(ip)
                    elif ip.startswith('10.164.116.'):
                        zones['DATA_TIER'].members.add(ip)
                    elif ip.startswith('10.164.144.'):
                        zones['CACHE_TIER'].members.add(ip)
                    elif ip.startswith('10.164.145.'):
                        zones['MESSAGING_TIER'].members.add(ip)

            # Create diagram generator
            generator = MermaidDiagramGenerator(
                flow_records=records,
                zones=zones,
                hostname_resolver=hostname_resolver
            )

            # Generate MMD + HTML
            output_mmd = output_dir / f"{app_code}_diagram.mmd"
            generator.generate_app_diagram(app_code, str(output_mmd))

            print("[OK]")
            success += 1

        except Exception as e:
            print(f"[ERROR: {e}]")
            failed += 1

    print("\n" + "="*80)
    print(f"REGENERATION COMPLETE")
    print("="*80)
    print(f"Success: {success}/{len(csv_files)}")
    print(f"Failed: {failed}/{len(csv_files)}")
    print(f"\nOutput: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
