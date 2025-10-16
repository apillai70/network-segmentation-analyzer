#!/usr/bin/env python3
"""
Generate DNS Validation Reports
=================================
Analyzes DNS validation data from all applications and generates comprehensive reports

Reads DNS validation data from topology JSON files and creates:
- Word document with findings and recommendations
- CSV export for detailed analysis
- JSON summary for programmatic access

Usage:
    python generate_dns_validation_report.py
    python generate_dns_validation_report.py --topology-dir persistent_data/topology
    python generate_dns_validation_report.py --output-dir outputs_final/dns_reports

Author: Enterprise Security Team
Version: 1.0
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dns_validation_reporter import DNSValidationReporter, collect_dns_validation_from_apps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate DNS Validation Reports from topology data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports with default settings
  python generate_dns_validation_report.py

  # Specify custom topology directory
  python generate_dns_validation_report.py --topology-dir persistent_data/topology

  # Specify custom output directory
  python generate_dns_validation_report.py --output-dir outputs_final/dns_reports

  # Generate only specific report format
  python generate_dns_validation_report.py --format word
  python generate_dns_validation_report.py --format csv
  python generate_dns_validation_report.py --format json
        """
    )

    parser.add_argument(
        '--topology-dir',
        default='persistent_data/topology',
        help='Directory containing topology JSON files (default: persistent_data/topology)'
    )

    parser.add_argument(
        '--output-dir',
        default='outputs_final/dns_reports',
        help='Output directory for reports (default: outputs_final/dns_reports)'
    )

    parser.add_argument(
        '--format',
        choices=['all', 'word', 'csv', 'json'],
        default='all',
        help='Report format to generate (default: all)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("DNS VALIDATION REPORT GENERATOR")
    logger.info("="*80)
    logger.info(f"  Topology directory: {args.topology_dir}")
    logger.info(f"  Output directory:   {args.output_dir}")
    logger.info(f"  Report format:      {args.format}")
    logger.info("="*80 + "\n")

    # Check if topology directory exists
    topology_path = Path(args.topology_dir)
    if not topology_path.exists():
        logger.error(f"ERROR: Topology directory not found: {topology_path}")
        logger.error("Please run batch processing first to generate topology files")
        return 1

    # Collect DNS validation data from all topology files
    logger.info("Collecting DNS validation data from topology files...")
    reporter = collect_dns_validation_from_apps(topology_dir=args.topology_dir)

    # Check if any validation data was found
    if reporter.stats['total_ips_validated'] == 0:
        logger.warning("\n" + "="*80)
        logger.warning("WARNING: No DNS validation data found")
        logger.warning("="*80)
        logger.warning("  No validation metadata found in topology files")
        logger.warning("  This means DNS validation has not been run yet")
        logger.warning("")
        logger.warning("To generate DNS validation data:")
        logger.warning("  1. Run batch processing: python run_batch_processing.py")
        logger.warning("  2. Ensure DNS validation is enabled in incremental_learner.py")
        logger.warning("  3. Re-run this script after processing completes")
        logger.warning("="*80 + "\n")
        return 1

    # Set custom output directory
    reporter.output_dir = Path(args.output_dir)
    reporter.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate reports based on format selection
    reports = {}

    if args.format == 'all':
        reports = reporter.generate_all_reports()
    elif args.format == 'word':
        reports['word'] = reporter.generate_word_report()
        logger.info(f"\n✓ Word report generated: {reports['word']}")
    elif args.format == 'csv':
        reports['csv'] = reporter.export_to_csv()
        logger.info(f"\n✓ CSV export generated: {reports['csv']}")
    elif args.format == 'json':
        reports['json'] = reporter.export_to_json()
        logger.info(f"\n✓ JSON export generated: {reports['json']}")

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"  Applications Analyzed:      {reporter.stats['applications_analyzed']}")
    logger.info(f"  Total IPs Validated:        {reporter.stats['total_ips_validated']}")
    logger.info(f"  Valid DNS (Perfect Match):  {reporter.stats['total_valid']}")
    logger.info(f"  Valid DNS (Multiple IPs):   {reporter.stats['total_valid_multiple']}")
    logger.info(f"  DNS Mismatches:             {reporter.stats['total_mismatches']}")
    logger.info(f"  NXDOMAIN:                   {reporter.stats['total_nxdomain']}")
    logger.info(f"  Validation Failures:        {reporter.stats['total_failed']}")
    logger.info("="*80)

    # Show report paths
    if reports:
        logger.info("\nGenerated Reports:")
        for format_type, path in reports.items():
            logger.info(f"  {format_type.upper():6} - {path}")

    logger.info("\n✅ DNS Validation Report Generation Complete\n")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Report generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
