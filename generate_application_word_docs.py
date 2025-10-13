#!/usr/bin/env python3
"""
Generate Word Documents for All Applications
=============================================
Creates individual Word documents for each application with embedded PNG diagrams.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from app_docx_generator import generate_application_document

# Setup logging
log_file = Path('logs') / f'word_docs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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


def main():
    """Generate Word documents for all applications"""

    print("=" * 80)
    print("APPLICATION WORD DOCUMENT GENERATION")
    print("=" * 80)
    print()

    # Setup directories
    diagrams_dir = Path('outputs_final/diagrams')
    word_docs_dir = Path('outputs_final/word_reports/netseg')

    word_docs_dir.mkdir(parents=True, exist_ok=True)

    # Find all PNG diagram files
    png_files = list(diagrams_dir.glob('*_application_diagram.png'))
    total_apps = len(png_files)

    logger.info(f"Found {total_apps} application PNG diagrams")

    if total_apps == 0:
        logger.error("No PNG diagrams found in outputs_final/diagrams/")
        return

    print()
    print("=" * 80)
    print("GENERATING WORD DOCUMENTS")
    print("=" * 80)

    stats = {
        'total': total_apps,
        'success': 0,
        'failed': 0
    }

    # Process each application
    for i, png_file in enumerate(sorted(png_files), 1):
        # Extract app name from filename
        app_name = png_file.stem.replace('_application_diagram', '')

        print(f"\n[{i}/{total_apps}] {app_name}...", end=' ', flush=True)

        # Output path
        docx_path = word_docs_dir / f"{app_name}_architecture.docx"

        try:
            # Generate Word document
            generate_application_document(
                app_name=app_name,
                png_path=str(png_file),
                output_path=str(docx_path)
            )

            stats['success'] += 1
            print("[OK]")

        except Exception as e:
            logger.error(f"Failed to generate Word doc for {app_name}: {e}")
            stats['failed'] += 1
            print("[FAILED]")

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total applications: {stats['total']}")
    print(f"  Success: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print()
    print("=" * 80)
    print("OUTPUT LOCATION")
    print("=" * 80)
    print(f"Word Documents (.docx): {word_docs_dir}")
    print()
    print(f"Log file: {log_file}")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nWarning: Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        sys.exit(1)
