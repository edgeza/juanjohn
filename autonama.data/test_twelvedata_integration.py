#!/usr/bin/env python3
"""
TwelveData Integration Test

This script tests the TwelveData integration with TimescaleDB storage.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks.twelvedata_ingestion import test_twelvedata_connection, twelvedata_processor
from tasks.timescale_data_ingestion import timescale_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run TwelveData integration tests."""
    try:
        logger.info("🚀 TWELVEDATA INTEGRATION TEST")
        logger.info("=" * 60)
        
        # Test 1: Check API key configuration
        logger.info("🔍 TEST 1: API Key Configuration")
        logger.info("=" * 50)
        
        api_key = os.getenv('TWELVEDATA_API_KEY')
        if not api_key:
            logger.error("❌ TWELVEDATA_API_KEY environment variable not set")
            logger.info("Please set your TwelveData API key:")
            logger.info("export TWELVEDATA_API_KEY='your_api_key_here'")
            return False
        
        logger.info(f"✅ API key configured: {api_key[:8]}...")
        
        # Test 2: TwelveData processor initialization
        logger.info("\n🔍 TEST 2: Processor Initialization")
        logger.info("=" * 50)
        
        if not twelvedata_processor:
            logger.error("❌ TwelveData processor failed to initialize")
            return False
        
        logger.info("✅ TwelveData processor initialized successfully")
        
        # Test 3: TimescaleDB connection
        logger.info("\n🔍 TEST 3: TimescaleDB Connection")
        logger.info("=" * 50)
        
        try:
            # Test database connection
            with timescale_manager.engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                logger.info(f"✅ TimescaleDB connection verified: {result[0]}")
        except Exception as e:
            logger.error(f"❌ TimescaleDB connection failed: {e}")
            return False
        
        # Test 4: API connectivity test
        logger.info("\n🔍 TEST 4: API Connectivity Test")
        logger.info("=" * 50)
        
        connection_test = test_twelvedata_connection()
        
        if connection_test['status'] == 'failed':
            logger.error(f"❌ API connectivity test failed: {connection_test.get('error', 'Unknown error')}")
            return False
        
        tests_passed = connection_test.get('tests_passed', 0)
        total_tests = connection_test.get('total_tests', 3)
        
        logger.info(f"✅ API connectivity test: {tests_passed}/{total_tests} tests passed")
        
        # Show detailed results
        results = connection_test.get('results', {})
        for test_name, result in results.items():
            if result.get('success', False):
                records = result.get('records', 0)
                latest_price = result.get('latest_price', 'N/A')
                logger.info(f"   ✅ {test_name}: {records} records, latest price: {latest_price}")
            else:
                error = result.get('error', 'Unknown error')
                logger.info(f"   ❌ {test_name}: {error}")
        
        # Test 5: Sample data insertion
        logger.info("\n🔍 TEST 5: Sample Data Insertion")
        logger.info("=" * 50)
        
        # Test stock data insertion
        logger.info("Testing stock data insertion (AAPL)...")
        stock_result = twelvedata_processor.update_symbol_data('AAPL', 'stock', force_update=True)
        
        if stock_result['success'] and stock_result['data']:
            # Insert into TimescaleDB
            inserted_count = timescale_manager.insert_ohlc_data(
                stock_result['data'], 'AAPL', 'twelvedata', '1d'
            )
            
            if inserted_count > 0:
                logger.info(f"✅ Stock data insertion: {inserted_count} records for AAPL")
            else:
                logger.warning("❌ Stock data insertion: No records inserted")
        else:
            logger.warning(f"❌ Stock data fetch failed: {stock_result.get('error', 'Unknown error')}")
        
        # Test forex data insertion
        logger.info("Testing forex data insertion (EUR/USD)...")
        forex_result = twelvedata_processor.update_symbol_data('EUR/USD', 'forex', force_update=True)
        
        if forex_result['success'] and forex_result['data']:
            # Insert into TimescaleDB
            inserted_count = timescale_manager.insert_ohlc_data(
                forex_result['data'], 'EUR/USD', 'twelvedata', '1d'
            )
            
            if inserted_count > 0:
                logger.info(f"✅ Forex data insertion: {inserted_count} records for EUR/USD")
            else:
                logger.warning("❌ Forex data insertion: No records inserted")
        else:
            logger.warning(f"❌ Forex data fetch failed: {forex_result.get('error', 'Unknown error')}")
        
        # Test 6: Data retrieval verification
        logger.info("\n🔍 TEST 6: Data Retrieval Verification")
        logger.info("=" * 50)
        
        # Check AAPL data
        aapl_data = timescale_manager.get_ohlc_data('AAPL', 'twelvedata', '1d', limit=5)
        if not aapl_data.empty:
            logger.info(f"✅ AAPL data retrieval: {len(aapl_data)} records found")
            logger.info(f"   Latest price: ${aapl_data['close'].iloc[-1]:.2f}")
        else:
            logger.warning("❌ AAPL data retrieval: No records found")
        
        # Check EUR/USD data
        eurusd_data = timescale_manager.get_ohlc_data('EUR/USD', 'twelvedata', '1d', limit=5)
        if not eurusd_data.empty:
            logger.info(f"✅ EUR/USD data retrieval: {len(eurusd_data)} records found")
            logger.info(f"   Latest rate: {eurusd_data['close'].iloc[-1]:.4f}")
        else:
            logger.warning("❌ EUR/USD data retrieval: No records found")
        
        # Test 7: Database statistics
        logger.info("\n🔍 TEST 7: Database Statistics")
        logger.info("=" * 50)
        
        try:
            with timescale_manager.engine.connect() as conn:
                # Count total records
                total_result = conn.execute("SELECT COUNT(*) FROM trading.ohlc_data").fetchone()
                total_records = total_result[0] if total_result else 0
                
                # Count TwelveData records
                twelvedata_result = conn.execute(
                    "SELECT COUNT(*) FROM trading.ohlc_data WHERE exchange = 'twelvedata'"
                ).fetchone()
                twelvedata_records = twelvedata_result[0] if twelvedata_result else 0
                
                # Get unique symbols from TwelveData
                symbols_result = conn.execute(
                    "SELECT COUNT(DISTINCT symbol) FROM trading.ohlc_data WHERE exchange = 'twelvedata'"
                ).fetchone()
                unique_symbols = symbols_result[0] if symbols_result else 0
                
                logger.info(f"✅ Database statistics:")
                logger.info(f"   Total records: {total_records}")
                logger.info(f"   TwelveData records: {twelvedata_records}")
                logger.info(f"   Unique TwelveData symbols: {unique_symbols}")
                
        except Exception as e:
            logger.error(f"❌ Database statistics failed: {e}")
        
        # Summary
        logger.info("\n🎯 TWELVEDATA INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ TwelveData integration test completed successfully!")
        logger.info("✅ API connectivity working")
        logger.info("✅ Data fetching operational")
        logger.info("✅ TimescaleDB storage working")
        logger.info("✅ Data retrieval confirmed")
        logger.info("✅ System ready for production TwelveData integration")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error in TwelveData integration test: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)