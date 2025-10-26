#!/usr/bin/env python3
"""
Verify Production Configuration
================================
This script verifies that your production environment is configured correctly.
Run this on the client side to ensure credentials are loaded properly.

Usage:
    python verify_production_config.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config


def verify_production_config():
    """Verify production configuration is loaded correctly"""

    print("=" * 80)
    print("PRODUCTION CONFIGURATION VERIFICATION")
    print("=" * 80)
    print()

    # Check environment variable
    env = os.getenv('ENVIRONMENT', 'NOT SET')
    print(f"1. Environment Variable: {env}")

    if env != 'production':
        print("   ⚠️  WARNING: ENVIRONMENT is not set to 'production'")
        print("   Set it with: export ENVIRONMENT=production (Linux/Mac)")
        print("               set ENVIRONMENT=production (Windows CMD)")
        print("               $env:ENVIRONMENT = 'production' (Windows PowerShell)")
        print()
    else:
        print("   ✅ Environment is set to production")
        print()

    # Check .env.production file exists
    env_file = Path(__file__).parent / '.env.production'
    print(f"2. .env.production File: {env_file}")

    if env_file.exists():
        print("   ✅ .env.production exists")
        print()
    else:
        print("   ❌ ERROR: .env.production NOT found!")
        print("   Create it from .env.example and add production credentials")
        print()
        return False

    # Load configuration
    print("3. Loading Configuration...")
    try:
        config = get_config()
        print("   ✅ Configuration loaded successfully")
        print()
    except Exception as e:
        print(f"   ❌ ERROR loading configuration: {e}")
        return False

    # Display configuration (MASK PASSWORD!)
    print("4. Configuration Details:")
    print(f"   Environment:     {config.environment}")
    print(f"   Database Host:   {config.db_host}")
    print(f"   Database Port:   {config.db_port}")
    print(f"   Database Name:   {config.db_name}")
    print(f"   Database Schema: {config.db_schema}")
    print(f"   Database User:   {config.db_user}")
    print(f"   Database Pass:   {'*' * len(config.db_password)} (hidden)")
    print(f"   SSL Mode:        {config.db_ssl_mode}")
    print(f"   DB Enabled:      {config.db_enabled}")
    print(f"   Debug Mode:      {config.debug}")
    print(f"   Log Level:       {config.log_level}")
    print()

    # Verify expected production values
    print("5. Production Validation:")
    errors = []

    if config.environment != 'production':
        errors.append(f"   ❌ Environment is '{config.environment}', expected 'production'")
    else:
        print("   ✅ Environment: production")

    if config.db_host != 'udideapdb01.unix.rgbk.com':
        errors.append(f"   ❌ DB Host is '{config.db_host}', expected 'udideapdb01.unix.rgbk.com'")
    else:
        print("   ✅ DB Host: udideapdb01.unix.rgbk.com")

    if config.db_name != 'prutech_bais':
        errors.append(f"   ❌ DB Name is '{config.db_name}', expected 'prutech_bais'")
    else:
        print("   ✅ DB Name: prutech_bais")

    if config.db_schema != 'activenet':
        errors.append(f"   ❌ DB Schema is '{config.db_schema}', expected 'activenet'")
    else:
        print("   ✅ DB Schema: activenet")

    if config.db_user != 'activenet_admin':
        errors.append(f"   ❌ DB User is '{config.db_user}', expected 'activenet_admin'")
    else:
        print("   ✅ DB User: activenet_admin")

    if config.debug:
        errors.append(f"   ❌ Debug mode is enabled (should be false in production)")
    else:
        print("   ✅ Debug: false")

    if not config.db_enabled:
        errors.append(f"   ❌ Database is disabled")
    else:
        print("   ✅ Database: enabled")

    print()

    # Display connection string (MASK PASSWORD)
    print("6. Connection String:")
    conn_str = config.db_connection_string
    masked_conn_str = conn_str.replace(config.db_password, '*' * len(config.db_password))
    print(f"   {masked_conn_str}")
    print()

    # Final result
    print("=" * 80)
    if errors:
        print("❌ VALIDATION FAILED")
        print()
        for error in errors:
            print(error)
        print()
        print("Fix the issues above and run this script again.")
        print("=" * 80)
        return False
    else:
        print("✅ ALL CHECKS PASSED - Production configuration is correct!")
        print()
        print("You can now run the pipeline:")
        print("  python run_batch_processing.py --batch-size 10")
        print("=" * 80)
        return True


if __name__ == '__main__':
    success = verify_production_config()
    sys.exit(0 if success else 1)
