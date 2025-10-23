#!/usr/bin/env python3
"""
Test Script: Verify Table Creation with Fully Qualified Names
==============================================================

This script tests if tables can be created using the fixed
database.schema.table syntax.

Based on user's working script that uses:
  CREATE TABLE prutech_bais.activenet.my_table (...)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.database import FlowRepository
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test table creation"""
    print("\n" + "="*80)
    print("TABLE CREATION TEST")
    print("="*80)

    try:
        # Load config
        print("\n1. Loading configuration...")
        config = get_config()

        print(f"   Database: {config.db_name}")
        print(f"   Schema: {config.db_schema}")
        print(f"   Host: {config.db_host}:{config.db_port}")
        print(f"   User: {config.db_user}")

        # Initialize repository (this creates tables)
        print("\n2. Initializing FlowRepository (creates tables)...")
        repo = FlowRepository(config)

        if not repo.connection_pool:
            print("❌ Failed to create connection pool")
            return False

        print("   ✓ Connection pool created")

        # Verify tables exist
        print("\n3. Verifying tables exist...")
        with repo.get_connection() as conn:
            with conn.cursor() as cur:
                # Check each table
                tables = ['enriched_flows', 'dns_cache', 'flow_aggregates']

                for table_name in tables:
                    # Method 1: Check in information_schema
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    """, (config.db_schema, table_name))

                    result = cur.fetchone()

                    if result:
                        # Try to access the table
                        full_name = f"{config.db_schema}.{table_name}"
                        cur.execute(f"SELECT COUNT(*) FROM {full_name}")
                        count = cur.fetchone()[0]
                        print(f"   ✓ {config.db_schema}.{table_name} exists ({count} rows)")
                    else:
                        print(f"   ❌ {config.db_schema}.{table_name} NOT FOUND")
                        return False

        print("\n" + "="*80)
        print("✅ SUCCESS! All tables created and verified!")
        print("="*80)

        print("\nYou can now:")
        print("  1. Run batch processing: python run_batch_processing.py --batch-size 10")
        print("  2. Generate diagrams from PostgreSQL: python generate_diagrams_from_db.py")
        print("  3. View data in database using psql or pgAdmin")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

        print("\n" + "="*80)
        print("TROUBLESHOOTING")
        print("="*80)
        print("\nIf you see permission errors:")
        print("  1. Send create_tables.sql to your DBA")
        print("  2. DBA runs: psql -h host -U postgres -d prutech_bais -f create_tables.sql")
        print("  3. Run this script again")

        print("\nIf you see connection errors:")
        print("  1. Check .env.production file exists")
        print("  2. Verify credentials are correct")
        print("  3. Test connection: python test_db_connection.py")

        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
