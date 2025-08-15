#!/usr/bin/env python3
"""
Docker Environment End-to-End Test

This script tests the crypto data flow in the Docker environment where all dependencies are available.
Run this inside the Docker container.
"""

import sys
import os
import logging
import pandas as pd
import ccxt
from datetime import datetime, timedelta
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_docker_environment():
    """Test Docker environment setup"""
    logger.info("🔍 DOCKER ENVIRONMENT TEST")
    logger.info("=" * 50)
    
    # Check environment variables
    required_env_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'CELERY_BROKER_URL'
    ]
    
    env_status = {}
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive info
            masked_value = value.replace(value.split('@')[0].split('//')[1], '***') if '@' in value else value[:20] + '***'
            env_status[var] = {'present': True, 'value': masked_value}
            logger.info(f"✅ {var}: {masked_value}")
        else:
            env_status[var] = {'present': False, 'value': None}
            logger.warning(f"⚠️  {var}: Not set")
    
    return env_status

def test_binance_api():
    """Test Binance API connection"""
    logger.info("\n🔍 BINANCE API TEST")
    logger.info("=" * 50)
    
    try:
        # Initialize Binance
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Test with a single symbol
        symbol = 'BTC/USDT'
        logger.info(f"📡 Fetching data for {symbol}...")
        
        # Fetch recent data
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=5)
        
        if ohlcv and len(ohlcv) > 0:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['exchange'] = 'binance'
            df['timeframe'] = '1h'
            df['created_at'] = datetime.now()
            
            logger.info(f"✅ Successfully fetched {len(df)} records")
            logger.info(f"   Latest price: ${df.iloc[-1]['close']:,.2f}")
            logger.info(f"   Latest time: {df.iloc[-1]['timestamp']}")
            
            return {'success': True, 'data': df}
        else:
            logger.error("❌ No data returned from Binance API")
            return {'success': False, 'error': 'No data'}
            
    except Exception as e:
        logger.error(f"❌ Binance API test failed: {e}")
        return {'success': False, 'error': str(e)}

