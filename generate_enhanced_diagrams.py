#!/usr/bin/env python3
"""
Generate Enhanced Application Diagrams from Production Data
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.enhanced_application_diagram_generator import EnhancedApplicationDiagramGenerator
from src.database.flow_repository import FlowRepository

def load_app_flows(app_code: str, flow_repo: FlowRepository) -> List[Dict]:
    """Load all flows for a given application from the database"""
    print(f"Loading flows for {app_code}...")

    # Get flows where this app is source or destination
    flows = []

    # Query from database
    all_flows = flow_repo.get_all_flows()

    for flow in all_flows:
        src_app = flow.get('source_app_code', '')
        dest_app = flow.get('dest_app_code', '')

        if src_app == app_code or dest_app == app_code:
            flows.append(flow)

    print(f"  Found {len(flows)} flows")
    return flows

def main():
    """Generate enhanced diagrams for all applications"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate enhanced application diagrams')
    parser.add_argument('--app-codes', nargs='+', help='Specific app codes to generate (default: all)')
    parser.add_argument('--max-batch', type=int, help='Maximum number of apps to process')
    parser.add_argument('--output-dir', default='outputs_final/enhanced_diagrams', help='Output directory')

    args = parser.parse_args()

    # Initialize (FlowRepository will auto-load config)
    flow_repo = FlowRepository()
    generator = EnhancedApplicationDiagramGenerator()

    # Get app codes
    if args.app_codes:
        app_codes = args.app_codes
    else:
        # Get all unique app codes from database
        all_flows = flow_repo.get_all_flows()
        app_codes = set()
        for flow in all_flows:
            if flow.get('source_app_code'):
                app_codes.add(flow['source_app_code'])
            if flow.get('dest_app_code'):
                app_codes.add(flow['dest_app_code'])
        app_codes = sorted(list(app_codes))

    if args.max_batch:
        app_codes = app_codes[:args.max_batch]

    print("="*80)
    print(f"GENERATING ENHANCED DIAGRAMS FOR {len(app_codes)} APPLICATIONS")
    print("="*80)
    print()

    success_count = 0
    failed_count = 0

    for app_code in app_codes:
        try:
            # Load flows for this app
            flows = load_app_flows(app_code, flow_repo)

            if len(flows) == 0:
                print(f"{app_code}... [SKIPPED] No flows found")
                continue

            # Generate enhanced diagram
            success = generator.generate_from_flows(
                app_code=app_code,
                flows_data=flows,
                output_dir=args.output_dir
            )

            if success:
                print(f"{app_code}... [OK] Enhanced diagram generated")
                success_count += 1
            else:
                print(f"{app_code}... [FAILED] Generation failed")
                failed_count += 1

        except Exception as e:
            print(f"{app_code}... [FAILED] {str(e)}")
            failed_count += 1

    print()
    print("="*80)
    print(f"GENERATION COMPLETE")
    print("="*80)
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Output: {args.output_dir}")
    print()

if __name__ == '__main__':
    main()
