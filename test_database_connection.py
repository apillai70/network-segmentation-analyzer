#!/usr/bin/env python3
"""
Test Database Connection
=========================
Tests PostgreSQL connection and creates sample data

Usage:
    python test_database_connection.py
"""

import sys
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import get_config
from src.database import FlowRepository

def test_connection():
    """Test database connection"""
    print("="*80)
    print("DATABASE CONNECTION TEST")
    print("="*80)
    print()

    try:
        # Load config
        print("Step 1: Loading configuration...")
        config = get_config(environment='development')
        print(f"✓ Config loaded")
        print(f"  Environment: {config.environment}")
        print(f"  DB Host: {config.db_host}")
        print(f"  DB Port: {config.db_port}")
        print(f"  DB Name: {config.db_name}")
        print(f"  DB Schema: {config.db_schema}")
        print(f"  DB Enabled: {config.db_enabled}")
        print()

        # Connect to database
        print("Step 2: Connecting to PostgreSQL...")
        repo = FlowRepository(config)
        print("✓ Connection successful!")
        print()

        # Get initial statistics
        print("Step 3: Checking database statistics...")
        stats = repo.get_statistics()
        print("✓ Statistics retrieved")
        print()
        print("Current database state:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Create sample data
        print("Step 4: Inserting sample flow data...")
        sample_data = pd.DataFrame({
            'source_app_code': ['BLZE', 'BLZE', 'CNET'],
            'source_ip': ['10.164.144.23', '10.164.144.112', '10.165.116.19'],
            'source_hostname': ['blze-cache-01.company.com', 'blze-cache-02.company.com', 'cnet-app-01.company.com'],
            'source_device_type': ['cache', 'cache', 'app'],
            'dest_ip': ['10.164.116.124', '10.164.116.32', '10.164.116.124'],
            'dest_hostname': ['blze-db-primary.company.com', 'blze-db-02.company.com', 'blze-db-primary.company.com'],
            'dest_device_type': ['database', 'database', 'database'],
            'dest_app_code': ['BLZE', 'BLZE', 'BLZE'],
            'protocol': ['HTTPS', 'TCP', 'HTTPS'],
            'port': [443, 5432, 443],
            'bytes_in': [160252, 1459939, 250000],
            'bytes_out': [822464, 606682, 180000],
            'flow_direction': ['intra-app', 'intra-app', 'inter-app'],
            'flow_count': [1, 1, 1],
            'has_missing_data': [False, False, False],
            'missing_fields': [[], [], []]
        })

        inserted = repo.insert_flows_batch(
            sample_data,
            batch_id='test_batch_001',
            file_source='test_database_connection.py'
        )
        print(f"✓ Inserted {inserted} sample flows")
        print()

        # Update aggregates
        print("Step 5: Updating flow aggregates...")
        repo.update_flow_aggregates()
        print("✓ Aggregates updated")
        print()

        # Query data back
        print("Step 6: Querying inserted data...")
        blze_flows = repo.get_flows_by_app('BLZE')
        print(f"✓ Found {len(blze_flows)} flows for app 'BLZE'")
        print()

        # Display sample
        if len(blze_flows) > 0:
            print("Sample flow data:")
            print(blze_flows[['source_app_code', 'source_ip', 'dest_ip', 'protocol', 'port', 'flow_direction']].head())
        print()

        # Test DNS cache
        print("Step 7: Testing DNS cache...")
        repo.cache_dns_lookup('10.164.144.99', 'test-server.company.com', ttl=3600)
        cached = repo.get_cached_dns('10.164.144.99')
        print(f"✓ DNS cache working: {cached}")
        print()

        # Final statistics
        print("Step 8: Final statistics...")
        stats = repo.get_statistics()
        print("Updated database state:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Close connection
        repo.close()

        print("="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        print()
        print("Your PostgreSQL database is ready for use!")
        print()
        print("You can now:")
        print("  1. Process CSV files with the main pipeline")
        print("  2. Query flows using repo.get_flows_by_app()")
        print("  3. Generate diagrams from database data")
        print()

        return 0

    except Exception as e:
        print()
        print("="*80)
        print("✗ TEST FAILED")
        print("="*80)
        print()
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check PostgreSQL is running (services.msc)")
        print("  2. Verify .env.development has correct password")
        print("  3. Ensure database 'network_analysis_dev' exists")
        print("  4. Run: python setup_dev_database.py")
        print()

        import traceback
        traceback.print_exc()

        return 1

if __name__ == '__main__':
    sys.exit(test_connection())
