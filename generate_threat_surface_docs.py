#!/usr/bin/env python3
"""
Batch Generator for Threat Surface Analysis Documents
======================================================
Generates threat surface analysis and network segmentation
best practices documents for all analyzed applications.

Usage:
    python generate_threat_surface_docs.py

Output Location:
    outputs_final/word_reports/threat_surface/
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from src.threat_surface_netseg_generator import generate_threat_surface_document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('threat_surface_docs_generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Generate threat surface documents for all applications"""
    print("="*80)
    print("THREAT SURFACE ANALYSIS & NETWORK SEGMENTATION DOCUMENTS")
    print("="*80)
    print()

    # Load topology data from persistent master topology
    topology_file = Path('persistent_data/master_topology.json')

    if not topology_file.exists():
        logger.error(f"Master topology file not found: {topology_file}")
        logger.error("Building master topology from persistent data...")

        # Try to build it automatically
        try:
            import subprocess
            result = subprocess.run(
                ['python', 'build_master_topology.py'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0 or not topology_file.exists():
                logger.error("Failed to build master topology")
                logger.error("Please run: python build_master_topology.py")
                return

            logger.info("Master topology built successfully")
        except Exception as e:
            logger.error(f"Error building master topology: {e}")
            return

    logger.info(f"Loading topology data from: {topology_file}")

    with open(topology_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    topology = data.get('topology', {})

    if not topology:
        logger.error("No topology data found in file")
        return

    logger.info(f"Found {len(topology)} applications in topology")
    print()

    # Setup output directory
    output_dir = Path('outputs_final/word_reports/threat_surface')
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output directory: {output_dir}")
    print()

    # Track statistics
    success_count = 0
    failed_count = 0
    failed_apps = []

    start_time = datetime.now()

    # Generate documents for each application
    print("Generating threat surface documents...")
    print("-"*80)

    for idx, (app_name, app_data) in enumerate(sorted(topology.items()), 1):
        try:
            # Progress indicator
            progress = f"[{idx}/{len(topology)}]"
            print(f"{progress} {app_name}...", end=' ', flush=True)

            # Output path
            output_path = output_dir / f'ThreatSurface-{app_name}.docx'

            # Generate document
            generate_threat_surface_document(
                app_name=app_name,
                app_data=app_data,
                output_path=str(output_path)
            )

            print("✓")
            success_count += 1

        except Exception as e:
            print(f"✗ Error: {e}")
            logger.error(f"Failed to generate document for {app_name}: {e}")
            failed_count += 1
            failed_apps.append(app_name)

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"Total Applications:  {len(topology)}")
    print(f"Successfully Generated: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Average: {duration/len(topology):.1f} seconds per document")
    print()
    print(f"📁 Output Location: {output_dir}")
    print("="*80)

    if failed_apps:
        print()
        print("⚠️  Failed Applications:")
        for app in failed_apps:
            print(f"   - {app}")
        print()

    # Log summary
    logger.info("="*80)
    logger.info(f"Generation Summary:")
    logger.info(f"  Total: {len(topology)}")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Duration: {duration:.1f}s")
    logger.info(f"  Output: {output_dir}")
    logger.info("="*80)


if __name__ == '__main__':
    main()
