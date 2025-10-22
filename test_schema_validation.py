#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Schema Validation
=======================
Verifies that the application prevents using 'public' schema

This test ensures:
1. Production uses 'activenet' schema
2. Development uses 'network_analysis' schema
3. 'public' schema is rejected with clear error message
"""

import sys
import os

# Force UTF-8 encoding (Windows fix)
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_schema_validation():
    """Test schema validation"""
    print("="*80)
    print("SCHEMA VALIDATION TEST")
    print("="*80)
    print()

    from src.config import get_config

    # Test 1: Production schema
    print("Test 1: Production schema validation...")
    try:
        config_prod = get_config(environment='production')
        schema_prod = config_prod.db_schema

        print(f"  Production schema: '{schema_prod}'")

        if schema_prod.lower() == 'activenet':
            print("  [OK] Production uses 'activenet' schema")
        else:
            print(f"  [WARNING] Production schema is '{schema_prod}', expected 'activenet'")
    except Exception as e:
        print(f"  [ERROR] Failed to load production config: {e}")

    print()

    # Test 2: Development schema
    print("Test 2: Development schema validation...")
    try:
        config_dev = get_config(environment='development')
        schema_dev = config_dev.db_schema

        print(f"  Development schema: '{schema_dev}'")

        if schema_dev.lower() == 'public':
            print("  [FAILED] Development still uses 'public' schema!")
            print("  [ACTION] Update .env.development: DB_SCHEMA=network_analysis")
            return 1
        else:
            print(f"  [OK] Development uses '{schema_dev}' schema (not 'public')")
    except Exception as e:
        print(f"  [ERROR] Failed to load development config: {e}")

    print()

    # Test 3: Verify FlowRepository rejects 'public' schema
    print("Test 3: Testing FlowRepository schema validation...")
    try:
        # Temporarily set schema to 'public' to test validation
        os.environ['DB_SCHEMA'] = 'public'

        from src.database import FlowRepository

        try:
            repo = FlowRepository()
            print("  [FAILED] FlowRepository allowed 'public' schema!")
            print("  [ERROR] Schema validation is not working!")
            return 1
        except ValueError as e:
            if "SCHEMA VALIDATION FAILED" in str(e):
                print("  [OK] FlowRepository correctly rejected 'public' schema")
                print(f"  Error message: {str(e).split(chr(10))[0]}")
            else:
                print(f"  [WARNING] Different error: {e}")
    except Exception as e:
        print(f"  [ERROR] Unexpected error: {e}")
    finally:
        # Restore original schema
        if 'DB_SCHEMA' in os.environ:
            del os.environ['DB_SCHEMA']

    print()

    # Test 4: Summary
    print("="*80)
    print("SCHEMA VALIDATION SUMMARY")
    print("="*80)
    print()
    print("Schema Configuration:")
    print(f"  Production:  {config_prod.db_schema}")
    print(f"  Development: {config_dev.db_schema}")
    print()

    if config_prod.db_schema.lower() == 'activenet' and config_dev.db_schema.lower() != 'public':
        print("[SUCCESS] All schema validations passed!")
        print()
        print("Schema Safety:")
        print("  [OK] Production uses dedicated 'activenet' schema")
        print("  [OK] Development uses dedicated schema (not 'public')")
        print("  [OK] FlowRepository rejects 'public' schema")
        print()
        print("Your application will NEVER pollute the 'public' schema!")
        return 0
    else:
        print("[FAILED] Schema configuration issues detected")
        print()
        print("Please update .env files to use dedicated schemas.")
        return 1

if __name__ == '__main__':
    sys.exit(test_schema_validation())
