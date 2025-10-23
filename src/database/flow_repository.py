"""
PostgreSQL Flow Repository
===========================
Manages persistence of network flows to PostgreSQL database

Schema:
- enriched_flows: Main table with all enriched flow data
- flow_aggregates: Pre-computed aggregations for performance
- dns_cache: Cache DNS lookup results
"""

import logging
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import execute_values
from contextlib import contextmanager

from src.config import get_config

logger = logging.getLogger(__name__)


class FlowRepository:
    """
    PostgreSQL repository for network flow data
    """

    def __init__(self, config=None):
        """
        Initialize database connection pool

        Args:
            config: Config instance (auto-loaded if None)
        """
        self.config = config or get_config()
        self.connection_pool = None
        self.schema = self.config.db_schema

        # IMPORTANT: Validate schema is NOT public
        if self.schema.lower() == 'public':
            raise ValueError(
                "SCHEMA VALIDATION FAILED: Cannot use 'public' schema!\n"
                f"Current schema: '{self.schema}'\n"
                "Please set DB_SCHEMA to a dedicated schema name in your .env file.\n"
                "Production: 'activenet'\n"
                "Development: 'network_analysis' or similar\n"
                "This prevents polluting the public schema with application tables."
            )

        if self.config.db_enabled:
            self._initialize_connection_pool()
            self._ensure_schema_exists()
            self._create_tables()
        else:
            logger.warning("PostgreSQL disabled. Flow persistence skipped.")

    def _initialize_connection_pool(self):
        """Create connection pool"""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=self.config.db_min_connections,
                maxconn=self.config.db_max_connections,
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                connect_timeout=self.config.db_connection_timeout,
                # Set search_path to dedicated schema FIRST, public as fallback only
                # This ensures all tables are created in the dedicated schema
                options=f'-c search_path={self.schema},public'
            )
            logger.info(f"✓ Connected to PostgreSQL: {self.config.db_host}:{self.config.db_port}/{self.config.db_name}")
            logger.info(f"  Schema: {self.schema}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.connection_pool = None
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if not self.connection_pool:
            raise RuntimeError("Database connection pool not initialized")

        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self.connection_pool.putconn(conn)

    def _ensure_schema_exists(self):
        """Create schema if it doesn't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # First check if schema exists
                    cur.execute("""
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name = %s
                    """, (self.schema,))

                    if cur.fetchone():
                        logger.info(f"✓ Schema '{self.schema}' already exists")
                    else:
                        # Try to create schema
                        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
                        logger.info(f"✓ Schema '{self.schema}' created")
                except Exception as e:
                    # If we don't have CREATE permission but schema exists, that's OK
                    if "permission denied" in str(e).lower():
                        # Verify schema exists
                        cur.execute("""
                            SELECT schema_name
                            FROM information_schema.schemata
                            WHERE schema_name = %s
                        """, (self.schema,))

                        if cur.fetchone():
                            logger.warning(f"⚠ No CREATE permission, but schema '{self.schema}' exists - continuing")
                        else:
                            logger.error(f"❌ Schema '{self.schema}' does not exist and cannot create it (no permission)")
                            raise
                    else:
                        raise

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Main enriched flows table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.enriched_flows (
                        id BIGSERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        -- Source information
                        source_app_code VARCHAR(50) NOT NULL,
                        source_ip INET NOT NULL,
                        source_hostname VARCHAR(255),
                        source_device_type VARCHAR(50),

                        -- Destination information
                        dest_ip INET NOT NULL,
                        dest_hostname VARCHAR(255),
                        dest_device_type VARCHAR(50),
                        dest_app_code VARCHAR(50),

                        -- Flow details
                        protocol VARCHAR(20),
                        port INTEGER,
                        bytes_in BIGINT DEFAULT 0,
                        bytes_out BIGINT DEFAULT 0,

                        -- Metadata
                        flow_direction VARCHAR(20),
                        flow_count INTEGER DEFAULT 1,
                        has_missing_data BOOLEAN DEFAULT FALSE,
                        missing_fields TEXT[],

                        -- Server Classification (added 2025-10-22)
                        source_server_type VARCHAR(50),
                        source_server_tier VARCHAR(50),
                        source_server_category VARCHAR(50),
                        dest_server_type VARCHAR(50),
                        dest_server_tier VARCHAR(50),
                        dest_server_category VARCHAR(50),

                        -- Batch tracking
                        batch_id VARCHAR(100),
                        file_source VARCHAR(255)
                    )
                """)

                # Create indexes for performance
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_app
                    ON {self.schema}.enriched_flows(source_app_code)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_app
                    ON {self.schema}.enriched_flows(dest_app_code)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_ip
                    ON {self.schema}.enriched_flows(source_ip)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_ip
                    ON {self.schema}.enriched_flows(dest_ip)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_flow_direction
                    ON {self.schema}.enriched_flows(flow_direction)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_created_at
                    ON {self.schema}.enriched_flows(created_at)
                """)

                # Indexes for server classification (added 2025-10-22)
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_type
                    ON {self.schema}.enriched_flows(source_server_type)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_type
                    ON {self.schema}.enriched_flows(dest_server_type)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_src_server_tier
                    ON {self.schema}.enriched_flows(source_server_tier)
                """)

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_enriched_flows_dst_server_tier
                    ON {self.schema}.enriched_flows(dest_server_tier)
                """)

                # DNS cache table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.dns_cache (
                        ip INET PRIMARY KEY,
                        hostname VARCHAR(255),
                        resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ttl INTEGER DEFAULT 86400
                    )
                """)

                # Flow aggregates (for fast queries)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.flow_aggregates (
                        id SERIAL PRIMARY KEY,
                        source_app_code VARCHAR(50),
                        dest_app_code VARCHAR(50),
                        flow_direction VARCHAR(20),
                        total_flows INTEGER,
                        total_bytes_in BIGINT,
                        total_bytes_out BIGINT,
                        unique_source_ips INTEGER,
                        unique_dest_ips INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        UNIQUE(source_app_code, dest_app_code, flow_direction)
                    )
                """)

                logger.info(f"✓ Database tables created in schema '{self.schema}'")

    def insert_flows_batch(self, df: pd.DataFrame, batch_id: str = None,
                          file_source: str = None) -> int:
        """
        Insert batch of flows from DataFrame

        Args:
            df: DataFrame with enriched flow data
            batch_id: Optional batch identifier
            file_source: Optional source file name

        Returns:
            Number of rows inserted
        """
        if not self.config.db_enabled or self.connection_pool is None:
            logger.warning("PostgreSQL disabled. Skipping flow insertion.")
            return 0

        batch_id = batch_id or datetime.now().strftime('%Y%m%d_%H%M%S')

        # Convert DataFrame to list of tuples
        records = []
        for _, row in df.iterrows():
            records.append((
                row.get('source_app_code'),
                str(row.get('source_ip')),
                row.get('source_hostname'),
                row.get('source_device_type'),
                str(row.get('dest_ip')),
                row.get('dest_hostname'),
                row.get('dest_device_type'),
                row.get('dest_app_code'),
                row.get('protocol'),
                int(row.get('port')) if pd.notna(row.get('port')) else None,
                int(row.get('bytes_in', 0)),
                int(row.get('bytes_out', 0)),
                row.get('flow_direction'),
                int(row.get('flow_count', 1)),
                bool(row.get('has_missing_data', False)),
                row.get('missing_fields', []) if isinstance(row.get('missing_fields'), list) else [],
                row.get('source_server_type'),  # Added 2025-10-22
                row.get('source_server_tier'),   # Added 2025-10-22
                row.get('source_server_category'),  # Added 2025-10-22
                row.get('dest_server_type'),     # Added 2025-10-22
                row.get('dest_server_tier'),      # Added 2025-10-22
                row.get('dest_server_category'),   # Added 2025-10-22
                batch_id,
                file_source
            ))

        # Bulk insert
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    f"""
                    INSERT INTO {self.schema}.enriched_flows (
                        source_app_code, source_ip, source_hostname, source_device_type,
                        dest_ip, dest_hostname, dest_device_type, dest_app_code,
                        protocol, port, bytes_in, bytes_out,
                        flow_direction, flow_count, has_missing_data, missing_fields,
                        source_server_type, source_server_tier, source_server_category,
                        dest_server_type, dest_server_tier, dest_server_category,
                        batch_id, file_source
                    ) VALUES %s
                    """,
                    records
                )

                inserted_count = cur.rowcount

        logger.info(f"✓ Inserted {inserted_count} flows to PostgreSQL (batch: {batch_id})")
        return inserted_count

    def get_flows_by_app(self, app_code: str) -> pd.DataFrame:
        """
        Get all flows for a specific app (source or destination)

        Args:
            app_code: Application code

        Returns:
            DataFrame with flows
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return pd.DataFrame()

        query = f"""
            SELECT *
            FROM {self.schema}.enriched_flows
            WHERE source_app_code = %s OR dest_app_code = %s
            ORDER BY created_at DESC
        """

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(app_code, app_code))

        logger.info(f"Retrieved {len(df)} flows for app '{app_code}'")
        return df

    def get_all_flows(self, limit: int = None) -> pd.DataFrame:
        """
        Get all flows from database

        Args:
            limit: Optional limit on number of rows

        Returns:
            DataFrame with all flows
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return pd.DataFrame()

        query = f"""
            SELECT *
            FROM {self.schema}.enriched_flows
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        logger.info(f"Retrieved {len(df)} total flows from database")
        return df

    def update_flow_aggregates(self):
        """
        Refresh flow aggregates table for fast queries
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.schema}.flow_aggregates (
                        source_app_code, dest_app_code, flow_direction,
                        total_flows, total_bytes_in, total_bytes_out,
                        unique_source_ips, unique_dest_ips, last_updated
                    )
                    SELECT
                        source_app_code,
                        dest_app_code,
                        flow_direction,
                        SUM(flow_count) as total_flows,
                        SUM(bytes_in) as total_bytes_in,
                        SUM(bytes_out) as total_bytes_out,
                        COUNT(DISTINCT source_ip) as unique_source_ips,
                        COUNT(DISTINCT dest_ip) as unique_dest_ips,
                        CURRENT_TIMESTAMP
                    FROM {self.schema}.enriched_flows
                    GROUP BY source_app_code, dest_app_code, flow_direction
                    ON CONFLICT (source_app_code, dest_app_code, flow_direction)
                    DO UPDATE SET
                        total_flows = EXCLUDED.total_flows,
                        total_bytes_in = EXCLUDED.total_bytes_in,
                        total_bytes_out = EXCLUDED.total_bytes_out,
                        unique_source_ips = EXCLUDED.unique_source_ips,
                        unique_dest_ips = EXCLUDED.unique_dest_ips,
                        last_updated = CURRENT_TIMESTAMP
                """)

        logger.info("✓ Flow aggregates updated")

    def cache_dns_lookup(self, ip: str, hostname: str, ttl: int = 86400):
        """
        Cache DNS lookup result

        Args:
            ip: IP address
            hostname: Resolved hostname
            ttl: Time to live in seconds (default 24 hours)
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.schema}.dns_cache (ip, hostname, ttl)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (ip)
                    DO UPDATE SET
                        hostname = EXCLUDED.hostname,
                        resolved_at = CURRENT_TIMESTAMP
                """, (ip, hostname, ttl))

    def get_cached_dns(self, ip: str) -> Optional[str]:
        """
        Get cached DNS result

        Args:
            ip: IP address

        Returns:
            Hostname if cached, None otherwise
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return None

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT hostname
                    FROM {self.schema}.dns_cache
                    WHERE ip = %s
                    AND resolved_at + (ttl || ' seconds')::INTERVAL > CURRENT_TIMESTAMP
                """, (ip,))

                result = cur.fetchone()
                return result[0] if result else None

    def get_statistics(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary with statistics
        """
        if not self.config.db_enabled or self.connection_pool is None:
            return {}

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT
                        COUNT(*) as total_flows,
                        COUNT(DISTINCT source_app_code) as unique_source_apps,
                        COUNT(DISTINCT dest_app_code) as unique_dest_apps,
                        COUNT(DISTINCT source_ip) as unique_source_ips,
                        COUNT(DISTINCT dest_ip) as unique_dest_ips,
                        SUM(bytes_in) as total_bytes_in,
                        SUM(bytes_out) as total_bytes_out,
                        MIN(created_at) as first_flow,
                        MAX(created_at) as last_flow
                    FROM {self.schema}.enriched_flows
                """)

                row = cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                stats = dict(zip(columns, row))

        return stats

    def close(self):
        """Close all database connections"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("✓ Database connections closed")


# Example usage
if __name__ == '__main__':
    # Test database connection
    repo = FlowRepository()

    # Get statistics
    stats = repo.get_statistics()
    print("="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("="*80)

    repo.close()
