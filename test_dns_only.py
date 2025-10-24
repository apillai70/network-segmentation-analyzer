#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test DNS Components Only
=========================
Test just the DNS validation components without full incremental learner
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

def main():
    logger.info("="*80)
    logger.info("TEST: DNS Validation Components")
    logger.info("="*80)

    try:
        # Import DNS components
        from src.utils.hostname_resolver import HostnameResolver
        from src.utils.cross_reference_manager import CrossReferenceManager
        from src.utils.dns_cache_manager import DNSCacheManager

        logger.info("[INIT] Initializing DNS components...")

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

        # Test with first file
        test_file = Path('data/input/App_Code_XECHK.csv')
        logger.info(f"[TEST] Processing: {test_file.name}")
        logger.info("")

        # Read CSV
        df = pd.read_csv(test_file)
        logger.info(f"  Loaded {len(df)} rows")
        logger.info(f"  Columns: {list(df.columns)}")
        logger.info("")

        # Process first 3 rows
        logger.info("[DNS] Testing DNS validation on first 3 rows:")
        logger.info("")

        for idx, row in df.head(3).iterrows():
            src_ip = str(row.get('IP', '')).strip()
            src_name = str(row.get('Name', '')).strip()
            dst_ip = str(row.get('Peer', '')).strip()

            logger.info(f"Row {idx+1}:")
            logger.info(f"  Source: {src_ip} ({src_name})")
            logger.info(f"  Dest: {dst_ip}")

            # Test Source DNS
            if src_ip:
                logger.info(f"  Resolving source IP {src_ip}...")
                src_result = hostname_resolver.resolve_with_vmware_detection(
                    ip_address=src_ip,
                    fallback_hostname=src_name
                )
                logger.info(f"    Hostname: {src_result['hostname']}")
                logger.info(f"    Full: {src_result['hostname_full']}")
                logger.info(f"    Status: {src_result['status']}")
                logger.info(f"    VMware: {src_result['is_vmware']}")

                # Add to cross-ref
                cross_ref_manager.add_source_ip(
                    app_id='XECHK',
                    ip=src_ip,
                    hostname=src_result['hostname'],
                    hostname_full=src_result['hostname_full'],
                    dns_status=src_result['status']
                )

            # Test Dest DNS
            if dst_ip:
                logger.info(f"  Resolving dest IP {dst_ip}...")

                # Check cross-ref first
                cross_ref = cross_ref_manager.check_cross_reference(dst_ip, is_source=False)
                if cross_ref['found']:
                    logger.info(f"    CROSS-REF MATCH! {dst_ip} -> {cross_ref['hostname']}")
                else:
                    dst_result = hostname_resolver.resolve_with_vmware_detection(
                        ip_address=dst_ip,
                        fallback_hostname=None
                    )
                    logger.info(f"    Hostname: {dst_result['hostname']}")
                    logger.info(f"    Full: {dst_result['hostname_full']}")
                    logger.info(f"    Status: {dst_result['status']}")

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

        logger.info("[OK] Test complete!")

    except Exception as e:
        logger.error("TEST FAILED!", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