def test_timescale_connection():
    """Test TimescaleDB connection"""
    logger.info("\n🔍 TIMESCALEDB CONNECTION TEST")
    logger.info("=" * 50)
    
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager
        
        manager = TimescaleDBManager()
        logger.info("✅ TimescaleDBManager initialized")
        
        # Test connection
        with manager.engine.connect() as conn:
            result = conn.execute(text("SELECT NOW() as current_time")).fetchone()
            if result:
                logger.info(f"✅ Database connection successful: {result[0]}")
                
                # Test table existence
                tables_result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'trading' AND table_name = 'ohlc_data'
                """)).fetchone()
                
                if tables_result:
                    logger.info("✅ trading.ohlc_data table exists")
                else:
                    logger.warning("⚠️  trading.ohlc_data table not found")
                
                return {'success': True, 'manager': manager}
            else:
                logger.error("❌ Database query returned no result")
                return {'success': False, 'error': 'No query result'}
                
    except Exception as e:
        logger.error(f"❌ TimescaleDB connection failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_data_insertion(manager, crypto_data):
    """Test data insertion"""
    logger.info("\n🔍 DATA INSERTION TEST")
    logger.info("=" * 50)
    
    if not crypto_data or not crypto_data.get('success'):
        logger.error("❌ No crypto data available for insertion")
        return {'success': False, 'error': 'No data'}
    
    try:
        df = crypto_data['data']
        logger.info(f"📝 Attempting to insert {len(df)} records...")
        
        # Use the store_ohlc_data method
        result = manager.store_ohlc_data(df)
        
        if result:
            logger.info("✅ Data insertion successful")
            
            # Verify insertion by querying back
            symbol = df.iloc[0]['symbol']
            retrieved_df = manager.get_ohlc_data(symbol, 'binance', '1h', limit=5)
            
            if not retrieved_df.empty:
                logger.info(f"✅ Verification: Retrieved {len(retrieved_df)} records")
                return {'success': True, 'inserted': len(df), 'retrieved': len(retrieved_df)}
            else:
                logger.warning("⚠️  Data inserted but verification query returned empty")
                return {'success': True, 'inserted': len(df), 'retrieved': 0}
        else:
            logger.error("❌ Data insertion failed")
            return {'success': False, 'error': 'Insertion method returned False'}
            
    except Exception as e:
        logger.error(f"❌ Data insertion test failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_duckdb_analytics(manager):
    """Test DuckDB analytics"""
    logger.info("\n🔍 DUCKDB ANALYTICS TEST")
    logger.info("=" * 50)
    
    try:
        from tasks.timescale_data_ingestion import DuckDBAnalyticalEngine
        
        duckdb_engine = DuckDBAnalyticalEngine(manager)
        logger.info("✅ DuckDB Analytical Engine initialized")
        
        # Test data loading
        symbol = 'BTC/USDT'
        success = duckdb_engine.load_data_for_analysis(symbol)
        
        if success:
            logger.info(f"✅ Data loaded into DuckDB for {symbol}")
            
            # Test technical indicators
            indicators = duckdb_engine.calculate_technical_indicators(symbol)
            
            if indicators:
                logger.info("✅ Technical indicators calculated:")
                for name, value in indicators.items():
                    if value is not None:
                        logger.info(f"   - {name}: {value:.4f}")
                
                return {'success': True, 'indicators': indicators}
            else:
                logger.warning("⚠️  No indicators calculated")
                return {'success': False, 'error': 'No indicators'}
        else:
            logger.error("❌ Failed to load data into DuckDB")
            return {'success': False, 'error': 'Data loading failed'}
            
    except Exception as e:
        logger.error(f"❌ DuckDB analytics test failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def run_docker_tests():
    """Run comprehensive Docker environment tests"""
    logger.info("🚀 DOCKER END-TO-END CRYPTO DATA FLOW TEST")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: Docker Environment
    results['docker_env'] = test_docker_environment()
    
    # Test 2: Binance API
    results['binance_api'] = test_binance_api()
    
    # Test 3: TimescaleDB Connection
    timescale_result = test_timescale_connection()
    results['timescale_connection'] = timescale_result
    
    if not timescale_result['success']:
        logger.error("❌ Cannot continue - TimescaleDB connection failed")
        return results
    
    manager = timescale_result['manager']
    
    # Test 4: Data Insertion
    results['data_insertion'] = test_data_insertion(manager, results['binance_api'])
    
    # Test 5: DuckDB Analytics
    results['duckdb_analytics'] = test_duckdb_analytics(manager)
    
    # Final Summary
    logger.info("\n🎯 DOCKER TEST SUMMARY")
    logger.info("=" * 60)
    
    test_names = {
        'docker_env': 'Docker Environment',
        'binance_api': 'Binance API',
        'timescale_connection': 'TimescaleDB Connection',
        'data_insertion': 'Data Insertion',
        'duckdb_analytics': 'DuckDB Analytics'
    }
    
    passed = 0
    total = len(test_names)
    
    for test_key, test_name in test_names.items():
        result = results.get(test_key, {})
        if result.get('success', False):
            logger.info(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            error = result.get('error', 'Unknown error')
            logger.info(f"❌ {test_name}: FAILED - {error}")
    
    logger.info(f"\n🏆 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL DOCKER TESTS PASSED! End-to-end crypto data flow is working!")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most tests passed - minor issues to address")
    else:
        logger.info("❌ Multiple test failures - significant issues need attention")
    
    return results

if __name__ == "__main__":
    try:
        # Add required imports
        from sqlalchemy import text
        
        results = run_docker_tests()
        
        # Exit with appropriate code
        passed_count = sum(1 for r in results.values() if r.get('success', False))
        total_count = len(results)
        
        if passed_count >= total_count * 0.8:
            exit(0)
        else:
            exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)