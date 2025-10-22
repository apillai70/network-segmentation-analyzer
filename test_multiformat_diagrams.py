#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Multi-Format Diagram Generation
=====================================
Tests PNG, SVG, HTML, MMD, and DOCX generation for enhanced diagrams.
"""

import logging
from pathlib import Path
from collections import defaultdict, Counter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.parser import parse_network_logs
from src.utils.hostname_resolver import HostnameResolver
from src.enhanced_diagram_generator import EnhancedDiagramGenerator


def main():
    """Main test execution"""
    print("=" * 80)
    print("MULTI-FORMAT DIAGRAM GENERATION TEST")
    print("=" * 80)

    # Parse network logs
    logger.info("Loading network flow data from data/input...")
    parser = parse_network_logs('data/input')

    logger.info(f"Total flow records loaded: {len(parser.records):,}")

    # Build hostname resolver
    logger.info("Building hostname resolution mappings...")
    resolver = HostnameResolver()

    mapping_count = 0
    for record in parser.records:
        # Add source IP → hostname mapping
        if record.src_hostname and record.src_hostname != 'nan':
            resolver.add_mapping(record.src_ip, record.src_hostname)
            mapping_count += 1

        # Add destination IP → hostname mapping
        if record.dst_hostname and record.dst_hostname != 'nan':
            resolver.add_mapping(record.dst_ip, record.dst_hostname)
            mapping_count += 1

    logger.info(f"Added {mapping_count} IP→hostname mappings to resolver")

    # Group records by application
    logger.info("Grouping records by application...")
    applications = defaultdict(list)
    for record in parser.records:
        app_name = record.app_name or 'unknown'
        applications[app_name].append(record)

    logger.info(f"Found {len(applications)} unique applications")

    # Find top applications by flow count
    app_counts = Counter({app: len(records) for app, records in applications.items()})
    top_apps = app_counts.most_common(3)

    logger.info(f"Top 3 applications by flow count:")
    for app_name, count in top_apps:
        logger.info(f"  {app_name}: {count:,} flows")

    # Create output directory
    output_dir = Path('outputs/diagrams/multiformat_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Initialize generator
    generator = EnhancedDiagramGenerator(hostname_resolver=resolver)

    # Generate diagrams for top 3 applications in ALL formats
    print("\n" + "=" * 80)
    print("GENERATING MULTI-FORMAT DIAGRAMS")
    print("=" * 80)

    for app_name, count in top_apps:
        print(f"\n{app_name} ({count:,} flows):")

        app_records = applications[app_name]

        # Generate ALL formats (MMD, HTML, PNG, SVG, DOCX)
        output_paths = generator.generate_enhanced_diagram(
            app_name=app_name,
            flow_records=app_records,
            output_dir=str(output_dir),
            output_formats=['mmd', 'html', 'png', 'svg', 'docx']  # All formats
        )

        # Print generated files
        for format_type, path in output_paths.items():
            file_path = Path(path)
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                print(f"  ✓ {format_type.upper()}: {file_path.name} ({size_kb:.1f} KB)")
            else:
                print(f"  ✗ {format_type.upper()}: {file_path.name} (not found)")

    print("\n" + "=" * 80)
    print("MULTI-FORMAT TEST COMPLETE")
    print("=" * 80)

    # Summary of generated files
    print(f"\nGenerated files in: {output_dir}")
    print("\nFile types:")
    print("  • MMD:  Mermaid source files (editable)")
    print("  • HTML: Interactive diagrams with zoom controls")
    print("  • PNG:  High-resolution images (4800px, for embedding)")
    print("  • SVG:  Vector graphics (infinite zoom, perfect quality)")
    print("  • DOCX: Word documents with embedded diagrams + instructions")

    print("\nUsage recommendations:")
    print("  - Use HTML for presentations (browser-based, interactive)")
    print("  - Use SVG for print/high-quality (infinite zoom)")
    print("  - Use DOCX for reports (professional documents)")
    print("  - Use PNG for compatibility (embeds in most tools)")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
