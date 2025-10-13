#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified System Startup Script
==============================
Orchestrates the complete Network Segmentation Analyzer system

Features:
- Dependency checking
- Database initialization (PostgreSQL or JSON fallback)
- Optional synthetic data generation
- Incremental learning (background)
- Web UI launch

Usage:
    # Full system with web UI
    python start_system.py --web

    # With synthetic data generation
    python start_system.py --web --generate-data 140

    # Incremental learning + web UI
    python start_system.py --web --incremental

    # Batch analysis only
    python start_system.py --batch

Author: Enterprise Security Team
Version: 3.0 - Unified System
"""

import sys
import os

# Force UTF-8 encoding for console output (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import argparse
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Setup logging (after UTF-8 fix)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/system_startup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 80)
    print("NETWORK SEGMENTATION ANALYZER v3.0")
    print("Complete Network + Application Topology Discovery")
    print("=" * 80)
    print("🔒 100% LOCAL PROCESSING - NO EXTERNAL APIs")
    print("🧠 Deep Learning + Agentic AI + Incremental Learning")
    print("=" * 80 + "\n")


def cleanup_previous_run():
    """Clean up previous run data to start fresh"""
    logger.info("🧹 Cleaning up previous run...")

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
    ]

    for item, item_type in cleanup_items:
        try:
            if item_type == 'glob':
                from pathlib import Path
                for file_path in Path('.').glob(item):
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"  ✓ Deleted {file_path}")
            elif item_type == 'file':
                file_path = Path(item)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"  ✓ Deleted {file_path}")
            elif item_type == 'dir':
                dir_path = Path(item)
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.info(f"  ✓ Deleted {dir_path}/")
        except Exception as e:
            logger.debug(f"  Skip: {item} ({e})")

    # Recreate essential directories
    essential_dirs = [
        'data/input', 'outputs_final', 'models/incremental',
        'models/ensemble', 'visualizations', 'logs'
    ]
    for dir_path in essential_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info("✓ Ready to start fresh\n")


def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("📦 Checking dependencies...")

    required_packages = [
        'pandas', 'numpy', 'networkx', 'sklearn',
        'matplotlib', 'flask', 'yaml'
    ]

    optional_packages = {
        'torch': 'Deep Learning (GAT, VAE, Transformer)',
        'psycopg2': 'PostgreSQL Support',
        'plotly': 'Interactive Visualizations'
    }

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            logger.warning(f"  ✗ {package} - REQUIRED")

    for package, description in optional_packages.items():
        try:
            __import__(package)
            logger.info(f"  ✓ {package} ({description})")
        except ImportError:
            logger.info(f"  ⚠ {package} - OPTIONAL ({description})")

    if missing:
        logger.error(f"\n❌ Missing required packages: {', '.join(missing)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False

    logger.info("✓ All required dependencies installed\n")
    return True


def initialize_directories():
    """Create necessary directories"""
    logger.info("📁 Initializing directories...")

    directories = [
        'data/input',
        'data/output',
        'outputs_final',
        'logs',
        'models/incremental',
        'models/ensemble',
        'web_app/static/css',
        'web_app/static/js',
        'web_app/templates'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {directory}")

    logger.info("✓ Directories ready\n")


def check_database():
    """Check database connectivity"""
    logger.info("💾 Checking database...")

    # Try PostgreSQL first
    try:
        import psycopg2
        # Try to connect (will use environment variables or defaults)
        # Not actually connecting here, just checking availability
        logger.info("  ✓ PostgreSQL driver available")
        logger.info("  ℹ Will attempt PostgreSQL connection at runtime")
        return 'postgresql'
    except ImportError:
        logger.info("  ⚠ PostgreSQL driver not installed")
        logger.info("  ✓ Will use JSON file-based persistence")
        return 'json'


def generate_synthetic_data(num_apps):
    """Generate synthetic flow files"""
    logger.info(f"🎲 Generating {num_apps} synthetic flow files...\n")

    try:
        result = subprocess.run(
            [sys.executable, 'scripts/generate_synthetic_flows.py', '--num-apps', str(num_apps)],
            check=True,
            capture_output=True,
            text=True
        )

        logger.info(result.stdout)
        logger.info("✓ Synthetic data generated\n")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to generate data: {e}")
        logger.error(e.stderr)
        return False


def run_batch_analysis(enable_all=False):
    """Run complete batch analysis"""
    logger.info("📊 Running batch analysis...\n")

    cmd = [sys.executable, 'run_complete_analysis.py']
    if enable_all:
        cmd.append('--enable-all')

    try:
        result = subprocess.run(cmd, check=True)
        logger.info("✓ Batch analysis complete\n")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Batch analysis failed: {e}")
        return False


def start_incremental_learning(continuous=True, enable_all=False):
    """Start incremental learning (background process)"""
    mode = "continuous" if continuous else "batch"
    logger.info(f"🔄 Starting incremental learning ({mode} mode)...\n")

    cmd = [sys.executable, 'run_incremental_learning.py']

    if continuous:
        cmd.append('--continuous')
    else:
        cmd.append('--batch')

    if enable_all:
        cmd.append('--enable-all')

    try:
        if continuous:
            # Start as background process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"✓ Incremental learning started (PID: {process.pid})")
            logger.info("  Check logs/incremental_*.log for details\n")
            return process
        else:
            # Run synchronously for batch mode
            result = subprocess.run(cmd, check=True)
            logger.info("✓ Incremental batch complete\n")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Incremental learning failed: {e}")
        return None


def start_web_ui(host='0.0.0.0', port=5000, debug=False):
    """Start Flask web UI"""
    logger.info(f"🌐 Starting web UI on http://{host}:{port}...\n")

    # Set environment variables for Flask
    os.environ['FLASK_APP'] = 'web_app.py'
    os.environ['FLASK_ENV'] = 'development' if debug else 'production'

    try:
        # Import Flask app directly from web_app.py file (not package)
        sys.path.insert(0, str(Path.cwd()))

        # Use importlib to avoid circular import with web_app/__init__.py
        import importlib.util
        web_app_path = Path.cwd() / 'web_app.py'

        if not web_app_path.exists():
            raise FileNotFoundError(f"web_app.py not found at {web_app_path}")

        spec = importlib.util.spec_from_file_location("web_app_module", web_app_path)
        web_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app_module)

        app = web_app_module.app

        if app is None:
            raise ValueError("Flask app object is None - web_app.py may have initialization errors")

        logger.info("=" * 80)
        logger.info("🚀 WEB UI STARTED")
        logger.info("=" * 80)
        logger.info(f"  URL: http://{host}:{port}")
        logger.info("  Dashboard: http://{host}:{port}/")
        logger.info(f"  Topology: http://{host}:{port}/topology")
        logger.info(f"  Applications: http://{host}:{port}/applications")
        logger.info("  Press Ctrl+C to stop")
        logger.info("=" * 80 + "\n")

        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        logger.error(f"❌ Failed to start web UI: {e}")
        logger.error("  Check if port is already in use")
        import traceback
        logger.error(traceback.format_exc())
        return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Unified Network Segmentation Analyzer System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full system with web UI
  python start_system.py --web

  # Generate data + incremental learning + web UI
  python start_system.py --web --incremental --generate-data 140

  # Batch analysis only
  python start_system.py --batch

  # Web UI on custom port
  python start_system.py --web --port 8080

  # Enable all features (deep learning)
  python start_system.py --web --incremental --enable-all
        """
    )

    parser.add_argument(
        '--web',
        action='store_true',
        help='Start web UI'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Run batch analysis'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Start incremental learning (continuous mode)'
    )

    parser.add_argument(
        '--generate-data',
        type=int,
        metavar='N',
        help='Generate N synthetic flow files'
    )

    parser.add_argument(
        '--enable-all',
        action='store_true',
        help='Enable all features (deep learning, graph algorithms, etc.)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web UI host (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Web UI port (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip dependency and database checks'
    )

    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup of previous run (used when called as subprocess)'
    )

    return parser.parse_args()


