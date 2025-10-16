#!/usr/bin/env python3
"""
Generate Enterprise Network Segmentation Strategy Document
===========================================================
Creates a comprehensive, data-driven segmentation strategy document
with multiple options and pros/cons analysis.

Usage:
    python generate_segmentation_strategy.py

Requirements:
    - Master topology must exist: persistent_data/master_topology.json
    - Run build_master_topology.py first if it doesn't exist

Output:
    outputs_final/word_reports/Enterprise_Network_Segmentation_Strategy.docx
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from enterprise_segmentation_strategy_generator import generate_enterprise_segmentation_strategy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main execution"""
    print()
    print("="*80)
    print("ENTERPRISE NETWORK SEGMENTATION STRATEGY DOCUMENT GENERATOR")
    print("="*80)
    print()

    # Check if master topology exists
    master_topology_path = Path('persistent_data/master_topology.json')

    if not master_topology_path.exists():
        print("[ERROR] Master topology not found!")
        print()
        print("You must run the following command first:")
        print("  python build_master_topology.py")
        print()
        print("This will create: persistent_data/master_topology.json")
        print()
        return 1

    logger.info(f"Using master topology: {master_topology_path}")

    # Output path
    output_path = Path('outputs_final/word_reports/Enterprise_Network_Segmentation_Strategy.docx')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Generate document
        logger.info("Generating enterprise segmentation strategy document...")
        result = generate_enterprise_segmentation_strategy(
            master_topology_path=str(master_topology_path),
            output_path=str(output_path)
        )

        print()
        print("[SUCCESS] Enterprise segmentation strategy document generated!")
        print(f"  Location: {result}")
        print()
        print("This document contains:")
        print("  - Current state network analysis (data-driven)")
        print("  - 4 segmentation options (Minimal, Standard, Advanced, Micro-segmentation)")
        print("  - Detailed pros & cons for each option")
        print("  - Cost-benefit analysis")
        print("  - Comparison matrix")
        print("  - Data-driven recommendations")
        print("  - Implementation roadmap")
        print()
        print("="*80)

    except Exception as e:
        logger.error(f"Failed to generate document: {e}")
        print()
        print(f"[ERROR] Failed to generate document: {e}")
        print()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
