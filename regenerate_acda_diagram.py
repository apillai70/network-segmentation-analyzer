#!/usr/bin/env python3
"""
Quick script to regenerate ACDA application diagram with updated Unknown explanation
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from application_diagram_generator import ApplicationDiagramGenerator
from parser import FlowRecord
from utils.hostname_resolver import HostnameResolver

print("="*80)
print("REGENERATING ACDA APPLICATION DIAGRAM")
print("="*80)

# Load persistent topology data
topology_file = Path('persistent_data/topology/ACDA.json')

if not topology_file.exists():
    print(f"Error: {topology_file} not found!")
    sys.exit(1)

with open(topology_file, 'r') as f:
    topology_data = json.load(f)

print(f"Loaded topology data for ACDA")
print(f"  Dependencies: {len(topology_data.get('predicted_dependencies', []))}")

# Create mock flow records from topology data
flow_records = []

# The topology data has the analysis but not the raw flows
# We'll generate the diagram from the topology data which includes
# predicted dependencies

# Create hostname resolver
hostname_resolver = HostnameResolver(demo_mode=True)

# Create diagram generator
generator = ApplicationDiagramGenerator(hostname_resolver=hostname_resolver)

# Generate the application diagram
output_path = Path('outputs_final/diagrams/ACDA_application_diagram.mmd')

# Generate diagram using topology data (no flow records needed - will use topology)
mermaid_content = generator.generate_application_diagram(
    app_name='ACDA',
    flow_records=[],  # Empty - will use topology data instead
    topology_data=topology_data,
    predictions=None,
    output_path=str(output_path)
)

print(f"\n[OK] Application diagram regenerated: {output_path}")
print(f"[OK] HTML version regenerated: {output_path.with_suffix('.html')}")
print("="*80)
print("COMPLETE - Diagram now includes detailed Unknown connections explanation")
print("="*80)
