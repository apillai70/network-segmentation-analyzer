#!/usr/bin/env python3
"""
Regenerate ALL HTML files from existing MMD files
==================================================
This script regenerates BOTH:
1. *_application_diagram.html (from ApplicationDiagramGenerator)
2. *_diagram.html (from NetworkDiagramGenerator via diagrams.py)

Use this after updating the HTML templates in the Python code.
"""

import sys
from pathlib import Path

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from src.application_diagram_generator import ApplicationDiagramGenerator
from src.diagrams import MermaidDiagramGenerator
from src.enhanced_application_diagram_generator import EnhancedApplicationDiagramGenerator
from src.database.flow_repository import FlowRepository

def regenerate_application_diagram_htmls(diagram_dir='outputs_final/diagrams'):
    """Regenerate HTML files for application diagrams"""

    diagram_path = Path(diagram_dir)

    if not diagram_path.exists():
        print(f"[ERROR] Directory not found: {diagram_dir}")
        return 0, 0

    # Find all application_diagram.mmd files
    mmd_files = list(diagram_path.glob('*_application_diagram.mmd'))

    if not mmd_files:
        print(f"No application diagram MMD files found in {diagram_dir}")
        return 0, 0

    print("="*80)
    print(f"REGENERATING HTML FOR {len(mmd_files)} APPLICATION DIAGRAMS")
    print("="*80)
    print()

    generator = ApplicationDiagramGenerator()

    success = 0
    failed = 0

    for mmd_file in mmd_files:
        app_name = mmd_file.stem.replace('_application_diagram', '')
        html_file = mmd_file.with_suffix('.html')

        print(f"{app_name}...", end=' ', flush=True)

        try:
            # Read MMD content
            with open(mmd_file, 'r', encoding='utf-8') as f:
                mermaid_content = f.read()

            # NOTE: Do NOT strip code fences for application diagrams!
            # ApplicationDiagramGenerator._generate_html_diagram expects them and strips them itself

            # Generate HTML using the generator's method
            generator._generate_html_diagram(mermaid_content, str(html_file))

            print(f"[OK] {html_file.name}")
            success += 1

        except Exception as e:
            print(f"[FAILED] {e}")
            failed += 1

    print()
    print(f"Application Diagrams: {success} successful, {failed} failed")
    print()

    return success, failed


def regenerate_network_diagram_htmls(diagram_dir='outputs_final/diagrams'):
    """Regenerate HTML files for network diagrams (non-application)"""

    diagram_path = Path(diagram_dir)

    if not diagram_path.exists():
        print(f"[ERROR] Directory not found: {diagram_dir}")
        return 0, 0

    # Find all _diagram.mmd files that are NOT application diagrams
    all_mmd_files = list(diagram_path.glob('*_diagram.mmd'))
    mmd_files = [f for f in all_mmd_files if '_application_diagram' not in f.name]

    if not mmd_files:
        print(f"No network diagram MMD files found in {diagram_dir}")
        return 0, 0

    print("="*80)
    print(f"REGENERATING HTML FOR {len(mmd_files)} NETWORK DIAGRAMS")
    print("="*80)
    print()

    success = 0
    failed = 0

    for mmd_file in mmd_files:
        app_name = mmd_file.stem.replace('_diagram', '')
        html_file = mmd_file.with_suffix('.html')

        print(f"{app_name}...", end=' ', flush=True)

        try:
            # Read MMD content
            with open(mmd_file, 'r', encoding='utf-8') as f:
                mermaid_content = f.read()

            # Strip markdown code fences if present
            mermaid_content = mermaid_content.strip()
            if mermaid_content.startswith('```mermaid'):
                mermaid_content = mermaid_content[len('```mermaid'):].strip()
            if mermaid_content.endswith('```'):
                mermaid_content = mermaid_content[:-len('```')].strip()

            # Generate HTML directly (MermaidDiagramGenerator requires full initialization)
            # So we'll call the method directly by creating a minimal instance
            title = f"{app_name} - Network Segmentation Diagram"

            # Create a minimal instance with dummy data just to call the method
            generator = MermaidDiagramGenerator([], {})
            generator._generate_html_diagram(mermaid_content, str(html_file), title)

            print(f"[OK] {html_file.name}")
            success += 1

        except Exception as e:
            print(f"[FAILED] {e}")
            failed += 1

    print()
    print(f"Network Diagrams: {success} successful, {failed} failed")
    print()

    return success, failed


