#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast Enrichment Test (No Real DNS Lookups)
===========================================
Create enriched CSV files quickly by simulating DNS results
"""

import sys
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def detect_vmware(hostname):
    """Detect if hostname contains VMware patterns"""
    if not hostname:
        return False
    hostname_lower = hostname.lower()
    return 'vmware' in hostname_lower or 'vm-' in hostname_lower or 'vmhost' in hostname_lower or 'esxi' in hostname_lower

def format_hostname_full(hostname, is_vmware):
    """Format full hostname with VMware info"""
    if is_vmware and hostname:
        if '|' in hostname:
            return hostname  # Already formatted
        elif '.' in hostname:
            vmware_part = hostname.split('.')[0]
            return f"{vmware_part} | {hostname}"
        else:
            return f"{hostname} | {hostname}"
    return hostname if hostname else "Unknown"

def main():
    logger.info("="*80)
    logger.info("FAST ENRICHMENT TEST (Simulated DNS)")
    logger.info("="*80)
    logger.info("")

    # Process first 5 test files
    input_dir = Path('data/input')
    test_files = sorted(input_dir.glob('App_Code_*.csv'))[:5]

    logger.info(f"[PROCESS] Processing {len(test_files)} files:")
    for f in test_files:
        logger.info(f"  - {f.name}")
    logger.info("")

    # Track cross-references
    cross_ref_db = {}

    for file_path in test_files:
        app_id = file_path.stem.replace('App_Code_', '')
        logger.info(f"[{app_id}] Processing...")

        # Read raw CSV
        df = pd.read_csv(file_path)

        # Process each row
        enriched_rows = []

        for idx, row in df.iterrows():
            # Extract raw data
            src_ip = str(row.get('IP', '')).strip()
            src_name = str(row.get('Name', '')).strip()
            dst_ip = str(row.get('Peer', '')).strip()
            protocol = str(row.get('Protocol', 'TCP')).strip()
            bytes_in = int(row.get('Bytes In', 0))
            bytes_out = int(row.get('Bytes Out', 0))

            # Parse port
            port = ''
            if ':' in protocol:
                parts = protocol.split(':', 1)
                protocol = parts[0]
                port = parts[1]

            # Source processing (use Name column as hostname since DNS will fail)
            src_hostname = src_name if src_name else src_ip
            src_is_vmware = detect_vmware(src_hostname)
            src_hostname_full = format_hostname_full(src_hostname, src_is_vmware)
            src_dns_status = 'NXDOMAIN'  # Simulated

            # Track source in cross-ref
            if src_ip:
                cross_ref_db[src_ip] = {
                    'hostname': src_hostname,
                    'hostname_full': src_hostname_full,
                    'dns_status': src_dns_status,
                    'is_vmware': src_is_vmware,
                    'app': app_id  # This is the destination app when cross-referenced
                }

            # Dest processing - check cross-reference first
            dst_app = ''  # Destination application
            if dst_ip and dst_ip in cross_ref_db:
                # Cross-reference match!
                cross_ref = cross_ref_db[dst_ip]
                dst_hostname = cross_ref['hostname']
                dst_hostname_full = cross_ref['hostname_full']
                dst_dns_status = cross_ref['dns_status']
                dst_is_vmware = cross_ref['is_vmware']
                dst_app = cross_ref['app']  # Capture the destination app!
                logger.info(f"  Cross-ref: {dst_ip} -> {dst_hostname} (app: {dst_app})")
            else:
                # No cross-reference
                dst_hostname = dst_ip  # Use IP as hostname
                dst_is_vmware = False
                dst_hostname_full = "Unknown"
                dst_dns_status = 'NXDOMAIN'
                dst_app = ''  # Unknown/external

            # Determine flow direction and dependency type
            if dst_app:
                # Inter-app communication
                if dst_app == app_id:
                    flow_direction = 'internal'  # Talking to itself
                    dependency_type = 'peer'
                else:
                    flow_direction = 'outbound'  # This app is CLIENT
                    dependency_type = 'client'   # This app depends on dst_app
            else:
                flow_direction = 'external'      # Talking to external/unknown
                dependency_type = 'client'

            # Build enriched row
            enriched_row = {
                'App': app_id,
                'Source IP': src_ip,
                'Source Hostname': src_hostname,
                'Source Hostname (Full)': src_hostname_full,
                'Source DNS Status': src_dns_status,
                'Source Is VMware': src_is_vmware,
                'Dest App': dst_app,  # NEW: Destination Application
                'Dest IP': dst_ip,
                'Dest Hostname': dst_hostname,
                'Dest Hostname (Full)': dst_hostname_full,
                'Dest DNS Status': dst_dns_status,
                'Dest Is VMware': dst_is_vmware,
                'Flow Direction': flow_direction,  # NEW: outbound/internal/external
                'Dependency Type': dependency_type,  # NEW: client/server/peer
                'Port': port,
                'Protocol': protocol,
                'Bytes In': bytes_in,
                'Bytes Out': bytes_out
            }
            enriched_rows.append(enriched_row)

        # Create enriched DataFrame
        enriched_df = pd.DataFrame(enriched_rows)

        # Save to persistent_data/applications/{APP}/flows.csv
        output_dir = Path('persistent_data/applications') / app_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'flows.csv'

        enriched_df.to_csv(output_file, index=False)

        logger.info(f"  [OK] Saved: {output_file}")
        logger.info(f"       Rows: {len(enriched_df)}, Columns: {len(enriched_df.columns)}")
        logger.info("")

    logger.info("="*80)
    logger.info("[OK] ENRICHMENT COMPLETE!")
    logger.info("="*80)
    logger.info("")
    logger.info("Enriched files created:")
    for file_path in test_files:
        app_id = file_path.stem.replace('App_Code_', '')
        output_file = Path('persistent_data/applications') / app_id / 'flows.csv'
        logger.info(f"  {output_file}")
    logger.info("")
    logger.info("Check the files to see all new columns:")
    logger.info("  - Source Hostname (Full)")
    logger.info("  - Source DNS Status")
    logger.info("  - Source Is VMware")
    logger.info("  - Dest App (shows which app this flow goes to)")
    logger.info("  - Dest Hostname (Full)")
    logger.info("  - Dest DNS Status")
    logger.info("  - Dest Is VMware")
    logger.info("  - Flow Direction (outbound/internal/external)")
    logger.info("  - Dependency Type (client/server/peer)")

if __name__ == '__main__':
    main()
