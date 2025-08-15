"""
Database Configuration Management

This module manages database connections and configurations for TimescaleDB, DuckDB, and Redis.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    TIMESCALEDB = "timescaledb"
    DUCKDB = "duckdb"
    REDIS = "redis"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConnection:
    """Database connection configuration."""
    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class DuckDBConfig:
    """DuckDB specific configuration."""
    database_path: str
    memory_limit: str = "2GB"
    threads: int = 4
    read_only: bool = False
    access_mode: str = "automatic"  # automatic, read_only, read_write


@dataclass
class RedisConfig:
    """Redis specific configuration."""
    host: str
    port: int
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    max_connections: int = 50
    retry_on_timeout: bool = True


class DatabaseConfig:
    """
    Centralized database configuration management.
    
    Handles connection strings, pool settings, and database-specific
    configurations for all database systems.
    """
    
    def __init__(self):
        """Initialize database configuration."""
        self._connections = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load database configuration from environment variables."""
        logger.info("Loading database configuration from environment")
        
        # Load TimescaleDB/PostgreSQL configuration
        self._load_timescaledb_config()
        
        # Load DuckDB configuration
        self._load_duckdb_config()
        
        # Load Redis configuration
        self._load_redis_config()
    
    def _load_timescaledb_config(self) -> None:
        """Load TimescaleDB configuration."""
        # Check for full DATABASE_URL first
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Parse DATABASE_URL
            parsed = urlparse(database_url)
            config = DatabaseConnection(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/') if parsed.path else 'autonama',
                username=parsed.username,
                password=parsed.password,
                ssl_mode=os.getenv('POSTGRES_SSL_MODE', 'prefer')
            )
        else:
            # Build from individual environment variables
            config = DatabaseConnection(
                host=os.getenv('POSTGRES_SERVER', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', '15432')),
                database=os.getenv('POSTGRES_DB', 'autonama'),
                username=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                ssl_mode=os.getenv('POSTGRES_SSL_MODE', 'prefer')
            )
        
        # Override pool settings if provided
        config.pool_size = int(os.getenv('POSTGRES_POOL_SIZE', '10'))
        config.max_overflow = int(os.getenv('POSTGRES_MAX_OVERFLOW', '20'))
        config.pool_timeout = int(os.getenv('POSTGRES_POOL_TIMEOUT', '30'))
        config.pool_recycle = int(os.getenv('POSTGRES_POOL_RECYCLE', '3600'))
        config.echo = os.getenv('POSTGRES_ECHO', 'false').lower() == 'true'
        
        self._connections[DatabaseType.TIMESCALEDB] = config
        self._connections[DatabaseType.POSTGRESQL] = config  # Same as TimescaleDB
        
        logger.info(f"TimescaleDB config: {config.host}:{config.port}/{config.database}")
    
    def _load_duckdb_config(self) -> None:
        """Load DuckDB configuration - REMOVED: No longer needed."""
        # DuckDB removed - all calculations done locally
        logger.info("DuckDB configuration removed - using local processing only")
    
    def _load_redis_config(self) -> None:
        """Load Redis configuration."""
        # Check for Redis URL first
        redis_url = os.getenv('REDIS_URL')
        
        if redis_url:
            parsed = urlparse(redis_url)
            config = RedisConfig(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                password=parsed.password,
                ssl=parsed.scheme == 'rediss'
            )
        else:
            # Build from individual environment variables
            config = RedisConfig(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB', '0')),
                password=os.getenv('REDIS_PASSWORD'),
                ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true'
            )
        
        # Override connection settings if provided
        config.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', '30'))
        config.socket_connect_timeout = int(os.getenv('REDIS_CONNECT_TIMEOUT', '30'))
        config.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
        config.retry_on_timeout = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        
        self._connections[DatabaseType.REDIS] = config
        
        logger.info(f"Redis config: {config.host}:{config.port}/{config.db}")
    
    def get_connection_config(self, db_type: DatabaseType) -> Any:
        """
        Get connection configuration for a database type.
        
        Args:
            db_type: Database type
            
        Returns:
            Connection configuration object
        """
        return self._connections.get(db_type)
    
    def get_timescaledb_url(self, include_password: bool = True) -> str:
        """
        Get TimescaleDB connection URL.
        
        Args:
            include_password: Whether to include password in URL
            
        Returns:
            Database connection URL
        """
        config = self.get_connection_config(DatabaseType.TIMESCALEDB)
        if not config:
            raise ValueError("TimescaleDB configuration not found")
        
        password_part = f":{config.password}" if include_password and config.password else ""
        
        return (
            f"postgresql://{config.username}{password_part}@"
            f"{config.host}:{config.port}/{config.database}"
        )
    
    def get_sqlalchemy_url(self, db_type: DatabaseType = DatabaseType.TIMESCALEDB) -> str:
        """
        Get SQLAlchemy connection URL.
        
        Args:
            db_type: Database type
            
        Returns:
            SQLAlchemy connection URL
        """
        if db_type in [DatabaseType.TIMESCALEDB, DatabaseType.POSTGRESQL]:
            return self.get_timescaledb_url()
        else:
            raise ValueError(f"SQLAlchemy URL not supported for {db_type}")
    
    def get_duckdb_path(self) -> str:
        """
        Get DuckDB database file path.
        
        Returns:
            DuckDB database file path
        """
        config = self.get_connection_config(DatabaseType.DUCKDB)
        if not config:
            raise ValueError("DuckDB configuration not found")
        
        return config.database_path
    
    def get_redis_connection_kwargs(self) -> Dict[str, Any]:
        """
        Get Redis connection keyword arguments.
        
        Returns:
            Dict of Redis connection parameters
        """
        config = self.get_connection_config(DatabaseType.REDIS)
        if not config:
            raise ValueError("Redis configuration not found")
        
        kwargs = {
            'host': config.host,
            'port': config.port,
            'db': config.db,
            'socket_timeout': config.socket_timeout,
            'socket_connect_timeout': config.socket_connect_timeout,
            'retry_on_timeout': config.retry_on_timeout,
            'ssl': config.ssl
        }
        
        if config.password:
            kwargs['password'] = config.password
        
        return kwargs
    
    def get_celery_broker_url(self) -> str:
        """
        Get Celery broker URL (Redis).
        
        Returns:
            Celery broker URL
        """
        config = self.get_connection_config(DatabaseType.REDIS)
        if not config:
            raise ValueError("Redis configuration not found")
        
        password_part = f":{config.password}@" if config.password else ""
        protocol = "rediss" if config.ssl else "redis"
        
        return f"{protocol}://{password_part}{config.host}:{config.port}/1"
    
    def get_celery_result_backend_url(self) -> str:
        """
        Get Celery result backend URL (Redis).
        
        Returns:
            Celery result backend URL
        """
        config = self.get_connection_config(DatabaseType.REDIS)
        if not config:
            raise ValueError("Redis configuration not found")
        
        password_part = f":{config.password}@" if config.password else ""
        protocol = "rediss" if config.ssl else "redis"
        
        return f"{protocol}://{password_part}{config.host}:{config.port}/2"
    
    def validate_connections(self) -> Dict[str, bool]:
        """
        Validate all database connections.
        
        Returns:
            Dict mapping database types to validation status
        """
        validation_results = {}
        
        for db_type in DatabaseType:
            config = self.get_connection_config(db_type)
            is_valid = config is not None
            validation_results[db_type.value] = is_valid
            
            if is_valid:
                logger.info(f"✅ {db_type.value} configuration is valid")
            else:
                logger.warning(f"❌ {db_type.value} configuration is missing")
        
        return validation_results
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        Get all database configurations.
        
        Returns:
            Dict containing all database configurations
        """
        return {
            'timescaledb': {
                'config': self.get_connection_config(DatabaseType.TIMESCALEDB),
                'url': self.get_timescaledb_url(include_password=False),
                'sqlalchemy_url': self.get_sqlalchemy_url()
            },
            'duckdb': {
                'config': self.get_connection_config(DatabaseType.DUCKDB),
                'path': self.get_duckdb_path()
            },
            'redis': {
                'config': self.get_connection_config(DatabaseType.REDIS),
                'connection_kwargs': self.get_redis_connection_kwargs(),
                'celery_broker_url': self.get_celery_broker_url(),
                'celery_result_backend_url': self.get_celery_result_backend_url()
            }
        }


# Global database configuration instance
db_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    return db_config


def reload_database_config() -> DatabaseConfig:
    """Reload database configuration from environment."""
    global db_config
    db_config = DatabaseConfig()
    return db_config
