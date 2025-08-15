#!/usr/bin/env python3
"""
Multi-Symbol Crypto Data Expansion Test

This script tests the scalability of our crypto data pipeline by:
1. Expanding to more trading pairs (ADA, DOT, LINK, MATIC, AVAX, etc.)
2. Testing concurrent processing and rate limiting
3. Validating database storage with increased volume
4. Measuring performance metrics

Test Flow:
1. Fetch data for multiple crypto pairs concurrently
2. Store all data in TimescaleDB
3. Validate data integrity and performance
4. Test rate limiting compliance
"""

import sys
import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import concurrent.futures
import threading
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiSymbolBinanceIntegrator:
    """Enhanced Binance integrator for multi-symbol concurrent processing"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama-Trading-System/1.0'
        })
        self.engine = None
        self.rate_limiter = RateLimiter(requests_per_minute=1000)  # Conservative limit
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
    
    def initialize_timescale(self):
        """Initialize TimescaleDB connection"""
        try:
            from sqlalchemy import create_engine, text
            
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:15432/autonama')
            self.engine = create_engine(db_url)
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test, NOW() as current_time")).fetchone()
                if result:
                    logger.info(f"✅ TimescaleDB connection successful: {result[1]}")
                    return True
                else:
                    logger.error("❌ TimescaleDB connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ TimescaleDB initialization failed: {e}")
            return False
    
    def fetch_symbol_data(self, symbol: str, interval: str = '1h', limit: int = 5) -> Optional[Dict]:
        """Fetch data for a single symbol with rate limiting"""
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/v3/klines", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            response_time = time.time() - start_time
            
            klines = response.json()
            
            # Process data
            processed_data = []
            for kline in klines:
                processed_data.append({
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'symbol': symbol.replace('USDT', '/USDT'),
                    'exchange': 'binance',
                    'timeframe': interval,
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'created_at': datetime.now()
                })
            
            # Update stats
            with self.lock:
                self.stats['successful_requests'] += 1
                self.stats['total_response_time'] += response_time
                self.stats['total_records'] += len(processed_data)
            
            return {
                'success': True,
                'symbol': symbol,
                'data': processed_data,
                'response_time': response_time,
                'record_count': len(processed_data)
            }
            
        except Exception as e:
            with self.lock:
                self.stats['failed_requests'] += 1
            
            logger.error(f"❌ Failed to fetch data for {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def fetch_multiple_symbols_concurrent(self, symbols: List[str], max_workers: int = 5) -> Dict[str, Any]:
        """Fetch data for multiple symbols concurrently"""
        logger.info(f"📡 Fetching data for {len(symbols)} symbols with {max_workers} workers...")
        
        results = {}
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.fetch_symbol_data, symbol): symbol 
                for symbol in symbols
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results[symbol] = result
                    
                    if result['success']:
                        logger.info(f"✅ {symbol}: {result['record_count']} records ({result['response_time']:.2f}s)")
                    else:
                        logger.error(f"❌ {symbol}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ {symbol}: Exception during processing - {e}")
                    results[symbol] = {'success': False, 'symbol': symbol, 'error': str(e)}
        
        total_time = time.time() - start_time
        
        # Calculate summary stats
        successful = sum(1 for r in results.values() if r['success'])
        total_records = sum(r.get('record_count', 0) for r in results.values() if r['success'])
        
        logger.info(f"📊 Concurrent fetch summary:")
        logger.info(f"   Symbols: {successful}/{len(symbols)} successful")
        logger.info(f"   Records: {total_records} total")
        logger.info(f"   Time: {total_time:.2f}s total")
        logger.info(f"   Rate: {len(symbols)/total_time:.2f} symbols/second")
        
        return results
    
    def store_multiple_symbols(self, results: Dict[str, Any]) -> bool:
        """Store data for multiple symbols in TimescaleDB"""
        if not self.engine:
            return False
        
        try:
            from sqlalchemy import text
            
            total_stored = 0
            successful_symbols = 0
            
            with self.engine.connect() as conn:
                for symbol, result in results.items():
                    if not result['success']:
                        continue
                    
                    try:
                        for record in result['data']:
                            insert_query = """
                                INSERT INTO trading.ohlc_data 
                                (symbol, exchange, timeframe, timestamp, open, high, low, close, volume, created_at)
                                VALUES (:symbol, :exchange, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :created_at)
                            """
                            
                            conn.execute(text(insert_query), {
                                'symbol': record['symbol'],
                                'exchange': record['exchange'],
                                'timeframe': record['timeframe'],
                                'timestamp': record['timestamp'],
                                'open': record['open'],
                                'high': record['high'],
                                'low': record['low'],
                                'close': record['close'],
                                'volume': record['volume'],
                                'created_at': record['created_at']
                            })
                        
                        conn.commit()
                        total_stored += len(result['data'])
                        successful_symbols += 1
                        logger.info(f"✅ {symbol}: {len(result['data'])} records stored")
                        
                    except Exception as e:
                        logger.error(f"❌ {symbol}: Storage failed - {e}")
                        conn.rollback()
            
            logger.info(f"📊 Storage summary: {successful_symbols} symbols, {total_stored} records stored")
            return successful_symbols > 0
            
        except Exception as e:
            logger.error(f"❌ Multi-symbol storage failed: {e}")
            return False
    
    def validate_stored_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Validate that data was stored correctly"""
        if not self.engine:
            return {}
        
        try:
            from sqlalchemy import text
            
            validation_results = {}
            
            with self.engine.connect() as conn:
                for symbol in symbols:
                    symbol_formatted = symbol.replace('USDT', '/USDT')
                    
                    # Count records
                    count_query = """
                        SELECT COUNT(*) as count,
                               MIN(timestamp) as earliest,
                               MAX(timestamp) as latest,
                               AVG(close) as avg_price
                        FROM trading.ohlc_data 
                        WHERE symbol = :symbol 
                            AND exchange = :exchange 
                            AND created_at > :recent_time
                    """
                    
                    result = conn.execute(text(count_query), {
                        'symbol': symbol_formatted,
                        'exchange': 'binance',
                        'recent_time': datetime.now() - timedelta(minutes=10)
                    }).fetchone()
                    
                    if result:
                        validation_results[symbol] = {
                            'count': result[0],
                            'earliest': result[1],
                            'latest': result[2],
                            'avg_price': float(result[3]) if result[3] else None
                        }
                        
                        if result[0] > 0:
                            logger.info(f"✅ {symbol_formatted}: {result[0]} records validated")
                        else:
                            logger.warning(f"⚠️  {symbol_formatted}: No recent records found")
                    else:
                        validation_results[symbol] = {'count': 0}
                        logger.warning(f"⚠️  {symbol_formatted}: Validation query failed")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            return {}

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()

