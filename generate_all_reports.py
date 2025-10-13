#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Report Generation for All Applications
=====================================================
Generates diagrams (Mermaid + HTML), Word documents, and Lucidchart exports
for all 139 processed applications.

Outputs Generated Per Application:
- {APP_ID}_diagram.mmd (Mermaid diagram)
- {APP_ID}_diagram.html (Interactive HTML)
- {APP_ID}_report.docx (Word document)
- Lucidchart CSV exports (combined)

Author: Enterprise Security Team
Version: 1.0
"""

import sys
import os

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import logging
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parser import FlowRecord
from diagrams import MermaidDiagramGenerator
from docx_generator import SolutionsArchitectureDocument
from utils.hostname_resolver import HostnameResolver
from persistence import create_persistence_manager

# Setup logging
log_file = Path('logs') / f'report_generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MockZone:
    """Mock zone object for diagram generation"""
    def __init__(self, name, tier):
        self.name = name
        self.tier = tier
        self.zone_type = 'micro'
        self.security_level = tier
        self.description = f"{name.replace('_', ' ').title()}"
        self.members = set()


def setup_zones():
    """Create zone definitions"""
    return {
        'MANAGEMENT_TIER': MockZone('MANAGEMENT_TIER', 1),
        'WEB_TIER': MockZone('WEB_TIER', 2),
        'APP_TIER': MockZone('APP_TIER', 3),
        'DATA_TIER': MockZone('DATA_TIER', 4),
        'CACHE_TIER': MockZone('CACHE_TIER', 5),
        'MESSAGING_TIER': MockZone('MESSAGING_TIER', 6),
        'INFRASTRUCTURE_TIER': MockZone('INFRASTRUCTURE_TIER', 7),
    }


def infer_zone_from_ip(ip, zones):
    """Infer zone membership from IP address"""
    if not ip or not isinstance(ip, str):
        return None

    if ip.startswith('10.100.160.'):
        zones['MANAGEMENT_TIER'].members.add(ip)
        return 'MANAGEMENT_TIER'
    elif ip.startswith('10.164.105.'):
        zones['WEB_TIER'].members.add(ip)
        return 'WEB_TIER'
    elif ip.startswith('10.100.246.') or ip.startswith('10.165.116.'):
        zones['APP_TIER'].members.add(ip)
        return 'APP_TIER'
    elif ip.startswith('10.164.116.'):
        zones['DATA_TIER'].members.add(ip)
        return 'DATA_TIER'
    elif ip.startswith('10.164.144.'):
        zones['CACHE_TIER'].members.add(ip)
        return 'CACHE_TIER'
    elif ip.startswith('10.164.145.'):
        zones['MESSAGING_TIER'].members.add(ip)
        return 'MESSAGING_TIER'
    return None


def load_flow_records(app_dir):
    """Load flow records from application directory"""
    flows_file = app_dir / 'flows.csv'

    if not flows_file.exists():
        return []

    df = pd.read_csv(flows_file)

    records = []
    for _, row in df.iterrows():
        try:
            # FlowRecord uses 'port' not 'dst_port' or 'src_port'
            dest_port = row.get('Dest Port')
            port_val = int(dest_port) if pd.notna(dest_port) else None

            record = FlowRecord(
                src_ip=row.get('Source IP'),
                dst_ip=row.get('Dest IP'),
                port=port_val,
                protocol=row.get('Protocol', 'TCP'),
                app_name=row.get('Application Code', app_dir.name)
            )
            records.append(record)
        except Exception as e:
            logger.debug(f"Skipping malformed row: {e}")
            continue

    return records


def load_topology_data(app_id):
    """Load topology data for application"""
    topology_file = Path('persistent_data/topology') / f'{app_id}.json'

    if not topology_file.exists():
        return None

    try:
        with open(topology_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load topology for {app_id}: {e}")
        return None


def generate_app_diagram(app_id, flow_records, zones, hostname_resolver, output_dir):
    """Generate Mermaid diagram for application"""
    try:
        diagram_gen = MermaidDiagramGenerator(
            flow_records=flow_records,
            zones=zones,
            hostname_resolver=hostname_resolver
        )

        mmd_path = output_dir / f"{app_id}_diagram.mmd"
        diagram_gen.generate_app_diagram(app_id, str(mmd_path))

        return True, mmd_path
    except Exception as e:
        logger.error(f"Failed to generate diagram for {app_id}: {e}")
        return False, None


def generate_app_word_document(app_id, flow_records, topology_data, zones, output_dir):
    """Generate Word document for application"""
    try:
        # Build analysis results
        total_flows = len(flow_records)
        total_bytes = sum(getattr(r, 'bytes', 0) for r in flow_records)
        total_packets = sum(getattr(r, 'packets', 0) for r in flow_records)

        # Get unique IPs
        unique_src_ips = set(r.src_ip for r in flow_records if r.src_ip)
        unique_dst_ips = set(r.dst_ip for r in flow_records if r.dst_ip)

        # Protocol distribution
        protocol_dist = defaultdict(int)
        for r in flow_records:
            proto = r.protocol if hasattr(r, 'protocol') else 'TCP'
            if hasattr(r, 'port') and r.port:
                proto = f"{proto}:{r.port}"
            protocol_dist[proto] += 1

        # Build analysis results dict
        analysis_results = {
            'summary': {
                'total_flows': total_flows,
                'total_bytes': total_bytes,
                'total_packets': total_packets,
                'unique_apps': 1,
                'suspicious_count': 0,
                'internal_flows': total_flows,
                'external_flows': 0,
                'protocol_distribution': dict(protocol_dist)
            },
            'top_talkers': {
                'top_sources_by_bytes': {},
                'top_destinations_by_bytes': {}
            },
            'suspicious_flows': []
        }

        # Build mock rules for document
        from collections import namedtuple
        SegmentationRule = namedtuple('SegmentationRule', [
            'priority', 'source', 'destination', 'protocol', 'port',
            'action', 'risk_score', 'justification'
        ])

        security_zone = topology_data.get('security_zone', 'APP_TIER') if topology_data else 'APP_TIER'

        rules = [
            SegmentationRule(
                priority=300,
                source='EXTERNAL',
                destination=security_zone,
                protocol='tcp',
                port='443',
                action='allow',
                risk_score=20,
                justification=f'Allow HTTPS access to {app_id}'
            )
        ]

        # Generate document
        doc_gen = SolutionsArchitectureDocument(
            analysis_results=analysis_results,
            zones=zones,
            rules=rules
        )

        docx_path = output_dir / f"{app_id}_report.docx"
        doc_gen.generate_document(str(docx_path))

        return True, docx_path
    except Exception as e:
        logger.error(f"Failed to generate Word doc for {app_id}: {e}")
        return False, None


def generate_lucidchart_export(all_records, zones, output_dir):
    """Generate Lucidchart CSV exports"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Basic export
        basic_csv = output_dir / f"lucidchart_export_{timestamp}.csv"
        with open(basic_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Id', 'Name', 'Shape Library', 'Shape Name'])

            node_ids = set()
            for record in all_records:
                if record.src_ip and record.src_ip not in node_ids:
                    writer.writerow([record.src_ip, record.src_ip, 'standard', 'Rectangle'])
                    node_ids.add(record.src_ip)
                if record.dst_ip and record.dst_ip not in node_ids:
                    writer.writerow([record.dst_ip, record.dst_ip, 'standard', 'Rectangle'])
                    node_ids.add(record.dst_ip)

            # Write edges
            writer.writerow([])
            writer.writerow(['Source', 'Target', 'Line Style'])
            for record in all_records[:1000]:  # Limit to 1000 for performance
                if record.src_ip and record.dst_ip:
                    writer.writerow([record.src_ip, record.dst_ip, 'solid'])

        # Zones export
        zones_csv = output_dir / f"lucidchart_zones_{timestamp}.csv"
        with open(zones_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Container Id', 'Container Name', 'Shape Library', 'Shape Name', 'Member Id'])

            for zone_name, zone in zones.items():
                for member_ip in list(zone.members)[:100]:  # Limit members
                    writer.writerow([zone_name, zone_name, 'standard', 'Container', member_ip])

        logger.info(f"Generated Lucidchart exports:")
        logger.info(f"  - {basic_csv}")
        logger.info(f"  - {zones_csv}")

        return True
    except Exception as e:
        logger.error(f"Failed to generate Lucidchart exports: {e}")
        return False


def main():
    """Main execution"""

    print("=" * 80)
    print("COMPREHENSIVE REPORT GENERATION FOR ALL APPLICATIONS")
    print("=" * 80)
    print()
    print("This will generate for each of 139 apps:")
    print("  - Mermaid diagram (.mmd)")
    print("  - Interactive HTML diagram (.html)")
    print("  - Word document report (.docx)")
    print("  - Lucidchart CSV exports (combined)")
    print()
    print("=" * 80)

    # Setup directories
    apps_dir = Path('persistent_data/applications')
    output_diagrams = Path('outputs_final/diagrams')
    output_reports = Path('outputs_final/word_reports')

    output_diagrams.mkdir(parents=True, exist_ok=True)
    output_reports.mkdir(parents=True, exist_ok=True)

    # Get all application directories
    app_dirs = [d for d in apps_dir.iterdir() if d.is_dir()]
    total_apps = len(app_dirs)

    logger.info(f"Found {total_apps} applications to process")

    if total_apps == 0:
        logger.error("No applications found in persistent_data/applications/")
        return

    # Setup zones
    zones = setup_zones()

    # Create hostname resolver (demo mode)
    hostname_resolver = HostnameResolver(demo_mode=True)

    # Track statistics
    stats = {
        'total': total_apps,
        'diagrams_success': 0,
        'diagrams_failed': 0,
        'docx_success': 0,
        'docx_failed': 0,
        'skipped': 0
    }

    all_flow_records = []

    print()
    print("=" * 80)
    print("PROCESSING APPLICATIONS")
    print("=" * 80)

    # Process each application
    for i, app_dir in enumerate(sorted(app_dirs), 1):
        app_id = app_dir.name

        print(f"\n[{i}/{total_apps}] {app_id}...", end=' ', flush=True)

        # Load flow records
        flow_records = load_flow_records(app_dir)

        if not flow_records:
            print("[SKIP - No flows]")
            stats['skipped'] += 1
            continue

        # Add to global list
        all_flow_records.extend(flow_records)

        # Infer zones from IPs
        for record in flow_records:
            infer_zone_from_ip(record.src_ip, zones)
            infer_zone_from_ip(record.dst_ip, zones)

        # Load topology data
        topology_data = load_topology_data(app_id)

        # Generate diagram
        diagram_success, mmd_path = generate_app_diagram(
            app_id, flow_records, zones, hostname_resolver, output_diagrams
        )

        if diagram_success:
            stats['diagrams_success'] += 1
            print("[DIAG ✓]", end=' ', flush=True)
        else:
            stats['diagrams_failed'] += 1
            print("[DIAG ✗]", end=' ', flush=True)

        # Generate Word document
        docx_success, docx_path = generate_app_word_document(
            app_id, flow_records, topology_data, zones, output_reports
        )

        if docx_success:
            stats['docx_success'] += 1
            print("[DOCX ✓]", end='', flush=True)
        else:
            stats['docx_failed'] += 1
            print("[DOCX ✗]", end='', flush=True)

        # Show zone
        if topology_data:
            zone = topology_data.get('security_zone', 'UNKNOWN')
            print(f" [{zone}]")
        else:
            print(" [NO_TOPOLOGY]")

    print()
    print("=" * 80)
    print("GENERATING LUCIDCHART EXPORTS")
    print("=" * 80)

    # Generate Lucidchart exports
    lucid_success = generate_lucidchart_export(all_flow_records, zones, output_diagrams)

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total applications: {stats['total']}")
    print(f"  Skipped (no flows): {stats['skipped']}")
    print()
    print("Diagrams:")
    print(f"  ✓ Success: {stats['diagrams_success']}")
    print(f"  ✗ Failed: {stats['diagrams_failed']}")
    print()
    print("Word Documents:")
    print(f"  ✓ Success: {stats['docx_success']}")
    print(f"  ✗ Failed: {stats['docx_failed']}")
    print()
    print("Lucidchart Exports:")
    print(f"  {'✓ Generated' if lucid_success else '✗ Failed'}")
    print()
    print("=" * 80)
    print("OUTPUT LOCATIONS")
    print("=" * 80)
    print(f"Diagrams (.mmd + .html): {output_diagrams}")
    print(f"Word Reports (.docx): {output_reports}")
    print(f"Lucidchart (.csv): {output_diagrams}")
    print()
    print(f"Log file: {log_file}")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        sys.exit(1)
