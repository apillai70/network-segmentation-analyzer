#!/usr/bin/env python3
"""
Single Application Network Segmentation Document Generator
===========================================================
Generates network segmentation document for specific application(s).

Usage:
    python generate_network_segmentation_single.py ACDA
    python generate_network_segmentation_single.py ACDA ALE AODSVY

Output:
    outputs_final/word_reports/netseg/NetSeg-{APP}.docx
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from docx_generator import generate_solutions_document

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


def create_analysis_results_for_app(app_name, app_data):
    """Create analysis results structure for a single app"""

    # Extract dependencies
    dependencies = app_data.get('predicted_dependencies', [])

    # Build applications dictionary for this app
    applications = {
        app_name: {
            'app_type': app_data.get('app_type', 'unknown'),
            'tier': app_data.get('tier', 'Unknown'),
            'dependencies': [dep.get('name', 'Unknown') for dep in dependencies],
            'security_zone': app_data.get('security_zone', 'APP_TIER'),
            'risk_level': app_data.get('risk_level', 'MEDIUM'),
            'confidence': app_data.get('confidence', 0.0)
        }
    }

    # Create analysis results structure
    analysis_results = {
        'applications': applications,
        'total_flows': len(dependencies),
        'total_apps': 1,
        'zones_used': [app_data.get('security_zone', 'APP_TIER')],
        'analysis_timestamp': app_data.get('analysis_timestamp', 'N/A')
    }

    return analysis_results


def create_zones_for_app(app_data):
    """Create zones dictionary for a single app"""
    from collections import namedtuple

    Zone = namedtuple('Zone', ['zone_type', 'members', 'security_level', 'description'])

    security_zone = app_data.get('security_zone', 'APP_TIER')
    app_name = app_data.get('app_name', 'Unknown')

    zones = {
        security_zone: Zone(
            zone_type='Application Tier',
            members=[app_name],
            security_level=app_data.get('risk_level', 'MEDIUM'),
            description=f'Security zone for {app_name} application tier'
        )
    }

    return zones


def create_rules_for_app(app_name, app_data):
    """Create segmentation rules for a single app"""
    from collections import namedtuple

    SegmentationRule = namedtuple('SegmentationRule', [
        'priority', 'source', 'destination', 'protocol', 'port',
        'action', 'risk_score', 'justification'
    ])

    rules = []
    security_zone = app_data.get('security_zone', 'APP_TIER')
    dependencies = app_data.get('predicted_dependencies', [])

    # Create rules for each dependency
    for idx, dep in enumerate(dependencies[:10], 1):  # Limit to 10 rules
        dep_type = dep.get('type', 'unknown')
        dep_name = dep.get('name', 'dependency')

        if 'database' in dep_type.lower():
            port = '3306,5432,1521'
            protocol = 'TCP'
            risk_score = 'HIGH'
        elif 'cache' in dep_type.lower():
            port = '6379,11211'
            protocol = 'TCP'
            risk_score = 'MEDIUM'
        elif 'message' in dep_type.lower():
            port = '5672,9092'
            protocol = 'TCP'
            risk_score = 'MEDIUM'
        else:
            port = '443'
            protocol = 'TCP'
            risk_score = 'LOW'

        rule = SegmentationRule(
            priority=idx,
            source=f'{security_zone} ({app_name})',
            destination=f'DATA_TIER ({dep_name})',
            protocol=protocol,
            port=port,
            action='ALLOW',
            risk_score=risk_score,
            justification=f'Required for {app_name} to access {dep_type} service: {dep_name}'
        )
        rules.append(rule)

    return rules


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_network_segmentation_single.py <APP_NAME> [APP_NAME2 ...]")
        print("Example: python generate_network_segmentation_single.py ACDA")
        print("Example: python generate_network_segmentation_single.py ACDA ALE AODSVY")
        sys.exit(1)

    app_names = sys.argv[1:]

    # Load topology data
    topology_data = load_topology_data()

    if not topology_data:
        logger.error("No topology data available. Exiting.")
        sys.exit(1)

    # Setup directories
    diagrams_dir = Path('outputs_final/diagrams')
    output_dir = Path('outputs_final/word_reports/netseg')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("NETWORK SEGMENTATION DOCUMENT GENERATOR (SINGLE APP MODE)")
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

        # Get app data
        app_data = topology_data[app_name]
        app_data['app_name'] = app_name  # Add app name to data

        # Find diagram (optional)
        png_path = diagrams_dir / f"{app_name}_diagram.png"
        png_path_str = str(png_path) if png_path.exists() else None

        # Output path
        output_path = output_dir / f"NetSeg-{app_name}.docx"

        try:
            print(f"Generating: {app_name}...", end=' ', flush=True)

            # Create analysis structure for single app
            analysis_results = create_analysis_results_for_app(app_name, app_data)
            zones = create_zones_for_app(app_data)
            rules = create_rules_for_app(app_name, app_data)

            # Generate document
            generate_solutions_document(
                analysis_results=analysis_results,
                zones=zones,
                rules=rules,
                output_path=str(output_path),
                png_path=png_path_str
            )

            print("[OK]")
            print(f"   Output: {output_path}")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Error: {e}")
            logger.error(f"Failed to generate document for {app_name}: {e}", exc_info=True)
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
