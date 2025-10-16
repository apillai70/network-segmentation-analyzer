#!/usr/bin/env python3
"""
Test script to regenerate ACDA diagram with new color coding
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from application_diagram_generator import ApplicationDiagramGenerator
from utils.hostname_resolver import HostnameResolver

def test_acda_diagram():
    """Test ACDA diagram generation with new color coding"""

    print("="*80)
    print("TESTING DIAGRAM COLOR CODING FOR ACDA")
    print("="*80)
    print()

    # Load ACDA topology
    topology_file = Path('persistent_data/topology/ACDA.json')

    if not topology_file.exists():
        print(f"ERROR: Topology file not found: {topology_file}")
        return

    with open(topology_file, 'r', encoding='utf-8') as f:
        acda_topology = json.load(f)

    print(f"Loaded ACDA topology with {len(acda_topology['dependencies'])} dependencies")
    print()

    # Count dependencies by source
    source_counts = {}
    for dep in acda_topology['dependencies']:
        source = dep.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    print("Dependencies by source:")
    for source, count in source_counts.items():
        print(f"  {source}: {count}")
    print()

    # Initialize diagram generator with hostname resolver
    hostname_resolver = HostnameResolver(demo_mode=True)
    generator = ApplicationDiagramGenerator(hostname_resolver=hostname_resolver)

    # Prepare topology data for diagram generator
    topology_data = {
        'app_id': acda_topology['app_id'],
        'security_zone': acda_topology['security_zone'],
        'predicted_dependencies': acda_topology['dependencies']
    }

    # Output path
    output_path = 'outputs_final/diagrams/ACDA_application_diagram.mmd'

    print("Generating diagram...")
    print(f"Output: {output_path}")
    print()

    # Generate diagram (no flow records needed since we're using topology data)
    diagram_content = generator.generate_application_diagram(
        app_name='ACDA',
        flow_records=[],  # Empty - using topology data instead
        topology_data=topology_data,
        predictions=None,
        output_path=output_path,
        max_nodes=50
    )

    print("✓ Diagram generated successfully!")
    print()

    # Check if color coding is present in output
    print("Checking color coding in output...")
    if 'stroke:#333' in diagram_content:
        print("  ✓ Black solid lines for network_observation found")
    if 'stroke:#3498db' in diagram_content:
        print("  ✓ Blue dashed lines for type_inference found")
    if 'Data Source Colors' in diagram_content:
        print("  ✓ Legend with data source colors found")
    print()

    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    print()
    print(f"View the diagram at: {output_path}")
    print(f"View HTML version at: {output_path.replace('.mmd', '.html')}")
    print()

if __name__ == '__main__':
    test_acda_diagram()
