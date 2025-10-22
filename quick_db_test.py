#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Database Test - Non-Interactive
======================================
Tests if PostgreSQL connection works with current .env.development settings

This script will:
1. Try to connect using settings in .env.development
2. Create database if needed
3. Test table creation
4. Insert sample data
"""

import sys
import os

# Force UTF-8 encoding (Windows fix) - MUST BE FIRST!
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_quick():
    """Quick test without creating database first"""
    print("="*80)
    print("QUICK DATABASE TEST")
    print("="*80)
    print()

    try:
        from src.config import get_config

        print("Step 1: Loading configuration from .env.development...")
        config = get_config(environment='development')

        print("[OK] Config loaded")
        print(f"  Host: {config.db_host}")
        print(f"  Port: {config.db_port}")
        print(f"  Database: {config.db_name}")
        print(f"  User: {config.db_user}")
        print(f"  Password: {'*' * len(config.db_password)}")
        print()

        print("Step 2: Testing connection to PostgreSQL...")

        import psycopg2

        # Try to connect to default 'postgres' database first
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database='postgres',  # Connect to default database
                user=config.db_user,
                password=config.db_password,
                connect_timeout=10
            )
            conn.close()
            print("[OK] PostgreSQL connection successful!")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to connect to PostgreSQL")
            print(f"Error: {e}")
            print()
            print("Common issues:")
            print("  1. PostgreSQL service not running")
            print("     -> Check in services.msc for 'postgresql-x64-17'")
            print("  2. Wrong password in .env.development")
            print("     -> Update DB_PASSWORD in .env.development")
            print("  3. Connection refused")
            print("     -> Check if PostgreSQL is listening on localhost:5432")
            print()
            return 1

        # Create database if it doesn't exist
        print("Step 3: Creating database (if needed)...")
        try:
            conn = psycopg2.connect(
                host=config.db_host,
                port=config.db_port,
                database='postgres',
                user=config.db_user,
                password=config.db_password
            )
            conn.autocommit = True
            cur = conn.cursor()

            # Check if database exists
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (config.db_name,)
            )
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {config.db_name}")
                print(f"[OK] Created database '{config.db_name}'")
            else:
                print(f"[OK] Database '{config.db_name}' already exists")

            cur.close()
            conn.close()
            print()

        except Exception as e:
            print(f"[WARNING] Could not create database: {e}")
            print("  -> You may need to create it manually")
            print()

        # Now test with FlowRepository
        print("Step 4: Initializing FlowRepository...")
        from src.database import FlowRepository

        repo = FlowRepository(config)
        print("[OK] FlowRepository initialized")
        print("[OK] Tables created/verified")
        print()

        # Get statistics
        print("Step 5: Getting database statistics...")
        stats = repo.get_statistics()

        print("Database statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Success!
        print("="*80)
        print("[SUCCESS] DATABASE CONNECTION SUCCESSFUL!")
        print("="*80)
        print()
        print("Your development environment is ready!")
        print()
        print("Next step: Run the full test")
        print("  python test_database_connection.py")
        print()

        repo.close()
        return 0

    except Exception as e:
        print()
        print("="*80)
        print("[FAILED] TEST FAILED")
        print("="*80)
        print()
        print(f"Error: {e}")
        print()

        import traceback
        traceback.print_exc()

        print()
        print("Please check:")
        print("  1. PostgreSQL is running")
        print("  2. .env.development has correct credentials")
        print("  3. User has permissions to create databases")
        print()

        return 1

if __name__ == '__main__':
    sys.exit(test_quick())
