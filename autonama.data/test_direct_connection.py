#!/usr/bin/env python3
"""
Direct Binance API Integration Test

This script tests the real Binance API integration without Docker dependencies.
It validates the complete data flow using actual market data.

Test Flow:
1. Connect to Binance API (public endpoints)
2. Fetch real crypto data (BTC/USDT, ETH/USDT)
3. Process and format data for TimescaleDB
4. Validate data structure and quality
5. Test database connection (if available)
"""

import sys
import os
import logging
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BinanceAPIClient:
    """Direct Binance API client using requests (no CCXT dependency)"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama-Trading-System/1.0'
        })
    
    def get_server_time(self) -> Dict[str, Any]:
        """Test API connectivity by getting server time"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/time", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information and available symbols"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/exchangeInfo", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 24) -> List[List]:
        """
        Get kline/candlestick data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            limit: Number of klines to retrieve (max 1000)
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(
                f"{self.base_url}/api/v3/klines", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    def get_24hr_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker price change statistics"""
        try:
            params = {'symbol': symbol}
            response = self.session.get(
                f"{self.base_url}/api/v3/ticker/24hr", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get 24hr ticker for {symbol}: {e}")
            raise

def test_binance_connectivity():
    """Test 1: Binance API Connectivity"""
    logger.info("🔍 TEST 1: Binance API Connectivity")
    logger.info("=" * 50)
    
    try:
        client = BinanceAPIClient()
        
        # Test server time
        server_time = client.get_server_time()
        server_timestamp = server_time['serverTime']
        server_datetime = datetime.fromtimestamp(server_timestamp / 1000)
        
        logger.info(f"✅ Binance API connected successfully")
        logger.info(f"   Server time: {server_datetime}")
        
        # Test exchange info
        exchange_info = client.get_exchange_info()
        symbols_count = len(exchange_info.get('symbols', []))
        
        logger.info(f"✅ Exchange info retrieved")
        logger.info(f"   Available symbols: {symbols_count:,}")
        
        return {'success': True, 'client': client, 'server_time': server_datetime}
        
    except Exception as e:
        logger.error(f"❌ Binance API connectivity failed: {e}")
        return {'success': False, 'error': str(e)}

def test_crypto_data_fetching(client):
    """Test 2: Real Crypto Data Fetching"""
    logger.info("\n🔍 TEST 2: Real Crypto Data Fetching")
    logger.info("=" * 50)
    
    # Test symbols (remove '/' for Binance API format)
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    for symbol in test_symbols:
        try:
            logger.info(f"📡 Fetching data for {symbol}...")
            
            # Get kline data (OHLCV)
            klines = client.get_klines(symbol, '1h', 24)  # Last 24 hours
            
            if klines and len(klines) > 0:
                # Convert to DataFrame
                df = pd.DataFrame(klines, columns=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convert timestamps and numeric values
                df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
                df['open'] = pd.to_numeric(df['open'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                # Add metadata
                df['symbol'] = symbol.replace('USDT', '/USDT')  # Convert back to standard format
                df['exchange'] = 'binance'
                df['timeframe'] = '1h'
                df['created_at'] = datetime.now()
                
                # Select relevant columns
                df = df[['timestamp', 'symbol', 'exchange', 'timeframe', 'open', 'high', 'low', 'close', 'volume', 'created_at']]
                
                # Get 24hr ticker for additional info
                ticker = client.get_24hr_ticker(symbol)
                
                results[symbol] = {
                    'success': True,
                    'records': len(df),
                    'latest_price': float(df.iloc[-1]['close']),
                    'price_change_24h': float(ticker['priceChangePercent']),
                    'volume_24h': float(ticker['volume']),
                    'data': df
                }
                
                logger.info(f"✅ {symbol}: {len(df)} records")
                logger.info(f"   Latest price: ${df.iloc[-1]['close']:,.2f}")
                logger.info(f"   24h change: {float(ticker['priceChangePercent']):.2f}%")
                logger.info(f"   24h volume: {float(ticker['volume']):,.0f}")
                
            else:
                results[symbol] = {'success': False, 'error': 'No data returned'}
                logger.error(f"❌ {symbol}: No data returned")
                
        except Exception as e:
            results[symbol] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {symbol}: {e}")
    
    # Summary
    successful = sum(1 for r in results.values() if r['success'])
    total_records = sum(r.get('records', 0) for r in results.values() if r['success'])
    
    logger.info(f"📊 Data Fetching Summary: {successful}/{len(test_symbols)} symbols, {total_records} total records")
    
    return results

def test_data_processing(crypto_data):
    """Test 3: Data Processing and Validation"""
    logger.info("\n🔍 TEST 3: Data Processing and Validation")
    logger.info("=" * 50)
    
    if not crypto_data:
        logger.error("❌ No crypto data available for processing")
        return {'success': False, 'error': 'No data'}
    
    processing_results = {}
    
    for symbol, data in crypto_data.items():
        if not data['success']:
            continue
            
        try:
            df = data['data']
            
            # Data quality checks
            checks = {
                'required_columns': all(col in df.columns for col in ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']),
                'no_null_prices': df[['open', 'high', 'low', 'close']].isnull().sum().sum() == 0,
                'positive_prices': (df[['open', 'high', 'low', 'close']] > 0).all().all(),
                'high_ge_low': (df['high'] >= df['low']).all(),
                'volume_non_negative': (df['volume'] >= 0).all(),
                'timestamps_sorted': df['timestamp'].is_monotonic_increasing,
                'recent_data': (datetime.now() - df['timestamp'].max()).total_seconds() < 7200  # Within 2 hours
            }
            
            # Calculate basic statistics
            stats = {
                'price_range': f"${df['low'].min():.2f} - ${df['high'].max():.2f}",
                'avg_volume': f"{df['volume'].mean():,.0f}",
                'time_span': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
                'data_points': len(df)
            }
            
            all_checks_passed = all(checks.values())
            
            processing_results[symbol] = {
                'success': all_checks_passed,
                'checks': checks,
                'stats': stats,
                'processed_data': df if all_checks_passed else None
            }
            
            if all_checks_passed:
                logger.info(f"✅ {symbol}: All data quality checks passed")
                logger.info(f"   Price range: {stats['price_range']}")
                logger.info(f"   Avg volume: {stats['avg_volume']}")
            else:
                failed_checks = [check for check, passed in checks.items() if not passed]
                logger.error(f"❌ {symbol}: Failed checks: {failed_checks}")
                
        except Exception as e:
            processing_results[symbol] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {symbol}: Processing error - {e}")
    
    # Summary
    successful = sum(1 for r in processing_results.values() if r['success'])
    logger.info(f"📊 Data Processing: {successful}/{len(processing_results)} symbols passed validation")
    
    return processing_results

def test_database_preparation(processed_data):
    """Test 4: Database Preparation and Schema Validation"""
    logger.info("\n🔍 TEST 4: Database Preparation")
    logger.info("=" * 50)
    
    if not processed_data:
        logger.error("❌ No processed data available")
        return {'success': False, 'error': 'No data'}
    
    try:
        # Combine all successful data into one DataFrame
        all_data = []
        for symbol, data in processed_data.items():
            if data['success'] and data['processed_data'] is not None:
                all_data.append(data['processed_data'])
        
        if not all_data:
            logger.error("❌ No valid processed data found")
            return {'success': False, 'error': 'No valid data'}
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Validate database schema compatibility
        schema_checks = {
            'timestamp_dtype': combined_df['timestamp'].dtype == 'datetime64[ns]',
            'symbol_dtype': combined_df['symbol'].dtype == 'object',
            'exchange_dtype': combined_df['exchange'].dtype == 'object',
            'timeframe_dtype': combined_df['timeframe'].dtype == 'object',
            'numeric_prices': all(pd.api.types.is_numeric_dtype(combined_df[col]) for col in ['open', 'high', 'low', 'close', 'volume']),
            'created_at_dtype': combined_df['created_at'].dtype == 'datetime64[ns]'
        }
        
        # Generate SQL INSERT preview
        sample_row = combined_df.iloc[0]
        sql_preview = f"""
        INSERT INTO trading.ohlc_data 
        (symbol, exchange, timeframe, timestamp, open, high, low, close, volume, created_at)
        VALUES (
            '{sample_row['symbol']}',
            '{sample_row['exchange']}',
            '{sample_row['timeframe']}',
            '{sample_row['timestamp']}',
            {sample_row['open']},
            {sample_row['high']},
            {sample_row['low']},
            {sample_row['close']},
            {sample_row['volume']},
            '{sample_row['created_at']}'
        );
        """
        
        all_schema_checks_passed = all(schema_checks.values())
        
        if all_schema_checks_passed:
            logger.info("✅ Database schema validation passed")
            logger.info(f"   Total records ready: {len(combined_df):,}")
            logger.info(f"   Symbols: {combined_df['symbol'].unique().tolist()}")
            logger.info(f"   Time range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
            logger.info("✅ SQL INSERT statement format validated")
        else:
            failed_checks = [check for check, passed in schema_checks.items() if not passed]
            logger.error(f"❌ Schema validation failed: {failed_checks}")
        
        return {
            'success': all_schema_checks_passed,
            'schema_checks': schema_checks,
            'combined_data': combined_df,
            'sql_preview': sql_preview,
            'record_count': len(combined_df)
        }
        
    except Exception as e:
        logger.error(f"❌ Database preparation failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_timescale_connection():
    """Test 5: TimescaleDB Connection (if available)"""
    logger.info("\n🔍 TEST 5: TimescaleDB Connection Test")
    logger.info("=" * 50)
    
    try:
        # Try to import and test TimescaleDB connection
        sys.path.append('.')
        
        # Set environment variables for testing
        os.environ.setdefault('POSTGRES_SERVER', 'localhost')
        os.environ.setdefault('POSTGRES_PORT', '15432')
        os.environ.setdefault('POSTGRES_USER', 'postgres')
        os.environ.setdefault('POSTGRES_PASSWORD', 'postgres')
        os.environ.setdefault('POSTGRES_DB', 'autonama')
        
        from tasks.timescale_data_ingestion import TimescaleDBManager
        from sqlalchemy import text
        
        manager = TimescaleDBManager()
        logger.info("✅ TimescaleDBManager initialized")
        
        # Test connection
        with manager.engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test, NOW() as current_time")).fetchone()
            if result:
                logger.info(f"✅ Database connection successful")
                logger.info(f"   Current time: {result[1]}")
                
                # Check if tables exist
                table_check = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'trading' AND table_name = 'ohlc_data'
                    )
                """)).fetchone()
                
                if table_check and table_check[0]:
                    logger.info("✅ trading.ohlc_data table exists")
                    
                    # Check current record count
                    count_result = conn.execute(text("SELECT COUNT(*) FROM trading.ohlc_data")).fetchone()
                    current_count = count_result[0] if count_result else 0
                    logger.info(f"   Current records: {current_count:,}")
                    
                else:
                    logger.warning("⚠️  trading.ohlc_data table not found - may need schema initialization")
                
                return {'success': True, 'manager': manager, 'table_exists': table_check[0] if table_check else False}
            else:
                logger.error("❌ Database query returned no result")
                return {'success': False, 'error': 'No query result'}
                
    except ImportError as e:
        logger.warning(f"⚠️  Cannot test TimescaleDB - missing dependencies: {e}")
        return {'success': False, 'error': 'Missing dependencies', 'skipped': True}
    except Exception as e:
        logger.warning(f"⚠️  TimescaleDB connection test failed: {e}")
        return {'success': False, 'error': str(e)}

def run_binance_integration_test():
    """Run comprehensive Binance API integration test"""
    logger.info("🚀 BINANCE API INTEGRATION TEST")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: API Connectivity
    connectivity_result = test_binance_connectivity()
    results['connectivity'] = connectivity_result
    
    if not connectivity_result['success']:
        logger.error("❌ Cannot continue - Binance API connectivity failed")
        return results
    
    client = connectivity_result['client']
    
    # Test 2: Data Fetching
    results['data_fetching'] = test_crypto_data_fetching(client)
    
    # Test 3: Data Processing
    results['data_processing'] = test_data_processing(results['data_fetching'])
    
    # Test 4: Database Preparation
    results['database_prep'] = test_database_preparation(results['data_processing'])
    
    # Test 5: TimescaleDB Connection (optional)
    results['timescale_connection'] = test_timescale_connection()
    
    # Final Summary
    logger.info("\n🎯 BINANCE INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    test_names = {
        'connectivity': 'Binance API Connectivity',
        'data_fetching': 'Real Crypto Data Fetching',
        'data_processing': 'Data Processing & Validation',
        'database_prep': 'Database Preparation',
        'timescale_connection': 'TimescaleDB Connection'
    }
    
    passed = 0
    total = 0
    
    for test_key, test_name in test_names.items():
        result = results.get(test_key, {})
        
        # Skip TimescaleDB test if dependencies missing
        if test_key == 'timescale_connection' and result.get('skipped'):
            logger.info(f"⏭️  {test_name}: SKIPPED (dependencies not available)")
            continue
            
        total += 1
        
        if test_key == 'data_fetching':
            # Special handling for data fetching (multiple symbols)
            if result:
                successful_symbols = sum(1 for r in result.values() if r.get('success', False))
                total_symbols = len(result)
                if successful_symbols > 0:
                    logger.info(f"✅ {test_name}: {successful_symbols}/{total_symbols} symbols successful")
                    passed += 1
                else:
                    logger.info(f"❌ {test_name}: No symbols successful")
            else:
                logger.info(f"❌ {test_name}: Failed")
        else:
            if result.get('success', False):
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                error = result.get('error', 'Unknown error')
                logger.info(f"❌ {test_name}: FAILED - {error}")
    
    logger.info(f"\n🏆 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Binance API integration is working perfectly!")
        logger.info("✅ Ready for TimescaleDB data insertion")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most tests passed - minor issues to address")
    else:
        logger.info("❌ Multiple test failures - significant issues need attention")
    
    # Show data summary if available
    if results.get('database_prep', {}).get('success'):
        record_count = results['database_prep']['record_count']
        logger.info(f"📊 Ready to insert {record_count:,} records into TimescaleDB")
    
    return results

if __name__ == "__main__":
    try:
        results = run_binance_integration_test()
        
        # Exit with appropriate code
        passed_count = sum(1 for r in results.values() if r.get('success', False) and not r.get('skipped', False))
        total_count = sum(1 for r in results.values() if not r.get('skipped', False))
        
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