#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
=================================
Consolidated script to set up PostgreSQL connection and initialize database.

This script handles:
1. Testing database connection
2. Creating dedicated schema
3. Creating all tables (enriched_flows, dns_cache, flow_aggregates)
4. Creating indexes for performance
5. Verifying setup

Usage:
    # Interactive setup (prompts for credentials)
    python setup_database.py

    # Use existing .env file
    python setup_database.py --use-env

    # Test connection only (no changes)
    python setup_database.py --test-only

    # Force recreate tables (WARNING: deletes existing data)
    python setup_database.py --force-recreate

Requirements:
    - PostgreSQL server must be running and accessible
    - User must have CREATE SCHEMA and CREATE TABLE permissions
    - Network connectivity to PostgreSQL server
"""

import sys
import os
from pathlib import Path
import logging
from typing import Optional, Dict, Tuple
# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database_setup.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles PostgreSQL database setup and initialization"""

    def __init__(self):
        self.config = None
        self.connection_params = {}

    def print_banner(self):
        """Print setup banner"""
        print("=" * 80)
        print("PostgreSQL Database Setup for Network Segmentation Analyzer")
        print("=" * 80)
        print()

    def prompt_for_credentials(self) -> Dict[str, str]:
        """
        Prompt user for database credentials

        Returns:
            Dictionary with connection parameters
        """
        print("\n" + "=" * 80)
        print("DATABASE CONNECTION SETUP")
        print("=" * 80)
        print("\nPlease provide PostgreSQL connection details:")
        print("(Press Enter to use default values shown in brackets)")
        print()

        # Host
        host = input("PostgreSQL Host [localhost]: ").strip()
        if not host:
            host = "udideapdb01.unix.rgbk.com"

        # Port
        port_input = input("PostgreSQL Port [5432]: ").strip()
        port = int(port_input) if port_input else 5432

        # Database
        database = input("Database Name [network_segmentation]: ").strip()
        if not database:
            database = "prutech_bais"

        # User
        user = input("Username [activenet_admin]: ").strip()
        if not user:
            user = "activenet_admin"

        # Password
        import getpass
        #password = getpass.getpass("Password: ").strip()
        password= "Xm9Kp2Nq7Rt4Wv8Yz3Lh6Jc5"

        # Schema (IMPORTANT: not 'public')
        print()
        print("⚠️  IMPORTANT: Schema name must NOT be 'public'")
        print("   Use a dedicated schema (e.g., 'network_analysis', 'activenet')")
        schema = input("Schema Name [activenet]: ").strip()
        if not schema:
            schema = "activenet"

        if schema.lower() == 'public':
            print()
            print("❌ ERROR: Cannot use 'public' schema!")
            print("   Please specify a dedicated schema name.")
            sys.exit(1)

        return {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'schema': schema
        }

    def load_from_env(self) -> Optional[Dict[str, str]]:
        """
        Load connection parameters from .env file

        Returns:
            Dictionary with connection parameters or None
        """
        try:
            from src.config import get_config

            print("\nLoading configuration from .env file...")
            config = get_config()

            if not config.db_enabled:
                print("❌ Database is disabled in configuration (DB_ENABLED=false)")
                print("   Please set DB_ENABLED=true in your .env file")
                return None

            params = {
                'host': config.db_host,
                'port': config.db_port,
                'database': config.db_name,
                'user': config.db_user,
                'password': config.db_password,
                'schema': config.db_schema
            }

            print(f"✓ Configuration loaded:")
            print(f"  Host: {params['host']}")
            print(f"  Port: {params['port']}")
            print(f"  Database: {params['database']}")
            print(f"  User: {params['user']}")
            print(f"  Schema: {params['schema']}")

            return params

        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return None

    def test_connection(self, params: Dict[str, str]) -> bool:
        """
        Test database connection

        Args:
            params: Connection parameters

        Returns:
            True if connection successful
        """
        print("\n" + "=" * 80)
        print("TESTING DATABASE CONNECTION")
        print("=" * 80)

        try:
            import psycopg2

            print(f"\nConnecting to {params['host']}:{params['port']}/{params['database']}...")

            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['user'],
                password=params['password'],
                connect_timeout=10
            )

            # Test query
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✓ Connected successfully!")
                print(f"  PostgreSQL version: {version.split(',')[0]}")

            conn.close()

            print("\n✅ DATABASE CONNECTION TEST: PASSED")
            return True

        except Exception as e:
            print(f"\n❌ DATABASE CONNECTION TEST: FAILED")
            print(f"   Error: {e}")
            print()
            print("Common issues:")
            print("  1. PostgreSQL server not running")
            print("  2. Incorrect host/port")
            print("  3. Incorrect credentials")
            print("  4. Firewall blocking connection")
            print("  5. Database does not exist")
            return False

    def create_schema(self, params: Dict[str, str]) -> bool:
        """
        Create dedicated schema

        Args:
            params: Connection parameters

        Returns:
            True if successful
        """
        print("\n" + "=" * 80)
        print(f"CREATING SCHEMA: {params['schema']}")
        print("=" * 80)

        try:
            import psycopg2

            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['user'],
                password=params['password']
            )

            with conn.cursor() as cur:
                # Check if schema exists
                cur.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                """, (params['schema'],))

                if cur.fetchone():
                    print(f"✓ Schema '{params['schema']}' already exists")
                else:
                    # Create schema
                    cur.execute(f"CREATE SCHEMA {params['schema']}")
                    conn.commit()
                    print(f"✓ Schema '{params['schema']}' created successfully")

            conn.close()
            return True

        except Exception as e:
            print(f"❌ Failed to create schema: {e}")
            return False

    def initialize_tables(self, params: Dict[str, str], force_recreate: bool = False) -> bool:
        """
        Initialize database tables using FlowRepository

        Args:
            params: Connection parameters
            force_recreate: If True, drop and recreate tables

        Returns:
            True if successful
        """
        print("\n" + "=" * 80)
        print("INITIALIZING DATABASE TABLES")
        print("=" * 80)

        if force_recreate:
            print("\n⚠️  WARNING: Force recreate enabled - existing data will be deleted!")
            response = input("Type 'yes' to continue: ").strip().lower()
            if response != 'yes':
                print("❌ Aborted by user")
                return False

        try:
            # Set environment variables for FlowRepository
            os.environ['DB_HOST'] = params['host']
            os.environ['DB_PORT'] = str(params['port'])
            os.environ['DB_NAME'] = params['database']
            os.environ['DB_USER'] = params['user']
            os.environ['DB_PASSWORD'] = params['password']  # Fixed: was DBPASSWORD (missing underscore)
            os.environ['DB_SCHEMA'] = params['schema']
            os.environ['DB_ENABLED'] = 'true'

            from src.database import FlowRepository

            print("\nInitializing FlowRepository...")
            repo = FlowRepository()

            if not repo.connection_pool:
                print("❌ Failed to create connection pool")
                return False

            print("✓ FlowRepository initialized")

            # If force recreate, drop tables first
            if force_recreate:
                self._drop_tables(repo, params['schema'])

            # Verify tables actually exist
            print("\nVerifying tables...")
            tables_verified = self._verify_tables(repo, params['schema'])

            if not tables_verified:
                print("\n❌ TABLES NOT CREATED")
                print("\nYou do NOT have CREATE TABLE permission on this schema.")
                print("\nREQUIRED ACTION:")
                print("  1. Send 'create_tables.sql' to your DBA")
                print("  2. Ask DBA to run the SQL script")
                print("  3. Run this setup script again")
                print("\nSQL script location: create_tables.sql")
                return False

            print("\n✓ All tables verified and accessible!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize tables: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _verify_tables(self, repo, schema: str) -> bool:
        """
        Verify that all required tables exist and are accessible

        Returns:
            True if all tables exist, False otherwise
        """
        required_tables = ['enriched_flows', 'dns_cache', 'flow_aggregates']

        try:
            with repo.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check each table
                    for table_name in required_tables:
                        cur.execute("""
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = %s AND table_name = %s
                        """, (schema, table_name))

                        if not cur.fetchone():
                            print(f"  ❌ {schema}.{table_name} - NOT FOUND")
                            return False

                        # Try to access the table
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                            count = cur.fetchone()[0]
                            print(f"  ✓ {schema}.{table_name} - exists ({count} rows)")
                        except Exception as e:
                            print(f"  ❌ {schema}.{table_name} - cannot access: {e}")
                            return False

                    return True

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def _drop_tables(self, repo, schema: str):
        """Drop all tables (used with --force-recreate)"""
        print("\n⚠️  Dropping existing tables...")

        with repo.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {schema}.enriched_flows CASCADE")
                cur.execute(f"DROP TABLE IF EXISTS {schema}.dns_cache CASCADE")
                cur.execute(f"DROP TABLE IF EXISTS {schema}.flow_aggregates CASCADE")

        print("✓ Existing tables dropped")

    def verify_setup(self, params: Dict[str, str]) -> bool:
        """
        Verify database setup

        Args:
            params: Connection parameters

        Returns:
            True if verification successful
        """
        print("\n" + "=" * 80)
        print("VERIFYING DATABASE SETUP")
        print("=" * 80)

        try:
            import psycopg2

            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['user'],
                password=params['password']
            )

            with conn.cursor() as cur:
                # Check schema
                cur.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                """, (params['schema'],))

                if not cur.fetchone():
                    print(f"❌ Schema '{params['schema']}' not found")
                    return False

                print(f"✓ Schema '{params['schema']}' exists")

                # Check tables
                expected_tables = ['enriched_flows', 'dns_cache', 'flow_aggregates']

                for table in expected_tables:
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    """, (params['schema'], table))

                    if not cur.fetchone():
                        print(f"❌ Table '{table}' not found in schema '{params['schema']}'")
                        return False

                    print(f"✓ Table '{params['schema']}.{table}' exists")

                # Check enriched_flows columns
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = 'enriched_flows'
                    ORDER BY ordinal_position
                """, (params['schema'],))

                columns = [row[0] for row in cur.fetchall()]

                required_columns = [
                    'source_server_type', 'source_server_tier', 'source_server_category',
                    'dest_server_type', 'dest_server_tier', 'dest_server_category'
                ]

                for col in required_columns:
                    if col in columns:
                        print(f"✓ Column '{col}' exists")
                    else:
                        print(f"❌ Column '{col}' missing")
                        return False

            conn.close()

            print("\n✅ DATABASE VERIFICATION: PASSED")
            return True

        except Exception as e:
            print(f"\n❌ DATABASE VERIFICATION: FAILED")
            print(f"   Error: {e}")
            return False

    def save_to_env_file(self, params: Dict[str, str], env_file: str = '.env.production'):
        """
        Save connection parameters to .env file

        Args:
            params: Connection parameters
            env_file: Path to .env file
        """
        print("\n" + "=" * 80)
        print(f"SAVING CONFIGURATION TO {env_file}")
        print("=" * 80)

        try:
            env_path = Path(env_file)

            # Read existing .env if it exists
            existing_lines = []
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()

            # Remove old database config lines
            filtered_lines = [
                line for line in existing_lines
                if not any(line.startswith(key) for key in [
                    'DB_ENABLED=', 'DB_HOST=', 'DB_PORT=',
                    'DB_NAME=', 'DB_USER=', 'DB_PASSWORD=',
                    'DB_SCHEMA='
                ])
            ]

            # Add new configuration
            with open(env_path, 'w', encoding='utf-8') as f:
                # Write filtered existing lines
                f.writelines(filtered_lines)

                # Add database configuration
                f.write("\n# PostgreSQL Database Configuration\n")
                f.write("DB_ENABLED=true\n")
                f.write(f"DB_HOST={params['host']}\n")
                f.write(f"DB_PORT={params['port']}\n")
                f.write(f"DB_NAME={params['database']}\n")
                f.write(f"DB_USERR={params['user']}\n")
                f.write(f"DB_PASSWORD={params['password']}\n")
                f.write(f"DB_SCHEMA={params['schema']}\n")

            print(f"✓ Configuration saved to {env_file}")

            # Remind about environment variable
            print("\n⚠️  IMPORTANT: Set environment variable on your system:")
            if sys.platform == 'win32':
                print(f"   setx ENVIRONMENT production /M")
            else:
                print(f"   export ENVIRONMENT=production")
                print(f"   # Add to ~/.bashrc or ~/.zshrc to make permanent")

        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")


