#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Segmentation Analyzer - Database Initialization Script
================================================================
Python wrapper for PostgreSQL database initialization

This script:
1. Creates the database "network_analysis" (if not exists)
2. Creates all required tables
3. Creates indexes for performance
4. Creates users and roles
5. Grants appropriate permissions

Usage:
    python scripts/init_db.py

    # With custom credentials
    python scripts/init_db.py --host localhost --user postgres --password postgres

    # Drop and recreate (DANGEROUS!)
    python scripts/init_db.py --drop-existing

Requirements:
    - PostgreSQL server running
    - psycopg2 Python package installed
    - Superuser access (postgres user)

Author: Enterprise Security Team
Version: 3.0
"""

import sys
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    logger.error("psycopg2 not installed. Please install it:")
    logger.error("  pip install psycopg2-binary")
    sys.exit(1)


class DatabaseInitializer:
    """PostgreSQL database initializer"""

    def __init__(self, host='localhost', port=5432, user='postgres', password='postgres'):
        """
        Initialize database setup

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            user: PostgreSQL superuser (usually 'postgres')
            password: PostgreSQL password
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database_name = 'network_analysis'

        logger.info(f"Database Initializer configured:")
        logger.info(f"  Host: {self.host}:{self.port}")
        logger.info(f"  User: {self.user}")
        logger.info(f"  Database: {self.database_name}")

    def connect_to_postgres(self):
        """Connect to PostgreSQL server (default postgres database)"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # Connect to default database first
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            logger.error("Please ensure:")
            logger.error("  1. PostgreSQL server is running")
            logger.error("  2. Credentials are correct")
            logger.error(f"  3. User '{self.user}' has superuser privileges")
            sys.exit(1)

    def connect_to_database(self):
        """Connect to network_analysis database"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database_name
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to {self.database_name}: {e}")
            return None

    def database_exists(self, conn):
        """Check if database exists"""
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database_name,)
            )
            exists = cur.fetchone() is not None
            cur.close()
            return exists
        except psycopg2.Error as e:
            logger.error(f"Error checking database existence: {e}")
            return False

    def create_database(self, conn, drop_if_exists=False):
        """Create the network_analysis database"""
        try:
            cur = conn.cursor()

            # Check if database exists
            if self.database_exists(conn):
                if drop_if_exists:
                    logger.warning(f"Dropping existing database: {self.database_name}")

                    # Terminate connections first
                    cur.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.database_name}'
                        AND pid <> pg_backend_pid();
                    """)

                    # Drop database
                    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(self.database_name)
                    ))
                    logger.info(f"[OK] Database {self.database_name} dropped")
                else:
                    logger.info(f"Database {self.database_name} already exists (skipping creation)")
                    cur.close()
                    return True

            # Create database
            logger.info(f"Creating database: {self.database_name}...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(self.database_name)
            ))
            logger.info(f"[OK] Database {self.database_name} created successfully")

            cur.close()
            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to create database: {e}")
            return False

    def create_schema(self):
        """Create database schema (tables, indexes, etc.)"""
        logger.info("Creating database schema...")

        # Connect to the database
        conn = self.connect_to_database()
        if not conn:
            logger.error("Cannot connect to database for schema creation")
            return False

        try:
            cur = conn.cursor()

            # ========================================================================
            # Extensions
            # ========================================================================
            logger.info("Enabling extensions...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

            # ========================================================================
            # Tables
            # ========================================================================
            logger.info("Creating tables...")

            # Applications table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    app_id VARCHAR(255) PRIMARY KEY,
                    app_name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)

            # Flow records table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS flow_records (
                    id SERIAL PRIMARY KEY,
                    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
                    src_ip VARCHAR(45),
                    src_hostname VARCHAR(255),
                    dst_ip VARCHAR(45),
                    dst_hostname VARCHAR(255),
                    protocol VARCHAR(50),
                    port INTEGER,
                    bytes_in BIGINT DEFAULT 0,
                    bytes_out BIGINT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)

            # Analysis results table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
                    analysis_type VARCHAR(100),
                    result JSONB,
                    confidence FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Topology data table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS topology_data (
                    id SERIAL PRIMARY KEY,
                    app_id VARCHAR(255) REFERENCES applications(app_id) ON DELETE CASCADE,
                    security_zone VARCHAR(100),
                    dependencies JSONB,
                    characteristics JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(app_id)
                )
            """)

            # Model metadata table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS model_metadata (
                    id SERIAL PRIMARY KEY,
                    model_name VARCHAR(255) NOT NULL,
                    model_type VARCHAR(100),
                    version VARCHAR(50),
                    metrics JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            logger.info("[OK] All tables created")

            # ========================================================================
            # Indexes
            # ========================================================================
            logger.info("Creating indexes...")

            # Flow records indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_app_id ON flow_records(app_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_src_ip ON flow_records(src_ip)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_dst_ip ON flow_records(dst_ip)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_protocol ON flow_records(protocol)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_port ON flow_records(port)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_created_at ON flow_records(created_at DESC)")

            # Analysis results indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_app_id ON analysis_results(app_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_confidence ON analysis_results(confidence DESC)")

            # Topology data indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_topology_app_id ON topology_data(app_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_topology_zone ON topology_data(security_zone)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_topology_updated_at ON topology_data(updated_at DESC)")

            # Model metadata indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_model_name ON model_metadata(model_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_model_type ON model_metadata(model_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_model_created_at ON model_metadata(created_at DESC)")

            # JSONB indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_app_metadata ON applications USING GIN (metadata)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_flow_metadata ON flow_records USING GIN (metadata)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_result ON analysis_results USING GIN (result)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_topology_dependencies ON topology_data USING GIN (dependencies)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_topology_characteristics ON topology_data USING GIN (characteristics)")

            logger.info("[OK] All indexes created")

            # ========================================================================
            # Roles and Users
            # ========================================================================
            logger.info("Creating roles and users...")

            # Create roles
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_readonly') THEN
                        CREATE ROLE network_analyzer_readonly;
                    END IF;
                END $$
            """)

            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_readwrite') THEN
                        CREATE ROLE network_analyzer_readwrite;
                    END IF;
                END $$
            """)

            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer_admin') THEN
                        CREATE ROLE network_analyzer_admin;
                    END IF;
                END $$
            """)

            # Create application user
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'network_analyzer') THEN
                        CREATE USER network_analyzer WITH PASSWORD 'postgres';
                    END IF;
                END $$
            """)

            logger.info("[OK] Roles and users created")

            # ========================================================================
            # Grant Permissions
            # ========================================================================
            logger.info("Granting permissions...")

            # Read-only permissions
            cur.execute("GRANT CONNECT ON DATABASE network_analysis TO network_analyzer_readonly")
            cur.execute("GRANT USAGE ON SCHEMA public TO network_analyzer_readonly")
            cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO network_analyzer_readonly")

            # Read-write permissions
            cur.execute("GRANT CONNECT ON DATABASE network_analysis TO network_analyzer_readwrite")
            cur.execute("GRANT USAGE ON SCHEMA public TO network_analyzer_readwrite")
            cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO network_analyzer_readwrite")
            cur.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO network_analyzer_readwrite")

            # Admin permissions
            cur.execute("GRANT ALL PRIVILEGES ON DATABASE network_analysis TO network_analyzer_admin")
            cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO network_analyzer_admin")
            cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO network_analyzer_admin")

            # Assign role to network_analyzer user
            cur.execute("GRANT network_analyzer_readwrite TO network_analyzer")

            logger.info("[OK] Permissions granted")

            # ========================================================================
            # Triggers
            # ========================================================================
            logger.info("Creating triggers...")

            # Update timestamp function
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)

            # Triggers for applications table
            cur.execute("DROP TRIGGER IF EXISTS update_applications_updated_at ON applications")
            cur.execute("""
                CREATE TRIGGER update_applications_updated_at
                BEFORE UPDATE ON applications
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
            """)

            # Triggers for topology_data table
            cur.execute("DROP TRIGGER IF EXISTS update_topology_updated_at ON topology_data")
            cur.execute("""
                CREATE TRIGGER update_topology_updated_at
                BEFORE UPDATE ON topology_data
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
            """)

            logger.info("[OK] Triggers created")

            # ========================================================================
            # Verify
            # ========================================================================
            logger.info("Verifying schema...")

            # Count tables
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cur.fetchone()[0]

            # Count indexes
            cur.execute("SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'")
            index_count = cur.fetchone()[0]

            logger.info(f"[OK] Schema verified: {table_count} tables, {index_count} indexes")

            cur.close()
            conn.close()

            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to create schema: {e}")
            conn.close()
            return False

    def run(self, drop_if_exists=False):
        """Run complete database initialization"""
        logger.info("="*60)
        logger.info("Network Segmentation Analyzer - Database Initialization")
        logger.info("="*60)

        # Step 1: Connect to PostgreSQL
        logger.info("\nStep 1: Connecting to PostgreSQL...")
        conn = self.connect_to_postgres()

        # Step 2: Create database
        logger.info("\nStep 2: Creating database...")
        if not self.create_database(conn, drop_if_exists):
            conn.close()
            return False
        conn.close()

        # Step 3: Create schema
        logger.info("\nStep 3: Creating schema...")
        if not self.create_schema():
            return False

        # Success!
        logger.info("\n" + "="*60)
        logger.info("Database initialization completed successfully!")
        logger.info("="*60)
        logger.info("\nConnection Details:")
        logger.info(f"  Database: {self.database_name}")
        logger.info(f"  Host: {self.host}:{self.port}")
        logger.info(f"  User: postgres / postgres")
        logger.info(f"  App User: network_analyzer / postgres")
        logger.info(f"\nConnection String:")
        logger.info(f"  postgresql://postgres:postgres@{self.host}:{self.port}/{self.database_name}")
        logger.info(f"\nYou can now:")
        logger.info(f"  1. Update config.yaml with database credentials")
        logger.info(f"  2. Run: python start_system.py --web")
        logger.info(f"  3. Open: http://localhost:5000")
        logger.info("="*60)

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize PostgreSQL database for Network Segmentation Analyzer'
    )
    parser.add_argument('--host', default='localhost', help='PostgreSQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL port (default: 5432)')
    parser.add_argument('--user', default='postgres', help='PostgreSQL superuser (default: postgres)')
    parser.add_argument('--password', default='postgres', help='PostgreSQL password (default: postgres)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop existing database (DANGEROUS!)')

    args = parser.parse_args()

    # Warn about dropping
    if args.drop_existing:
        logger.warning("="*60)
        logger.warning("WARNING: You are about to DROP the existing database!")
        logger.warning("All data will be permanently deleted!")
        logger.warning("="*60)
        response = input("Are you sure? Type 'YES' to continue: ")
        if response != 'YES':
            logger.info("Aborted by user")
            sys.exit(0)

    # Initialize database
    initializer = DatabaseInitializer(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password
    )

    success = initializer.run(drop_if_exists=args.drop_existing)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
