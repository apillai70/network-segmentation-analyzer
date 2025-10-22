#!/usr/bin/env python3
"""
Setup Development Database
===========================
Creates local PostgreSQL database for development

Usage:
    python setup_dev_database.py
"""

import sys
import subprocess
import getpass
from pathlib import Path

def run_psql_command(command, database='postgres', user='postgres', password=None):
    """Run a psql command"""
    psql_path = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"

    # Build command
    cmd = [
        psql_path,
        '-U', user,
        '-d', database,
        '-c', command
    ]

    # Set password if provided
    env = None
    if password:
        import os
        env = os.environ.copy()
        env['PGPASSWORD'] = password

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    """Setup development database"""
    print("="*80)
    print("DEVELOPMENT DATABASE SETUP")
    print("="*80)
    print()

    # Get postgres password
    print("Please enter your PostgreSQL 'postgres' user password:")
    print("(If you just installed PostgreSQL, this is the password you set during installation)")
    password = getpass.getpass("Password: ")

    print()
    print("Testing connection to PostgreSQL...")

    # Test connection
    success, output = run_psql_command(
        "SELECT version();",
        user='postgres',
        password=password
    )

    if not success:
        print(f"✗ Failed to connect to PostgreSQL")
        print(f"Error: {output}")
        print()
        print("Common issues:")
        print("  1. Wrong password")
        print("  2. PostgreSQL service not running")
        print("  3. Connection settings incorrect")
        print()
        print("To check if PostgreSQL is running:")
        print("  services.msc → Look for 'postgresql-x64-17'")
        return 1

    print("✓ Connected to PostgreSQL")
    print()

    # Create database
    print("Creating database 'network_analysis_dev'...")
    success, output = run_psql_command(
        "CREATE DATABASE network_analysis_dev;",
        user='postgres',
        password=password
    )

    if success:
        print("✓ Database created successfully")
    elif "already exists" in output:
        print("✓ Database already exists")
    else:
        print(f"✗ Failed to create database: {output}")
        return 1

    print()
    print("="*80)
    print("✓ DEVELOPMENT DATABASE READY")
    print("="*80)
    print()
    print("Connection details:")
    print("  Host: localhost")
    print("  Port: 5432")
    print("  Database: network_analysis_dev")
    print("  User: postgres")
    print("  Schema: public")
    print()
    print("Next steps:")
    print("  1. Update .env.development with your password")
    print("  2. Run: python test_database_connection.py")
    print()

    # Update .env.development with password
    env_file = Path('.env.development')
    if env_file.exists():
        print("Updating .env.development with your password...")
        content = env_file.read_text(encoding='utf-8')

        # Replace password line
        lines = []
        for line in content.split('\n'):
            if line.startswith('DB_PASSWORD='):
                lines.append(f'DB_PASSWORD={password}')
            else:
                lines.append(line)

        env_file.write_text('\n'.join(lines), encoding='utf-8')
        print("✓ Updated .env.development")

    print()
    print("="*80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
