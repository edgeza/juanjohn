#!/usr/bin/env python3
"""
Simple TimescaleDB connection test script.

This script tests the TimescaleDB connection configuration to ensure
the Docker container can connect to the PostgreSQL service.
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_basic_connection():
    """Test basic TimescaleDB connection."""
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager
        
        print("Testing TimescaleDB connection...")
        print(f"Environment variables:")
        print(f"  POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER', 'not set')}")
        print(f"  POSTGRES_PORT: {os.getenv('POSTGRES_PORT', 'not set')}")
        print(f"  POSTGRES_USER: {os.getenv('POSTGRES_USER', 'not set')}")
        print(f"  POSTGRES_DB: {os.getenv('POSTGRES_DB', 'not set')}")
        print(f"  DOCKER_CONTAINER: {os.getenv('DOCKER_CONTAINER', 'not set')}")
        print()
        
        manager = TimescaleDBManager()
        print(f"Database URL: {manager.db_url}")
        
        # Test basic connection
        with manager.engine.connect() as conn:
            result = conn.execute("SELECT 1 as test").fetchone()
            print(f"✅ Basic connection successful: {result[0]}")
            
            # Test TimescaleDB extension
            result = conn.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'").fetchone()
            if result:
                print(f"✅ TimescaleDB extension found: {result[0]}")
            else:
                print("⚠️  TimescaleDB extension not found")
            
            # Test schema access
            result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'trading'").fetchone()
            print(f"✅ Trading schema accessible: {result[0]} tables found")
            
            # Test ohlc_data table
            try:
                result = conn.execute("SELECT COUNT(*) FROM trading.ohlc_data").fetchone()
                print(f"✅ OHLC data table accessible: {result[0]} records")
            except Exception as table_error:
                print(f"⚠️  OHLC data table issue: {table_error}")
            
        return True
        
    except Exception as e:
        print(f"❌ TimescaleDB connection failed: {e}")
        return False

def test_duckdb_postgres_extension():
    """Test DuckDB PostgreSQL extension."""
    try:
        import duckdb
        
        print("\nTesting DuckDB PostgreSQL extension...")
        
        conn = duckdb.connect(':memory:')
        
        # Try to install postgres extension
        try:
            conn.execute("INSTALL postgres")
            print("✅ DuckDB postgres extension installed")
        except Exception as install_error:
            print(f"❌ Failed to install postgres extension: {install_error}")
            return False
        
        # Try to load postgres extension
        try:
            conn.execute("LOAD postgres")
            print("✅ DuckDB postgres extension loaded")
        except Exception as load_error:
            print(f"❌ Failed to load postgres extension: {load_error}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DuckDB postgres extension test failed: {e}")
        return False

def test_environment_setup():
    """Test environment variable setup."""
    print("\nTesting environment setup...")
    
    required_vars = [
        'POSTGRES_SERVER',
        'POSTGRES_PORT', 
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure to set these in your .env file")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def main():
    """Main test function."""
    print("="*60)
    print("TIMESCALEDB CONNECTION TEST")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("DuckDB PostgreSQL Extension", test_duckdb_postgres_extension),
        ("TimescaleDB Connection", test_basic_connection),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("CONNECTION TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("\n✅ All connection tests passed!")
        print("TimescaleDB connection is properly configured.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed.")
        print("Please check the configuration and ensure:")
        print("  • PostgreSQL/TimescaleDB is running")
        print("  • Environment variables are set correctly")
        print("  • Network connectivity is available")
        return 1

if __name__ == "__main__":
    exit(main())
