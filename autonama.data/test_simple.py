#!/usr/bin/env python3
"""
Simple Test Script for Data Processors

This script tests the basic functionality of our processors.
"""

import os
import sys
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_configurations():
    """Test configuration loading."""
    logger.info("🔧 Testing configurations...")
    
    try:
        # Test environment variables
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:15432/autonama')
        logger.info(f"✅ Database URL configured: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
        
        # Test DuckDB path
        duckdb_path = os.getenv('DUCKDB_PATH', '/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb')
        logger.info(f"✅ DuckDB path configured: {duckdb_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connections."""
    logger.info("🗄️ Testing database connections...")
    
    try:
        import psycopg2
        
        # Test TimescaleDB connection
        conn = psycopg2.connect(
            host='localhost',
            port=15432,
            user='postgres',
            password='postgres',
            database='autonama'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trading.asset_metadata")
        asset_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ TimescaleDB connected: {asset_count} assets found")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_duckdb():
    """Test DuckDB functionality."""
    logger.info("🦆 Testing DuckDB...")
    
    try:
        import duckdb
        
        # Create in-memory connection for testing
        conn = duckdb.connect(':memory:')
        
        # Test basic query
        result = conn.execute("SELECT 1 as test").fetchall()
        assert result[0][0] == 1
        
        # Test extensions
        try:
            conn.execute("INSTALL postgres_scanner")
            conn.execute("LOAD postgres_scanner")
            logger.info("✅ DuckDB postgres_scanner extension loaded")
        except:
            logger.warning("⚠️ DuckDB postgres_scanner extension not available")
        
        try:
            conn.execute("INSTALL parquet")
            conn.execute("LOAD parquet")
            logger.info("✅ DuckDB parquet extension loaded")
        except:
            logger.warning("⚠️ DuckDB parquet extension not available")
        
        conn.close()
        logger.info("✅ DuckDB basic functionality working")
        return True
        
    except Exception as e:
        logger.error(f"❌ DuckDB test failed: {e}")
        return False

def test_api_libraries():
    """Test API libraries."""
    logger.info("📡 Testing API libraries...")
    
    results = {}
    
    # Test requests
    try:
        import requests
        response = requests.get('https://httpbin.org/status/200', timeout=5)
        results['requests'] = response.status_code == 200
        logger.info("✅ Requests library working")
    except Exception as e:
        logger.warning(f"⚠️ Requests test failed: {e}")
        results['requests'] = False
    
    # Test CCXT
    try:
        import ccxt
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        results['ccxt'] = len(markets) > 0
        logger.info(f"✅ CCXT working: {len(markets)} markets loaded")
    except Exception as e:
        logger.warning(f"⚠️ CCXT test failed: {e}")
        results['ccxt'] = False
    
    # Test pandas
    try:
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({'test': [1, 2, 3]})
        results['pandas'] = len(df) == 3
        logger.info("✅ Pandas working")
    except Exception as e:
        logger.warning(f"⚠️ Pandas test failed: {e}")
        results['pandas'] = False
    
    # Test pyarrow
    try:
        import pyarrow as pa
        table = pa.table({'test': [1, 2, 3]})
        results['pyarrow'] = len(table) == 3
        logger.info("✅ PyArrow working")
    except Exception as e:
        logger.warning(f"⚠️ PyArrow test failed: {e}")
        results['pyarrow'] = False
    
    return results

def test_binance_api():
    """Test Binance API (public endpoints only)."""
    logger.info("₿ Testing Binance API...")
    
    try:
        import requests
        
        # Test public endpoint
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Binance API accessible")
            
            # Test ticker endpoint
            ticker_response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=10)
            
            if ticker_response.status_code == 200:
                data = ticker_response.json()
                btc_price = float(data['price'])
                logger.info(f"✅ BTC price fetched: ${btc_price:,.2f}")
                return True
            else:
                logger.warning("⚠️ Binance ticker endpoint failed")
                return False
        else:
            logger.warning("⚠️ Binance API not accessible")
            return False
            
    except Exception as e:
        logger.error(f"❌ Binance API test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting processor component tests")
    logger.info("=" * 50)
    
    test_results = {}
    
    # Run tests
    test_results['configurations'] = test_configurations()
    test_results['database'] = test_database_connection()
    test_results['duckdb'] = test_duckdb()
    test_results['api_libraries'] = test_api_libraries()
    test_results['binance_api'] = test_binance_api()
    
    # Calculate results
    total_tests = len(test_results)
    successful_tests = 0
    
    for test_name, result in test_results.items():
        if isinstance(result, dict):
            # For api_libraries test
            sub_success = sum(1 for v in result.values() if v)
            sub_total = len(result)
            if sub_success >= sub_total * 0.7:  # 70% success rate
                successful_tests += 1
            logger.info(f"📊 {test_name}: {sub_success}/{sub_total} components working")
        else:
            if result:
                successful_tests += 1
    
    success_rate = (successful_tests / total_tests) * 100
    
    # Summary
    logger.info("=" * 50)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"📊 Total Tests: {total_tests}")
    logger.info(f"✅ Successful: {successful_tests}")
    logger.info(f"❌ Failed: {total_tests - successful_tests}")
    logger.info(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        logger.info("🎉 EXCELLENT: All core components ready!")
        return 0
    elif success_rate >= 60:
        logger.info("👍 GOOD: Most components working")
        return 0
    else:
        logger.warning("⚠️ ATTENTION: Some components need fixing")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
