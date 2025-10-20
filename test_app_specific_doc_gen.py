#!/usr/bin/env python3
"""
Test script for app-specific threat surface document generator
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from app_specific_threat_surface_generator import AppSpecificThreatSurfaceDocument


def test_document_generation():
    """Test document generation with real app data"""

    # Load ACDA app topology data
    topology_file = Path('persistent_data/topology/ACDA.json')

    if not topology_file.exists():
        print(f"ERROR: Topology file not found: {topology_file}")
        return False

    with open(topology_file, 'r') as f:
        app_data = json.load(f)

    app_name = app_data.get('app_id', 'ACDA')

    # Map topology data to expected format
    formatted_data = {
        'security_zone': app_data.get('security_zone', 'UNKNOWN'),
        'predicted_dependencies': app_data.get('dependencies', []),
        'dns_validation': app_data.get('dns_validation', {}),
        'validation_metadata': app_data.get('validation_metadata', {})
    }

    print(f"Generating app-specific threat surface document for: {app_name}")
    print(f"   Zone: {formatted_data['security_zone']}")
    print(f"   Dependencies: {len(formatted_data['predicted_dependencies'])}")
    print(f"   DNS Issues: {formatted_data['dns_validation'].get('mismatch', 0) + formatted_data['dns_validation'].get('nxdomain', 0)}")

    # Generate document
    output_dir = Path('test_output')
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f'{app_name}_threat_surface_app_specific.docx'

    try:
        doc_gen = AppSpecificThreatSurfaceDocument(app_name, formatted_data)
        doc_gen.generate_document(str(output_path))

        print(f"SUCCESS: Document generated: {output_path}")
        print(f"   File size: {output_path.stat().st_size:,} bytes")
        return True

    except Exception as e:
        print(f"ERROR: Failed to generate document: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_document_generation()
    sys.exit(0 if success else 1)
