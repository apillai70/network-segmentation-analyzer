#!/usr/bin/env python3
"""
Quick script to verify what tables exist in the schema
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import get_config
import psycopg2

config = get_config()

print(f"Connecting to: {config.db_host}/{config.db_name}")
print(f"Schema: {config.db_schema}")
print()

try:
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password
    )

    with conn.cursor() as cur:
        # Method 1: Check via information_schema
        print("=" * 80)
        print("Method 1: Querying information_schema.tables")
        print("=" * 80)
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
        """, (config.db_schema,))

        tables = cur.fetchall()
        if tables:
            print(f"Found {len(tables)} tables:")
            for schema, table in tables:
                print(f"  - {schema}.{table}")
        else:
            print(f"❌ No tables found in schema '{config.db_schema}' via information_schema")
        print()

        # Method 2: Direct query to pg_tables
        print("=" * 80)
        print("Method 2: Querying pg_tables")
        print("=" * 80)
        cur.execute("""
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname = %s
            ORDER BY tablename
        """, (config.db_schema,))

        tables = cur.fetchall()
        if tables:
            print(f"Found {len(tables)} tables:")
            for schema, table in tables:
                print(f"  - {schema}.{table}")
        else:
            print(f"❌ No tables found in schema '{config.db_schema}' via pg_tables")
        print()

        # Method 3: Check if tables are accessible directly
        print("=" * 80)
        print("Method 3: Direct table access test")
        print("=" * 80)

        test_tables = ['enriched_flows', 'dns_cache', 'flow_aggregates']
        for table in test_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {config.db_schema}.{table}")
                count = cur.fetchone()[0]
                print(f"✓ {config.db_schema}.{table} - accessible ({count} rows)")
            except Exception as e:
                print(f"❌ {config.db_schema}.{table} - error: {e}")
        print()

        # Method 4: Check current search_path
        print("=" * 80)
        print("Method 4: Check search_path")
        print("=" * 80)
        cur.execute("SHOW search_path")
        search_path = cur.fetchone()[0]
        print(f"Current search_path: {search_path}")
        print()

        # Method 5: Check schema exists
        print("=" * 80)
        print("Method 5: Verify schema exists")
        print("=" * 80)
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = %s
        """, (config.db_schema,))

        if cur.fetchone():
            print(f"✓ Schema '{config.db_schema}' exists")
        else:
            print(f"❌ Schema '{config.db_schema}' not found")
        print()

        # Method 6: Check user permissions
        print("=" * 80)
        print("Method 6: Check permissions on schema")
        print("=" * 80)
        cur.execute("""
            SELECT
                nspname as schema_name,
                has_schema_privilege(current_user, nspname, 'USAGE') as has_usage,
                has_schema_privilege(current_user, nspname, 'CREATE') as has_create
            FROM pg_namespace
            WHERE nspname = %s
        """, (config.db_schema,))

        result = cur.fetchone()
        if result:
            schema, has_usage, has_create = result
            print(f"Schema: {schema}")
            print(f"  USAGE permission: {'✓ Yes' if has_usage else '❌ No'}")
            print(f"  CREATE permission: {'✓ Yes' if has_create else '❌ No'}")
        else:
            print(f"❌ Schema '{config.db_schema}' not found")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
