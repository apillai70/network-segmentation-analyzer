#!/usr/bin/env python3
"""Test updated controls"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from application_diagram_generator import ApplicationDiagramGenerator
from utils.hostname_resolver import HostnameResolver

topology_file = Path('persistent_data/topology/ACDA.json')
with open(topology_file, 'r', encoding='utf-8') as f:
    acda_topology = json.load(f)

hostname_resolver = HostnameResolver(demo_mode=True)
generator = ApplicationDiagramGenerator(hostname_resolver=hostname_resolver)

topology_data = {
    'app_id': acda_topology['app_id'],
    'security_zone': acda_topology['security_zone'],
    'predicted_dependencies': acda_topology['dependencies']
}

output_path = 'outputs_final/diagrams/ACDA_application_diagram.mmd'
generator.generate_application_diagram(
    app_name='ACDA',
    flow_records=[],
    topology_data=topology_data,
    predictions=None,
    output_path=output_path,
    max_nodes=50
)

print("Diagram regenerated with 4-way pan control!")
print(f"Open: {output_path.replace('.mmd', '.html')}")
