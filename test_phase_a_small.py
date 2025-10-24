#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase A with Small Sample
===============================
Test DNS validation with just 3 files
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_phase_a_small.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("TEST: Phase A with 3 Files")
    logger.info("="*80)

    try:
        # Import required components
        from src.persistence.unified_persistence import UnifiedPersistenceManager
        from src.ensemble_model import EnsembleModel
        from src.semantic_analyzer import SemanticAnalyzer
        from src.topology_system import UnifiedTopologySystem
        from src.core.incremental_learner import IncrementalLearningSystem

        logger.info("[INIT] Initializing components...")

        pm = UnifiedPersistenceManager()
        ensemble = EnsembleModel()
        semantic_analyzer = SemanticAnalyzer()
        topology_system = UnifiedTopologySystem()

        learner = IncrementalLearningSystem(
            persistence_manager=pm,
            ensemble_model=ensemble,
            semantic_analyzer=semantic_analyzer,
            topology_system=topology_system,
            watch_dir='./data/input',
            checkpoint_dir='./models/incremental',
            only_json=False
        )

        logger.info("  [OK] Initialized")
        logger.info("")

        # Get first 3 files only
        input_dir = Path('data/input')
        test_files = sorted(input_dir.glob('App_Code_*.csv'))[:3]

        logger.info(f"[TEST] Processing {len(test_files)} files:")
        for f in test_files:
            logger.info(f"  - {f.name}")
        logger.info("")

        # Process each file
        for idx, file_path in enumerate(test_files, 1):
            logger.info(f"[{idx}/{len(test_files)}] Processing: {file_path.name}")
            logger.info("-" * 80)

            try:
                result = learner.process_new_file(file_path)

                if result['status'] == 'success':
                    logger.info(f"  [OK] Success!")
                    logger.info(f"       Flows: {result['num_flows']}")
                    logger.info(f"       Time: {result['process_time']:.2f}s")
                elif result['status'] == 'duplicate':
                    logger.info(f"  [SKIP] Duplicate: {result['reason']}")
                else:
                    logger.error(f"  [ERROR] Failed: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"  [ERROR] Exception: {e}", exc_info=True)

            logger.info("")

        # Show statistics
        logger.info("="*80)
        logger.info("TEST RESULTS")
        logger.info("="*80)

        if learner.hostname_resolver.dns_cache_manager:
            stats = learner.hostname_resolver.dns_cache_manager.get_statistics()
            logger.info("DNS Cache Statistics:")
            logger.info(f"  Total IPs: {stats['total_ips']}")
            logger.info(f"  Valid: {stats['valid_ips']}")
            logger.info(f"  VMware: {stats['vmware_ips']}")
            logger.info(f"  NXDOMAIN: {stats['nxdomain_ips']}")
            logger.info("")

        cross_ref_stats = learner.cross_ref_manager.get_statistics()
        logger.info("Cross-Reference Statistics:")
        logger.info(f"  Total IPs: {cross_ref_stats['total_ips']}")
        logger.info(f"  Source IPs: {cross_ref_stats['source_ips']}")
        logger.info(f"  Dest IPs: {cross_ref_stats['dest_ips']}")
        logger.info("")

        logger.info("[OK] Test complete!")

    except Exception as e:
        logger.error("TEST FAILED!", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
