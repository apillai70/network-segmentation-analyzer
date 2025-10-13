#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reprocess All Applications
===========================
Re-analyzes all 139 processed applications with improved zone inference and
persists topology data for web UI display.

Fixes:
- IP-based zone classification (instead of APP_TIER default)
- Saves topology JSON files to persistent_data/topology/
- Updates statistics

Usage:
    python reprocess_all_apps.py

Author: Enterprise Security Team
Version: 3.1 - Topology Fix
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/reprocessing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from persistence import create_persistence_manager
from agentic.local_semantic_analyzer import LocalSemanticAnalyzer


def main():
    """Main reprocessing function"""

    print("=" * 80)
    print("REPROCESSING ALL APPLICATIONS")
    print("=" * 80)
    print("Fixing topology persistence and zone classification...")
    print()

    # Initialize components
    logger.info("Initializing persistence manager and semantic analyzer...")
    pm = create_persistence_manager()
    semantic_analyzer = LocalSemanticAnalyzer(pm)

    # Find all application directories
    apps_dir = Path('persistent_data/applications')
    if not apps_dir.exists():
        logger.error(f"Applications directory not found: {apps_dir}")
        return

    app_dirs = [d for d in apps_dir.iterdir() if d.is_dir()]
    logger.info(f"Found {len(app_dirs)} applications to reprocess")

    print()
    print(f"Processing {len(app_dirs)} applications...")
    print("-" * 80)

    # Statistics
    stats = {
        'total': len(app_dirs),
        'success': 0,
        'failed': 0,
        'zone_distribution': {}
    }

    # Process each application
    for i, app_dir in enumerate(app_dirs, 1):
        app_id = app_dir.name
        flows_file = app_dir / 'flows.csv'

        print(f"[{i}/{len(app_dirs)}] {app_id}...", end=' ', flush=True)

        if not flows_file.exists():
            logger.warning(f"No flows.csv for {app_id}")
            print("[SKIP - No flows]")
            stats['failed'] += 1
            continue

        try:
            # Load flow data
            flows_df = pd.read_csv(flows_file)

            # Extract observed IPs (Source and Dest IPs)
            observed_ips = []
            if 'Source IP' in flows_df.columns:
                observed_ips.extend(flows_df['Source IP'].dropna().unique().tolist())
            if 'Dest IP' in flows_df.columns:
                observed_ips.extend(flows_df['Dest IP'].dropna().unique().tolist())

            # Limit to first 20 IPs for analysis
            observed_peers = [str(ip) for ip in observed_ips if pd.notna(ip)][:20]

            # Run semantic analysis with IP-based zone inference
            analysis = semantic_analyzer.analyze_application(
                app_name=app_id,
                metadata=None,
                observed_peers=observed_peers
            )

            # Save topology to persistent storage
            pm.save_topology_data(
                app_id=app_id,
                security_zone=analysis['security_zone'],
                dependencies=analysis['predicted_dependencies'],
                characteristics=analysis.get('characteristics', [])
            )

            # Update statistics
            zone = analysis['security_zone']
            stats['zone_distribution'][zone] = stats['zone_distribution'].get(zone, 0) + 1
            stats['success'] += 1

            print(f"[OK] {zone}")

        except Exception as e:
            logger.error(f"Failed to process {app_id}: {e}", exc_info=True)
            print(f"[ERROR] {e}")
            stats['failed'] += 1

    # Print summary
    print()
    print("=" * 80)
    print("REPROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total applications: {stats['total']}")
    print(f"Successfully processed: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print()
    print("Zone Distribution:")
    print("-" * 80)
    for zone, count in sorted(stats['zone_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {zone:20s}: {count:3d} apps")
    print("=" * 80)
    print()
    print(f"Topology files saved to: persistent_data/topology/")
    print(f"Log file saved to: logs/reprocessing_{datetime.now().strftime('%Y%m%d')}_*.log")

    logger.info("Reprocessing complete")
    logger.info(f"Success: {stats['success']}, Failed: {stats['failed']}")


if __name__ == '__main__':
    main()
