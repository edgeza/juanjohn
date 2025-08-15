import os
# import duckdb  # REMOVED: No longer needed
import redis
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Optional, Generator, Any, Dict
from dotenv import load_dotenv

load_dotenv()

# Database configuration
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER', 'localhost')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'autonama')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '15432')
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DuckDB connection
duckdb_conn = None
DUCKDB_PATH = os.getenv('DUCKDB_PATH', ':memory:')

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=int(os.getenv('REDIS_DB', '0')),
    decode_responses=True
)

def get_db() -> Generator:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_timescale_connection():
    """Get a database session"""
    return SessionLocal()

def get_duckdb() -> Optional[Any]:
    """Get DuckDB connection - REMOVED: No longer needed"""
    # DuckDB removed - all calculations done locally
    return None

def get_redis():
    """Get Redis client"""
    return redis_client

class DatabaseManager:
    """Database manager for handling multiple database connections"""
    
    def __init__(self):
        self.postgres_engine = engine
        self.duckdb_conn = None
        self.redis_client = redis_client
    
    def get_postgres_session(self):
        """Get PostgreSQL session"""
        return SessionLocal()
    
    def get_duckdb_connection(self):
        """Get DuckDB connection - REMOVED: No longer needed"""
        # DuckDB removed - all calculations done locally
        return None
    
    def load_dataframe_to_duckdb(self, df: pd.DataFrame, table_name: str):
        """Load DataFrame to DuckDB table - REMOVED: No longer needed"""
        # DuckDB removed - all calculations done locally
        pass
    
    def cache_data(self, key: str, data: Any, expire: int = 3600):
        """Cache data in Redis"""
        import json
        if isinstance(data, pd.DataFrame):
            data = data.to_json()
        elif not isinstance(data, str):
            data = json.dumps(data)
        
        self.redis_client.setex(key, expire, data)
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data from Redis"""
        data = self.redis_client.get(key)
        if data:
            try:
                import json
                return json.loads(data)
            except:
                return data
        return None
    
    def close_connections(self):
        """Close all database connections"""
        # if self.duckdb_conn:  # REMOVED: No longer needed
        #     self.duckdb_conn.close()
        self.postgres_engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()
