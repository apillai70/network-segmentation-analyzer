#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Incremental Learning Runner
============================
Monitors data/input directory and processes new files as they arrive

This script enables CONTINUOUS LEARNING:
- As each App_Code_*.csv file is added, it's automatically processed
- Models are incrementally updated (no full retrain needed)
- Topology continuously evolves and is automatically persisted
- Progress tracked and checkpointed

NEW in v3.1:
- Topology data automatically saved to persistent_data/topology/
- IP-based zone inference for accurate classification
- Applications immediately visible in web UI after processing

Usage:
    # Continuous mode (watches for new files forever)
    python run_incremental_learning.py --continuous

    # Batch mode (process all new files once)
    python run_incremental_learning.py --batch

    # Process specific number of files
    python run_incremental_learning.py --batch --max-files 10

    # Change check interval
    python run_incremental_learning.py --continuous --check-interval 60

Troubleshooting:
    # If topology is missing for existing apps, run reprocessing:
    python reprocess_all_apps.py

    # See REPROCESSING_GUIDE.md for details

Author: Enterprise Security Team
Version: 3.1 - Topology Persistence + IP-Based Zones
"""

import sys
import os

# Force UTF-8 encoding for console output (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging (after UTF-8 fix)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/incremental_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Incremental Learning System for Network Topology Discovery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Continuous learning (watches for new files)
  python run_incremental_learning.py --continuous

  # Process all new files once
  python run_incremental_learning.py --batch

  # Process only 10 new files
  python run_incremental_learning.py --batch --max-files 10

  # Continuous with custom check interval
  python run_incremental_learning.py --continuous --check-interval 60

  # Enable all features (deep learning, RL, etc.)
  python run_incremental_learning.py --continuous --enable-all
        """
    )

    parser.add_argument(
        '--mode',
        choices=['batch', 'continuous'],
        default='continuous',
        help='Learning mode: batch (process once) or continuous (watch forever)'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch mode (shortcut for --mode batch)'
    )

    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Continuous mode (shortcut for --mode continuous) - DEFAULT'
    )

    parser.add_argument(
        '--watch-dir',
        type=str,
        default='./data/input',
        help='Directory to watch for new files (default: ./data/input)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./outputs_final',
        help='Output directory for results (default: ./outputs_final)'
    )

    parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Seconds between checks for new files (continuous mode only, default: 30)'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum files to process per batch (default: unlimited)'
    )

    parser.add_argument(
        '--enable-deep-learning',
        action='store_true',
        help='Enable deep learning models (GAT, VAE, Transformer)'
    )

    parser.add_argument(
        '--enable-all',
        action='store_true',
        help='Enable all features (deep learning + graph algorithms + RL)'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        choices=['cpu', 'cuda'],
        help='Device for PyTorch models (default: cpu)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging'
    )

    return parser.parse_args()


def main():
    """Main execution"""

    print("=" * 80)
    print("INCREMENTAL LEARNING SYSTEM v3.0")
    print("=" * 80)
    print("[CONTINUOUS] Topology discovery as files arrive...")
    print()

    # Parse arguments
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine mode
    if args.batch:
        mode = 'batch'
    elif args.continuous:
        mode = 'continuous'
    else:
        mode = args.mode

    # Create output directories
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    models_dir = Path('models/incremental')
    models_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Mode: {mode.upper()}")
    logger.info(f"Watch directory: {args.watch_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Determine features
    enable_dl = args.enable_deep_learning or args.enable_all

    logger.info(f"Deep Learning: {enable_dl}")

    try:
        # ====================================================================
        # Initialize Components
        # ====================================================================
        logger.info("\n📦 Initializing components...")

        from persistence import UnifiedPersistenceManager, create_persistence_manager
        from core.ensemble_model import EnsembleNetworkModel
        from agentic.local_semantic_analyzer import LocalSemanticAnalyzer
        from agentic.unified_topology_system import UnifiedTopologyDiscoverySystem
        from core.incremental_learner import IncrementalLearningSystem, ContinuousLearner

        # Initialize persistence using factory
        # create_persistence_manager() uses defaults and auto-fallback
        pm = create_persistence_manager()

        # Initialize ensemble model
        ensemble = EnsembleNetworkModel(pm)

        # Initialize semantic analyzer
        semantic_analyzer = LocalSemanticAnalyzer(pm)

        # Initialize topology system
        topology_system = UnifiedTopologyDiscoverySystem(
            persistence_manager=pm,
            use_deep_learning=enable_dl,
            use_graph_algorithms=True,
            use_rl_optimization=False,  # Disable RL for incremental (too slow)
            device=args.device
        )

        # Initialize incremental learning system
        incremental_learner = IncrementalLearningSystem(
            persistence_manager=pm,
            ensemble_model=ensemble,
            semantic_analyzer=semantic_analyzer,
            topology_system=topology_system,
            watch_dir=args.watch_dir,
            checkpoint_dir=str(models_dir)
        )

        logger.info("✓ All components initialized")

        # ====================================================================
        # Run Learning
        # ====================================================================

        if mode == 'batch':
            # Batch mode: Process all new files once
            logger.info("\n📊 Running in BATCH mode...")

            result = incremental_learner.run_incremental_batch(max_files=args.max_files)

            if result['status'] == 'success':
                logger.info(f"\n✅ Batch processing complete!")
                logger.info(f"  Files processed: {result['files_processed']}")
                logger.info(f"  Successful: {result['successful']}")
                logger.info(f"  Failed: {result['failed']}")

                # Export topology
                incremental_learner.export_current_topology(
                    str(output_dir / 'incremental_topology.json')
                )
            else:
                logger.info(f"\n⚠️  No new files to process")

        else:
            # Continuous mode: Watch forever
            logger.info("\n🔄 Running in CONTINUOUS mode...")
            logger.info(f"  Check interval: {args.check_interval} seconds")
            logger.info(f"  Press Ctrl+C to stop")

            continuous_learner = ContinuousLearner(
                incremental_learner,
                check_interval=args.check_interval
            )

            continuous_learner.start()

        # ====================================================================
        # Final Statistics
        # ====================================================================
        stats = incremental_learner.get_statistics()

        print("\n" + "=" * 80)
        print("[STATISTICS] FINAL STATISTICS")
        print("=" * 80)
        print(f"  Files processed: {stats['total_files_processed']}")
        print(f"  Flows analyzed: {stats['total_flows_processed']}")
        print(f"  Apps observed: {stats['apps_observed']}")
        print(f"  Model updates: {stats['model_updates']}")
        print(f"  Topology apps: {stats['topology_apps']}")
        print("=" * 80)

        print(f"\n[SUCCESS] Results saved to: {output_dir}")

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
