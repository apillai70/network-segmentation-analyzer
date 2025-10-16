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
import subprocess
import tempfile
import shutil
import argparse

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

# Add these imports at the top with the other imports
import subprocess
import tempfile
import shutil

# Add these functions after the imports section, before setup_zones()

def find_mmdc():
    """
    Find mmdc command with Windows + GitBash support
    
    Returns:
        str: Path to mmdc command, or None if not found
    """
    project_root = Path(__file__).parent
    
    # Method 1: Add nodeenv to PATH first (helps with GitBash on Windows)
    nodeenv_scripts = project_root / 'nodeenv' / 'Scripts'
    if nodeenv_scripts.exists():
        os.environ['PATH'] = f"{nodeenv_scripts};{os.environ['PATH']}"
        logger.debug(f"Added to PATH: {nodeenv_scripts}")
    
    # Method 2: Check if mmdc is now in PATH (works after adding nodeenv)
    mmdc_in_path = shutil.which('mmdc')
    if mmdc_in_path:
        try:
            result = subprocess.run([mmdc_in_path, '--version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"✓ Found mmdc in PATH: {mmdc_in_path}")
                return mmdc_in_path
        except:
            pass
    
    # Method 3: Check nodeenv directly with .cmd extension (Windows)
    for ext in ['.cmd', '.bat', '']:
        nodeenv_mmdc = project_root / 'nodeenv' / 'Scripts' / f'mmdc{ext}'
        if nodeenv_mmdc.exists():
            try:
                result = subprocess.run([str(nodeenv_mmdc), '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"✓ Found mmdc in nodeenv: {nodeenv_mmdc}")
                    return str(nodeenv_mmdc)
            except:
                pass
    
    # Method 4: Check Windows npm global location
    if sys.platform == 'win32':
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            for ext in ['.cmd', '.bat']:
                npm_mmdc = Path(user_profile) / 'AppData' / 'Roaming' / 'npm' / f'mmdc{ext}'
                if npm_mmdc.exists():
                    try:
                        result = subprocess.run([str(npm_mmdc), '--version'], 
                                              capture_output=True, timeout=5)
                        if result.returncode == 0:
                            logger.info(f"✓ Found mmdc in npm global: {npm_mmdc}")
                            return str(npm_mmdc)
                    except:
                        pass
    
    # Method 5: Last resort - try 'mmdc' directly
    try:
        result = subprocess.run(['mmdc', '--version'], 
                              capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ Found mmdc (direct command)")
            return 'mmdc'
    except:
        pass
    
    logger.warning("✗ mmdc (mermaid-cli) not found")
    logger.info("Install with: npm install -g @mermaid-js/mermaid-cli")
    return None


def generate_png_from_mmd(mmd_path, mmdc_cmd):
    """
    Generate PNG from Mermaid .mmd file
    
    Args:
        mmd_path: Path to .mmd file
        mmdc_cmd: Path to mmdc command
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read and clean mermaid content
        with open(mmd_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract graph content (remove markdown code fences if present)
        lines = content.split('\n')
        graph_lines = []
        in_graph = False
        
        for line in lines:
            if line.strip().startswith('```mermaid'):
                in_graph = True
                continue
            elif line.strip() == '```':
                in_graph = False
                break
            elif in_graph or (not line.strip().startswith('```')):
                graph_lines.append(line)
        
        clean_content = '\n'.join(graph_lines).strip()
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', 
                                        delete=False, encoding='utf-8') as tmp:
            tmp.write(clean_content)
            tmp_path = tmp.name
        
        # Generate PNG with high resolution (scale=4 for 300+ DPI equivalent)
        png_path = mmd_path.with_suffix('.png')
        # Use puppeteer config to disable sandboxing for customer environments
        puppeteer_config = Path(__file__).parent / 'puppeteer-config.json'
        result = subprocess.run(
            [mmdc_cmd, '-i', tmp_path, '-o', str(png_path),
             '-p', str(puppeteer_config),
             '-w', '4800', '-H', '3600', '-s', '4', '-t', 'neutral', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        if result.returncode == 0:
            return True
        else:
            logger.debug(f"mmdc error for {mmd_path.name}: {result.stderr[:100]}")
            return False
            
    except Exception as e:
        logger.debug(f"Failed to generate PNG for {mmd_path.name}: {e}")
        return False


def generate_pngs_for_all_diagrams(diagrams_dir, mmdc_cmd):
    """
    Generate PNG files for all .mmd diagrams
    
    Args:
        diagrams_dir: Directory containing .mmd files
        mmdc_cmd: Path to mmdc command
    
    Returns:
        dict: Statistics about PNG generation
    """
    if not mmdc_cmd:
        logger.warning("Skipping PNG generation - mmdc not found")
        return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
    
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING PNG DIAGRAMS")
    logger.info("=" * 80)
    
    # Find all .mmd files
    mmd_files = list(diagrams_dir.glob('*_diagram.mmd'))
    
    if not mmd_files:
        logger.info("No .mmd files found")
        return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
    
    stats = {
        'total': len(mmd_files),
        'success': 0,
        'failed': 0,
        'skipped': 0
    }
    
    print(f"\nGenerating {len(mmd_files)} PNG diagrams...")
    print()
    
    for i, mmd_file in enumerate(sorted(mmd_files), 1):
        app_id = mmd_file.stem.replace('_diagram', '')
        
        # Check if PNG already exists
        png_file = mmd_file.with_suffix('.png')
        if png_file.exists():
            print(f"[{i}/{len(mmd_files)}] {app_id} [SKIP - exists]")
            stats['skipped'] += 1
            continue
        
        # Generate PNG
        print(f"[{i}/{len(mmd_files)}] {app_id}...", end=' ', flush=True)
        
        if generate_png_from_mmd(mmd_file, mmdc_cmd):
            stats['success'] += 1
            print("[PNG ✓]")
        else:
            stats['failed'] += 1
            print("[PNG ✗]")
    
    print()
    logger.info(f"PNG Generation Results:")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  ✓ Success: {stats['success']}")
    logger.info(f"  ✗ Failed: {stats['failed']}")
    logger.info(f"  ⊘ Skipped: {stats['skipped']}")
    
    return stats
    
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


def load_flow_records(app_dir, hostname_resolver=None, filter_nonexistent=False):  # ← DISABLED
    """Load flow records from application directory with optional filtering

    Args:
        app_dir: Application directory path
        hostname_resolver: HostnameResolver instance for filtering (optional)
        filter_nonexistent: If True, filter flows with both IPs non-existent (default: True)

    Returns:
        List of FlowRecord objects (filtered if resolver provided)
    """
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

    # Apply filtering if hostname resolver provided
    #if hostname_resolver and filter_nonexistent and records:
        #from utils.flow_filter import apply_filtering_to_records
        #records = apply_filtering_to_records(
            #records,
            #hostname_resolver,
            #filter_enabled=True,
            #log_stats=False  # Don't log per-app (too verbose)
        #)

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


def generate_app_word_document(app_id, flow_records, topology_data, zones, output_dir, diagrams_dir):
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

        # Construct PNG path for diagram embedding
        png_path = diagrams_dir / f"{app_id}_diagram.png"
        png_path_str = str(png_path) if png_path.exists() else None

        # Generate document with PNG diagram
        doc_gen = SolutionsArchitectureDocument(
            analysis_results=analysis_results,
            zones=zones,
            rules=rules,
            png_path=png_path_str
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
    print("This will generate for each app:")
    print("  - Mermaid diagram (.mmd)")
    print("  - Interactive HTML diagram (.html)")
    print("  - PNG diagram (.png) [if mmdc available]")
    print("  - Word document report (.docx) [if not skipped]")
    print("  - Lucidchart CSV exports (combined)")
    print()
    print("=" * 80)

    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate network reports')
    parser.add_argument('--skip-docx', action='store_true',
                       help='Skip Word document generation (faster)')
    parser.add_argument('--skip-diagrams', action='store_true',
                       help='Skip diagram generation (Mermaid/HTML/PNG) - only generate documentation')
    parser.add_argument(
        '--apps',
        type=str,
        nargs='+',
        help='List of app codes to process (e.g., DNMET XECHK). If not specified, processes all apps.'
    )
    args = parser.parse_args()

    # Setup directories
    apps_dir = Path('persistent_data/applications')
    output_diagrams = Path('outputs_final/diagrams')
    output_reports = Path('outputs_final/word_reports/netseg')

    output_diagrams.mkdir(parents=True, exist_ok=True)
    output_reports.mkdir(parents=True, exist_ok=True)

    # Find mmdc early
    mmdc_cmd = find_mmdc()

    # Check if mmdc is available
    if mmdc_cmd:
        logger.info("✓ PNG generation will be enabled")
    else:
        logger.warning("⚠ PNG generation will be skipped (mmdc not found)")

    # Get application directories (filtered by --apps if provided)
    if args.apps:
        # Only process specified apps
        app_dirs = []
        for app_code in args.apps:
            app_path = apps_dir / app_code
            if app_path.exists() and app_path.is_dir():
                app_dirs.append(app_path)
            else:
                logger.warning(f"⚠ Warning: Application '{app_code}' not found in {apps_dir}")
    else:
        # Process all apps
        app_dirs = [d for d in apps_dir.iterdir() if d.is_dir()]

    total_apps = len(app_dirs)

    if args.apps:
        logger.info(f"Found {total_apps}/{len(args.apps)} requested applications to process")
    else:
        logger.info(f"Found {total_apps} applications to process")

    if total_apps == 0:
        logger.error("No applications found in persistent_data/applications/")
        return

    # Setup zones
    zones = setup_zones()

    # Create hostname resolver with filtering DISABLED
    hostname_resolver = HostnameResolver(
        demo_mode=True,
        filter_nonexistent=False,  # DISABLED
        mark_nonexistent=False      # DISABLED
    )

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

    # ========================================================================
    # MAIN PROCESSING LOOP WITH DEBUG
    # ========================================================================
    for i, app_dir in enumerate(sorted(app_dirs), 1):
        app_id = app_dir.name

        print(f"\n{'='*80}")
        print(f"[{i}/{total_apps}] Processing: {app_id}")
        print(f"{'='*80}")

        # Load flow records with filtering disabled
        flow_records = load_flow_records(app_dir, hostname_resolver, filter_nonexistent=False)

        # ===================================================================
        # DEBUG 1: Check what load_flow_records returned
        # ===================================================================
        print(f"\nDEBUG 1: After load_flow_records")
        print(f"  Records loaded: {len(flow_records)}")
        
        if not flow_records:
            print("[SKIP - No flows after loading]")
            stats['skipped'] += 1
            continue

        # ===================================================================
        # DEBUG 2: Inspect first record
        # ===================================================================
        if flow_records:
            r = flow_records[0]
            print(f"\nDEBUG 2: Sample record")
            print(f"  {r.src_ip} -> {r.dst_ip}")
            print(f"  Protocol: {r.protocol}")
            print(f"  Port: {r.port if hasattr(r, 'port') else 'N/A'}")
            print(f"  App name: {r.app_name}")
            print(f"  Has bytes: {hasattr(r, 'bytes')}")
            if hasattr(r, 'bytes'):
                print(f"  Bytes: {r.bytes}")

        # Add to global list
        all_flow_records.extend(flow_records)

        # Infer zones from IPs
        for record in flow_records:
            infer_zone_from_ip(record.src_ip, zones)
            infer_zone_from_ip(record.dst_ip, zones)

        # Load topology data
        topology_data = load_topology_data(app_id)

        # Generate diagram (unless skipped)
        diagram_success = False
        if not args.skip_diagrams:
            # ===================================================================
            # DEBUG 3: Before creating diagram generator
            # ===================================================================
            print(f"\nDEBUG 3: Creating MermaidDiagramGenerator")
            print(f"  Input records: {len(flow_records)}")

            # Generate diagram
            try:
                diagram_gen = MermaidDiagramGenerator(
                    flow_records=flow_records,
                    zones=zones,
                    hostname_resolver=hostname_resolver
                )

                # ===================================================================
                # DEBUG 4: After diagram generator init
                # ===================================================================
                print(f"\nDEBUG 4: After MermaidDiagramGenerator.__init__")
                print(f"  Generator.records: {len(diagram_gen.records)}")

                if len(diagram_gen.records) == 0:
                    print("  ⚠ WARNING: All records filtered out in MermaidDiagramGenerator!")
                    print("  Check diagrams.py __init__ lines 42-51 for filtering logic")

                mmd_path = output_diagrams / f"{app_id}_diagram.mmd"

                # ===================================================================
                # DEBUG 5: Before generate_app_diagram
                # ===================================================================
                print(f"\nDEBUG 5: Calling generate_app_diagram")
                print(f"  App name: {app_id}")
                print(f"  Output path: {mmd_path}")

                content = diagram_gen.generate_app_diagram(app_id, str(mmd_path))

                # ===================================================================
                # DEBUG 6: After generate_app_diagram
                # ===================================================================
                print(f"\nDEBUG 6: After generate_app_diagram")
                print(f"  Content length: {len(content)} chars")
                print(f"  File exists: {mmd_path.exists()}")
                if mmd_path.exists():
                    with open(mmd_path, 'r') as f:
                        lines = f.readlines()
                    print(f"  File lines: {len(lines)}")
                    print(f"  Has nodes: {'Application Components' in ''.join(lines)}")
                    print(f"  Has flows: {'Traffic Flows' in ''.join(lines)}")

                diagram_success = len(content) > 0 and mmd_path.exists()
                if diagram_success:
                    stats['diagrams_success'] += 1
                    print(f"\n✓ [DIAG SUCCESS]")
                else:
                    stats['diagrams_failed'] += 1
                    print(f"\n✗ [DIAG FAILED]")
                    
            except Exception as e:
                print(f"\n✗ [DIAG EXCEPTION]: {e}")
                import traceback
                traceback.print_exc()
                stats['diagrams_failed'] += 1
                diagram_success = False

            # ===================================================================
            # WORD DOCUMENT GENERATION (Architecture Document)
            # ===================================================================
            if not args.skip_docx and diagram_success:
                print("\n[DOCX]...", end=' ', flush=True)
                
                # Architecture document goes to /architecture subfolder
                arch_output = Path('outputs_final/word_reports/architecture')
                arch_output.mkdir(parents=True, exist_ok=True)
                
                docx_path = arch_output / f"{app_id}_architecture.docx"
                
                try:
                    # Import the generator
                    from app_docx_generator import generate_application_document
                    
                    # Check if PNG exists (will be generated later by PNG batch)
                    # For now, we'll use the mmd diagram
                    # Word doc generation will happen AFTER PNG generation completes
                    
                    # We'll generate this later after PNGs are created
                    print("[DEFER - After PNG]")
                    
                except Exception as e:
                    logger.error(f"Word doc setup failed for {app_id}: {e}")
                    stats['docx_failed'] += 1
                    print("[FAILED]")
            elif not args.skip_docx:
                print("\n[DOCX SKIP - No diagram]")
            else:
                print("\n[DOCX SKIP - Flag set]")

            # Show zone
            if topology_data:
                zone = topology_data.get('security_zone', 'UNKNOWN')
                print(f"Zone: [{zone}]")
            else:
                print(f"Zone: [NO_TOPOLOGY]")

            print(f"{'='*80}\n")
    # ========================================================================
    # PNG GENERATION
    # ========================================================================
    if not args.skip_diagrams:
        png_stats = generate_pngs_for_all_diagrams(output_diagrams, mmdc_cmd)
    else:
        png_stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

    # ========================================================================
    # WORD DOCUMENT GENERATION (After PNGs are ready)
    # ========================================================================
    if not args.skip_docx:
        print()
        print("=" * 80)
        print("GENERATING WORD DOCUMENTS (Architecture)")
        print("=" * 80)

        from app_docx_generator import generate_application_document

        arch_output = Path('outputs_final/word_reports/architecture')
        arch_output.mkdir(parents=True, exist_ok=True)

        # Find all PNG diagrams
        png_files = list(output_diagrams.glob('*_diagram.png'))

        for png_file in png_files:
            app_id = png_file.stem.replace('_diagram', '')
            docx_path = arch_output / f"{app_id}_architecture.docx"

            print(f"  {app_id}...", end=' ', flush=True)

            try:
                generate_application_document(
                    app_name=app_id,
                    png_path=str(png_file),
                    output_path=str(docx_path)
                )
                stats['docx_success'] += 1
                print("[OK]")
            except Exception as e:
                logger.error(f"Failed: {e}")
                stats['docx_failed'] += 1
                print("[FAILED]")

    print()
    print("=" * 80)
    print("GENERATING LUCIDCHART EXPORTS")
    print("=" * 80)

    # Generate Lucidchart exports
    lucid_success = generate_lucidchart_export(all_flow_records, zones, output_diagrams)

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
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
    print("PNG Diagrams:")
    if mmdc_cmd:
        print(f"  ✓ Success: {png_stats['success']}")
        print(f"  ✗ Failed: {png_stats['failed']}")
        print(f"  ⊘ Skipped: {png_stats['skipped']}")
    else:
        print(f"  ⚠ Skipped (mmdc not found)")
    print()
    print("Lucidchart Exports:")
    print(f"  {'✓ Generated' if lucid_success else '✗ Failed'}")
    print()
    print("=" * 80)
    print("OUTPUT LOCATIONS")
    print("=" * 80)
    print(f"Diagrams (.mmd + .html + .png): {output_diagrams}")
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
