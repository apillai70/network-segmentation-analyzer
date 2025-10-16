#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Report Generation with Template-Based Diagrams
===========================================================
Generates application-level data flow diagrams and reports following
the Data Flow Diagram template format.

Features:
- Template-based diagrams (circles, rectangles, color-coded)
- Application-level flows only (NO ports/protocols)
- Markov chain predictions (dashed lines, different colors)
- Integrates with incremental learning pipeline
- Word documents with embedded diagrams

Author: Enterprise Security Team
Version: 2.0 - Template-based Application Reports
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
from application_diagram_generator import ApplicationDiagramGenerator
from docx_generator import SolutionsArchitectureDocument
from utils.hostname_resolver import HostnameResolver
from persistence import create_persistence_manager

# Setup logging
log_file = Path('logs') / f'app_reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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


def load_flow_records(app_dir):
    """Load flow records from application directory"""
    flows_file = app_dir / 'flows.csv'

    if not flows_file.exists():
        return []

    df = pd.read_csv(flows_file)

    records = []
    for _, row in df.iterrows():
        try:
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


def load_predictions(app_id):
    """Load Markov chain predictions for application"""
    predictions_file = Path('persistent_data/predictions') / f'{app_id}_predictions.json'

    if not predictions_file.exists():
        return None

    try:
        with open(predictions_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"No predictions for {app_id}: {e}")
        return None


def generate_app_diagram(app_id, flow_records, topology_data, predictions, hostname_resolver, output_dir):
    """Generate application-level data flow diagram"""
    try:
        diagram_gen = ApplicationDiagramGenerator(hostname_resolver=hostname_resolver)

        mmd_path = output_dir / f"{app_id}_application_diagram.mmd"

        diagram_gen.generate_application_diagram(
            app_name=app_id,
            flow_records=flow_records,
            topology_data=topology_data,
            predictions=predictions,
            output_path=str(mmd_path)
        )

        return True, mmd_path
    except Exception as e:
        logger.error(f"Failed to generate diagram for {app_id}: {e}")
        return False, None


def generate_lucidchart_export(all_records, zones, predictions_map, output_dir):
    """Generate Lucidchart CSV exports with predictions"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Application-level export (NO infrastructure details)
        app_csv = output_dir / f"lucidchart_applications_{timestamp}.csv"
        with open(app_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Id', 'Name', 'Shape Library', 'Shape', 'Color', 'Type'])

            node_ids = set()

            # Add observed applications
            for record in all_records:
                if record.app_name and record.app_name not in node_ids:
                    writer.writerow([
                        record.app_name,
                        record.app_name,
                        'standard',
                        'Ellipse',  # Circle for services
                        '#ccffff',  # Cyan for observed
                        'observed'
                    ])
                    node_ids.add(record.app_name)

            # Add predicted applications
            for app_id, predictions in predictions_map.items():
                pred_deps = predictions.get('predicted_dependencies', [])
                for pred in pred_deps:
                    pred_name = pred.get('name', 'Unknown')
                    if pred_name not in node_ids:
                        writer.writerow([
                            pred_name,
                            pred_name,
                            'standard',
                            'Ellipse',  # Circle for predicted services
                            '#ffcccc',  # Pink for predicted
                            'predicted'
                        ])
                        node_ids.add(pred_name)

            # Write flows
            writer.writerow([])
            writer.writerow(['Source', 'Target', 'Line Style', 'Label', 'Type'])

            # Observed flows
            for record in all_records[:500]:  # Limit for performance
                if record.app_name and record.dst_ip:
                    writer.writerow([
                        record.app_name,
                        record.dst_ip,
                        'solid',
                        'data flow',
                        'observed'
                    ])

            # Predicted flows
            for app_id, predictions in predictions_map.items():
                pred_deps = predictions.get('predicted_dependencies', [])
                for pred in pred_deps:
                    pred_name = pred.get('name', 'Unknown')
                    label = pred.get('description', 'predicted flow')
                    writer.writerow([
                        app_id,
                        pred_name,
                        'dashed',
                        f'predicted: {label}',
                        'predicted'
                    ])

        logger.info(f"Generated Lucidchart export: {app_csv}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate Lucidchart export: {e}")
        return False


def main():
    """Main execution"""

    print("=" * 80)
    print("APPLICATION REPORT GENERATION - TEMPLATE-BASED")
    print("=" * 80)
    print()
    print("Following Data Flow Diagram template format:")
    print("  ⚪ Circles = Services/APIs")
    print("  ▭ Rectangles = Data stores")
    print("  ▢ Rounded Rectangles = External systems")
    print("  ─── Solid lines = Observed flows (actual data)")
    print("  ╌╌╌ Dashed lines = Predicted flows (Markov chain)")
    print("  🎨 Color-coded by security zone")
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

    # Create hostname resolver (demo mode)
    hostname_resolver = HostnameResolver(demo_mode=True)

    # Track statistics
    stats = {
        'total': total_apps,
        'diagrams_success': 0,
        'diagrams_failed': 0,
        'with_predictions': 0,
        'without_predictions': 0
    }

    all_flow_records = []
    predictions_map = {}

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
            continue

        # Add to global list
        all_flow_records.extend(flow_records)

        # Load topology data
        topology_data = load_topology_data(app_id)

        # Load predictions (Markov chain)
        predictions = load_predictions(app_id)
        if predictions:
            predictions_map[app_id] = predictions
            stats['with_predictions'] += 1
        else:
            stats['without_predictions'] += 1

        # Generate diagram
        diagram_success, mmd_path = generate_app_diagram(
            app_id, flow_records, topology_data, predictions, hostname_resolver, output_diagrams
        )

        if diagram_success:
            stats['diagrams_success'] += 1
            pred_indicator = "[DATA]+🔮" if predictions else "[DATA]"
            print(f"[{pred_indicator} [OK]]", end=' ', flush=True)
        else:
            stats['diagrams_failed'] += 1
            print("[DIAG [ERROR]]", end=' ', flush=True)

        # Show zone
        if topology_data:
            zone = topology_data.get('security_zone', 'UNKNOWN')
            print(f"[{zone}]")
        else:
            print("[NO_TOPOLOGY]")

    print()
    print("=" * 80)
    print("GENERATING LUCIDCHART EXPORTS")
    print("=" * 80)

    # Generate Lucidchart exports with predictions
    lucid_success = generate_lucidchart_export(all_flow_records, {}, predictions_map, output_diagrams)

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total applications: {stats['total']}")
    print(f"  With predictions: {stats['with_predictions']}")
    print(f"  Without predictions: {stats['without_predictions']}")
    print()
    print("Diagrams (Template-based):")
    print(f"  [OK] Success: {stats['diagrams_success']}")
    print(f"  [ERROR] Failed: {stats['diagrams_failed']}")
    print()
    print("Lucidchart Exports:")
    print(f"  {'[OK] Generated (with predictions)' if lucid_success else '[ERROR] Failed'}")
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
        logger.warning("\n[WARNING]️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n[ERROR] Error: {e}", exc_info=True)
        sys.exit(1)
