#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Application Verification Script
====================================
Verify that all web app components are properly installed

Usage:
    python verify_web_app.py

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print header text"""
    print()
    print(Colors.BOLD + "=" * 80 + Colors.ENDC)
    print(Colors.BOLD + text + Colors.ENDC)
    print(Colors.BOLD + "=" * 80 + Colors.ENDC)
    print()


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {text}")


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are installed"""
    print_header("Checking Python Dependencies")

    required = [
        ('flask', 'Flask web framework'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('networkx', 'Graph algorithms'),
    ]

    optional = [
        ('psycopg2', 'PostgreSQL support'),
        ('gunicorn', 'Production WSGI server'),
    ]

    missing = []
    all_ok = True

    # Check required
    for package, description in required:
        try:
            __import__(package)
            print_success(f"{package:20s} - {description}")
        except ImportError:
            print_error(f"{package:20s} - {description} (REQUIRED)")
            missing.append(package)
            all_ok = False

    print()

    # Check optional
    for package, description in optional:
        try:
            __import__(package)
            print_success(f"{package:20s} - {description} (optional)")
        except ImportError:
            print_warning(f"{package:20s} - {description} (optional, not installed)")

    return all_ok, missing


def check_files() -> bool:
    """Check if all required files exist"""
    print_header("Checking Files")

    required_files = [
        'web_app.py',
        'web_app/__init__.py',
        'web_app/api_routes.py',
        'web_app/templates/index.html',
        'web_app/templates/topology.html',
        'web_app/templates/base.html',
        'web_app/templates/error.html',
        'web_app/static/js/topology.js',
        'web_app/static/css/style.css',
        'src/persistence/__init__.py',
        'src/persistence/unified_persistence.py',
    ]

    all_ok = True

    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} (MISSING)")
            all_ok = False

    return all_ok


def check_directories() -> bool:
    """Check if required directories exist"""
    print_header("Checking Directories")

    required_dirs = [
        'web_app',
        'web_app/templates',
        'web_app/static',
        'web_app/static/js',
        'web_app/static/css',
        'src/persistence',
    ]

    all_ok = True

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.is_dir():
            print_success(f"{dir_path}/")
        else:
            print_error(f"{dir_path}/ (MISSING)")
            all_ok = False

    return all_ok


def check_persistence() -> bool:
    """Test persistence manager"""
    print_header("Testing Persistence Manager")

    try:
        from src.persistence.unified_persistence import create_persistence_manager

        # Try to create persistence manager
        pm = create_persistence_manager(prefer_postgres=False)

        print_success(f"Persistence manager created successfully")
        print_info(f"  Backend: {pm.backend}")
        print_info(f"  Auto-fallback: {pm.auto_fallback}")

        # Test basic operations
        stats = pm.get_statistics()
        print_success(f"Statistics retrieved: {stats}")

        pm.close()
        return True

    except Exception as e:
        print_error(f"Failed to initialize persistence manager: {e}")
        return False


def check_web_app() -> bool:
    """Test web application import"""
    print_header("Testing Web Application")

    try:
        # Test import
        import web_app

        print_success("Web app module imported successfully")

        # Check Flask app
        if hasattr(web_app, 'app'):
            print_success("Flask app instance found")
            print_info(f"  Name: {web_app.app.name}")
            print_info(f"  Template folder: {web_app.app.template_folder}")
            print_info(f"  Static folder: {web_app.app.static_folder}")
        else:
            print_error("Flask app instance not found")
            return False

        # Check API routes
        if hasattr(web_app, 'api_bp'):
            print_success("API blueprint registered")
        else:
            print_error("API blueprint not found")
            return False

        return True

    except Exception as e:
        print_error(f"Failed to import web app: {e}")
        return False


def check_api_routes() -> bool:
    """Test API routes"""
    print_header("Testing API Routes")

    try:
        from web_app.api_routes import init_api_routes
        from src.persistence.unified_persistence import create_persistence_manager

        pm = create_persistence_manager(prefer_postgres=False)
        api_bp = init_api_routes(pm)

        print_success("API routes initialized successfully")
        print_info(f"  Blueprint name: {api_bp.name}")
        print_info(f"  URL prefix: {api_bp.url_prefix}")

        # List routes
        print()
        print_info("Available API endpoints:")
        for rule in api_bp.deferred_functions:
            print(f"    - {rule}")

        pm.close()
        return True

    except Exception as e:
        print_error(f"Failed to initialize API routes: {e}")
        return False


def print_summary(results: dict):
    """Print verification summary"""
    print_header("Verification Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print()
    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[ERROR] FAIL"
        color = Colors.OKGREEN if result else Colors.FAIL
        print(f"  {color}{status}{Colors.ENDC} - {test_name}")

    print()
    print(f"Total: {total} tests")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print()

    if failed == 0:
        print_success("All verifications passed! You're ready to run the web app.")
        print()
        print_info("Next steps:")
        print("  1. Run: python web_app.py")
        print("  2. Or:  python run_web_app.py")
        print("  3. Open: http://localhost:5000")
        print()
    else:
        print_error("Some verifications failed. Please fix the issues above.")
        print()
        print_info("Common fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Install Flask: pip install flask")
        print("  3. Install optional deps: pip install psycopg2-binary gunicorn")
        print()


def main():
    """Main verification function"""
    print()
    print(Colors.BOLD + Colors.OKBLUE)
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║   Network Segmentation Analyzer v3.0 - Web App Verification          ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)

    results = {}

    # Run checks
    results['Dependencies'], missing = check_dependencies()
    results['Directories'] = check_directories()
    results['Files'] = check_files()
    results['Persistence Manager'] = check_persistence()
    results['Web Application'] = check_web_app()
    results['API Routes'] = check_api_routes()

    # Print summary
    print_summary(results)

    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
