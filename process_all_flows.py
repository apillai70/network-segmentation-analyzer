#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase A: Process All Flows with DNS Validation
===============================================
Process all 166 CSV files with DNS validation, VMware detection, and cross-referencing.
This is Phase A - NO diagram generation yet!

Process:
1. Initialize DNS validation components
2. Process all App_Code_*.csv files from data/input/
3. Perform DNS validation (reverse + forward)
4. Detect VMware patterns
5. Cross-reference IPs across all applications
6. Save enriched flows to persistent_data/applications/*/flows.csv
7. Perform retroactive updates when new hostname info discovered

Phase B (batch diagram generation) happens AFTER this completes.

Author: Enterprise Security Team
Version: 1.0
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase_a_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Phase A: Process all flows with DNS validation

    NO diagram generation in this phase!
    """
    logger.info("="*80)
    logger.info("PHASE A: Processing All Flows with DNS Validation")
    logger.info("="*80)
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("")

    try:
        # Import required components
        from src.persistence.unified_persistence import UnifiedPersistenceManager
        from src.ensemble_model import EnsembleModel
        from src.semantic_analyzer import SemanticAnalyzer
        from src.topology_system import UnifiedTopologySystem
        from src.core.incremental_learner import IncrementalLearningSystem

        logger.info("[INIT] Initializing components...")

        # Initialize persistence manager
        pm = UnifiedPersistenceManager()
        logger.info("  [OK] Persistence manager initialized")

        # Initialize models (needed for incremental learner)
        ensemble = EnsembleModel()
        semantic_analyzer = SemanticAnalyzer()
        topology_system = UnifiedTopologySystem()
        logger.info("  [OK] Models initialized")

        # Initialize incremental learning system with DNS validation
        learner = IncrementalLearningSystem(
            persistence_manager=pm,
            ensemble_model=ensemble,
            semantic_analyzer=semantic_analyzer,
            topology_system=topology_system,
            watch_dir='./data/input',
            checkpoint_dir='./models/incremental',
            only_json=False
        )
        logger.info("  [OK] Incremental learner initialized")
        logger.info("")

        # Scan for new files
        logger.info("[SCAN] Scanning for App_Code_*.csv files...")
        new_files = learner.scan_for_new_files()

        if not new_files:
            logger.info("  No new files to process")
            logger.info("")
            logger.info("PHASE A: Complete - No new files")
            return

        logger.info(f"  Found {len(new_files)} files to process")
        logger.info("")

        # Process each file
        logger.info("[PROCESS] Processing files with DNS validation...")
        logger.info(f"  Total files: {len(new_files)}")
        logger.info(f"  Rate limiting: 0.1s between DNS lookups")
        logger.info("")

        success_count = 0
        error_count = 0
        duplicate_count = 0

        for idx, file_path in enumerate(new_files, 1):
            logger.info(f"[{idx}/{len(new_files)}] Processing: {file_path.name}")

            try:
                result = learner.process_new_file(file_path)

                if result['status'] == 'success':
                    success_count += 1
                    logger.info(f"  [OK] Success: {result['num_flows']} flows in {result['process_time']:.2f}s")
                elif result['status'] == 'duplicate':
                    duplicate_count += 1
                    logger.info(f"  [SKIP] Duplicate: {result['reason']}")
                else:
                    error_count += 1
                    logger.warning(f"  [ERROR] Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                error_count += 1
                logger.error(f"  [ERROR] Exception: {e}", exc_info=True)

            logger.info("")

        # Summary
        logger.info("="*80)
        logger.info("PHASE A: Processing Complete")
        logger.info("="*80)
        logger.info(f"Total files scanned: {len(new_files)}")
        logger.info(f"Successfully processed: {success_count}")
        logger.info(f"Duplicates skipped: {duplicate_count}")
        logger.info(f"Errors encountered: {error_count}")
        logger.info("")

        # DNS validation statistics
        if learner.hostname_resolver.dns_cache_manager:
            stats = learner.hostname_resolver.dns_cache_manager.get_statistics()
            logger.info("DNS Validation Statistics:")
            logger.info(f"  Total IPs cached: {stats['total_ips']}")
            logger.info(f"  Valid DNS: {stats['valid_ips']}")
            logger.info(f"  VMware detected: {stats['vmware_ips']}")
            logger.info(f"  NXDOMAIN: {stats['nxdomain_ips']}")
            logger.info(f"  DNS changes detected: {stats['changes_detected']}")
            logger.info("")

        # Cross-reference statistics
        cross_ref_stats = learner.cross_ref_manager.get_statistics()
        logger.info("Cross-Reference Statistics:")
        logger.info(f"  Total IPs tracked: {cross_ref_stats['total_ips']}")
        logger.info(f"  IPs used as source: {cross_ref_stats['source_ips']}")
        logger.info(f"  IPs used as dest: {cross_ref_stats['dest_ips']}")
        logger.info(f"  Inter-app flows: {cross_ref_stats.get('inter_app_flows', 0)}")
        logger.info("")

        # Retroactive update statistics
        retro_stats = learner.retroactive_updater.get_update_statistics()
        logger.info("Retroactive Update Statistics:")
        logger.info(f"  Files updated: {retro_stats['files_updated']}")
        logger.info(f"  Total updates: {retro_stats['total_updates']}")
        logger.info("")

        # Persistent data location
        logger.info("Persistent Data:")
        logger.info(f"  Applications: persistent_data/applications/")
        logger.info(f"  DNS cache: persistent_data/dns_cache.json")
        logger.info(f"  Cross-reference DB: persistent_data/cross_reference/ip_hostname_db.json")
        logger.info(f"  Retroactive updates log: persistent_data/retroactive_updates.log")
        logger.info("")

        logger.info("="*80)
        logger.info("PHASE A: Complete")
        logger.info(f"End time: {datetime.now().isoformat()}")
        logger.info("")
        logger.info("Next step: Run Phase B for batch diagram generation")
        logger.info("  Command: python run_batch_processing.py --phase-b-only")
        logger.info("="*80)

    except Exception as e:
        logger.error("="*80)
        logger.error("PHASE A: FAILED")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        logger.error("")
        sys.exit(1)


if __name__ == '__main__':
    main()
