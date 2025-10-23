#!/usr/bin/env python3
"""
Quick Database Connection Test
===============================
Tests PostgreSQL connection and lists available databases

Usage:
    python test_db_connection.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_connection():
    """Test database connection and list databases"""

    print("=" * 80)
    print("DATABASE CONNECTION TEST")
    print("=" * 80)
    print()

    try:
        import psycopg2
        from src.config import get_config

        # Load configuration
        config = get_config()

        print(f"Environment: {config.environment}")
        print(f"DB Enabled: {config.db_enabled}")
        print()
        print(f"Connecting to:")
        print(f"  Host: {config.db_host}")
        print(f"  Port: {config.db_port}")
        print(f"  User: {config.db_user}")
        print(f"  Database: {config.db_name}")
        print(f"  Schema: {config.db_schema}")
        print()

        if not config.db_enabled:
            print("❌ Database is DISABLED in configuration")
            print("   Set DB_ENABLED=true in .env.production")
            return False

        # Try connecting to the configured database first
        print("Attempting to connect to configured database...")
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                connect_timeout=10
            )

            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✓ Connected to configured database: {config.db_name}")
                print(f"  PostgreSQL version: {version.split(',')[0]}")

            conn.close()
            print()
            print("✅ SUCCESS: Can connect to configured database")
            print()
            return True

        except psycopg2.OperationalError as e:
            print(f"❌ Cannot connect to database '{config.db_name}'")
            print(f"   Error: {e}")
            print()
            print("Trying to connect to 'postgres' database to list available databases...")
            print()

        # If configured database fails, try connecting to 'postgres' default database
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database='postgres',  # Default database
                user=config.db_user,
                password=config.db_password,
                connect_timeout=10
            )

            print("✓ Connected to 'postgres' default database")
            print()

            # List all databases
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT datname, pg_database_size(datname) as size
                    FROM pg_database
                    WHERE datistemplate = false
                    ORDER BY datname
                """)

                databases = cur.fetchall()

                print(f"Found {len(databases)} databases you can see:")
                print()
                for db_name, size in databases:
                    size_mb = size / (1024 * 1024) if size else 0
                    print(f"  - {db_name:<30} ({size_mb:.2f} MB)")

                print()
                print("💡 TIP: Update DB_NAME in .env.production to one of these databases")
                print(f"   Current value: {config.db_name}")

            conn.close()
            return False  # Connected but not to configured database

        except psycopg2.OperationalError as e:
            print(f"❌ Cannot connect to any database")
            print(f"   Error: {e}")
            print()
            print("Possible issues:")
            print("  1. PostgreSQL server is not running")
            print("  2. Incorrect host or port")
            print("  3. Incorrect username or password")
            print("  4. Firewall blocking connection")
            print("  5. User has no database permissions")
            return False

    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install with: pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = test_connection()

    print()
    print("=" * 80)

    if success:
        print("✅ READY TO USE")
        print()
        print("Next steps:")
        print("  1. Run batch processing:")
        print("     python run_batch_processing.py --batch-size 10")
        print()
        print("  2. Generate enhanced diagrams:")
        print("     python generate_diagrams_from_db.py")
    else:
        print("❌ NOT READY")
        print()
        print("Next steps:")
        print("  1. Fix database connection issues above")
        print("  2. Update .env.production with correct database name")
        print("  3. Run: python setup_database.py")

    print("=" * 80)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