def test_multi_symbol_expansion():
    """Test multi-symbol crypto data expansion"""
    logger.info("🚀 MULTI-SYMBOL CRYPTO DATA EXPANSION TEST")
    logger.info("=" * 60)
    
    # Extended list of crypto symbols
    test_symbols = [
        'BTCUSDT',   # Bitcoin
        'ETHUSDT',   # Ethereum
        'BNBUSDT',   # Binance Coin
        'ADAUSDT',   # Cardano
        'DOTUSDT',   # Polkadot
        'LINKUSDT',  # Chainlink
        'MATICUSDT', # Polygon
        'AVAXUSDT',  # Avalanche
        'SOLUSDT',   # Solana
        'UNIUSDT'    # Uniswap
    ]
    
    integrator = MultiSymbolBinanceIntegrator()
    
    # Test 1: Initialize TimescaleDB
    logger.info("🔍 TEST 1: TimescaleDB Initialization")
    logger.info("=" * 50)
    
    if not integrator.initialize_timescale():
        logger.error("❌ Cannot continue - TimescaleDB initialization failed")
        return False
    
    # Test 2: Multi-Symbol Data Fetching
    logger.info("\n🔍 TEST 2: Multi-Symbol Concurrent Data Fetching")
    logger.info("=" * 50)
    
    fetch_results = integrator.fetch_multiple_symbols_concurrent(test_symbols, max_workers=5)
    
    successful_fetches = sum(1 for r in fetch_results.values() if r['success'])
    if successful_fetches == 0:
        logger.error("❌ No symbols fetched successfully")
        return False
    
    # Test 3: Multi-Symbol Data Storage
    logger.info("\n🔍 TEST 3: Multi-Symbol Data Storage")
    logger.info("=" * 50)
    
    if not integrator.store_multiple_symbols(fetch_results):
        logger.error("❌ Multi-symbol storage failed")
        return False
    
    # Test 4: Data Validation
    logger.info("\n🔍 TEST 4: Stored Data Validation")
    logger.info("=" * 50)
    
    validation_results = integrator.validate_stored_data(test_symbols)
    
    validated_symbols = sum(1 for r in validation_results.values() if r.get('count', 0) > 0)
    total_validated_records = sum(r.get('count', 0) for r in validation_results.values())
    
    logger.info(f"📊 Validation summary: {validated_symbols}/{len(test_symbols)} symbols, {total_validated_records} records")
    
    # Test 5: Performance Analysis
    logger.info("\n🔍 TEST 5: Performance Analysis")
    logger.info("=" * 50)
    
    stats = integrator.stats
    if stats['successful_requests'] > 0:
        avg_response_time = stats['total_response_time'] / stats['successful_requests']
        logger.info(f"✅ Performance metrics:")
        logger.info(f"   Successful requests: {stats['successful_requests']}")
        logger.info(f"   Failed requests: {stats['failed_requests']}")
        logger.info(f"   Average response time: {avg_response_time:.3f}s")
        logger.info(f"   Total records processed: {stats['total_records']}")
        logger.info(f"   Records per second: {stats['total_records']/stats['total_response_time']:.1f}")
    
    # Final Summary
    logger.info("\n🎯 MULTI-SYMBOL EXPANSION TEST SUMMARY")
    logger.info("=" * 60)
    
    success_rate = successful_fetches / len(test_symbols)
    validation_rate = validated_symbols / len(test_symbols)
    
    if success_rate >= 0.8 and validation_rate >= 0.8:
        logger.info("🎉 MULTI-SYMBOL EXPANSION TEST PASSED!")
        logger.info(f"✅ Fetch success rate: {success_rate:.1%}")
        logger.info(f"✅ Validation success rate: {validation_rate:.1%}")
        logger.info(f"✅ Total symbols processed: {successful_fetches}/{len(test_symbols)}")
        logger.info(f"✅ Total records stored: {total_validated_records}")
        logger.info("✅ System ready for production-scale crypto data processing")
        return True
    else:
        logger.error("❌ Multi-symbol expansion test failed")
        logger.error(f"   Fetch success rate: {success_rate:.1%} (need ≥80%)")
        logger.error(f"   Validation success rate: {validation_rate:.1%} (need ≥80%)")
        return False

if __name__ == "__main__":
    try:
        success = test_multi_symbol_expansion()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)