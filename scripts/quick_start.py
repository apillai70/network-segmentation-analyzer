#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start Script for Network Segmentation Analyzer
======================================================
One-command setup and execution

This script:
1. Checks dependencies
2. Initializes database (if needed)
3. Generates synthetic data (optional)
4. Starts the analysis system
5. Launches web UI

Usage:
    python scripts/quick_start.py

    # With custom options
    python scripts/quick_start.py --generate-data 140 --web --port 5000

    # Skip database initialization
    python scripts/quick_start.py --skip-db-init

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_previous_run():
    """Clean up previous run data to start fresh"""
    logger.info("="*60)
    logger.info("Cleaning up previous run...")
    logger.info("="*60)

    import shutil

    cleanup_items = [
        # Generated flow files (keep applicationList.csv)
        ('data/input/App_Code_*.csv', 'glob'),
        ('data/input/generation_summary.json', 'file'),

        # Output data
        ('outputs_final/network_analysis.db', 'file'),
        ('outputs_final/incremental_topology.json', 'file'),
        ('outputs_final/persistent_data', 'dir'),

        # Model checkpoints
        ('models/incremental', 'dir'),
        ('models/ensemble', 'dir'),

        # Visualizations
        ('visualizations/*.html', 'glob'),
        ('visualizations/*.csv', 'glob'),

        # Logs (optional - keep for debugging)
        # ('logs/*.log', 'glob'),
    ]

    for item, item_type in cleanup_items:
        try:
            if item_type == 'glob':
                # Handle glob patterns
                from pathlib import Path
                for file_path in Path('.').glob(item):
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"  [DELETED] {file_path}")
            elif item_type == 'file':
                file_path = Path(item)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"  [DELETED] {file_path}")
            elif item_type == 'dir':
                dir_path = Path(item)
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.info(f"  [DELETED] {dir_path}/")
        except Exception as e:
            logger.warning(f"  [SKIP] Could not delete {item}: {e}")

    # Recreate essential directories
    essential_dirs = [
        'data/input',
        'outputs_final',
        'models/incremental',
        'models/ensemble',
        'visualizations',
        'logs'
    ]

    for dir_path in essential_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info("[OK] Cleanup complete - starting fresh!")
    logger.info("="*60)
    logger.info("")


def check_python_version():
    """Check Python version"""
    logger.info("Checking Python version...")
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        logger.error(f"Current version: {sys.version}")
        return False
    logger.info(f"[OK] Python {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check required Python packages"""
    logger.info("Checking dependencies...")

    # Map pip package names to Python module names
    required = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'networkx': 'networkx',
        'flask': 'flask',
        'scikit-learn': 'sklearn',  # pip name != module name
        'matplotlib': 'matplotlib',
        'pyyaml': 'yaml'  # pip name != module name
    }

    # Optional packages (system works without these)
    optional = {
        'psycopg2-binary': 'psycopg2'  # PostgreSQL support (will fallback to JSON)
    }

    missing = []
    for pip_name, module_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    # Check optional packages
    missing_optional = []
    for pip_name, module_name in optional.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_optional.append(pip_name)

    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False

    if missing_optional:
        logger.warning(f"Optional packages not installed: {', '.join(missing_optional)}")
        logger.warning("System will use JSON fallback for persistence")

    logger.info("[OK] All required dependencies installed")
    return True


def check_database():
    """Check database connectivity"""
    logger.info("Checking database...")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='network_analysis',
            connect_timeout=3
        )
        conn.close()
        logger.info("[OK] Database connection successful")
        return True
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Database will need initialization")
        return False