def main():
    """Main setup routine"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PostgreSQL Database Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--use-env', action='store_true',
                       help='Use existing .env file (no prompts)')
    parser.add_argument('--test-only', action='store_true',
                       help='Test connection only (no changes)')
    parser.add_argument('--force-recreate', action='store_true',
                       help='Drop and recreate tables (WARNING: deletes data)')
    parser.add_argument('--skip-save', action='store_true',
                       help='Skip saving to .env file')

    args = parser.parse_args()

    setup = DatabaseSetup()
    setup.print_banner()

    # Get connection parameters
    if args.use_env:
        params = setup.load_from_env()
        if not params:
            print("\n❌ Failed to load from .env file")
            print("   Please run without --use-env to enter credentials manually")
            sys.exit(1)
    else:
        params = setup.prompt_for_credentials()

    # Test connection
    if not setup.test_connection(params):
        print("\n❌ Setup failed: Cannot connect to database")
        print("\nPlease check:")
        print("  1. PostgreSQL server is running")
        print("  2. Host and port are correct")
        print("  3. Credentials are correct")
        print("  4. Database exists")
        print("  5. Firewall allows connection")
        sys.exit(1)

    if args.test_only:
        print("\n✅ Connection test successful (--test-only mode, no changes made)")
        sys.exit(0)

    # Create schema
    if not setup.create_schema(params):
        print("\n❌ Setup failed: Cannot create schema")
        sys.exit(1)

    # Initialize tables
    if not setup.initialize_tables(params, force_recreate=args.force_recreate):
        print("\n❌ Setup failed: Cannot initialize tables")
        sys.exit(1)

    # Verify setup
    if not setup.verify_setup(params):
        print("\n❌ Setup failed: Verification failed")
        sys.exit(1)

    # Save to .env file
    if not args.skip_save:
        setup.save_to_env_file(params)

    # Success!
    print("\n" + "=" * 80)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 80)
    print("\nYour database is ready to use!")
    print()
    print("Next steps:")
    print("  1. Set environment variable (if not already set):")
    if sys.platform == 'win32':
        print("     setx ENVIRONMENT production /M")
    else:
        print("     export ENVIRONMENT=production")
    print()
    print("  2. Run batch processing:")
    print("     python run_batch_processing.py --batch-size 10")
    print()
    print("  3. Verify data population:")
    print("     python -c \"from src.database import FlowRepository; print(FlowRepository().get_statistics())\"")
    print()
    print("  4. Generate enhanced diagrams:")
    print("     python generate_diagrams_from_db.py")
    print()


if __name__ == '__main__':
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
