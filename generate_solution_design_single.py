#!/usr/bin/env python3
"""
Single Application Solution Design Document Generator
======================================================
Generates comprehensive solution design document for specific application(s).

Usage:
    python generate_solution_design_single.py ACDA
    python generate_solution_design_single.py ACDA ALE AODSVY

Output:
    outputs_final/word_reports/architecture/Solution_Design-{APP}.docx
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from comprehensive_solution_doc_generator import generate_comprehensive_solution_document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_topology_data():
    """Load application topology data"""
    # Check master_topology.json FIRST (most complete)
    topology_file = Path('persistent_data/master_topology.json')

    if not topology_file.exists():
        # Fall back to incremental topology
        topology_file = Path('outputs_final/incremental_topology.json')

    if not topology_file.exists():
        logger.error(f"Topology file not found")
        logger.info("Please run analysis pipeline first or build master topology:")
        logger.info("  python start_system.py")
        logger.info("  or")
        logger.info("  python build_master_topology.py")
        return {}

    try:
        with open(topology_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        topology = data.get('topology', {})
        logger.info(f"Loaded topology data from {topology_file.name}: {len(topology)} applications")
        return topology

    except Exception as e:
        logger.error(f"Error loading topology data: {e}")
        return {}


def find_diagrams(app_name, diagrams_dir):
    """Find PNG and Mermaid diagrams for application"""
    png_path = diagrams_dir / f"{app_name}_application_diagram.png"
    mermaid_path = diagrams_dir / f"{app_name}_application_diagram.mmd"

    # Fallback to regular diagram if application_diagram doesn't exist
    if not png_path.exists():
        png_path = diagrams_dir / f"{app_name}_diagram.png"
    if not mermaid_path.exists():
        mermaid_path = diagrams_dir / f"{app_name}_diagram.mmd"

    return (
        str(png_path) if png_path.exists() else None,
        str(mermaid_path) if mermaid_path.exists() else None
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_solution_design_single.py <APP_NAME> [APP_NAME2 ...]")
        print("Example: python generate_solution_design_single.py ACDA")
        print("Example: python generate_solution_design_single.py ACDA ALE AODSVY")
        sys.exit(1)

    app_names = sys.argv[1:]

    # Load topology data
    topology_data = load_topology_data()

    if not topology_data:
        logger.error("No topology data available. Exiting.")
        sys.exit(1)

    # Setup directories
    diagrams_dir = Path('outputs_final/diagrams')
    output_dir = Path('outputs_final/word_reports/architecture')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("SOLUTION DESIGN DOCUMENT GENERATOR (SINGLE APP MODE)")
    print("="*80)
    print()

    success_count = 0
    failed_count = 0
    skipped_count = 0

    # Process each application
    for app_name in app_names:
        if app_name not in topology_data:
            print(f"[WARNING] {app_name}: Not found in topology data")
            print(f"          Available apps: {', '.join(sorted(topology_data.keys())[:10])}...")
            skipped_count += 1
            continue

        # Find diagrams
        png_path, mermaid_path = find_diagrams(app_name, diagrams_dir)

        if not png_path and not mermaid_path:
            print(f"[WARNING] {app_name}: No diagrams found - skipping")
            skipped_count += 1
            continue

        # Output path
        output_path = output_dir / f"Solution_Design-{app_name}.docx"

        try:
            print(f"Generating: {app_name}...", end=' ', flush=True)

            # Generate document
            app_data = topology_data[app_name]
            generate_comprehensive_solution_document(
                app_name=app_name,
                app_data=app_data,
                png_path=png_path,
                mermaid_path=mermaid_path,
                output_path=str(output_path)
            )

            print("[OK]")
            print(f"   Output: {output_path}")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Error: {e}")
            logger.error(f"Failed to generate document for {app_name}: {e}")
            failed_count += 1

    # Summary
    print()
    print("="*80)
    print("COMPLETE")
    print("="*80)
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Output: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
