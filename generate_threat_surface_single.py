#!/usr/bin/env python3
"""
Single Application Threat Surface Document Generator
=====================================================
Generates threat surface document for a specific application.

Usage:
    python generate_threat_surface_single.py ACDA
    python generate_threat_surface_single.py DNMET XECHK CMAR
"""

import sys
import json
from pathlib import Path
from src.threat_surface_netseg_generator import generate_threat_surface_document


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_threat_surface_single.py <APP_NAME> [APP_NAME2 ...]")
        print("Example: python generate_threat_surface_single.py ACDA")
        print("Example: python generate_threat_surface_single.py DNMET XECHK CMAR")
        sys.exit(1)

    app_names = sys.argv[1:]

    # Load topology data from persistent master topology
    topology_file = Path('persistent_data/master_topology.json')

    if not topology_file.exists():
        print(f"ERROR: Master topology file not found: {topology_file}")
        print("Building master topology from persistent data...")

        # Try to build it automatically
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, 'build_master_topology.py'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0 or not topology_file.exists():
                print("Failed to build master topology")
                print("Please run: python build_master_topology.py")
                sys.exit(1)

            print("Master topology built successfully\n")
        except Exception as e:
            print(f"Error building master topology: {e}")
            sys.exit(1)

    with open(topology_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    topology = data.get('topology', {})

    # Setup output directory
    output_dir = Path('outputs_final/word_reports/threat_surface')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("THREAT SURFACE DOCUMENT GENERATOR (SINGLE APP MODE)")
    print("="*80)
    print()

    # Generate documents for specified applications
    for app_name in app_names:
        if app_name not in topology:
            print(f"[WARNING]️  {app_name}: Not found in topology data")
            print(f"   Available apps: {', '.join(sorted(topology.keys())[:10])}...")
            continue

        try:
            print(f"Generating: {app_name}...", end=' ', flush=True)

            app_data = topology[app_name]
            output_path = output_dir / f'ThreatSurface-{app_name}.docx'

            generate_threat_surface_document(
                app_name=app_name,
                app_data=app_data,
                output_path=str(output_path)
            )

            print("[OK]")
            print(f"   Output: {output_path}")

        except Exception as e:
            print(f"[ERROR] Error: {e}")

    print()
    print("="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
