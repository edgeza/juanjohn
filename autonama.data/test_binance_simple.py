#!/usr/bin/env python3
"""
Simple Binance API Integration Test

This script tests the Binance API integration without pandas dependency.
It validates the API connection and data fetching using only standard libraries.
"""

import sys
import os
import logging
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

class SimpleBinanceClient:
    """Simple Binance API client using only requests"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama-Trading-System/1.0'
        })
    
    def test_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/ping", timeout=10)
            response.raise_for_status()
            
            # Get server time
            time_response = self.session.get(f"{self.base_url}/api/v3/time", timeout=10)
            time_response.raise_for_status()
            server_time = time_response.json()
            
            return {
                'success': True,
                'server_time': server_time['serverTime'],
                'server_datetime': datetime.fromtimestamp(server_time['serverTime'] / 1000)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/exchangeInfo", timeout=10)
            response.raise_for_status()
            exchange_info = response.json()
            
            # Find the specific symbol
            for sym_info in exchange_info.get('symbols', []):
                if sym_info['symbol'] == symbol:
                    return {'success': True, 'symbol_info': sym_info}
            
            return {'success': False, 'error': f'Symbol {symbol} not found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker price"""
        try:
            params = {'symbol': symbol}
            response = self.session.get(
                f"{self.base_url}/api/v3/ticker/price", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_24hr_stats(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker statistics"""
        try:
            params = {'symbol': symbol}
            response = self.session.get(
                f"{self.base_url}/api/v3/ticker/24hr", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 5) -> Dict[str, Any]:
        """Get kline/candlestick data"""
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
            
            klines = response.json()
            
            # Process klines data
            processed_data = []
            for kline in klines:
                processed_data.append({
                    'open_time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6]),
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'symbol': symbol.replace('USDT', '/USDT'),  # Convert to standard format
                    'exchange': 'binance',
                    'timeframe': interval
                })
            
            return {'success': True, 'data': processed_data}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

def test_api_connectivity():
    """Test 1: API Connectivity"""
    logger.info("🔍 TEST 1: Binance API Connectivity")
    logger.info("=" * 50)
    
    try:
        client = SimpleBinanceClient()
        result = client.test_connectivity()
        
        if result['success']:
            logger.info("✅ Binance API connection successful")
            logger.info(f"   Server time: {result['server_datetime']}")
            logger.info(f"   Timestamp: {result['server_time']}")
            return {'success': True, 'client': client}
        else:
            logger.error(f"❌ API connectivity failed: {result['error']}")
            return {'success': False, 'error': result['error']}
            
    except Exception as e:
        logger.error(f"❌ Connectivity test failed: {e}")
        return {'success': False, 'error': str(e)}

def test_symbol_validation(client):
    """Test 2: Symbol Validation"""
    logger.info("\n🔍 TEST 2: Symbol Validation")
    logger.info("=" * 50)
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    for symbol in test_symbols:
        logger.info(f"🔍 Validating {symbol}...")
        
        result = client.get_symbol_info(symbol)
        if result['success']:
            symbol_info = result['symbol_info']
            logger.info(f"✅ {symbol}: Valid symbol")
            logger.info(f"   Status: {symbol_info['status']}")
            logger.info(f"   Base asset: {symbol_info['baseAsset']}")
            logger.info(f"   Quote asset: {symbol_info['quoteAsset']}")
            results[symbol] = {'success': True, 'info': symbol_info}
        else:
            logger.error(f"❌ {symbol}: {result['error']}")
            results[symbol] = {'success': False, 'error': result['error']}
    
    successful = sum(1 for r in results.values() if r['success'])
    logger.info(f"📊 Symbol validation: {successful}/{len(test_symbols)} symbols valid")
    
    return results

def test_price_data(client):
    """Test 3: Price Data Fetching"""
    logger.info("\n🔍 TEST 3: Price Data Fetching")
    logger.info("=" * 50)
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    for symbol in test_symbols:
        logger.info(f"📡 Fetching price data for {symbol}...")
        
        try:
            # Get current price
            price_result = client.get_ticker_price(symbol)
            
            # Get 24hr stats
            stats_result = client.get_24hr_stats(symbol)
            
            if price_result['success'] and stats_result['success']:
                price_data = price_result['data']
                stats_data = stats_result['data']
                
                current_price = float(price_data['price'])
                price_change = float(stats_data['priceChangePercent'])
                volume = float(stats_data['volume'])
                high_24h = float(stats_data['highPrice'])
                low_24h = float(stats_data['lowPrice'])
                
                logger.info(f"✅ {symbol}: Price data retrieved")
                logger.info(f"   Current price: ${current_price:,.2f}")
                logger.info(f"   24h change: {price_change:.2f}%")
                logger.info(f"   24h volume: {volume:,.0f}")
                logger.info(f"   24h range: ${low_24h:,.2f} - ${high_24h:,.2f}")
                
                results[symbol] = {
                    'success': True,
                    'current_price': current_price,
                    'price_change_24h': price_change,
                    'volume_24h': volume,
                    'high_24h': high_24h,
                    'low_24h': low_24h
                }
            else:
                error = price_result.get('error') or stats_result.get('error')
                logger.error(f"❌ {symbol}: {error}")
                results[symbol] = {'success': False, 'error': error}
                
        except Exception as e:
            logger.error(f"❌ {symbol}: {e}")
            results[symbol] = {'success': False, 'error': str(e)}
    
    successful = sum(1 for r in results.values() if r['success'])
    logger.info(f"📊 Price data: {successful}/{len(test_symbols)} symbols successful")
    
    return results

def test_ohlcv_data(client):
    """Test 4: OHLCV Data Fetching"""
    logger.info("\n🔍 TEST 4: OHLCV Data Fetching")
    logger.info("=" * 50)
    
    test_symbols = ['BTCUSDT', 'ETHUSDT']
    results = {}
    
    for symbol in test_symbols:
        logger.info(f"📊 Fetching OHLCV data for {symbol}...")
        
        result = client.get_klines(symbol, '1h', 5)
        
        if result['success']:
            data = result['data']
            
            logger.info(f"✅ {symbol}: {len(data)} OHLCV records retrieved")
            
            # Show sample data
            if data:
                latest = data[-1]
                logger.info(f"   Latest candle:")
                logger.info(f"     Time: {latest['timestamp']}")
                logger.info(f"     OHLC: ${latest['open']:.2f} / ${latest['high']:.2f} / ${latest['low']:.2f} / ${latest['close']:.2f}")
                logger.info(f"     Volume: {latest['volume']:,.0f}")
            
            # Validate data structure
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'exchange', 'timeframe']
            data_valid = all(all(field in record for field in required_fields) for record in data)
            
            if data_valid:
                logger.info(f"   ✅ Data structure validation passed")
                results[symbol] = {'success': True, 'data': data, 'record_count': len(data)}
            else:
                logger.error(f"   ❌ Data structure validation failed")
                results[symbol] = {'success': False, 'error': 'Invalid data structure'}
        else:
            logger.error(f"❌ {symbol}: {result['error']}")
            results[symbol] = {'success': False, 'error': result['error']}
    
    successful = sum(1 for r in results.values() if r['success'])
    total_records = sum(r.get('record_count', 0) for r in results.values() if r['success'])
    
    logger.info(f"📊 OHLCV data: {successful}/{len(test_symbols)} symbols, {total_records} total records")
    
    return results

def test_data_quality(ohlcv_results):
    """Test 5: Data Quality Validation"""
    logger.info("\n🔍 TEST 5: Data Quality Validation")
    logger.info("=" * 50)
    
    if not ohlcv_results:
        logger.error("❌ No OHLCV data available for quality testing")
        return {'success': False, 'error': 'No data'}
    
    quality_results = {}
    
    for symbol, result in ohlcv_results.items():
        if not result['success']:
            continue
            
        logger.info(f"🔍 Validating data quality for {symbol}...")
        
        data = result['data']
        
        # Quality checks
        checks = {
            'non_empty': len(data) > 0,
            'positive_prices': all(record['open'] > 0 and record['high'] > 0 and record['low'] > 0 and record['close'] > 0 for record in data),
            'high_ge_low': all(record['high'] >= record['low'] for record in data),
            'high_ge_open_close': all(record['high'] >= max(record['open'], record['close']) for record in data),
            'low_le_open_close': all(record['low'] <= min(record['open'], record['close']) for record in data),
            'non_negative_volume': all(record['volume'] >= 0 for record in data),
            'recent_data': (datetime.now() - data[-1]['timestamp']).total_seconds() < 7200,  # Within 2 hours
            'chronological_order': all(data[i]['timestamp'] <= data[i+1]['timestamp'] for i in range(len(data)-1))
        }
        
        all_checks_passed = all(checks.values())
        
        if all_checks_passed:
            logger.info(f"✅ {symbol}: All quality checks passed")
            
            # Calculate some basic stats
            prices = [record['close'] for record in data]
            volumes = [record['volume'] for record in data]
            
            logger.info(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            logger.info(f"   Avg volume: {sum(volumes)/len(volumes):,.0f}")
            logger.info(f"   Time span: {data[0]['timestamp']} to {data[-1]['timestamp']}")
            
        else:
            failed_checks = [check for check, passed in checks.items() if not passed]
            logger.error(f"❌ {symbol}: Failed quality checks: {failed_checks}")
        
        quality_results[symbol] = {
            'success': all_checks_passed,
            'checks': checks,
            'data_points': len(data)
        }
    
    successful = sum(1 for r in quality_results.values() if r['success'])
    logger.info(f"📊 Data quality: {successful}/{len(quality_results)} symbols passed all checks")
    
    return quality_results

def run_simple_binance_test():
    """Run simple Binance API integration test"""
    logger.info("🚀 SIMPLE BINANCE API INTEGRATION TEST")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: API Connectivity
    connectivity_result = test_api_connectivity()
    results['connectivity'] = connectivity_result
    
    if not connectivity_result['success']:
        logger.error("❌ Cannot continue - API connectivity failed")
        return results
    
    client = connectivity_result['client']
    
    # Test 2: Symbol Validation
    results['symbol_validation'] = test_symbol_validation(client)
    
    # Test 3: Price Data
    results['price_data'] = test_price_data(client)
    
    # Test 4: OHLCV Data
    results['ohlcv_data'] = test_ohlcv_data(client)
    
    # Test 5: Data Quality
    results['data_quality'] = test_data_quality(results['ohlcv_data'])
    
    # Final Summary
    logger.info("\n🎯 SIMPLE BINANCE TEST SUMMARY")
    logger.info("=" * 60)
    
    test_names = {
        'connectivity': 'API Connectivity',
        'symbol_validation': 'Symbol Validation',
        'price_data': 'Price Data Fetching',
        'ohlcv_data': 'OHLCV Data Fetching',
        'data_quality': 'Data Quality Validation'
    }
    
    passed = 0
    total = len(test_names)
    
    for test_key, test_name in test_names.items():
        result = results.get(test_key, {})
        
        if test_key in ['symbol_validation', 'price_data', 'ohlcv_data', 'data_quality']:
            # Multi-symbol tests
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
            # Single result tests
            if result.get('success', False):
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                error = result.get('error', 'Unknown error')
                logger.info(f"❌ {test_name}: FAILED - {error}")
    
    logger.info(f"\n🏆 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Binance API integration is working perfectly!")
        logger.info("✅ Real crypto data successfully fetched and validated")
        logger.info("✅ Ready for TimescaleDB integration")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most tests passed - minor issues to address")
    else:
        logger.info("❌ Multiple test failures - significant issues need attention")
    
    return results

if __name__ == "__main__":
    try:
        results = run_simple_binance_test()
        
        # Exit with appropriate code
        passed_count = sum(1 for test_key, result in results.items() if 
                          test_key in ['connectivity'] and result.get('success', False) or
                          test_key in ['symbol_validation', 'price_data', 'ohlcv_data', 'data_quality'] and 
                          sum(1 for r in result.values() if r.get('success', False)) > 0)
        
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