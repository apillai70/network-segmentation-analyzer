#!/usr/bin/env python3
"""
Batch Generator for Threat Surface Analysis Documents
======================================================
Generates threat surface analysis and network segmentation
best practices documents for all analyzed applications.

Now includes:
1. Word documents (existing)
2. NetworkX-based threat analysis (NEW)
3. HTML visualizations (NEW)

Usage:
    python generate_threat_surface_docs.py

Output Locations:
    - Word docs: outputs_final/word_reports/threat_surface/
    - JSON analysis: outputs/threat_analysis/
    - HTML viz: outputs/visualizations/
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from src.threat_surface_netseg_generator import generate_threat_surface_document

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

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


def run_networkx_threat_analysis():
    """
    Run NetworkX-based threat analysis using graph_analyzer and threat_surface_analyzer

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info("STEP 1: Running NetworkX-based Threat Surface Analysis")
    logger.info("="*80)

    try:
        # Import the new threat analysis modules
        from src.parser import parse_network_logs
        from src.graph_analyzer import GraphAnalyzer
        from src.threat_surface_analyzer import ThreatSurfaceAnalyzer

        # Parse network flows from processed files OR master topology
        logger.info("Loading network flows...")

        # Try data/input/processed first (where files are moved after processing)
        processed_dir = Path('data/input/processed')
        if processed_dir.exists() and list(processed_dir.glob('*.csv')):
            logger.info("  Reading from data/input/processed/...")
            parser = parse_network_logs('data/input/processed')
        # Fallback to data/input if files haven't been moved yet
        elif Path('data/input').exists() and list(Path('data/input').glob('*.csv')):
            logger.info("  Reading from data/input/...")
            parser = parse_network_logs('data/input')
        else:
            logger.error("  No CSV files found in data/input/ or data/input/processed/")
            logger.error("  Please run batch processing first: python run_batch_processing.py --batch-size 10")
            return None

        logger.info(f"  ✓ Loaded {len(parser.records)} flow records")

        # Build graph
        logger.info("Building network graph with NetworkX...")
        graph_analyzer = GraphAnalyzer(parser.records)
        logger.info(f"  ✓ Graph built: {graph_analyzer.graph.number_of_nodes()} nodes, "
                   f"{graph_analyzer.graph.number_of_edges()} edges")

        # Perform threat surface analysis
        logger.info("Analyzing threat surface (attack paths, exposure, chokepoints)...")
        threat_analyzer = ThreatSurfaceAnalyzer(graph_analyzer)
        results = threat_analyzer.analyze_attack_surface()

        summary = results.get('summary', {})
        logger.info(f"  ✓ Found {summary.get('total_attack_paths', 0)} attack paths")
        logger.info(f"  ✓ Identified {summary.get('exposed_nodes', 0)} high-exposure nodes")
        logger.info(f"  ✓ {summary.get('critical_assets_at_risk', 0)} critical assets at risk")

        # Export results to JSON
        output_dir = Path('outputs/threat_analysis')
        output_dir.mkdir(parents=True, exist_ok=True)

        json_output = output_dir / 'threat_surface_analysis.json'
        threat_analyzer.export_analysis(str(json_output))
        logger.info(f"  ✓ JSON exported to: {json_output}")

        logger.info("[OK] NetworkX threat analysis completed successfully")
        return True

    except Exception as e:
        logger.error(f"[ERROR] NetworkX threat analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_threat_html_visualization():
    """
    Generate HTML visualization from threat analysis JSON

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info("STEP 2: Generating HTML Threat Surface Visualization")
    logger.info("="*80)

    try:
        # Check if JSON exists
        json_path = Path('outputs/threat_analysis/threat_surface_analysis.json')

        if not json_path.exists():
            logger.warning(f"[WARNING] Threat analysis JSON not found: {json_path}")
            logger.warning("Skipping HTML generation. Run threat analysis first.")
            return False

        # Read threat analysis results
        with open(json_path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loading threat data from: {json_path}")

        # Import HTML generator functions (inline to avoid import at top)
        import sys
        from pathlib import Path

        # Load generate_threat_html module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generate_threat_html",
            Path(__file__).parent / "generate_threat_html.py"
        )
        threat_html_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(threat_html_module)

        # Generate HTML
        output_path = threat_html_module.generate_threat_html()

        if output_path:
            logger.info(f"  ✓ HTML generated: {output_path}")
            logger.info("[OK] HTML visualization completed successfully")
            return True
        else:
            logger.warning("[WARNING] HTML generation returned no output")
            return False

    except Exception as e:
        logger.error(f"[ERROR] HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Generate threat surface documents for all applications"""
    print("="*80)
    print("THREAT SURFACE ANALYSIS & NETWORK SEGMENTATION DOCUMENTS")
    print("="*80)
    print()

    # =========================================================================
    # NEW: Run NetworkX-based threat analysis first
    # =========================================================================
    networkx_success = run_networkx_threat_analysis()
    print()

    # Generate HTML visualization if analysis succeeded
    if networkx_success:
        html_success = generate_threat_html_visualization()
        print()
    else:
        logger.warning("[WARNING] Skipping HTML generation (threat analysis failed)")
        html_success = False

    print()
    logger.info("="*80)
    logger.info("STEP 3: Generating Word Documents (per-application)")
    logger.info("="*80)

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

            print("[OK]")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Error: {e}")
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
    print(f"[FOLDER] Word Documents: {output_dir}")

    # Show new outputs
    if networkx_success:
        print(f"[FOLDER] Threat Analysis JSON: outputs/threat_analysis/")
        print(f"[FOLDER] HTML Visualization: outputs/visualizations/threat_surface.html")

    print("="*80)

    if failed_apps:
        print()
        print("[WARNING] Failed Applications:")
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
