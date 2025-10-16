#!/usr/bin/env python3
"""
Generate Enterprise Network Analysis Report
=============================================
Consolidates data from all applications into comprehensive enterprise report

Analyzes:
- All 139 applications
- Cross-application dependencies
- Security zone distribution
- DNS validation summaries
- Network segmentation recommendations

Usage:
    python generate_enterprise_report.py
    python generate_enterprise_report.py --topology-dir persistent_data/topology
    python generate_enterprise_report.py --output-dir results

Author: Enterprise Security Team
Version: 1.0
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from enterprise_report_generator import EnterpriseNetworkReportGenerator

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
        description='Generate Enterprise Network Analysis Report from all applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate reports with default settings
  python generate_enterprise_report.py

  # Specify custom topology directory
  python generate_enterprise_report.py --topology-dir persistent_data/topology

  # Specify custom output directory
  python generate_enterprise_report.py --output-dir results

  # Generate only JSON report
  python generate_enterprise_report.py --format json

  # Generate only Word report
  python generate_enterprise_report.py --format word
        """
    )

    parser.add_argument(
        '--topology-dir',
        default='persistent_data/topology',
        help='Directory containing topology JSON files (default: persistent_data/topology)'
    )

    parser.add_argument(
        '--output-dir',
        default='results',
        help='Output directory for reports (default: results)'
    )

    parser.add_argument(
        '--format',
        choices=['all', 'json', 'word'],
        default='all',
        help='Report format to generate (default: all)'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("ENTERPRISE NETWORK ANALYSIS REPORT GENERATOR")
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

    # Create report generator
    generator = EnterpriseNetworkReportGenerator(
        topology_dir=args.topology_dir,
        output_dir=args.output_dir
    )

    # Load all topology data
    generator.load_all_topology_data()

    if len(generator.applications) == 0:
        logger.warning("\n" + "="*80)
        logger.warning("WARNING: No applications found")
        logger.warning("="*80)
        logger.warning("  No topology files found in directory")
        logger.warning("")
        logger.warning("To generate topology data:")
        logger.warning("  1. Run batch processing: python run_batch_processing.py")
        logger.warning("  2. Re-run this script after processing completes")
        logger.warning("="*80 + "\n")
        return 1

    # Analyze network topology
    generator.analyze_network_topology()

    # Generate reports based on format selection
    reports = {}

    if args.format == 'all':
        reports = generator.generate_all_reports()
    elif args.format == 'json':
        reports['json'] = generator.generate_json_report()
        logger.info(f"\n✓ JSON report generated: {reports['json']}")
    elif args.format == 'word':
        reports['word'] = generator.generate_word_report()
        logger.info(f"\n✓ Word report generated: {reports['word']}")

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"  Total Applications:     {generator.stats['total_applications']}")
    logger.info(f"  Total Dependencies:     {generator.stats['total_dependencies']}")
    logger.info(f"  Unique IP Addresses:    {generator.stats['total_unique_ips']}")
    logger.info(f"  Security Zones:         {len(generator.security_zones)}")
    logger.info(f"  Cross-Zone Connections: {generator.stats['cross_zone_connections']}")
    logger.info("="*80)

    # Show DNS validation stats if available
    dns_stats = generator.stats['dns_validation_summary']
    if dns_stats.get('apps_with_validation', 0) > 0:
        logger.info("\nDNS Validation Summary:")
        logger.info(f"  Applications Validated: {dns_stats['apps_with_validation']}")
        logger.info(f"  IPs Validated:          {dns_stats['total_validated']}")
        logger.info(f"  Valid:                  {dns_stats['total_valid']}")
        logger.info(f"  Mismatches:             {dns_stats['total_mismatches']}")
        logger.info(f"  NXDOMAIN:               {dns_stats['total_nxdomain']}")

    # Show zone distribution
    logger.info("\nSecurity Zone Distribution:")
    for zone in sorted(generator.security_zones.keys()):
        count = len(generator.security_zones[zone])
        percentage = (count / generator.stats['total_applications'] * 100) if generator.stats['total_applications'] > 0 else 0
        logger.info(f"  {zone:25} {count:4} apps ({percentage:5.1f}%)")

    # Show report paths
    if reports:
        logger.info("\nGenerated Reports:")
        for format_type, path in reports.items():
            logger.info(f"  {format_type.upper():6} - {path}")

    logger.info("\n✅ Enterprise Network Analysis Report Generation Complete\n")

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
