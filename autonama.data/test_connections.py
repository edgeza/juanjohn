import sys
import os
from pathlib import Path
from sqlalchemy import text

# Add the parent directory to the path so we can import from utils
sys.path.append(str(Path(__file__).parent))

from utils.database import get_db, get_duckdb, get_redis


def test_postgres_connection():
    """Test PostgreSQL/TimescaleDB connection"""
    try:
        # Get a database session
        db = next(get_db())
        
        # Execute a simple query
        result = db.execute(text("SELECT 1")).scalar()
        print("✅ PostgreSQL connection successful")
        print(f"   Test query result: {result}")
        return True
    except Exception as e:
        print("❌ PostgreSQL connection failed")
        print(f"   Error: {str(e)}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def test_duckdb_connection():
    """Test DuckDB connection"""
    try:
        conn = get_duckdb()
        if conn is None:
            print("⚠️ DuckDB connection not available")
            return False
            
        # Execute a simple query
        result = conn.execute("SELECT 1").fetchone()[0]
        print("✅ DuckDB connection successful")
        print(f"   Test query result: {result}")
        return True
    except Exception as e:
        print("❌ DuckDB connection failed")
        print(f"   Error: {str(e)}")
        return False


def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_client = get_redis()
        # Test the connection
        redis_client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print("❌ Redis connection failed")
        print(f"   Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n=== Testing Database Connections ===\n")
    
    # Test PostgreSQL connection
    print("Testing PostgreSQL connection...")
    pg_success = test_postgres_connection()
    
    # Test DuckDB connection
    print("\nTesting DuckDB connection...")
    duckdb_success = test_duckdb_connection()
    
    # Test Redis connection
    print("\nTesting Redis connection...")
    redis_success = test_redis_connection()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"PostgreSQL: {'✅' if pg_success else '❌'}")
    print(f"DuckDB:    {'✅' if duckdb_success else '❌'}")
    print(f"Redis:      {'✅' if redis_success else '❌'}")
    
    # Exit with appropriate status code
    sys.exit(0 if all([pg_success, duckdb_success, redis_success]) else 1)