def initialize_database():
    """Initialize database using init_db.py"""
    logger.info("="*60)
    logger.info("Initializing database...")
    logger.info("="*60)

    init_script = project_root / 'scripts' / 'init_db.py'

    if not init_script.exists():
        logger.error(f"init_db.py not found at {init_script}")
        return False

    try:
        # Run init_db.py
        result = subprocess.run(
            [sys.executable, str(init_script)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("[OK] Database initialized successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error("Database initialization failed")
            logger.error(result.stderr)
            return False

    except Exception as e:
        logger.error(f"Failed to run database initialization: {e}")
        return False


def generate_synthetic_data(num_apps=140):
    """Generate synthetic flow data"""
    logger.info("="*60)
    logger.info(f"Generating synthetic data for {num_apps} applications...")
    logger.info("="*60)

    try:
        from scripts.generate_synthetic_flows import main as gen_main

        # Call the generator
        sys.argv = ['generate_synthetic_flows.py', '--num-apps', str(num_apps)]
        gen_main()

        logger.info(f"[OK] Generated data for {num_apps} applications")
        return True

    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        return False


def start_system(web=True, port=5000, incremental=True, debug=False):
    """Start the analysis system"""
    logger.info("="*60)
    logger.info("Starting Network Segmentation Analyzer...")
    logger.info("="*60)

    start_script = project_root / 'start_system.py'

    if not start_script.exists():
        logger.error(f"start_system.py not found at {start_script}")
        return False

    try:
        # Build command
        cmd = [sys.executable, str(start_script)]

        if web:
            cmd.append('--web')

        if incremental:
            cmd.append('--incremental')

        if port != 5000:
            cmd.extend(['--port', str(port)])

        if debug:
            cmd.append('--debug')

        # Skip cleanup since quick_start.py already did it
        cmd.append('--skip-cleanup')

        logger.info(f"Running: {' '.join(cmd)}")
        logger.info("")
        logger.info("="*60)
        logger.info("System starting... Press Ctrl+C to stop")
        logger.info("="*60)

        # Run start_system.py (this will block)
        subprocess.run(cmd)

        return True

    except KeyboardInterrupt:
        logger.info("\n[STOP] System stopped by user")
        return True
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Quick Start - Network Segmentation Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick start with all features
  python scripts/quick_start.py --generate-data 140 --web

  # Start web UI only (with existing data)
  python scripts/quick_start.py --web --skip-db-init --skip-data-gen

  # Initialize database only
  python scripts/quick_start.py --skip-data-gen --skip-system

  # Custom port
  python scripts/quick_start.py --web --port 8080
        """
    )

    parser.add_argument('--generate-data', type=int, metavar='N',
                        help='Generate synthetic data for N applications (default: skip)')
    parser.add_argument('--web', action='store_true',
                        help='Start web UI (default: True)')
    parser.add_argument('--no-web', action='store_true',
                        help='Do not start web UI')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web UI port (default: 5000)')
    parser.add_argument('--incremental', action='store_true', default=True,
                        help='Enable incremental learning (default: True)')
    parser.add_argument('--no-incremental', action='store_true',
                        help='Disable incremental learning')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--skip-db-init', action='store_true',
                        help='Skip database initialization')
    parser.add_argument('--skip-data-gen', action='store_true',
                        help='Skip synthetic data generation')
    parser.add_argument('--skip-system', action='store_true',
                        help='Skip starting the system (useful for setup only)')

    args = parser.parse_args()

    # Determine options
    start_web = not args.no_web if not args.no_web else args.web
    use_incremental = not args.no_incremental if not args.no_incremental else args.incremental

    logger.info("="*60)
    logger.info("NETWORK SEGMENTATION ANALYZER - QUICK START")
    logger.info("="*60)
    logger.info("")

    # Step 0: Clean up previous run (start fresh)
    cleanup_previous_run()

    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 2: Check dependencies
    if not check_dependencies():
        logger.error("Please install dependencies first:")
        logger.error("  pip install -r requirements.txt")
        sys.exit(1)

    # Step 3: Check/initialize database
    if not args.skip_db_init:
        db_ok = check_database()

        if not db_ok:
            logger.info("")
            logger.info("Database not found or not accessible")

            # Check if psycopg2 is available
            try:
                import psycopg2
                logger.info("Attempting to initialize database...")
                if not initialize_database():
                    logger.warning("Database initialization failed - will use JSON fallback")
                    logger.info("System will continue with JSON file storage")
            except ImportError:
                logger.warning("PostgreSQL not available - using JSON file storage")
                logger.info("This is normal and the system will work fine!")
    else:
        logger.info("Skipping database initialization (--skip-db-init)")

    # Step 4: Generate synthetic data (if requested)
    if args.generate_data and not args.skip_data_gen:
        logger.info("")
        if not generate_synthetic_data(args.generate_data):
            logger.error("Data generation failed")
            sys.exit(1)
    elif args.skip_data_gen:
        logger.info("Skipping data generation (--skip-data-gen)")

    # Step 5: Start system
    if not args.skip_system:
        logger.info("")
        if not start_system(
            web=start_web,
            port=args.port,
            incremental=use_incremental,
            debug=args.debug
        ):
            logger.error("System failed to start")
            sys.exit(1)
    else:
        logger.info("Skipping system start (--skip-system)")
        logger.info("")
        logger.info("="*60)
        logger.info("Setup complete!")
        logger.info("="*60)
        logger.info("To start the system manually:")
        logger.info("  python start_system.py --web --incremental")

    logger.info("")
    logger.info("Done!")


if __name__ == '__main__':
    main()