def generate_enhanced_diagrams(diagram_dir='outputs_final/diagrams', max_batch=None):
    """Generate enhanced diagrams from database"""

    print()
    print("="*80)
    print("GENERATING ENHANCED DIAGRAMS FROM DATABASE")
    print("="*80)
    print()

    try:
        # Initialize
        flow_repo = FlowRepository()
        enhanced_gen = EnhancedApplicationDiagramGenerator()

        # Get all unique app codes from database
        all_flows = flow_repo.get_all_flows()
        app_codes = set()
        for flow in all_flows:
            if flow.get('source_app_code'):
                app_codes.add(flow['source_app_code'])
            if flow.get('dest_app_code'):
                app_codes.add(flow['dest_app_code'])

        app_codes = sorted(list(app_codes))

        if max_batch:
            app_codes = app_codes[:max_batch]

        print(f"Found {len(app_codes)} applications")
        print()

        success = 0
        failed = 0

        for app_code in app_codes:
            print(f"{app_code}...", end=' ', flush=True)

            try:
                # Get flows for this app
                app_flows = [f for f in all_flows
                           if f.get('source_app_code') == app_code
                           or f.get('dest_app_code') == app_code]

                if not app_flows:
                    print("[SKIPPED] No flows")
                    continue

                # Generate enhanced diagram
                result = enhanced_gen.generate_from_flows(
                    app_code=app_code,
                    flows_data=app_flows,
                    output_dir='outputs_final/enhanced_diagrams'
                )

                if result:
                    print("[OK] Enhanced diagram generated")
                    success += 1
                else:
                    print("[FAILED] Generation failed")
                    failed += 1

            except Exception as e:
                print(f"[FAILED] {e}")
                failed += 1

        print()
        print(f"Enhanced Diagrams: {success} successful, {failed} failed")
        print()

        return success, failed

    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}")
        print("Skipping enhanced diagram generation")
        print()
        return 0, 0


def main(diagram_dir='outputs_final/diagrams', generate_enhanced=False, max_batch=None):
    """Regenerate both types of HTML files"""

    print()
    print("="*80)
    print("REGENERATING ALL HTML FILES")
    print("="*80)
    print()

    # Regenerate application diagrams
    app_success, app_failed = regenerate_application_diagram_htmls(diagram_dir)

    # Regenerate network diagrams
    net_success, net_failed = regenerate_network_diagram_htmls(diagram_dir)

    # Generate enhanced diagrams if requested
    enh_success = 0
    enh_failed = 0
    if generate_enhanced:
        enh_success, enh_failed = generate_enhanced_diagrams(diagram_dir, max_batch)

    # Summary
    total_success = app_success + net_success + enh_success
    total_failed = app_failed + net_failed + enh_failed

    print()
    print("="*80)
    print("REGENERATION COMPLETE")
    print("="*80)
    print(f"Total Success: {total_success}")
    print(f"Total Failed: {total_failed}")
    print()
    print(f"Regular diagrams: {diagram_dir}")
    if generate_enhanced:
        print(f"Enhanced diagrams: outputs_final/enhanced_diagrams")
    print()
    print("Next Steps:")
    print("1. Open any *_application_diagram.html file to verify pan/zoom controls")
    print("2. Open any *_diagram.html file to verify NO svgPanZoom errors")
    print("3. Verify diagrams appear centered and properly scaled")
    if generate_enhanced:
        print("4. Click 'View Enhanced Analysis' button to verify enhanced diagrams")

    return 0 if total_failed == 0 else 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Regenerate ALL HTML files from existing MMD files')
    parser.add_argument('--dir', type=str, default='outputs_final/diagrams',
                      help='Directory containing MMD files')
    parser.add_argument('--enhanced', action='store_true',
                      help='Also generate enhanced diagrams from database')
    parser.add_argument('--max-batch', type=int, default=None,
                      help='Maximum number of enhanced diagrams to generate (default: all)')

    args = parser.parse_args()

    sys.exit(main(args.dir, generate_enhanced=args.enhanced, max_batch=args.max_batch))
