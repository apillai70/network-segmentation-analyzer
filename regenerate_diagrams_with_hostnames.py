#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate Diagrams with Hostnames
===================================
Re-generates Mermaid diagrams from existing data with hostname resolver enabled
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser import FlowRecord
from diagrams import MermaidDiagramGenerator
from utils.hostname_resolver import HostnameResolver
import pandas as pd


def load_flow_records(csv_path):
    """Load flow records from CSV"""
    logger.info(f"Loading flow records from: {csv_path}")

    df = pd.read_csv(csv_path)

    records = []
    for _, row in df.iterrows():
        record = FlowRecord(
            src_ip=row.get('src_ip', row.get('Source IP')),
            dst_ip=row.get('dst_ip', row.get('Destination IP')),
            src_port=int(row.get('src_port', row.get('Source Port', 0))),
            dst_port=int(row.get('dst_port', row.get('Destination Port', 0))),
            protocol=row.get('protocol', row.get('Protocol', 'TCP')),
            app_name=row.get('app_name', row.get('Application Code', 'UNKNOWN'))
        )
        records.append(record)

    logger.info(f"  ✓ Loaded {len(records)} flow records")
    return records


def main():
    """Main function"""

    logger.info("="*80)
    logger.info("REGENERATING DIAGRAMS WITH HOSTNAMES")
    logger.info("="*80)

    # Configure paths
    input_file = Path('data/input/duplicates/App_Code_ALE.csv')
    output_dir = Path('outputs_final/diagrams')
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    # Load flow records
    records = load_flow_records(input_file)

    # Get unique apps
    apps = {}
    for record in records:
        if record.app_name not in apps:
            apps[record.app_name] = []
        apps[record.app_name].append(record)

    logger.info(f"  ✓ Found {len(apps)} applications")

    # Mock zones for diagram generation
    class MockZone:
        def __init__(self, name, tier):
            self.name = name
            self.tier = tier
            self.zone_type = 'micro'  # All zones are micro zones
            self.security_level = tier  # Use tier as security level
            self.description = f"{name.replace('_', ' ').title()}"
            self.members = set()

    zones = {
        'MANAGEMENT_TIER': MockZone('MANAGEMENT_TIER', 1),
        'WEB_TIER': MockZone('WEB_TIER', 2),
        'APP_TIER': MockZone('APP_TIER', 3),
        'DATA_TIER': MockZone('DATA_TIER', 4),
        'CACHE_TIER': MockZone('CACHE_TIER', 5),
        'MESSAGING_TIER': MockZone('MESSAGING_TIER', 6),
    }

    # Infer zones from IPs
    for record in records:
        for ip in [record.src_ip, record.dst_ip]:
            if not ip or not isinstance(ip, str):
                continue
            if ip.startswith('10.100.160.'):
                zones['MANAGEMENT_TIER'].members.add(ip)
            elif ip.startswith('10.164.105.'):
                zones['WEB_TIER'].members.add(ip)
            elif ip.startswith('10.100.246.'):
                zones['APP_TIER'].members.add(ip)
            elif ip.startswith('10.164.116.'):
                zones['DATA_TIER'].members.add(ip)
            elif ip.startswith('10.164.144.'):
                zones['CACHE_TIER'].members.add(ip)
            elif ip.startswith('10.164.145.'):
                zones['MESSAGING_TIER'].members.add(ip)
            elif ip.startswith('10.165.116.'):
                zones['APP_TIER'].members.add(ip)

    # Create hostname resolver (demo mode)
    hostname_resolver = HostnameResolver(demo_mode=True)

    # Create diagram generator with hostname resolver
    diagram_gen = MermaidDiagramGenerator(
        flow_records=records,
        zones=zones,
        hostname_resolver=hostname_resolver
    )

    logger.info("\n" + "="*80)
    logger.info("GENERATING DIAGRAMS")
    logger.info("="*80)

    # Generate per-app diagrams
    for app_name, app_records in apps.items():
        logger.info(f"\nGenerating diagram for: {app_name}")

        diagram_path = output_dir / f"{app_name}_diagram.mmd"

        diagram_gen.generate_app_diagram(app_name, str(diagram_path))

        logger.info(f"  ✓ Mermaid: {diagram_path}")
        logger.info(f"  ✓ HTML: {diagram_path.with_suffix('.html')}")

    # Generate overall network diagram
    logger.info(f"\nGenerating overall network diagram")

    overall_mmd = output_dir / "overall_network.mmd"

    diagram_gen.generate_overall_network_diagram(str(overall_mmd))

    logger.info(f"  ✓ Mermaid: {overall_mmd}")
    logger.info(f"  ✓ HTML: {overall_mmd.with_suffix('.html')}")

    # Generate zone flows diagram
    logger.info(f"\nGenerating zone flows diagram")

    zone_mmd = output_dir / "zone_flows.mmd"

    diagram_gen.generate_zone_flow_diagram(str(zone_mmd))

    logger.info(f"  ✓ Mermaid: {zone_mmd}")
    logger.info(f"  ✓ HTML: {zone_mmd.with_suffix('.html')}")

    logger.info("\n" + "="*80)
    logger.info("✅ DIAGRAMS REGENERATED WITH HOSTNAMES!")
    logger.info("="*80)
    logger.info(f"\nOutput location: {output_dir}")
    logger.info("\nHostnames are now displayed in format: hostname<br/>(IP)")
    logger.info("Example: web-web-248<br/>(10.164.105.248)")


if __name__ == '__main__':
    main()
