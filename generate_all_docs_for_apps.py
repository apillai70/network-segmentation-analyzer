#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Document Generator - Generate ALL Document Types for Apps
==================================================================
Generates all 4 document types for specified applications or ALL applications.

Document Types Generated:
1. Architecture Document ({APP}_architecture.docx)
2. Solution Design Document (Solution_Design-{APP}.docx)
3. Network Segmentation Document (NetSeg-{APP}.docx)
4. Threat Surface Document (ThreatSurface-{APP}.docx)

Usage:
    # Generate all docs for specific apps
    python generate_all_docs_for_apps.py ACDA ALE AODSVY

    # Generate all docs for ALL apps
    python generate_all_docs_for_apps.py --all

    # Generate specific doc types for specific apps
    python generate_all_docs_for_apps.py ACDA --types architecture threat

Output:
    outputs_final/word_reports/architecture/
    outputs_final/word_reports/netseg/
    outputs_final/word_reports/threat_surface/
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def load_topology_data():
    """Load application topology data"""
    topology_file = Path('outputs_final/incremental_topology.json')

    if not topology_file.exists():
        # Try alternate location
        topology_file = Path('persistent_data/master_topology.json')

    if not topology_file.exists():
        print("ERROR: Topology file not found")
        print("Please run analysis pipeline first or build master topology:")
        print("  python start_system.py")
        print("  or")
        print("  python build_master_topology.py")
        return {}

    try:
        with open(topology_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        topology = data.get('topology', {})
        return topology

    except Exception as e:
        print(f"ERROR loading topology data: {e}")
        return {}


def validate_app_codes(app_codes):
    """
    Validate app codes against topology data

    Args:
        app_codes: List of app codes to validate

    Returns:
        Tuple of (valid_apps, invalid_apps)
    """
    topology = load_topology_data()
    if not topology:
        return [], app_codes

    topology_apps = set(topology.keys())
    requested_apps = set(app_codes)

    valid_apps = sorted(list(topology_apps & requested_apps))
    invalid_apps = sorted(list(requested_apps - topology_apps))

    return valid_apps, invalid_apps


def run_generator(script_name, app_names):
    """Run a document generator script for specified apps"""
    cmd = [sys.executable, script_name] + app_names

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout (increased from 10 minutes)
        )

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", f"ERROR: Process timed out after 30 minutes (processing {len(app_names)} apps)"
    except Exception as e:
        return False, "", f"ERROR: {e}"


def print_header(text):
    """Print formatted header"""
    print()
    print("="*80)
    print(text)
    print("="*80)
    print()


def print_section(text):
    """Print formatted section header"""
    print()
    print("-"*80)
    print(text)
    print("-"*80)


