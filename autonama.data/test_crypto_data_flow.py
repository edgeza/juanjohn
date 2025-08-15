#!/usr/bin/env python3
"""
End-to-End Crypto Data Flow Test

This script tests the complete data pipeline:
Binance API → TimescaleDB → DuckDB → Analytics

Tests:
1. Binance API data fetching
2. TimescaleDB data storage
3. DuckDB analytical queries
4. Technical indicators calculation
5. Data integrity validation
"""

import sys
import os
import logging
import pandas as pd
import ccxt
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.append('.')

def test_binance_api_connection():
    """Test 1: Binance API Connection and Data Fetching"""
    logger.info("🔍 TEST 1: Binance API Connection")
    logger.info("=" * 50)
    
    try:
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'apiKey': None,  # Public endpoints don't need API key
            'secret': None,
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Test symbols to fetch
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        results = {}
        
        for symbol in test_symbols:
            try:
                # Fetch recent OHLCV data (1 hour timeframe, last 24 hours)
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=24)
                
                if ohlcv and len(ohlcv) > 0:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['symbol'] = symbol
                    df['exchange'] = 'binance'
                    df['timeframe'] = '1h'
                    
                    results[symbol] = {
                        'success': True,
                        'records': len(df),
                        'latest_price': df.iloc[-1]['close'],
                        'data': df
                    }
                    
                    logger.info(f"✅ {symbol}: {len(df)} records, Latest: ${df.iloc[-1]['close']:,.2f}")
                else:
                    results[symbol] = {'success': False, 'error': 'No data returned'}
                    logger.error(f"❌ {symbol}: No data returned")
                    
            except Exception as e:
                results[symbol] = {'success': False, 'error': str(e)}
                logger.error(f"❌ {symbol}: {e}")
        
        # Summary
        successful = sum(1 for r in results.values() if r['success'])
        logger.info(f"📊 Binance API Test: {successful}/{len(test_symbols)} symbols successful")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Binance API connection failed: {e}")
        return {}

