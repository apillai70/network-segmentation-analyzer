#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Document Generator - Discovers and validates all apps automatically
========================================================================
This script automatically:
1. Scans for all App_Code_*.csv files
2. Validates against topology
3. Generates documents for all valid apps

Usage:
    python generate_docs_auto.py --types threat
    python generate_docs_auto.py --types architecture solution netseg threat
    python generate_docs_auto.py  # Generates ALL document types
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import re
import argparse

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def discover_app_codes():
    """Discover all app codes from CSV files"""
    processed_dir = Path('data/input/processed')

    if not processed_dir.exists():
        print(f"ERROR: Directory not found: {processed_dir}")
        return []

    pattern = re.compile(r'^App_Code_([A-Za-z0-9_-]+)\.csv$', re.IGNORECASE)
    app_codes = []

    for file_path in processed_dir.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)
            if match:
                app_codes.append(match.group(1))

    return sorted(app_codes)


def load_topology():
    """Load topology data - always prefer master_topology.json"""
    # Check master_topology.json FIRST (most complete)
    topology_file = Path('persistent_data/master_topology.json')

    if not topology_file.exists():
        # Fall back to incremental topology (may be incomplete)
        topology_file = Path('outputs_final/incremental_topology.json')

    if not topology_file.exists():
        return {}

    try:
        with open(topology_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('topology', {})
    except Exception as e:
        print(f"ERROR loading topology: {e}")
        return {}


def validate_apps(app_codes, topology):
    """Validate app codes against topology"""
    topology_apps = set(topology.keys())
    requested_apps = set(app_codes)

    valid_apps = sorted(list(topology_apps & requested_apps))
    invalid_apps = sorted(list(requested_apps - topology_apps))

    return valid_apps, invalid_apps


def main():
    parser = argparse.ArgumentParser(description='Auto-generate documents for all valid apps')
    parser.add_argument('--types', nargs='+',
                       choices=['architecture', 'solution', 'netseg', 'threat'],
                       help='Document types to generate (default: all)')

    args = parser.parse_args()

    print("="*80)
    print("AUTO DOCUMENT GENERATOR")
    print("="*80)
    print()

    # Step 1: Discover all app codes from files
    print("[1/5] Discovering app codes from CSV files...")
    discovered_apps = discover_app_codes()
    print(f"      Found {len(discovered_apps)} CSV files")
    print()

    if not discovered_apps:
        print("ERROR: No App_Code_*.csv files found in data/input/processed/")
        sys.exit(1)

    # Step 2: Load topology
    print("[2/5] Loading topology data...")
    topology = load_topology()
    print(f"      Loaded {len(topology)} apps from topology")
    print()

    if not topology:
        print("ERROR: No topology data available")
        sys.exit(1)

    # Step 3: Validate apps
    print("[3/5] Validating apps...")
    valid_apps, invalid_apps = validate_apps(discovered_apps, topology)
    print(f"      Valid apps: {len(valid_apps)}")
    print(f"      Invalid apps: {len(invalid_apps)} (will be skipped)")
    print()

    if invalid_apps:
        print(f"      Apps not in topology ({len(invalid_apps)}):")
        for i in range(0, len(invalid_apps), 10):
            chunk = invalid_apps[i:i+10]
            print(f"        {' '.join(chunk)}")
        print()

    if not valid_apps:
        print("ERROR: No valid apps found")
        sys.exit(1)

    # Step 4: Save valid apps to file
    print("[4/5] Saving valid apps to file...")
    valid_apps_file = Path('auto_valid_apps.txt')
    valid_apps_file.write_text(' '.join(valid_apps), encoding='utf-8')
    print(f"      Saved to: {valid_apps_file}")
    print()

    # Step 5: Generate documents
    print("[5/5] Generating documents...")
    print()

    # Determine which document types to generate
    if args.types:
        doc_types_list = args.types
        doc_types = ', '.join(args.types)
    else:
        doc_types_list = ['architecture', 'solution', 'netseg', 'threat']
        doc_types = 'ALL (architecture, solution, netseg, threat)'

    print(f"      Apps: {len(valid_apps)}")
    print(f"      Document types: {doc_types}")
    print()
    print("="*80)
    print("STARTING DOCUMENT GENERATION")
    print("="*80)
    print()

    # Map document types to their generator scripts
    generators = {
        'architecture': 'generate_architecture_single.py',
        'solution': 'generate_solution_design_single.py',
        'netseg': 'generate_network_segmentation_single.py',
        'threat': 'generate_threat_surface_single.py'
    }

    # Run each document type generator directly
    # Pass ALL apps from topology, not just validated ones
    # This ensures we generate docs for all apps that have topology data
    overall_success = True
    for doc_type in doc_types_list:
        if doc_type not in generators:
            print(f"[WARNING] Unknown document type: {doc_type}")
            continue

        script = generators[doc_type]
        print(f"\n{'='*80}")
        print(f"Generating {doc_type} documents...")
        print(f"{'='*80}\n")

        # Build command: python script.py APP1 APP2 APP3 ...
        # Use ALL apps from topology instead of just validated CSV apps
        topology_apps = sorted(topology.keys())
        cmd = [sys.executable, script] + topology_apps

        print(f"Generating {len(topology_apps)} documents from topology data...\n")

        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                overall_success = False
                print(f"\n[WARNING] {doc_type} generation had errors\n")
        except Exception as e:
            print(f"\n[ERROR] Failed to run {doc_type} generator: {e}\n")
            overall_success = False

    # Exit with appropriate code
    try:
        sys.exit(0 if overall_success else 1)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
