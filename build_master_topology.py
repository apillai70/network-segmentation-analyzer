#!/usr/bin/env python3
"""
Master Topology Builder
=======================
Builds a cumulative master topology from all individual application
topologies in persistent_data/topology/

This creates a single consolidated JSON file that represents ALL
applications analyzed over time.

Usage:
    python build_master_topology.py

Output:
    persistent_data/master_topology.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def build_master_topology():
    """Build master topology from all individual topology files"""

    topology_dir = Path('persistent_data/topology')

    if not topology_dir.exists():
        logger.error(f"Topology directory not found: {topology_dir}")
        logger.error("Please run batch processing first to generate topology data")
        return None

    logger.info("="*80)
    logger.info("BUILDING MASTER TOPOLOGY")
    logger.info("="*80)
    logger.info(f"Source: {topology_dir}")

    # Find all topology JSON files
    topology_files = sorted(topology_dir.glob('*.json'))

    if not topology_files:
        logger.error("No topology files found")
        return None

    logger.info(f"Found {len(topology_files)} application topologies")

    # Build master topology
    master_topology = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_applications': len(topology_files),
            'source': 'persistent_data/topology/',
            'description': 'Cumulative topology of all analyzed applications'
        },
        'topology': {}
    }

    # Load each application topology
    loaded_count = 0
    error_count = 0

    for topo_file in topology_files:
        try:
            app_name = topo_file.stem  # Filename without .json

            with open(topo_file, 'r', encoding='utf-8') as f:
                app_data = json.load(f)

            # Store in master topology
            # Convert to format expected by document generators
            master_topology['topology'][app_name] = {
                'app_id': app_data.get('app_id', app_name),
                'security_zone': app_data.get('security_zone', 'UNKNOWN'),
                'predicted_dependencies': app_data.get('dependencies', []),
                'characteristics': app_data.get('characteristics', []),
                'created_at': app_data.get('created_at'),
                'updated_at': app_data.get('updated_at')
            }

            loaded_count += 1

        except Exception as e:
            logger.error(f"Error loading {topo_file.name}: {e}")
            error_count += 1

    logger.info(f"Successfully loaded: {loaded_count} applications")

    if error_count > 0:
        logger.warning(f"Errors: {error_count} applications")

    # Save master topology
    output_file = Path('persistent_data/master_topology.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_topology, f, indent=2, ensure_ascii=False)

    logger.info(f"Master topology saved: {output_file}")
    logger.info(f"Total applications in master: {len(master_topology['topology'])}")
    logger.info("="*80)

    return output_file


def main():
    """Main execution"""
    print()
    result = build_master_topology()
    print()

    if result:
        print(f"✓ Master topology built successfully")
        print(f"  Location: {result}")
        print(f"\nYou can now generate threat surface documents with:")
        print(f"  python generate_threat_surface_docs.py")
    else:
        print("✗ Failed to build master topology")
        print("  Check logs for details")


if __name__ == '__main__':
    main()
