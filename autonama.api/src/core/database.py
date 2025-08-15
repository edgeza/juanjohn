from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# import duckdb  # REMOVED: No longer needed
import redis
import os
from typing import Generator, Optional, Any

from src.core.config import settings

# PostgreSQL/TimescaleDB
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Ensure models are imported so Base.metadata is aware of them before create_all
try:
    from src.models import asset_models  # noqa: F401
except Exception:
    # Safe to continue; endpoints also import models, but we prefer to load early
    pass

# DuckDB connection - REMOVED: No longer needed
# duckdb_conn: Optional[Any] = None

# Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


def get_db() -> Generator:
    """Get database session"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# def get_duckdb() -> Optional[Any]:
#     """Get DuckDB connection - REMOVED: No longer needed"""
#     # DuckDB removed - all calculations done locally
#     return None


def get_redis():
    """Get Redis client"""
    return redis_client


async def init_db():
    """Initialize database connections and create tables"""
    try:
        # Test PostgreSQL connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("PostgreSQL/TimescaleDB connection successful")
        
        # Create tables if needed
        Base.metadata.create_all(bind=engine)

        # Ensure new columns exist (idempotent)
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS has_access BOOLEAN DEFAULT FALSE NOT NULL"))
                conn.execute(text("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE IF NOT EXISTS users ADD COLUMN IF NOT EXISTS stripe_subscription_status VARCHAR(50)"))
                conn.execute(text("ALTER TABLE IF NOT EXISTS users ADD COLUMN IF NOT EXISTS stripe_current_period_end TIMESTAMP"))
        except Exception as e:
            print(f"Non-fatal: failed to apply user column migrations: {e}")
        
        # Initialize DuckDB (optional) - REMOVED: No longer needed
        # duck_conn = get_duckdb()
        # if duck_conn:
        #     # Create analytical tables in DuckDB
        #     duck_conn.execute("""
        #         CREATE TABLE IF NOT EXISTS temp_market_data (
        #             symbol VARCHAR,
        #             timestamp TIMESTAMP,
        #             open DECIMAL,
        #             high DECIMAL,
        #             low DECIMAL,
        #             close DECIMAL,
        #             volume DECIMAL
        #         )
        #     """)
        #     
        #     duck_conn.execute("""
        #         CREATE TABLE IF NOT EXISTS temp_indicators (
        #             symbol VARCHAR,
        #             timestamp TIMESTAMP,
        #             indicator_name VARCHAR,
        #             value DECIMAL
        #         )
        #     """)
        #     print("DuckDB initialized successfully")
        # else:
        print("DuckDB initialization skipped (no longer needed)")
        
        # Test Redis connection
        try:
            redis_client.ping()
            print("Redis connection successful")
        except Exception as e:
            print(f"Redis connection failed: {e}")
        
        print("Database initialization completed")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
