"""
Generate Comprehensive Solution Design Documents
================================================
Generates detailed Solution Design documents for all applications using
the comprehensive document generator.

Usage:
    python generate_solution_design_docs.py

Output:
    outputs_final/word_reports/architecture/Solution_Design-{AppID}.docx

Author: Enterprise Architecture Team
Version: 1.0
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from comprehensive_solution_doc_generator import generate_comprehensive_solution_document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('solution_docs_generation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_application_data(topology_file: str) -> dict:
    """Load application topology data

    Args:
        topology_file: Path to topology JSON file

    Returns:
        Dictionary of application data
    """
    try:
        with open(topology_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        topology = data.get('topology', {})
        logger.info(f"Loaded data for {len(topology)} applications")

        return topology
    except FileNotFoundError:
        logger.warning(f"Topology file not found: {topology_file}")
        return {}
    except Exception as e:
        logger.error(f"Error loading topology data: {e}")
        return {}


def find_application_diagrams(app_name: str, diagrams_dir: Path) -> tuple:
    """Find PNG and Mermaid diagrams for application

    Args:
        app_name: Application name
        diagrams_dir: Directory containing diagrams

    Returns:
        Tuple of (png_path, mermaid_path)
    """
    png_path = diagrams_dir / f"{app_name}_application_diagram.png"
    mermaid_path = diagrams_dir / f"{app_name}_application_diagram.mmd"

    return (
        str(png_path) if png_path.exists() else None,
        str(mermaid_path) if mermaid_path.exists() else None
    )


def generate_all_solution_docs(
    topology_data: dict,
    diagrams_dir: Path,
    output_dir: Path
):
    """Generate solution design documents for all applications

    Args:
        topology_data: Dictionary of application topology data
        diagrams_dir: Directory containing diagrams
        output_dir: Output directory for generated documents
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("GENERATING SOLUTION DESIGN DOCUMENTS")
    logger.info("=" * 80)

    total_apps = len(topology_data)
    successful = 0
    failed = 0
    skipped = 0

    for idx, (app_name, app_data) in enumerate(topology_data.items(), 1):
        logger.info(f"\n[{idx}/{total_apps}] Processing: {app_name}")

        # Find diagrams
        png_path, mermaid_path = find_application_diagrams(app_name, diagrams_dir)

        if not png_path and not mermaid_path:
            logger.warning(f"  No diagrams found for {app_name} - skipping")
            skipped += 1
            continue

        # Output path
        output_path = output_dir / f"Solution_Design-{app_name}.docx"

        try:
            # Generate document
            generate_comprehensive_solution_document(
                app_name=app_name,
                app_data=app_data,
                png_path=png_path,
                mermaid_path=mermaid_path,
                output_path=str(output_path)
            )

            successful += 1
            logger.info(f"  [OK] Document generated: {output_path.name}")

        except Exception as e:
            logger.error(f"  [FAIL] Failed to generate document: {e}")
            failed += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total applications: {total_apps}")
    logger.info(f"Documents generated: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped (no diagrams): {skipped}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 80)


def main():
    """Main execution function"""
    start_time = datetime.now()

    logger.info("\n" + "=" * 80)
    logger.info("SOLUTION DESIGN DOCUMENT GENERATOR")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80 + "\n")

    # Paths
    base_dir = Path(__file__).parent
    topology_file = base_dir / 'outputs_final' / 'incremental_topology.json'
    diagrams_dir = base_dir / 'outputs_final' / 'diagrams'
    output_dir = base_dir / 'outputs_final' / 'word_reports' / 'architecture'

    # Check if topology file exists
    if not topology_file.exists():
        logger.error(f"Topology file not found: {topology_file}")
        logger.info("\nPlease run the analysis pipeline first:")
        logger.info("  python start_system.py")
        logger.info("  or")
        logger.info("  python run_complete_analysis.py")
        return

    # Load application data
    logger.info("Loading application topology data...")
    topology_data = load_application_data(str(topology_file))

    if not topology_data:
        logger.error("No application data found!")
        return

    # Check diagrams directory
    if not diagrams_dir.exists():
        logger.error(f"Diagrams directory not found: {diagrams_dir}")
        return

    logger.info(f"Diagrams directory: {diagrams_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("")

    # Generate documents
    generate_all_solution_docs(topology_data, diagrams_dir, output_dir)

    # Completion
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    logger.info(f"\n[SUCCESS] All done! Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"[FOLDER] Documents saved to: {output_dir}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n[WARNING]  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)