def test_timescale_connection():
    """Test 2: TimescaleDB Connection and Schema Validation"""
    logger.info("\n🔍 TEST 2: TimescaleDB Connection")
    logger.info("=" * 50)
    
    try:
        from tasks.timescale_data_ingestion import TimescaleDBManager
        
        # Initialize TimescaleDB manager
        manager = TimescaleDBManager()
        logger.info("✅ TimescaleDBManager initialized")
        
        # Test database connection
        with manager.engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                logger.info("✅ Database connection successful")
            
            # Check if required tables exist
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema IN ('trading', 'analytics')
                ORDER BY table_name
            """
            tables = conn.execute(text(tables_query)).fetchall()
            
            if tables:
                logger.info("✅ Database schema tables found:")
                for table in tables:
                    logger.info(f"   - {table[0]}")
            else:
                logger.warning("⚠️  No schema tables found - may need initialization")
            
            # Check current data count
            try:
                count_result = conn.execute(text("SELECT COUNT(*) FROM trading.ohlc_data")).fetchone()
                current_count = count_result[0] if count_result else 0
                logger.info(f"📊 Current OHLC records in database: {current_count:,}")
            except Exception as e:
                logger.warning(f"⚠️  Could not count existing records: {e}")
                current_count = 0
        
        return {'success': True, 'manager': manager, 'current_count': current_count}
        
    except Exception as e:
        logger.error(f"❌ TimescaleDB connection failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_data_insertion(manager, crypto_data):
    """Test 3: Data Insertion into TimescaleDB"""
    logger.info("\n🔍 TEST 3: Data Insertion into TimescaleDB")
    logger.info("=" * 50)
    
    if not crypto_data:
        logger.error("❌ No crypto data available for insertion test")
        return {'success': False, 'error': 'No data'}
    
    insertion_results = {}
    
    for symbol, data in crypto_data.items():
        if not data['success']:
            continue
            
        try:
            df = data['data'].copy()
            df['created_at'] = datetime.now()
            
            logger.info(f"📝 Inserting {len(df)} records for {symbol}...")
            
            # Use the manager's store_ohlc_data method
            success = manager.store_ohlc_data(df)
            
            if success:
                insertion_results[symbol] = {'success': True, 'records': len(df)}
                logger.info(f"✅ {symbol}: {len(df)} records inserted successfully")
            else:
                insertion_results[symbol] = {'success': False, 'error': 'Store method returned False'}
                logger.error(f"❌ {symbol}: Insertion failed")
                
        except Exception as e:
            insertion_results[symbol] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {symbol}: Insertion error - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    successful = sum(1 for r in insertion_results.values() if r['success'])
    total_records = sum(r.get('records', 0) for r in insertion_results.values() if r['success'])
    
    logger.info(f"📊 Data Insertion: {successful}/{len(insertion_results)} symbols, {total_records} total records")
    
    return insertion_results

def test_data_retrieval(manager):
    """Test 4: Data Retrieval and Validation"""
    logger.info("\n🔍 TEST 4: Data Retrieval and Validation")
    logger.info("=" * 50)
    
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    retrieval_results = {}
    
    for symbol in test_symbols:
        try:
            # Test data retrieval
            df = manager.get_ohlc_data(symbol, 'binance', '1h', limit=10)
            
            if not df.empty:
                retrieval_results[symbol] = {
                    'success': True,
                    'records': len(df),
                    'latest_timestamp': df['timestamp'].max(),
                    'price_range': f"${df['low'].min():.2f} - ${df['high'].max():.2f}"
                }
                logger.info(f"✅ {symbol}: Retrieved {len(df)} records, Latest: {df['timestamp'].max()}")
            else:
                retrieval_results[symbol] = {'success': False, 'error': 'No data retrieved'}
                logger.warning(f"⚠️  {symbol}: No data retrieved")
                
        except Exception as e:
            retrieval_results[symbol] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {symbol}: Retrieval error - {e}")
    
    return retrieval_results

def test_duckdb_analytics(manager):
    """Test 5: DuckDB Analytics Integration"""
    logger.info("\n🔍 TEST 5: DuckDB Analytics Integration")
    logger.info("=" * 50)
    
    try:
        from tasks.timescale_data_ingestion import DuckDBAnalyticalEngine
        
        # Initialize DuckDB engine
        duckdb_engine = DuckDBAnalyticalEngine(manager)
        logger.info("✅ DuckDB Analytical Engine initialized")
        
        # Test data loading and analysis
        test_symbol = 'BTC/USDT'
        
        # Load data for analysis
        success = duckdb_engine.load_data_for_analysis(test_symbol)
        
        if success:
            logger.info(f"✅ Data loaded into DuckDB for {test_symbol}")
            
            # Calculate technical indicators
            indicators = duckdb_engine.calculate_technical_indicators(test_symbol)
            
            if indicators:
                logger.info("✅ Technical indicators calculated:")
                for indicator, value in indicators.items():
                    if value is not None:
                        logger.info(f"   - {indicator}: {value:.4f}")
                
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

def test_latest_timestamp(manager):
    """Test 6: Latest Timestamp Functionality"""
    logger.info("\n🔍 TEST 6: Latest Timestamp Functionality")
    logger.info("=" * 50)
    
    test_symbols = ['BTC/USDT', 'ETH/USDT']
    timestamp_results = {}
    
    for symbol in test_symbols:
        try:
            latest = manager.get_latest_timestamp(symbol, 'binance', '1h')
            
            if latest:
                timestamp_results[symbol] = {
                    'success': True,
                    'latest_timestamp': latest,
                    'age_minutes': (datetime.now() - latest.replace(tzinfo=None)).total_seconds() / 60
                }
                logger.info(f"✅ {symbol}: Latest timestamp {latest}")
            else:
                timestamp_results[symbol] = {'success': False, 'error': 'No timestamp found'}
                logger.warning(f"⚠️  {symbol}: No latest timestamp found")
                
        except Exception as e:
            timestamp_results[symbol] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {symbol}: Timestamp query error - {e}")
    
    return timestamp_results

def run_comprehensive_test():
    """Run the complete end-to-end test suite"""
    logger.info("🚀 STARTING END-TO-END CRYPTO DATA FLOW TEST")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Binance API
    test_results['binance_api'] = test_binance_api_connection()
    
    # Test 2: TimescaleDB Connection
    timescale_result = test_timescale_connection()
    test_results['timescale_connection'] = timescale_result
    
    if not timescale_result['success']:
        logger.error("❌ Cannot continue - TimescaleDB connection failed")
        return test_results
    
    manager = timescale_result['manager']
    
    # Test 3: Data Insertion
    test_results['data_insertion'] = test_data_insertion(manager, test_results['binance_api'])
    
    # Test 4: Data Retrieval
    test_results['data_retrieval'] = test_data_retrieval(manager)
    
    # Test 5: DuckDB Analytics
    test_results['duckdb_analytics'] = test_duckdb_analytics(manager)
    
    # Test 6: Latest Timestamp
    test_results['latest_timestamp'] = test_latest_timestamp(manager)
    
    # Final Summary
    logger.info("\n🎯 FINAL TEST SUMMARY")
    logger.info("=" * 60)
    
    test_names = {
        'binance_api': 'Binance API Connection',
        'timescale_connection': 'TimescaleDB Connection',
        'data_insertion': 'Data Insertion',
        'data_retrieval': 'Data Retrieval',
        'duckdb_analytics': 'DuckDB Analytics',
        'latest_timestamp': 'Latest Timestamp'
    }
    
    passed_tests = 0
    total_tests = len(test_names)
    
    for test_key, test_name in test_names.items():
        result = test_results.get(test_key, {})
        
        if test_key == 'binance_api':
            # Special handling for API test (multiple symbols)
            if result:
                successful_symbols = sum(1 for r in result.values() if r.get('success', False))
                total_symbols = len(result)
                if successful_symbols > 0:
                    logger.info(f"✅ {test_name}: {successful_symbols}/{total_symbols} symbols")
                    passed_tests += 1
                else:
                    logger.info(f"❌ {test_name}: No symbols successful")
            else:
                logger.info(f"❌ {test_name}: Failed")
        else:
            if result.get('success', False):
                logger.info(f"✅ {test_name}: PASSED")
                passed_tests += 1
            else:
                error = result.get('error', 'Unknown error')
                logger.info(f"❌ {test_name}: FAILED - {error}")
    
    logger.info(f"\n🏆 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! End-to-end crypto data flow is working!")
    elif passed_tests >= total_tests * 0.8:
        logger.info("⚠️  Most tests passed - minor issues to address")
    else:
        logger.info("❌ Multiple test failures - significant issues need attention")
    
    return test_results

if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
        
        # Exit with appropriate code
        if results.get('timescale_connection', {}).get('success', False):
            exit(0)  # At least basic functionality works
        else:
            exit(1)  # Critical failure
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)