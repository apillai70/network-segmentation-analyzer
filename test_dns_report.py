#!/usr/bin/env python3
"""
Test DNS Validation Report Generation with Sample Data
========================================================
Creates sample DNS validation data and generates reports
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dns_validation_reporter import DNSValidationReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_validation_data():
    """Create sample validation data for testing"""

    # Create sample DNS validation metadata
    sample_metadata = {
        '8.8.8.8': {
            'valid': True,
            'ip': '8.8.8.8',
            'reverse_hostname': 'dns.google',
            'forward_ip': '8.8.4.4',
            'forward_ips': ['8.8.4.4', '8.8.8.8'],
            'mismatch': None,
            'status': 'valid_multiple_ips',
            'timestamp': datetime.now().timestamp()
        },
        '1.1.1.1': {
            'valid': True,
            'ip': '1.1.1.1',
            'reverse_hostname': 'one.one.one.one',
            'forward_ip': '1.1.1.1',
            'forward_ips': ['1.1.1.1', '1.0.0.1'],
            'mismatch': None,
            'status': 'valid',
            'timestamp': datetime.now().timestamp()
        },
        '10.164.105.136': {
            'valid': False,
            'ip': '10.164.105.136',
            'reverse_hostname': 'web-server.local',
            'forward_ip': '10.164.105.137',
            'forward_ips': ['10.164.105.137'],
            'mismatch': 'Forward DNS (10.164.105.137) ≠ Original IP (10.164.105.136)',
            'status': 'mismatch',
            'timestamp': datetime.now().timestamp()
        },
        '192.168.1.1': {
            'valid': False,
            'ip': '192.168.1.1',
            'reverse_hostname': None,
            'forward_ip': None,
            'forward_ips': [],
            'mismatch': 'Reverse DNS lookup returned NXDOMAIN',
            'status': 'nxdomain',
            'timestamp': datetime.now().timestamp()
        },
        '10.100.160.214': {
            'valid': True,
            'ip': '10.100.160.214',
            'reverse_hostname': 'mgmt-server01.corp.local',
            'forward_ip': '10.100.160.214',
            'forward_ips': ['10.100.160.214', '10.100.160.215'],
            'mismatch': None,
            'status': 'valid_multiple_ips',
            'timestamp': datetime.now().timestamp()
        },
        '10.1.2.3': {
            'valid': False,
            'ip': '10.1.2.3',
            'reverse_hostname': None,
            'forward_ip': None,
            'forward_ips': [],
            'mismatch': 'Reverse DNS lookup failed',
            'status': 'reverse_lookup_failed',
            'timestamp': datetime.now().timestamp()
        }
    }

    return sample_metadata


def create_sample_topology_with_validation():
    """Create sample topology file with DNS validation data"""

    logger.info("Creating sample topology with DNS validation data...")

    # Create test directory
    test_dir = Path('test_dns_data/topology')
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create 3 sample applications with validation data
    apps = ['TEST_APP_1', 'TEST_APP_2', 'TEST_APP_3']

    for app_id in apps:
        # Get sample metadata
        metadata = create_sample_validation_data()

        # Add app_id to each validation record
        for ip, validation in metadata.items():
            validation['app_id'] = app_id

        # Create topology structure
        topology = {
            'app_id': app_id,
            'security_zone': 'APP_TIER',
            'confidence': 0.85,
            'dependencies': [],
            'characteristics': [],
            'dns_validation': {
                'total_validated': len(metadata),
                'valid': sum(1 for v in metadata.values() if v['status'] == 'valid'),
                'valid_multiple_ips': sum(1 for v in metadata.values() if v['status'] == 'valid_multiple_ips'),
                'mismatch': sum(1 for v in metadata.values() if v['status'] == 'mismatch'),
                'nxdomain': sum(1 for v in metadata.values() if v['status'] == 'nxdomain'),
                'failed': sum(1 for v in metadata.values() if v['status'] not in ['valid', 'valid_multiple_ips', 'mismatch', 'nxdomain'])
            },
            'validation_metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }

        # Save to JSON
        json_path = test_dir / f'{app_id}.json'
        with open(json_path, 'w') as f:
            json.dump(topology, f, indent=2)

        logger.info(f"  Created: {json_path}")

    logger.info(f"Sample topology files created in: {test_dir}")
    return str(test_dir)


def main():
    """Test DNS validation report generation"""

    logger.info("\n" + "="*80)
    logger.info("DNS VALIDATION REPORT - TEST")
    logger.info("="*80 + "\n")

    # Create sample topology data
    topology_dir = create_sample_topology_with_validation()

    # Create reporter and collect data
    logger.info("\nCollecting DNS validation data...")
    reporter = DNSValidationReporter(output_dir='test_dns_data/reports')

    # Manually add sample data
    from dns_validation_reporter import collect_dns_validation_from_apps
    reporter = collect_dns_validation_from_apps(topology_dir=topology_dir)

    # Generate all reports
    logger.info("\nGenerating DNS validation reports...")
    reports = reporter.generate_all_reports()

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)
    logger.info(f"\nGenerated test reports:")
    for format_type, path in reports.items():
        logger.info(f"  {format_type.upper():6} - {path}")

    logger.info(f"\nValidation Summary:")
    logger.info(f"  Applications:     {reporter.stats['applications_analyzed']}")
    logger.info(f"  IPs Validated:    {reporter.stats['total_ips_validated']}")
    logger.info(f"  Valid:            {reporter.stats['total_valid']}")
    logger.info(f"  Multiple IPs:     {reporter.stats['total_valid_multiple']}")
    logger.info(f"  Mismatches:       {reporter.stats['total_mismatches']}")
    logger.info(f"  NXDOMAIN:         {reporter.stats['total_nxdomain']}")
    logger.info(f"  Failed:           {reporter.stats['total_failed']}")

    logger.info("\n" + "="*80)
    logger.info("NOTE: These are test reports with sample data.")
    logger.info("To generate real reports:")
    logger.info("  1. Run: python run_batch_processing.py")
    logger.info("  2. Run: python generate_dns_validation_report.py")
    logger.info("="*80 + "\n")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