def main():
    """Main execution"""
    print_banner()

    args = parse_arguments()

    # If no mode specified, show help
    if not any([args.web, args.batch, args.incremental, args.generate_data]):
        logger.warning("⚠️  No operation mode specified")
        logger.info("Use --help to see available options")
        logger.info("\nQuick start: python start_system.py --web")
        return 1

    try:
        # Clean up previous run (start fresh) - unless skipped
        if not args.skip_cleanup:
            cleanup_previous_run()
        else:
            logger.info("⏭️  Skipping cleanup (--skip-cleanup flag set)\n")

        # Pre-flight checks
        if not args.skip_checks:
            if not check_dependencies():
                return 1

            initialize_directories()
            db_type = check_database()

            logger.info(f"ℹ️  Using {db_type.upper()} persistence\n")

        # Generate synthetic data if requested
        if args.generate_data:
            if not generate_synthetic_data(args.generate_data):
                logger.error("Failed to generate data, continuing anyway...")

        # Run batch analysis if requested
        if args.batch:
            if not run_batch_analysis(enable_all=args.enable_all):
                logger.error("Batch analysis failed")
                return 1

        # Start incremental learning if requested
        incremental_process = None
        if args.incremental:
            incremental_process = start_incremental_learning(
                continuous=True,
                enable_all=args.enable_all
            )

        # Start web UI if requested (blocks here)
        if args.web:
            try:
                start_web_ui(
                    host=args.host,
                    port=args.port,
                    debug=args.debug
                )
            except KeyboardInterrupt:
                logger.info("\n⚠️  Shutting down web UI...")
            finally:
                # Clean up incremental learning process if running
                if incremental_process:
                    logger.info("Stopping incremental learning...")
                    incremental_process.terminate()
                    incremental_process.wait(timeout=5)
                    logger.info("✓ Incremental learning stopped")

        logger.info("\n✨ System shutdown complete")
        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        return 0

    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
