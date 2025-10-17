#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start Script - Web Application
=====================================
Launch the Network Segmentation Analyzer web interface

Usage:
    python run_web_app.py                    # Default: localhost:5000
    python run_web_app.py --port 8080        # Custom port
    python run_web_app.py --debug            # Debug mode
    python run_web_app.py --postgres         # Force PostgreSQL (no fallback)

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []

    try:
        import flask
    except ImportError:
        missing.append('flask')

    try:
        import pandas
    except ImportError:
        missing.append('pandas')

    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False

    # Check optional dependencies
    try:
        import psycopg2
        logger.info("[OK] PostgreSQL support available (psycopg2)")
    except ImportError:
        logger.warning("PostgreSQL support not available (will use JSON fallback)")
        logger.warning("Install with: pip install psycopg2-binary")

    return True


def setup_directories():
    """Create necessary directories"""
    directories = [
        'persistent_data',
        'persistent_data/applications',
        'persistent_data/flows',
        'persistent_data/analysis',
        'persistent_data/topology',
        'persistent_data/models',
        'logs',
        'web_app/templates',
        'web_app/static',
        'web_app/static/js',
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    logger.info("[OK] Directories initialized")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Network Segmentation Analyzer - Web Interface'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--postgres',
        action='store_true',
        help='Force PostgreSQL (no JSON fallback)'
    )
    parser.add_argument(
        '--postgres-host',
        help='PostgreSQL host'
    )
    parser.add_argument(
        '--postgres-port',
        type=int,
        help='PostgreSQL port'
    )
    parser.add_argument(
        '--postgres-db',
        help='PostgreSQL database'
    )
    parser.add_argument(
        '--postgres-user',
        help='PostgreSQL user'
    )
    parser.add_argument(
        '--postgres-password',
        help='PostgreSQL password'
    )

    args = parser.parse_args()

    # Print banner
    print()
    print("=" * 80)
    print("Network Segmentation Analyzer v3.0")
    print("Web Interface")
    print("=" * 80)
    print()

    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)

    # Setup directories
    logger.info("Setting up directories...")
    setup_directories()

    # Import web app
    logger.info("Loading web application...")
    try:
        from web_app import app, pm

        # Update PostgreSQL config if provided
        if any([args.postgres_host, args.postgres_port, args.postgres_db,
                args.postgres_user, args.postgres_password]):
            logger.info("Updating PostgreSQL configuration...")

            from src.persistence.unified_persistence import create_persistence_manager

            postgres_config = {
                'host': args.postgres_host or 'localhost',
                'port': args.postgres_port or 5432,
                'database': args.postgres_db or 'network_segmentation',
                'user': args.postgres_user or 'postgres',
                'password': args.postgres_password or 'postgres'
            }

            # Recreate persistence manager with custom config
            pm = create_persistence_manager(
                postgres_config=postgres_config,
                prefer_postgres=True,
                auto_fallback=not args.postgres
            )

            # Update app's pm
            from web_app import api_routes
            api_routes.pm = pm

    except ImportError as e:
        logger.error(f"Failed to import web application: {e}")
        logger.error("Make sure all files are in place:")
        logger.error("  - web_app.py")
        logger.error("  - web_app/api_routes.py")
        logger.error("  - web_app/templates/")
        logger.error("  - src/persistence/unified_persistence.py")
        sys.exit(1)

    # Print configuration
    print()
    print("Configuration:")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Debug: {args.debug}")
    print(f"  Backend: {pm.backend}")
    print(f"  Auto-fallback: {pm.auto_fallback}")
    print()
    print("=" * 80)
    print(f"Server starting at: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
    print("=" * 80)
    print()
    print("Press Ctrl+C to stop")
    print()

    # Run server
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.debug
        )
    except KeyboardInterrupt:
        print()
        logger.info("Shutting down gracefully...")
        pm.close()
        logger.info("Goodbye!")
    except Exception as e:
        logger.error(f"Server error: {e}")
        pm.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