def main():
    start_time = datetime.now()

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_all_docs_for_apps.py <APP_NAME> [APP_NAME2 ...] [--all] [--types TYPE1 TYPE2 ...]")
        print()
        print("Examples:")
        print("  python generate_all_docs_for_apps.py ACDA ALE")
        print("  python generate_all_docs_for_apps.py --all")
        print("  python generate_all_docs_for_apps.py ACDA --types architecture threat")
        print()
        print("Available types: architecture, solution, netseg, threat")
        sys.exit(1)

    args = sys.argv[1:]

    # Check for --all flag
    generate_all = '--all' in args
    if generate_all:
        args.remove('--all')

    # Check for --types flag
    selected_types = None
    if '--types' in args:
        types_idx = args.index('--types')
        # Get all args after --types until end or next flag
        selected_types = []
        for i in range(types_idx + 1, len(args)):
            if args[i].startswith('--'):
                break
            selected_types.append(args[i])

        # Remove --types and its values from args
        args = args[:types_idx]

    # Get app names
    if generate_all:
        # Load all apps from topology
        topology = load_topology_data()
        if not topology:
            print("ERROR: No topology data available")
            sys.exit(1)
        app_names = sorted(topology.keys())
        print(f"Found {len(app_names)} applications in topology")
    else:
        app_names = args

    if not app_names:
        print("ERROR: No applications specified")
        sys.exit(1)

    # Validate app codes against topology
    valid_apps, invalid_apps = validate_app_codes(app_names)

    if invalid_apps:
        print()
        print(f"[WARNING] {len(invalid_apps)} apps not found in topology (will be skipped):")
        for i in range(0, len(invalid_apps), 10):
            chunk = invalid_apps[i:i+10]
            print(f"  {' '.join(chunk)}")
        print()

    if not valid_apps:
        print("ERROR: No valid applications found in topology")
        print()
        print("Run this to see available apps:")
        print("  python validate_app_codes.py")
        sys.exit(1)

    # Use only valid apps
    app_names = valid_apps

    print_header("MASTER DOCUMENT GENERATOR")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Applications: {len(app_names)}")
    print(f"Apps: {', '.join(app_names[:10])}" + ("..." if len(app_names) > 10 else ""))

    if selected_types:
        print(f"Document Types: {', '.join(selected_types)}")
    else:
        print("Document Types: ALL (architecture, solution, netseg, threat)")

    # Define document generators
    doc_generators = {
        'architecture': {
            'script': 'generate_architecture_single.py',
            'name': 'Architecture Documents',
            'output': 'outputs_final/word_reports/architecture/{APP}_architecture.docx'
        },
        'solution': {
            'script': 'generate_solution_design_single.py',
            'name': 'Solution Design Documents',
            'output': 'outputs_final/word_reports/architecture/Solution_Design-{APP}.docx'
        },
        'netseg': {
            'script': 'generate_network_segmentation_single.py',
            'name': 'Network Segmentation Documents',
            'output': 'outputs_final/word_reports/netseg/NetSeg-{APP}.docx'
        },
        'threat': {
            'script': 'generate_threat_surface_single.py',
            'name': 'Threat Surface Documents',
            'output': 'outputs_final/word_reports/threat_surface/ThreatSurface-{APP}.docx'
        }
    }

    # Filter generators if specific types selected
    if selected_types:
        doc_generators = {k: v for k, v in doc_generators.items() if k in selected_types}

    # Track results
    results = {key: {'success': 0, 'failed': 0} for key in doc_generators.keys()}
    total_docs = 0
    total_success = 0
    total_failed = 0

    # Generate each document type
    for doc_type, config in doc_generators.items():
        print_section(f"GENERATING: {config['name']}")
        print(f"Script: {config['script']}")
        print(f"Processing {len(app_names)} applications...")
        print()

        success, stdout, stderr = run_generator(config['script'], app_names)

        # Print output
        if stdout:
            print(stdout)

        # Always print stderr if present (not just on failure)
        if stderr:
            if not success:
                print("ERRORS:")
            else:
                print("WARNINGS/INFO:")
            print(stderr)

        # Count successes from output
        if success:
            # Count [OK] markers in output
            success_count = stdout.count('[OK]')
            failed_count = stdout.count('[ERROR]') + stdout.count('[WARNING]')

            results[doc_type]['success'] = success_count
            results[doc_type]['failed'] = len(app_names) - success_count

            total_docs += len(app_names)
            total_success += success_count
            total_failed += (len(app_names) - success_count)

            print(f"[OK] Completed: {success_count} successful, {len(app_names) - success_count} failed/skipped")
        else:
            results[doc_type]['failed'] = len(app_names)
            total_docs += len(app_names)
            total_failed += len(app_names)
            print(f"[ERROR] Failed: Error running generator")

    # Final summary
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print_header("GENERATION COMPLETE")

    print("Document Type Summary:")
    print()
    for doc_type, config in doc_generators.items():
        success = results[doc_type]['success']
        failed = results[doc_type]['failed']
        total = success + failed
        print(f"  {config['name']}:")
        print(f"    Success: {success}/{total}")
        print(f"    Failed:  {failed}/{total}")
        print()

    print(f"Overall Statistics:")
    print(f"  Total Documents Attempted: {total_docs}")
    print(f"  Total Successful:          {total_success}")
    print(f"  Total Failed/Skipped:      {total_failed}")
    print(f"  Success Rate:              {(total_success/total_docs*100):.1f}%")
    print()
    print(f"Time Elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print()
    print("Output Locations:")
    print("  Architecture:        outputs_final/word_reports/architecture/")
    print("  Solution Design:     outputs_final/word_reports/architecture/")
    print("  Network Segmentation: outputs_final/word_reports/netseg/")
    print("  Threat Surface:      outputs_final/word_reports/threat_surface/")
    print()
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
