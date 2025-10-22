#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Enhanced Diagram Generator
================================
Test script for enhanced diagrams with server classification
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_diagrams():
    """Test enhanced diagram generation with sample data"""

    logger.info("=" * 80)
    logger.info("Testing Enhanced Diagram Generator with Server Classification")
    logger.info("=" * 80)

    # Import modules
    from src.parser import parse_network_logs
    from src.utils.hostname_resolver import HostnameResolver
    from src.enhanced_diagram_generator import EnhancedDiagramGenerator

    # Step 1: Load network flow data
    logger.info("\nStep 1: Loading network flow data")
    parser = parse_network_logs('data/input')

    # Group records by application
    from collections import defaultdict
    applications = defaultdict(list)
    for record in parser.records:
        app_name = record.app_name or 'unknown'
        applications[app_name].append(record)

    logger.info(f"  Loaded {len(parser.records)} flow records from {len(applications)} applications")

    if not parser.records:
        logger.error("No flow records found. Please ensure data files are in data/input/")
        return False

    # Step 2: Initialize hostname resolver
    logger.info("\nStep 2: Initializing hostname resolver")
    resolver = HostnameResolver()

    # Build DNS mapping from flow records
    mapping_count = 0
    for record in parser.records:
        if hasattr(record, 'src_ip') and hasattr(record, 'src_hostname'):
            if record.src_hostname and record.src_hostname != 'nan':
                resolver.add_mapping(record.src_ip, record.src_hostname)
                mapping_count += 1
        if hasattr(record, 'dst_ip') and hasattr(record, 'dst_hostname'):
            if record.dst_hostname and record.dst_hostname != 'nan':
                resolver.add_mapping(record.dst_ip, record.dst_hostname)
                mapping_count += 1

    logger.info(f"  Added {mapping_count} IP→hostname mappings to resolver")

    # Step 3: Select test applications
    logger.info("\nStep 3: Selecting test applications")

    # Get applications with most flows
    app_flow_counts = {}
    for app_name, app_records in applications.items():
        app_flow_counts[app_name] = len(app_records)

    # Sort and get top 3
    top_apps = sorted(app_flow_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    if not top_apps:
        logger.error("No applications found with flow records")
        return False

    logger.info(f"  Testing with top {len(top_apps)} applications:")
    for app_name, count in top_apps:
        logger.info(f"    - {app_name}: {count} flow records")

    # Step 4: Generate enhanced diagrams
    logger.info("\nStep 4: Generating enhanced diagrams with server classification")

    generator = EnhancedDiagramGenerator(hostname_resolver=resolver)

    output_dir = Path('outputs/diagrams/enhanced')
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for app_name, count in top_apps:
        logger.info(f"\n  Generating diagram for: {app_name}")

        app_records = applications[app_name]

        try:
            output_paths = generator.generate_enhanced_diagram(
                app_name=app_name,
                flow_records=app_records,
                output_dir=str(output_dir),
                output_formats=['mmd', 'html']
            )

            logger.info(f"    Generated {len(output_paths)} output files:")
            for format_type, path in output_paths.items():
                logger.info(f"      {format_type.upper()}: {path}")

            success_count += 1

        except Exception as e:
            logger.error(f"    Failed to generate diagram: {e}", exc_info=True)

    # Step 5: Summary
    logger.info("\n" + "=" * 80)
    logger.info(f"SUMMARY: Successfully generated {success_count}/{len(top_apps)} enhanced diagrams")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info("=" * 80)

    return success_count > 0


if __name__ == '__main__':
    try:
        success = test_enhanced_diagrams()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
