#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Full Enrichment Flow
==========================
Process raw CSV files and create enriched flows.csv with ALL new columns
"""

import sys
import logging
import pandas as pd
from pathlib import Path
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("TEST: Full Enrichment Flow")
    logger.info("="*80)

    try:
        # Import DNS components
        from src.utils.hostname_resolver import HostnameResolver
        from src.utils.cross_reference_manager import CrossReferenceManager

        logger.info("[INIT] Initializing components...")

        hostname_resolver = HostnameResolver(
            demo_mode=False,
            enable_dns_lookup=True,
            enable_forward_dns=True,
            timeout=2.0,
            use_dns_cache=True
        )

        cross_ref_manager = CrossReferenceManager()

        logger.info("  [OK] Components initialized")
        logger.info("")

        # Process first 3 test files
        input_dir = Path('data/input')
        test_files = sorted(input_dir.glob('App_Code_*.csv'))[:3]

        logger.info(f"[PROCESS] Processing {len(test_files)} files:")
        for f in test_files:
            logger.info(f"  - {f.name}")
        logger.info("")

        for file_path in test_files:
            app_id = file_path.stem.replace('App_Code_', '')
            logger.info(f"[FILE] Processing {app_id}...")
            logger.info("-" * 80)

            # Read raw CSV
            df = pd.read_csv(file_path)
            logger.info(f"  Loaded {len(df)} rows")
            logger.info(f"  Raw columns: {list(df.columns)}")

            # Process each row with DNS validation
            enriched_rows = []

            for idx, row in df.iterrows():
                # Extract raw data
                src_ip = str(row.get('IP', '')).strip()
                src_name = str(row.get('Name', '')).strip()
                dst_ip = str(row.get('Peer', '')).strip()
                protocol = str(row.get('Protocol', 'TCP')).strip()
                bytes_in = int(row.get('Bytes In', 0))
                bytes_out = int(row.get('Bytes Out', 0))

                # Parse port from protocol if needed
                port = ''
                if ':' in protocol:
                    parts = protocol.split(':', 1)
                    protocol = parts[0]
                    port = parts[1]

                # DNS validation for source
                if src_ip:
                    src_result = hostname_resolver.resolve_with_vmware_detection(
                        ip_address=src_ip,
                        fallback_hostname=src_name
                    )
                    src_hostname = src_result['hostname'] if src_result['hostname'] else src_name
                    src_hostname_full = src_result['hostname_full']
                    src_dns_status = src_result['status']
                    src_is_vmware = src_result['is_vmware']

                    # Track in cross-ref
                    cross_ref_manager.add_source_ip(
                        app_id=app_id,
                        ip=src_ip,
                        hostname=src_hostname,
                        hostname_full=src_hostname_full,
                        dns_status=src_dns_status
                    )
                    time.sleep(0.1)  # Rate limiting
                else:
                    src_hostname = ''
                    src_hostname_full = 'Unknown'
                    src_dns_status = 'unknown'
                    src_is_vmware = False

                # DNS validation for dest (with cross-reference check)
                if dst_ip:
                    # Check cross-reference first
                    cross_ref = cross_ref_manager.check_cross_reference(dst_ip, is_source=False)

                    if cross_ref['found'] and cross_ref['is_valid_flow']:
                        # Valid inter-app flow! Use cross-referenced hostname
                        dst_hostname = cross_ref['hostname']
                        dst_hostname_full = cross_ref['hostname_full']
                        dst_dns_status = cross_ref['dns_status']
                        dst_is_vmware = cross_ref.get('is_vmware', False)
                        logger.info(f"    Cross-ref: {dst_ip} -> {dst_hostname}")
                    else:
                        # No cross-reference, perform DNS
                        dst_result = hostname_resolver.resolve_with_vmware_detection(
                            ip_address=dst_ip,
                            fallback_hostname=None
                        )
                        dst_hostname = dst_result['hostname']
                        dst_hostname_full = dst_result['hostname_full']
                        dst_dns_status = dst_result['status']
                        dst_is_vmware = dst_result['is_vmware']
                        time.sleep(0.1)  # Rate limiting

                    # Track in cross-ref
                    cross_ref_manager.add_dest_ip(
                        app_id=app_id,
                        ip=dst_ip,
                        hostname=dst_hostname,
                        hostname_full=dst_hostname_full,
                        dns_status=dst_dns_status
                    )
                else:
                    dst_hostname = ''
                    dst_hostname_full = 'Unknown'
                    dst_dns_status = 'unknown'
                    dst_is_vmware = False

                # Build enriched row
                enriched_row = {
                    'App': app_id,
                    'Source IP': src_ip,
                    'Source Hostname': src_hostname,
                    'Source Hostname (Full)': src_hostname_full,
                    'Source DNS Status': src_dns_status,
                    'Source Is VMware': src_is_vmware,
                    'Dest IP': dst_ip,
                    'Dest Hostname': dst_hostname,
                    'Dest Hostname (Full)': dst_hostname_full,
                    'Dest DNS Status': dst_dns_status,
                    'Dest Is VMware': dst_is_vmware,
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

            logger.info(f"  [OK] Saved enriched flows: {output_file}")
            logger.info(f"       Rows: {len(enriched_df)}")
            logger.info(f"       Columns: {len(enriched_df.columns)}")
            logger.info(f"       New columns: Source Hostname (Full), Source DNS Status, etc.")
            logger.info("")

        # Save cache files
        logger.info("="*80)
        logger.info("SAVING CACHE FILES")
        logger.info("="*80)

        if hostname_resolver.dns_cache_manager:
            hostname_resolver.dns_cache_manager.save_cache()
            logger.info(f"  [OK] DNS cache: {hostname_resolver.dns_cache_manager.cache_path}")

        cross_ref_manager.save_database()
        logger.info(f"  [OK] Cross-ref DB: {cross_ref_manager.db_path}")
        logger.info("")

        # Show statistics
        logger.info("="*80)
        logger.info("STATISTICS")
        logger.info("="*80)

        if hostname_resolver.dns_cache_manager:
            stats = hostname_resolver.dns_cache_manager.get_statistics()
            logger.info("DNS Cache:")
            logger.info(f"  Total IPs: {stats['total_ips']}")
            logger.info(f"  Valid: {stats['valid_ips']}")
            logger.info(f"  VMware: {stats['vmware_ips']}")
            logger.info(f"  NXDOMAIN: {stats['nxdomain_ips']}")
            logger.info("")

        cross_ref_stats = cross_ref_manager.get_statistics()
        logger.info("Cross-Reference:")
        logger.info(f"  Total IPs: {cross_ref_stats['total_ips']}")
        logger.info(f"  IPs as source: {cross_ref_stats['ips_as_source']}")
        logger.info(f"  IPs as dest: {cross_ref_stats['ips_as_dest']}")
        logger.info(f"  IPs as both: {cross_ref_stats['ips_as_both']}")
        logger.info(f"  VMware IPs: {cross_ref_stats['vmware_ips']}")
        logger.info("")

        logger.info("="*80)
        logger.info("[OK] TEST COMPLETE!")
        logger.info("="*80)
        logger.info("")
        logger.info("Check the enriched files:")
        for file_path in test_files:
            app_id = file_path.stem.replace('App_Code_', '')
            output_file = Path('persistent_data/applications') / app_id / 'flows.csv'
            logger.info(f"  {output_file}")

    except Exception as e:
        logger.error("TEST FAILED!", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
