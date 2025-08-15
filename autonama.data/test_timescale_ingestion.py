#!/usr/bin/env python3
"""
Test script for TimescaleDB-first data ingestion system.

This script tests the new hybrid architecture where:
1. Data is stored primarily in TimescaleDB
2. DuckDB is used as an analytical engine that queries FROM TimescaleDB
3. Results are stored back to TimescaleDB
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_timescale_connection():
    """Test TimescaleDB connection."""
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager
        
        print("Testing TimescaleDB connection...")
        manager = TimescaleDBManager()
        
        # Test basic connection
        with manager.engine.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            print(f"✅ TimescaleDB connection successful: {result[0]}")
            
            # Test schema access
            result = conn.execute("SELECT COUNT(*) FROM trading.ohlc_data").fetchone()
            print(f"✅ Trading schema accessible: {result[0]} records in ohlc_data")
            
        return True
        
    except Exception as e:
        print(f"❌ TimescaleDB connection failed: {e}")
        return False

def test_duckdb_timescale_integration():
    """Test DuckDB integration with TimescaleDB."""
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager, DuckDBAnalyticalEngine
        
        print("\nTesting DuckDB-TimescaleDB integration...")
        
        timescale_manager = TimescaleDBManager()
        duckdb_engine = DuckDBAnalyticalEngine(timescale_manager)
        
        # Test loading data for analysis
        success = duckdb_engine.load_data_for_analysis('BTC/USDT', 'binance', '1h', 10)
        
        if success:
            print("✅ DuckDB successfully loaded data from TimescaleDB")
            
            # Test analytical capabilities
            try:
                result = duckdb_engine.conn.execute("SELECT COUNT(*) FROM ohlc_data").fetchone()
                print(f"✅ DuckDB analytical query successful: {result[0]} records loaded")
                return True
            except Exception as query_error:
                print(f"⚠️  DuckDB query failed: {query_error}")
                return False
        else:
            print("❌ DuckDB failed to load data from TimescaleDB")
            return False
            
    except Exception as e:
        print(f"❌ DuckDB-TimescaleDB integration failed: {e}")
        return False

def test_data_insertion():
    """Test data insertion into TimescaleDB."""
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager
        from datetime import datetime, timedelta
        
        print("\nTesting data insertion...")
        
        manager = TimescaleDBManager()
        
        # Create test data
        test_data = []
        base_time = datetime.utcnow() - timedelta(hours=2)
        
        for i in range(5):
            test_data.append({
                'timestamp': base_time + timedelta(minutes=i),
                'open': 50000 + i,
                'high': 50100 + i,
                'low': 49900 + i,
                'close': 50050 + i,
                'volume': 1000 + i
            })
        
        # Insert test data
        inserted_count = manager.insert_ohlc_data(test_data, 'TEST/USDT', 'test_exchange', '1m')
        
        if inserted_count > 0:
            print(f"✅ Successfully inserted {inserted_count} test records")
            
            # Verify data retrieval
            df = manager.get_ohlc_data('TEST/USDT', 'test_exchange', '1m', 10)
            if not df.empty:
                print(f"✅ Successfully retrieved {len(df)} test records")
                return True
            else:
                print("❌ Failed to retrieve inserted test data")
                return False
        else:
            print("❌ Failed to insert test data")
            return False
            
    except Exception as e:
        print(f"❌ Data insertion test failed: {e}")
        return False

def test_indicator_calculation():
    """Test technical indicator calculation."""
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager, DuckDBAnalyticalEngine
        
        print("\nTesting indicator calculation...")
        
        timescale_manager = TimescaleDBManager()
        duckdb_engine = DuckDBAnalyticalEngine(timescale_manager)
        
        # Calculate indicators for BTC/USDT
        indicators = duckdb_engine.calculate_technical_indicators('BTC/USDT')
        
        if indicators:
            print(f"✅ Successfully calculated {len(indicators)} indicators:")
            for name, value in indicators.items():
                print(f"   {name}: {value}")
            
            # Test storing indicators back to TimescaleDB
            success = duckdb_engine.store_indicators_to_timescale('BTC/USDT', indicators, '1h')
            
            if success:
                print("✅ Successfully stored indicators to TimescaleDB")
                return True
            else:
                print("❌ Failed to store indicators to TimescaleDB")
                return False
        else:
            print("❌ No indicators calculated")
            return False
            
    except Exception as e:
        print(f"❌ Indicator calculation test failed: {e}")
        return False

def test_crypto_data_update():
    """Test the crypto data update function."""
    try:
        from tasks.timescale_data_ingestion import update_crypto_data_timescale
        
        print("\nTesting crypto data update...")
        
        # Run crypto data update
        result = update_crypto_data_timescale(force_update=False)
        
        success = result.get('success', 0)
        failed = result.get('failed', 0)
        message = result.get('message', 'No message')
        
        print(f"Crypto update results:")
        print(f"   Success: {success}")
        print(f"   Failed: {failed}")
        print(f"   Message: {message}")
        
        if success > 0:
            print("✅ Crypto data update successful")
            return True
        else:
            print("⚠️  Crypto data update completed but no successful updates")
            return False
            
    except Exception as e:
        print(f"❌ Crypto data update test failed: {e}")
        return False

def test_hybrid_task():
    """Test the hybrid data ingestion task."""
    try:
        from tasks.data_ingestion import update_market_data
        
        print("\nTesting hybrid data ingestion task...")
        
        # Test the task directly (not via Celery)
        result = update_market_data(categories=['crypto'], force_update=False)
        
        approach = result.get('approach', 'unknown')
        status = result.get('status', 'unknown')
        summary = result.get('summary', {})
        
        print(f"Hybrid task results:")
        print(f"   Approach: {approach}")
        print(f"   Status: {status}")
        print(f"   Success: {summary.get('total_success', 0)}")
        print(f"   Failed: {summary.get('total_failed', 0)}")
        print(f"   Skipped: {summary.get('total_skipped', 0)}")
        
        if status == 'completed':
            print("✅ Hybrid data ingestion task successful")
            return True
        else:
            print("❌ Hybrid data ingestion task failed")
            return False
            
    except Exception as e:
        print(f"❌ Hybrid task test failed: {e}")
        return False

def main():
    """Main test function."""
    print("="*60)
    print("TIMESCALEDB-FIRST DATA INGESTION TEST")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    tests = [
        ("TimescaleDB Connection", test_timescale_connection),
        ("DuckDB-TimescaleDB Integration", test_duckdb_timescale_integration),
        ("Data Insertion", test_data_insertion),
        ("Indicator Calculation", test_indicator_calculation),
        ("Crypto Data Update", test_crypto_data_update),
        ("Hybrid Task", test_hybrid_task),
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
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("\n✅ All TimescaleDB-first tests passed!")
        print("The hybrid architecture is working correctly:")
        print("  • Data is stored primarily in TimescaleDB")
        print("  • DuckDB queries data FROM TimescaleDB for analytics")
        print("  • Results are stored back to TimescaleDB")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        print("This may be expected if TimescaleDB is not running or not configured.")
        print("The system will fall back to legacy approaches.")
        return 1

if __name__ == "__main__":
    exit(main())
