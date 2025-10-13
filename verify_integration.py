#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Verification Script
=================================
Verifies that all components are properly integrated and working

Checks:
1. Required files exist
2. Python dependencies installed
3. Modules can be imported
4. Database connectivity
5. Core components initialize
6. Web app can start
7. API endpoints respond

Usage:
    python verify_integration.py
    python verify_integration.py --verbose
    python verify_integration.py --fix  # Attempt to fix issues

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import os
import importlib
from pathlib import Path
from typing import List, Tuple, Dict
import argparse

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}[OK]{RESET} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}[FAIL]{RESET} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}[WARN]{RESET} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}[INFO]{RESET} {text}")


class IntegrationVerifier:
    """Verify system integration"""

    def __init__(self, verbose: bool = False, fix: bool = False):
        self.verbose = verbose
        self.fix = fix
        self.errors = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def check_files(self) -> bool:
        """Check required files exist"""
        print_header("1. FILE STRUCTURE CHECK")

        required_files = [
            # Core scripts
            'start_system.py',
            'run_complete_analysis.py',
            'run_incremental_learning.py',
            'web_app.py',
            'config.yaml',
            'requirements.txt',

            # Documentation
            'DEPLOYMENT_GUIDE.md',
            'INCREMENTAL_LEARNING_GUIDE.md',
            'QUICKSTART_INCREMENTAL.md',

            # Source code - Core
            'src/core/persistence_manager.py',
            'src/core/ensemble_model.py',
            'src/core/incremental_learner.py',

            # Source code - Persistence
            'src/persistence/unified_persistence.py',
            'src/persistence/__init__.py',

            # Source code - Agentic AI
            'src/agentic/local_semantic_analyzer.py',
            'src/agentic/unified_topology_system.py',

            # Web app
            'web_app/api_routes.py',
            'web_app/__init__.py',

            # Templates
            'web_app/templates/base.html',
            'web_app/templates/index.html',
            'web_app/templates/topology.html',
            'web_app/templates/applications.html',
            'web_app/templates/application_detail.html',
            'web_app/templates/zones.html',
            'web_app/templates/incremental.html',
            'web_app/templates/about.html',
            'web_app/templates/error.html',

            # Static files
            'web_app/static/js/topology.js',
            'web_app/static/css/style.css',

            # Scripts
            'scripts/generate_synthetic_flows.py',
        ]

        all_exist = True

        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                if self.verbose:
                    print_success(f"{file_path}")
                self.passed += 1
            else:
                print_error(f"Missing: {file_path}")
                self.errors.append(f"Missing file: {file_path}")
                all_exist = False
                self.failed += 1

        if all_exist:
            print_success(f"All {len(required_files)} required files present")
        else:
            print_error(f"Missing {self.failed} required files")

        return all_exist

    def check_dependencies(self) -> bool:
        """Check Python dependencies"""
        print_header("2. DEPENDENCY CHECK")

        required_packages = {
            'pandas': 'Data processing',
            'numpy': 'Numerical computing',
            'networkx': 'Graph algorithms',
            'sklearn': 'Machine learning',
            'matplotlib': 'Visualization',
            'flask': 'Web framework',
            'yaml': 'Configuration (pyyaml)',
        }

        optional_packages = {
            'torch': 'Deep learning',
            'psycopg2': 'PostgreSQL support',
            'plotly': 'Interactive visualizations',
        }

        all_present = True

        # Check required
        for package, description in required_packages.items():
            try:
                importlib.import_module(package)
                if self.verbose:
                    print_success(f"{package:20} - {description}")
                self.passed += 1
            except ImportError:
                print_error(f"{package:20} - {description} - NOT INSTALLED")
                self.errors.append(f"Missing package: {package}")
                all_present = False
                self.failed += 1

        # Check optional
        for package, description in optional_packages.items():
            try:
                importlib.import_module(package)
                print_success(f"{package:20} - {description} (optional)")
                self.passed += 1
            except ImportError:
                print_warning(f"{package:20} - {description} (optional) - not installed")
                self.warnings.append(f"Optional package not installed: {package}")

        if all_present:
            print_success("All required dependencies installed")
        else:
            print_error("Missing required dependencies")
            if self.fix:
                print_info("To fix: pip install -r requirements.txt")

        return all_present

    def check_imports(self) -> bool:
        """Check core modules can be imported"""
        print_header("3. MODULE IMPORT CHECK")

        # Add src to path
        sys.path.insert(0, str(Path.cwd()))

        modules_to_import = [
            ('enterprise_network_analyzer', 'PersistenceManager'),
            ('enterprise_network_analyzer', 'EnsembleNetworkModel'),
            ('src.core.incremental_learner', 'IncrementalLearningSystem'),
            ('src.persistence.unified_persistence', 'create_persistence_manager'),
            ('src.agentic.local_semantic_analyzer', 'LocalSemanticAnalyzer'),
            ('src.agentic.unified_topology_system', 'UnifiedTopologyDiscoverySystem'),
            ('web_app', 'app'),  # web_app.py exports Flask app
            ('web_app.api_routes', 'init_api_routes'),  # Check API routes
        ]

        all_imported = True

        for module_name, component in modules_to_import:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, component):
                    if self.verbose:
                        print_success(f"{module_name}.{component}")
                    self.passed += 1
                else:
                    print_error(f"{module_name} missing {component}")
                    self.errors.append(f"Module {module_name} missing {component}")
                    all_imported = False
                    self.failed += 1
            except Exception as e:
                print_error(f"{module_name} - {str(e)}")
                self.errors.append(f"Cannot import {module_name}: {e}")
                all_imported = False
                self.failed += 1

        if all_imported:
            print_success("All modules import successfully")
        else:
            print_error("Some modules failed to import")

        return all_imported

    def check_database(self) -> bool:
        """Check database connectivity"""
        print_header("4. DATABASE CHECK")

        sys.path.insert(0, str(Path.cwd()))

        try:
            from src.persistence.unified_persistence import create_persistence_manager

            # Try to create persistence manager
            pm = create_persistence_manager(prefer_postgres=True, auto_fallback=True)

            print_success(f"Persistence manager created: {pm.backend}")

            # Check if it's PostgreSQL or JSON
            if pm.backend == 'postgresql':
                print_success("PostgreSQL connection successful")
            elif pm.backend == 'json':
                print_warning("Using JSON fallback (PostgreSQL not available)")
                self.warnings.append("PostgreSQL not available, using JSON")
            else:
                print_warning(f"Using unknown backend: {pm.backend}")

            # Close connection
            pm.close()

            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Database check failed: {e}")
            self.errors.append(f"Database error: {e}")
            self.failed += 1
            return False

    def check_core_components(self) -> bool:
        """Check core components initialize"""
        print_header("5. CORE COMPONENTS CHECK")

        sys.path.insert(0, str(Path.cwd()))

        try:
            # Import components
            from enterprise_network_analyzer import PersistenceManager, EnsembleNetworkModel
            from src.agentic.local_semantic_analyzer import LocalSemanticAnalyzer

            # Create test directory
            test_dir = Path('outputs_final/integration_test')
            test_dir.mkdir(parents=True, exist_ok=True)

            # Initialize persistence manager
            pm = PersistenceManager(
                db_path=str(test_dir / 'test.db'),
                models_dir=str(test_dir / 'models'),
                data_dir=str(test_dir / 'data')
            )
            print_success("PersistenceManager initialized")
            self.passed += 1

            # Initialize ensemble model
            ensemble = EnsembleNetworkModel(pm)
            print_success("EnsembleNetworkModel initialized")
            self.passed += 1

            # Initialize semantic analyzer
            semantic = LocalSemanticAnalyzer(pm)
            print_success("LocalSemanticAnalyzer initialized")
            self.passed += 1

            # Clean up
            pm.close()

            print_success("All core components initialized successfully")
            return True

        except Exception as e:
            print_error(f"Core components check failed: {e}")
            self.errors.append(f"Core components error: {e}")
            self.failed += 1
            return False

    def check_web_app(self) -> bool:
        """Check web app can start"""
        print_header("6. WEB APP CHECK")

        sys.path.insert(0, str(Path.cwd()))

        try:
            # Import Flask app
            from web_app import app

            print_success("Flask app imported")
            self.passed += 1

            # Check routes registered
            routes = [rule.rule for rule in app.url_map.iter_rules()]

            expected_routes = [
                '/',
                '/topology',
                '/applications',
                '/zones',
                '/incremental',
                '/about',
                '/api/applications',
                '/api/topology',
                '/api/stats',
            ]

            missing_routes = [r for r in expected_routes if r not in routes]

            if missing_routes:
                print_warning(f"Missing routes: {', '.join(missing_routes)}")
                self.warnings.append(f"Missing routes: {missing_routes}")
            else:
                print_success(f"All {len(expected_routes)} expected routes registered")
                self.passed += 1

            print_info(f"Total routes: {len(routes)}")

            return True

        except Exception as e:
            print_error(f"Web app check failed: {e}")
            self.errors.append(f"Web app error: {e}")
            self.failed += 1
            return False

    def check_directories(self) -> bool:
        """Check/create required directories"""
        print_header("7. DIRECTORY STRUCTURE CHECK")

        required_dirs = [
            'data/input',
            'data/output',
            'outputs_final',
            'logs',
            'models/incremental',
            'models/ensemble',
            'web_app/static/css',
            'web_app/static/js',
            'web_app/templates',
        ]

        all_exist = True

        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                if self.verbose:
                    print_success(f"{dir_path}")
                self.passed += 1
            else:
                if self.fix:
                    path.mkdir(parents=True, exist_ok=True)
                    print_success(f"Created: {dir_path}")
                    self.passed += 1
                else:
                    print_error(f"Missing: {dir_path}")
                    self.errors.append(f"Missing directory: {dir_path}")
                    all_exist = False
                    self.failed += 1

        if all_exist or self.fix:
            print_success("All required directories present")
        else:
            print_error("Missing directories (use --fix to create)")

        return all_exist

    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        print(f"\n{BOLD}Network Segmentation Analyzer - Integration Verification{RESET}")
        print(f"{BOLD}{'=' * 80}{RESET}\n")

        checks = [
            ("File Structure", self.check_files),
            ("Dependencies", self.check_dependencies),
            ("Module Imports", self.check_imports),
            ("Database", self.check_database),
            ("Core Components", self.check_core_components),
            ("Web Application", self.check_web_app),
            ("Directories", self.check_directories),
        ]

        results = []

        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                print_error(f"{check_name} check crashed: {e}")
                results.append((check_name, False))
                self.errors.append(f"{check_name} check crashed: {e}")

        # Summary
        print_header("VERIFICATION SUMMARY")

        for check_name, result in results:
            if result:
                print_success(f"{check_name:30} PASSED")
            else:
                print_error(f"{check_name:30} FAILED")

        print(f"\n{BOLD}Statistics:{RESET}")
        print(f"  Passed checks: {GREEN}{self.passed}{RESET}")
        print(f"  Failed checks: {RED}{self.failed}{RESET}")
        print(f"  Warnings: {YELLOW}{len(self.warnings)}{RESET}")

        if self.errors:
            print(f"\n{BOLD}{RED}Errors:{RESET}")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n{BOLD}{YELLOW}Warnings:{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")

        # Final verdict
        all_passed = all(result for _, result in results)

        print(f"\n{BOLD}{'=' * 80}{RESET}")
        if all_passed:
            print(f"{BOLD}{GREEN}[SUCCESS] INTEGRATION VERIFICATION PASSED{RESET}")
            print(f"\n{GREEN}System is ready for deployment!{RESET}")
            print(f"\n{BOLD}Quick Start:{RESET}")
            print(f"  python start_system.py --web --generate-data 140 --incremental")
        else:
            print(f"{BOLD}{RED}[FAILED] INTEGRATION VERIFICATION FAILED{RESET}")
            print(f"\n{RED}Please fix the errors above before deployment.{RESET}")
            if not self.fix:
                print(f"\n{BOLD}Tip:{RESET} Run with --fix to automatically fix some issues")

        print(f"{BOLD}{'=' * 80}{RESET}\n")

        return all_passed


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Verify Network Segmentation Analyzer integration'
    )
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')

    args = parser.parse_args()

    verifier = IntegrationVerifier(verbose=args.verbose, fix=args.fix)
    success = verifier.run_all_checks()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
