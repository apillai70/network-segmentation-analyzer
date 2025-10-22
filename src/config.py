"""
Configuration Management for Network Segmentation Analyzer
===========================================================
Loads configuration from:
1. .env files (environment-specific credentials)
2. config.yaml (public configuration)

Environment files (.env) are NEVER committed to git.
Credentials are loaded from .env.production or .env.development
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Application configuration loaded from .env and config.yaml
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration

        Args:
            environment: 'production', 'development', or None (auto-detect)
        """
        self.project_root = Path(__file__).parent.parent
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')

        # Load configurations
        self._load_env_file()
        self._load_yaml_config()

        logger.info(f"Configuration loaded for environment: {self.environment}")

    def _load_env_file(self):
        """
        Load environment-specific .env file
        Priority:
        1. .env.{environment} (e.g., .env.production)
        2. .env (generic)
        """
        env_file = self.project_root / f'.env.{self.environment}'
        fallback_env = self.project_root / '.env'

        # Try environment-specific file first
        if env_file.exists():
            self._parse_env_file(env_file)
            logger.info(f"Loaded environment file: {env_file}")
        elif fallback_env.exists():
            self._parse_env_file(fallback_env)
            logger.info(f"Loaded fallback environment file: {fallback_env}")
        else:
            logger.warning(f"No .env file found. Using defaults.")

    def _parse_env_file(self, env_path: Path):
        """Parse .env file and set environment variables"""
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Strip inline comments (after value)
                    # Handle: DB_SCHEMA=network_analysis  # comment
                    if '#' in value:
                        value = value.split('#')[0].strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Set environment variable
                    os.environ[key] = value

    def _load_yaml_config(self):
        """Load public configuration from config.yaml"""
        config_path = self.project_root / 'config.yaml'

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.yaml_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded YAML config: {config_path}")
        else:
            self.yaml_config = {}
            logger.warning("No config.yaml found. Using defaults.")

    # Database Configuration
    @property
    def db_host(self) -> str:
        return os.getenv('DB_HOST', 'localhost')

    @property
    def db_port(self) -> int:
        return int(os.getenv('DB_PORT', '5432'))

    @property
    def db_name(self) -> str:
        return os.getenv('DB_NAME', 'network_analysis_dev')

    @property
    def db_schema(self) -> str:
        return os.getenv('DB_SCHEMA', 'public')

    @property
    def db_user(self) -> str:
        return os.getenv('DB_USER', 'postgres')

    @property
    def db_password(self) -> str:
        return os.getenv('DB_PASSWORD', 'postgres')

    @property
    def db_ssl_mode(self) -> str:
        return os.getenv('DB_SSL_MODE', 'disable')

    @property
    def db_min_connections(self) -> int:
        return int(os.getenv('DB_MIN_CONNECTIONS', '2'))

    @property
    def db_max_connections(self) -> int:
        return int(os.getenv('DB_MAX_CONNECTIONS', '10'))

    @property
    def db_connection_timeout(self) -> int:
        return int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))

    @property
    def db_connection_string(self) -> str:
        """
        Build PostgreSQL connection string
        Format: postgresql://user:password@host:port/database?sslmode=disable
        """
        return (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode={self.db_ssl_mode}"
        )

    @property
    def db_enabled(self) -> bool:
        """Check if PostgreSQL is enabled"""
        yaml_enabled = self.yaml_config.get('database', {}).get('postgresql', {}).get('enabled', True)
        env_enabled = os.getenv('DB_ENABLED', 'true').lower() == 'true'
        return yaml_enabled and env_enabled

    # Application Settings
    @property
    def debug(self) -> bool:
        return os.getenv('DEBUG', 'false').lower() == 'true'

    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')

    @property
    def is_production(self) -> bool:
        return self.environment == 'production'

    @property
    def is_development(self) -> bool:
        return self.environment == 'development'

    # Paths
    @property
    def data_input_dir(self) -> Path:
        return self.project_root / 'data' / 'input'

    @property
    def output_dir(self) -> Path:
        return self.project_root / 'outputs_final'

    @property
    def logs_dir(self) -> Path:
        log_dir = self.yaml_config.get('logging', {}).get('dir', './logs')
        return self.project_root / log_dir

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value from YAML config

        Args:
            key: Dot-notation key (e.g., 'database.postgresql.host')
            default: Default value if key not found
        """
        keys = key.split('.')
        value = self.yaml_config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def __repr__(self):
        """String representation (HIDE CREDENTIALS!)"""
        return (
            f"Config(\n"
            f"  environment={self.environment}\n"
            f"  db_host={self.db_host}\n"
            f"  db_port={self.db_port}\n"
            f"  db_name={self.db_name}\n"
            f"  db_schema={self.db_schema}\n"
            f"  db_user={self.db_user}\n"
            f"  db_password=*** (hidden)\n"
            f"  db_enabled={self.db_enabled}\n"
            f"  debug={self.debug}\n"
            f")"
        )


# Singleton instance
_config_instance = None


def get_config(environment: Optional[str] = None) -> Config:
    """
    Get singleton configuration instance

    Args:
        environment: Force specific environment (production, development)

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(environment)

    return _config_instance


# Example usage:
if __name__ == '__main__':
    # Test configuration loading
    config = get_config()

    print("="*80)
    print("CONFIGURATION TEST")
    print("="*80)
    print(config)
    print()
    print("Connection String:")
    print(f"  {config.db_connection_string}")
    print()
    print("Paths:")
    print(f"  Input: {config.data_input_dir}")
    print(f"  Output: {config.output_dir}")
    print(f"  Logs: {config.logs_dir}")
    print("="*80)
