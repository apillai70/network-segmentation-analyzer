# -*- coding: utf-8 -*-
"""
Unified Persistence Manager
============================
Enhanced persistence manager with PostgreSQL support and automatic JSON fallback

Features:
- Primary: PostgreSQL database (using psycopg2)
- Fallback: JSON file-based storage
- Automatic fallback detection
- Compatible API with existing PersistenceManager
- Migration support between backends
- Connection pooling
- Transaction support

100% LOCAL - NO EXTERNAL APIs

Author: Enterprise Security Team
Version: 3.0 - Unified Persistence
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from contextlib import contextmanager

# Try to import PostgreSQL support
try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("psycopg2 not installed. PostgreSQL support disabled. Using JSON fallback only.")

logger = logging.getLogger(__name__)


class UnifiedPersistenceManager:
    """
    Unified persistence manager with PostgreSQL primary and JSON fallback

    Provides seamless transition between storage backends with identical API.
    Automatically detects PostgreSQL availability and falls back to JSON files.
    """

    def __init__(
        self,
        postgres_config: Optional[Dict[str, str]] = None,
        json_storage_path: str = './persistent_data',
        auto_fallback: bool = True,
        prefer_postgres: bool = True
    ):
        """
        Initialize unified persistence manager

        Args:
            postgres_config: PostgreSQL connection config
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'network_segmentation',
                    'user': 'postgres',
                    'password': 'password'
                }
            json_storage_path: Path for JSON fallback storage
            auto_fallback: Automatically fallback to JSON if PostgreSQL fails
            prefer_postgres: Prefer PostgreSQL if available
        """
        self.postgres_config = postgres_config or self._load_default_postgres_config()
        self.json_storage_path = Path(json_storage_path)
        self.json_storage_path.mkdir(parents=True, exist_ok=True)
        self.auto_fallback = auto_fallback
        self.prefer_postgres = prefer_postgres

        # Connection pool
        self.connection_pool: Optional[Any] = None

        # Current backend
        self.backend = None  # 'postgres' or 'json'

        # Initialize storage backend
        self._initialize_backend()

        logger.info(f"✓ Unified Persistence Manager initialized")
        logger.info(f"  Backend: {self.backend}")
        logger.info(f"  Auto-fallback: {self.auto_fallback}")

    def _load_default_postgres_config(self) -> Dict[str, str]:
        """Load PostgreSQL config from environment or defaults"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'network_segmentation'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }

    def _initialize_backend(self):
        """Initialize storage backend with automatic fallback"""

        if self.prefer_postgres and POSTGRES_AVAILABLE:
            # Try PostgreSQL first
            if self._try_postgres_connection():
                self.backend = 'postgres'
                self._initialize_postgres_schema()
                logger.info("✓ Using PostgreSQL backend")
                return

        # Fallback to JSON
        if self.auto_fallback:
            self.backend = 'json'
            self._initialize_json_storage()
            logger.info("✓ Using JSON file backend (fallback)")
        else:
            raise RuntimeError("PostgreSQL connection failed and auto_fallback is disabled")

    def _try_postgres_connection(self) -> bool:
        """Test PostgreSQL connection"""
        if not POSTGRES_AVAILABLE:
            return False

        try:
            # Create connection pool
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=self.postgres_config['database'],
                user=self.postgres_config['user'],
                password=self.postgres_config['password'],
                connect_timeout=5
            )

            # Test connection
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")

            logger.info("✓ PostgreSQL connection successful")
            return True

        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            if self.connection_pool:
                self.connection_pool.closeall()
                self.connection_pool = None
            return False

    @contextmanager
    def _get_connection(self):
        """Get database connection from pool"""
        if self.backend != 'postgres' or not self.connection_pool:
            raise RuntimeError("PostgreSQL not available")

        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)

    def _initialize_postgres_schema(self):
        """Initialize PostgreSQL database schema"""

        schema_sql = """
        -- Applications table
        CREATE TABLE IF NOT EXISTS applications (
            app_id VARCHAR(255) PRIMARY KEY,
            app_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Flow records table
        CREATE TABLE IF NOT EXISTS flow_records (
            id SERIAL PRIMARY KEY,
            app_id VARCHAR(255) REFERENCES applications(app_id),
            src_ip VARCHAR(45),
            src_hostname VARCHAR(255),
            dst_ip VARCHAR(45),
            dst_hostname VARCHAR(255),
            protocol VARCHAR(50),
            port INTEGER,
            bytes_in BIGINT,
            bytes_out BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );

        -- Analysis results table
        CREATE TABLE IF NOT EXISTS analysis_results (
            id SERIAL PRIMARY KEY,
            app_id VARCHAR(255) REFERENCES applications(app_id),
            analysis_type VARCHAR(100),
            result JSONB,
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Topology data table
        CREATE TABLE IF NOT EXISTS topology_data (
            id SERIAL PRIMARY KEY,
            app_id VARCHAR(255) REFERENCES applications(app_id),
            security_zone VARCHAR(100),
            dependencies JSONB,
            characteristics JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Model metadata table
        CREATE TABLE IF NOT EXISTS model_metadata (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(255) NOT NULL,
            model_type VARCHAR(100),
            version VARCHAR(50),
            metrics JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_flow_app_id ON flow_records(app_id);
        CREATE INDEX IF NOT EXISTS idx_flow_src_ip ON flow_records(src_ip);
        CREATE INDEX IF NOT EXISTS idx_flow_dst_ip ON flow_records(dst_ip);
        CREATE INDEX IF NOT EXISTS idx_analysis_app_id ON analysis_results(app_id);
        CREATE INDEX IF NOT EXISTS idx_topology_app_id ON topology_data(app_id);
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            logger.info("✓ PostgreSQL schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise

    def _initialize_json_storage(self):
        """Initialize JSON file storage structure"""

        # Create subdirectories
        (self.json_storage_path / 'applications').mkdir(exist_ok=True)
        (self.json_storage_path / 'flows').mkdir(exist_ok=True)
        (self.json_storage_path / 'analysis').mkdir(exist_ok=True)
        (self.json_storage_path / 'topology').mkdir(exist_ok=True)
        (self.json_storage_path / 'models').mkdir(exist_ok=True)

        logger.info("✓ JSON storage structure initialized")

    # ========================================================================
    # Public API - Backend Agnostic
    # ========================================================================

    def save_application(self, app_id: str, flows_df: pd.DataFrame, metadata: Optional[Dict] = None) -> bool:
        """
        Save application and its flow data

        Args:
            app_id: Application identifier
            flows_df: DataFrame with flow records
            metadata: Optional application metadata

        Returns:
            Success status
        """
        try:
            if self.backend == 'postgres':
                return self._save_application_postgres(app_id, flows_df, metadata)
            else:
                return self._save_application_json(app_id, flows_df, metadata)
        except Exception as e:
            logger.error(f"Failed to save application {app_id}: {e}")

            # Try fallback if enabled
            if self.auto_fallback and self.backend == 'postgres':
                logger.warning("Attempting fallback to JSON storage...")
                self.backend = 'json'
                return self._save_application_json(app_id, flows_df, metadata)

            return False

    def get_application(self, app_id: str) -> Optional[Dict]:
        """Get application data"""
        try:
            if self.backend == 'postgres':
                return self._get_application_postgres(app_id)
            else:
                return self._get_application_json(app_id)
        except Exception as e:
            logger.error(f"Failed to get application {app_id}: {e}")
            return None

    def list_applications(self) -> List[Dict]:
        """List all applications"""
        try:
            if self.backend == 'postgres':
                return self._list_applications_postgres()
            else:
                return self._list_applications_json()
        except Exception as e:
            logger.error(f"Failed to list applications: {e}")
            return []

    def save_analysis_result(self, app_id: str, analysis_type: str, result: Dict, confidence: float = 1.0) -> bool:
        """Save analysis result"""
        try:
            if self.backend == 'postgres':
                return self._save_analysis_postgres(app_id, analysis_type, result, confidence)
            else:
                return self._save_analysis_json(app_id, analysis_type, result, confidence)
        except Exception as e:
            logger.error(f"Failed to save analysis for {app_id}: {e}")
            return False

    def get_analysis_results(self, app_id: Optional[str] = None, analysis_type: Optional[str] = None) -> List[Dict]:
        """Get analysis results"""
        try:
            if self.backend == 'postgres':
                return self._get_analysis_postgres(app_id, analysis_type)
            else:
                return self._get_analysis_json(app_id, analysis_type)
        except Exception as e:
            logger.error(f"Failed to get analysis results: {e}")
            return []

    def save_topology_data(self, app_id: str, security_zone: str, dependencies: List[Dict],
                          characteristics: List[str]) -> bool:
        """Save topology data"""
        try:
            if self.backend == 'postgres':
                return self._save_topology_postgres(app_id, security_zone, dependencies, characteristics)
            else:
                return self._save_topology_json(app_id, security_zone, dependencies, characteristics)
        except Exception as e:
            logger.error(f"Failed to save topology for {app_id}: {e}")
            return False

    def get_topology_data(self, app_id: Optional[str] = None) -> List[Dict]:
        """Get topology data"""
        try:
            if self.backend == 'postgres':
                return self._get_topology_postgres(app_id)
            else:
                return self._get_topology_json(app_id)
        except Exception as e:
            logger.error(f"Failed to get topology data: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            if self.backend == 'postgres':
                return self._get_statistics_postgres()
            else:
                return self._get_statistics_json()
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    # ========================================================================
    # PostgreSQL Implementation
    # ========================================================================

    def _save_application_postgres(self, app_id: str, flows_df: pd.DataFrame, metadata: Optional[Dict]) -> bool:
        """Save application to PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Insert/update application
                cur.execute("""
                    INSERT INTO applications (app_id, app_name, metadata, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (app_id)
                    DO UPDATE SET updated_at = EXCLUDED.updated_at, metadata = EXCLUDED.metadata
                """, (app_id, app_id, json.dumps(metadata or {}), datetime.now()))

                # Insert flow records
                for _, row in flows_df.iterrows():
                    cur.execute("""
                        INSERT INTO flow_records
                        (app_id, src_ip, src_hostname, dst_ip, dst_hostname, protocol, port, bytes_in, bytes_out)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        app_id,
                        row.get('Source IP', row.get('src_ip')),
                        row.get('Source Hostname', row.get('src_hostname')),
                        row.get('Dest IP', row.get('dst_ip')),
                        row.get('Dest Hostname', row.get('dst_hostname')),
                        row.get('Protocol', 'TCP'),
                        row.get('Port', None),
                        row.get('Bytes In', 0),
                        row.get('Bytes Out', 0)
                    ))

        logger.info(f"✓ Saved application {app_id} to PostgreSQL ({len(flows_df)} flows)")
        return True

    def _get_application_postgres(self, app_id: str) -> Optional[Dict]:
        """Get application from PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM applications WHERE app_id = %s", (app_id,))
                app = cur.fetchone()

                if not app:
                    return None

                # Get flow count
                cur.execute("SELECT COUNT(*) as count FROM flow_records WHERE app_id = %s", (app_id,))
                flow_count = cur.fetchone()['count']

                return {
                    'app_id': app['app_id'],
                    'app_name': app['app_name'],
                    'flow_count': flow_count,
                    'created_at': app['created_at'].isoformat() if app['created_at'] else None,
                    'updated_at': app['updated_at'].isoformat() if app['updated_at'] else None,
                    'metadata': app['metadata']
                }

    def _list_applications_postgres(self) -> List[Dict]:
        """List all applications from PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.app_id, a.app_name, a.created_at, a.updated_at,
                           COUNT(f.id) as flow_count
                    FROM applications a
                    LEFT JOIN flow_records f ON a.app_id = f.app_id
                    GROUP BY a.app_id, a.app_name, a.created_at, a.updated_at
                    ORDER BY a.updated_at DESC
                """)

                apps = cur.fetchall()

                return [
                    {
                        'app_id': app['app_id'],
                        'app_name': app['app_name'],
                        'flow_count': app['flow_count'],
                        'created_at': app['created_at'].isoformat() if app['created_at'] else None,
                        'updated_at': app['updated_at'].isoformat() if app['updated_at'] else None
                    }
                    for app in apps
                ]

    def _save_analysis_postgres(self, app_id: str, analysis_type: str, result: Dict, confidence: float) -> bool:
        """Save analysis result to PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_results (app_id, analysis_type, result, confidence)
                    VALUES (%s, %s, %s, %s)
                """, (app_id, analysis_type, json.dumps(result), confidence))

        return True

    def _get_analysis_postgres(self, app_id: Optional[str], analysis_type: Optional[str]) -> List[Dict]:
        """Get analysis results from PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM analysis_results WHERE 1=1"
                params = []

                if app_id:
                    query += " AND app_id = %s"
                    params.append(app_id)

                if analysis_type:
                    query += " AND analysis_type = %s"
                    params.append(analysis_type)

                query += " ORDER BY created_at DESC"

                cur.execute(query, params)
                results = cur.fetchall()

                return [
                    {
                        'id': r['id'],
                        'app_id': r['app_id'],
                        'analysis_type': r['analysis_type'],
                        'result': r['result'],
                        'confidence': r['confidence'],
                        'created_at': r['created_at'].isoformat() if r['created_at'] else None
                    }
                    for r in results
                ]

    def _save_topology_postgres(self, app_id: str, security_zone: str, dependencies: List[Dict],
                               characteristics: List[str]) -> bool:
        """Save topology data to PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO topology_data (app_id, security_zone, dependencies, characteristics, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET security_zone = EXCLUDED.security_zone,
                                  dependencies = EXCLUDED.dependencies,
                                  characteristics = EXCLUDED.characteristics,
                                  updated_at = EXCLUDED.updated_at
                """, (
                    app_id,
                    security_zone,
                    json.dumps(dependencies),
                    json.dumps(characteristics),
                    datetime.now()
                ))

        return True

    def _get_topology_postgres(self, app_id: Optional[str]) -> List[Dict]:
        """Get topology data from PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if app_id:
                    cur.execute("SELECT * FROM topology_data WHERE app_id = %s ORDER BY updated_at DESC", (app_id,))
                else:
                    cur.execute("SELECT * FROM topology_data ORDER BY updated_at DESC")

                results = cur.fetchall()

                return [
                    {
                        'id': r['id'],
                        'app_id': r['app_id'],
                        'security_zone': r['security_zone'],
                        'dependencies': r['dependencies'],
                        'characteristics': r['characteristics'],
                        'created_at': r['created_at'].isoformat() if r['created_at'] else None,
                        'updated_at': r['updated_at'].isoformat() if r['updated_at'] else None
                    }
                    for r in results
                ]

    def _get_statistics_postgres(self) -> Dict:
        """Get statistics from PostgreSQL"""

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get counts
                cur.execute("SELECT COUNT(*) as count FROM applications")
                app_count = cur.fetchone()['count']

                cur.execute("SELECT COUNT(*) as count FROM flow_records")
                flow_count = cur.fetchone()['count']

                cur.execute("SELECT COUNT(*) as count FROM analysis_results")
                analysis_count = cur.fetchone()['count']

                cur.execute("SELECT COUNT(*) as count FROM topology_data")
                topology_count = cur.fetchone()['count']

                return {
                    'backend': 'postgres',
                    'applications': app_count,
                    'flow_records': flow_count,
                    'analysis_results': analysis_count,
                    'topology_records': topology_count
                }

    # ========================================================================
    # JSON Implementation
    # ========================================================================

    def _save_application_json(self, app_id: str, flows_df: pd.DataFrame, metadata: Optional[Dict]) -> bool:
        """Save application to JSON files"""

        app_dir = self.json_storage_path / 'applications' / app_id
        app_dir.mkdir(exist_ok=True)

        # Save application metadata
        app_data = {
            'app_id': app_id,
            'app_name': app_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'flow_count': len(flows_df)
        }

        with open(app_dir / 'application.json', 'w') as f:
            json.dump(app_data, f, indent=2)

        # Save flows as CSV
        flows_df.to_csv(app_dir / 'flows.csv', index=False)

        logger.info(f"✓ Saved application {app_id} to JSON ({len(flows_df)} flows)")
        return True

    def _get_application_json(self, app_id: str) -> Optional[Dict]:
        """Get application from JSON files"""

        app_file = self.json_storage_path / 'applications' / app_id / 'application.json'

        if not app_file.exists():
            return None

        with open(app_file, 'r') as f:
            return json.load(f)

    def _list_applications_json(self) -> List[Dict]:
        """List all applications from JSON files"""

        apps_dir = self.json_storage_path / 'applications'
        apps = []

        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                app_file = app_dir / 'application.json'
                if app_file.exists():
                    with open(app_file, 'r') as f:
                        apps.append(json.load(f))

        return sorted(apps, key=lambda x: x.get('updated_at', ''), reverse=True)

    def _save_analysis_json(self, app_id: str, analysis_type: str, result: Dict, confidence: float) -> bool:
        """Save analysis result to JSON"""

        analysis_dir = self.json_storage_path / 'analysis' / app_id
        analysis_dir.mkdir(parents=True, exist_ok=True)

        analysis_data = {
            'app_id': app_id,
            'analysis_type': analysis_type,
            'result': result,
            'confidence': confidence,
            'created_at': datetime.now().isoformat()
        }

        # Append to analysis file
        analysis_file = analysis_dir / f'{analysis_type}.json'

        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
            existing.append(analysis_data)
        else:
            existing = [analysis_data]

        with open(analysis_file, 'w') as f:
            json.dump(existing, f, indent=2)

        return True

    def _get_analysis_json(self, app_id: Optional[str], analysis_type: Optional[str]) -> List[Dict]:
        """Get analysis results from JSON"""

        results = []
        analysis_dir = self.json_storage_path / 'analysis'

        if app_id:
            # Get specific app analysis
            app_analysis_dir = analysis_dir / app_id
            if app_analysis_dir.exists():
                for analysis_file in app_analysis_dir.glob('*.json'):
                    if analysis_type and analysis_file.stem != analysis_type:
                        continue

                    with open(analysis_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            results.extend(data)
                        else:
                            results.append(data)
        else:
            # Get all analysis
            for app_analysis_dir in analysis_dir.iterdir():
                if app_analysis_dir.is_dir():
                    for analysis_file in app_analysis_dir.glob('*.json'):
                        if analysis_type and analysis_file.stem != analysis_type:
                            continue

                        with open(analysis_file, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                results.extend(data)
                            else:
                                results.append(data)

        return results

    def _save_topology_json(self, app_id: str, security_zone: str, dependencies: List[Dict],
                           characteristics: List[str]) -> bool:
        """Save topology data to JSON"""

        topology_dir = self.json_storage_path / 'topology'
        topology_dir.mkdir(exist_ok=True)

        topology_data = {
            'app_id': app_id,
            'security_zone': security_zone,
            'dependencies': dependencies,
            'characteristics': characteristics,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        with open(topology_dir / f'{app_id}.json', 'w') as f:
            json.dump(topology_data, f, indent=2)

        return True

    def _get_topology_json(self, app_id: Optional[str]) -> List[Dict]:
        """Get topology data from JSON"""

        topology_dir = self.json_storage_path / 'topology'
        results = []

        if app_id:
            topology_file = topology_dir / f'{app_id}.json'
            if topology_file.exists():
                with open(topology_file, 'r') as f:
                    results.append(json.load(f))
        else:
            for topology_file in topology_dir.glob('*.json'):
                with open(topology_file, 'r') as f:
                    results.append(json.load(f))

        return results

    def _get_statistics_json(self) -> Dict:
        """Get statistics from JSON files"""

        app_count = len(list((self.json_storage_path / 'applications').iterdir()))
        analysis_count = sum(1 for _ in (self.json_storage_path / 'analysis').rglob('*.json'))
        topology_count = len(list((self.json_storage_path / 'topology').glob('*.json')))

        # Count flows
        flow_count = 0
        for app_dir in (self.json_storage_path / 'applications').iterdir():
            flow_file = app_dir / 'flows.csv'
            if flow_file.exists():
                try:
                    df = pd.read_csv(flow_file)
                    flow_count += len(df)
                except:
                    pass

        return {
            'backend': 'json',
            'applications': app_count,
            'flow_records': flow_count,
            'analysis_results': analysis_count,
            'topology_records': topology_count
        }

    # ========================================================================
    # Migration Support
    # ========================================================================

    def migrate_to_postgres(self) -> bool:
        """Migrate JSON data to PostgreSQL"""

        if self.backend != 'json':
            logger.warning("Migration only supported from JSON to PostgreSQL")
            return False

        if not POSTGRES_AVAILABLE:
            logger.error("PostgreSQL not available for migration")
            return False

        logger.info("Starting migration from JSON to PostgreSQL...")

        try:
            # Switch to postgres
            self.backend = 'postgres'
            self._initialize_postgres_schema()

            # Migrate applications
            apps = self._list_applications_json()
            for app in apps:
                app_id = app['app_id']

                # Load flows
                flow_file = self.json_storage_path / 'applications' / app_id / 'flows.csv'
                if flow_file.exists():
                    flows_df = pd.read_csv(flow_file)
                    self._save_application_postgres(app_id, flows_df, app.get('metadata'))

                # Migrate topology
                topology = self._get_topology_json(app_id)
                for topo in topology:
                    self._save_topology_postgres(
                        topo['app_id'],
                        topo['security_zone'],
                        topo['dependencies'],
                        topo['characteristics']
                    )

            logger.info(f"✓ Migration complete: {len(apps)} applications migrated")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.backend = 'json'  # Rollback
            return False

    def export_to_json(self, output_path: str) -> bool:
        """Export current data to JSON backup"""

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export all data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'backend': self.backend,
            'applications': self.list_applications(),
            'topology': self.get_topology_data(),
            'analysis': self.get_analysis_results(),
            'statistics': self.get_statistics()
        }

        with open(output_dir / 'backup.json', 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"✓ Data exported to {output_path}/backup.json")
        return True

    def close(self):
        """Close connections and cleanup"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("✓ PostgreSQL connections closed")


# ============================================================================
# Factory Function
# ============================================================================

def create_persistence_manager(
    postgres_config: Optional[Dict] = None,
    prefer_postgres: bool = True,
    auto_fallback: bool = True
) -> UnifiedPersistenceManager:
    """
    Factory function to create persistence manager

    Usage:
        # Try PostgreSQL first, fallback to JSON
        pm = create_persistence_manager()

        # Force JSON only
        pm = create_persistence_manager(prefer_postgres=False)

        # Custom PostgreSQL config
        pm = create_persistence_manager(
            postgres_config={
                'host': 'localhost',
                'database': 'mydb',
                'user': 'myuser',
                'password': 'mypass'
            }
        )
    """
    return UnifiedPersistenceManager(
        postgres_config=postgres_config,
        prefer_postgres=prefer_postgres,
        auto_fallback=auto_fallback
    )
