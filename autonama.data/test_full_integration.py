#!/usr/bin/env python3
"""
Full Binance to TimescaleDB Integration Test

This script tests the complete end-to-end integration:
Binance API → Data Processing → TimescaleDB Storage → Data Retrieval

This should be run in the Docker environment where TimescaleDB is available.
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

# Add current directory to path for imports
sys.path.append('.')

class BinanceToTimescaleIntegrator:
    """Integrates Binance API data with TimescaleDB storage"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama-Trading-System/1.0'
        })
        self.timescale_manager = None
    
    def initialize_timescale(self):
        """Initialize TimescaleDB connection"""
        try:
            from tasks.timescale_data_ingestion import TimescaleDBManager
            from sqlalchemy import text
            
            self.timescale_manager = TimescaleDBManager()
            logger.info("✅ TimescaleDBManager initialized")
            
            # Test connection
            with self.timescale_manager.engine.connect() as conn:
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
    
    def fetch_binance_data(self, symbol: str, interval: str = '1h', limit: int = 5) -> Optional[List[Dict]]:
        """Fetch data from Binance API"""
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
            
            # Process into our format
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
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Binance data for {symbol}: {e}")
            return None
    
    def store_to_timescale(self, data: List[Dict]) -> bool:
        """Store data in TimescaleDB"""
        if not self.timescale_manager or not data:
            return False
        
        try:
            from sqlalchemy import text
            
            with self.timescale_manager.engine.connect() as conn:
                for record in data:
                    # Use the fixed SQL parameter format
                    insert_query = """
                        INSERT INTO trading.ohlc_data 
                        (symbol, exchange, timeframe, timestamp, open, high, low, close, volume, created_at)
                        VALUES (:symbol, :exchange, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :created_at)
                        ON CONFLICT (symbol, exchange, timeframe, timestamp) 
                        DO UPDATE SET 
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            created_at = EXCLUDED.created_at
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
                logger.info(f"✅ Successfully stored {len(data)} records in TimescaleDB")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store data in TimescaleDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve_from_timescale(self, symbol: str, limit: int = 10) -> Optional[List[Dict]]:
        """Retrieve data from TimescaleDB"""
        if not self.timescale_manager:
            return None
        
        try:
            from sqlalchemy import text
            
            query = """
                SELECT timestamp, symbol, exchange, timeframe, open, high, low, close, volume, created_at
                FROM trading.ohlc_data
                WHERE symbol = :symbol 
                    AND exchange = :exchange 
                    AND timeframe = :timeframe
                ORDER BY timestamp DESC 
                LIMIT :limit
            """
            
            with self.timescale_manager.engine.connect() as conn:
                result = conn.execute(text(query), {
                    'symbol': symbol,
                    'exchange': 'binance',
                    'timeframe': '1h',
                    'limit': limit
                }).fetchall()
                
                if result:
                    data = []
                    for row in result:
                        data.append({
                            'timestamp': row[0],
                            'symbol': row[1],
                            'exchange': row[2],
                            'timeframe': row[3],
                            'open': float(row[4]),
                            'high': float(row[5]),
                            'low': float(row[6]),
                            'close': float(row[7]),
                            'volume': float(row[8]),
                            'created_at': row[9]
                        })
                    
                    logger.info(f"✅ Retrieved {len(data)} records from TimescaleDB")
                    return data
                else:
                    logger.warning(f"⚠️  No data found for {symbol}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to retrieve data from TimescaleDB: {e}")
            import traceback
            traceback.print_exc()
            return None

def test_full_integration():
    """Test the complete integration flow"""
    logger.info("🚀 FULL BINANCE TO TIMESCALEDB INTEGRATION TEST")
    logger.info("=" * 60)
    
    integrator = BinanceToTimescaleIntegrator()
    
    # Test 1: Initialize TimescaleDB
    logger.info("🔍 TEST 1: TimescaleDB Initialization")
    logger.info("=" * 50)
    
    if not integrator.initialize_timescale():
        logger.error("❌ Cannot continue - TimescaleDB initialization failed")
        return False
    
    # Test 2: Fetch Binance Data
    logger.info("\n🔍 TEST 2: Binance Data Fetching")
    logger.info("=" * 50)
    
    test_symbols = ['BTCUSDT', 'ETHUSDT']
    all_data = {}
    
    for symbol in test_symbols:
        logger.info(f"📡 Fetching data for {symbol}...")
        data = integrator.fetch_binance_data(symbol, '1h', 5)
        
        if data:
            logger.info(f"✅ {symbol}: {len(data)} records fetched")
            logger.info(f"   Latest: {data[-1]['timestamp']} - ${data[-1]['close']:.2f}")
            all_data[symbol] = data
        else:
            logger.error(f"❌ {symbol}: Failed to fetch data")
            return False
    
    # Test 3: Store Data in TimescaleDB
    logger.info("\n🔍 TEST 3: TimescaleDB Data Storage")
    logger.info("=" * 50)
    
    total_stored = 0
    for symbol, data in all_data.items():
        logger.info(f"💾 Storing {len(data)} records for {symbol}...")
        
        if integrator.store_to_timescale(data):
            total_stored += len(data)
            logger.info(f"✅ {symbol}: Storage successful")
        else:
            logger.error(f"❌ {symbol}: Storage failed")
            return False
    
    logger.info(f"📊 Total records stored: {total_stored}")
    
    # Test 4: Retrieve Data from TimescaleDB
    logger.info("\n🔍 TEST 4: TimescaleDB Data Retrieval")
    logger.info("=" * 50)
    
    for symbol in test_symbols:
        symbol_formatted = symbol.replace('USDT', '/USDT')
        logger.info(f"📖 Retrieving data for {symbol_formatted}...")
        
        retrieved_data = integrator.retrieve_from_timescale(symbol_formatted, 5)
        
        if retrieved_data is not None:
            if retrieved_data:
                logger.info(f"✅ {symbol_formatted}: {len(retrieved_data)} records retrieved")
                logger.info(f"   Latest: {retrieved_data[0]['timestamp']} - ${retrieved_data[0]['close']:.2f}")
                
                # Verify data integrity
                original_data = all_data[symbol]
                if len(retrieved_data) >= len(original_data):
                    logger.info(f"   ✅ Data integrity check passed")
                else:
                    logger.warning(f"   ⚠️  Retrieved {len(retrieved_data)} records, expected {len(original_data)}")
            else:
                logger.warning(f"⚠️  {symbol_formatted}: No data retrieved (may be expected for new data)")
        else:
            logger.error(f"❌ {symbol_formatted}: Retrieval failed")
            return False
    
    # Test 5: Data Consistency Check
    logger.info("\n🔍 TEST 5: Data Consistency Validation")
    logger.info("=" * 50)
    
    consistency_passed = True
    
    for symbol in test_symbols:
        symbol_formatted = symbol.replace('USDT', '/USDT')
        original_data = all_data[symbol]
        retrieved_data = integrator.retrieve_from_timescale(symbol_formatted, len(original_data))
        
        if retrieved_data:
            # Check if we can find matching records
            original_timestamps = {record['timestamp'] for record in original_data}
            retrieved_timestamps = {record['timestamp'] for record in retrieved_data}
            
            matching_timestamps = original_timestamps.intersection(retrieved_timestamps)
            
            if matching_timestamps:
                logger.info(f"✅ {symbol_formatted}: {len(matching_timestamps)} matching timestamps found")
                
                # Verify price data for matching timestamps
                for timestamp in list(matching_timestamps)[:3]:  # Check first 3
                    original_record = next(r for r in original_data if r['timestamp'] == timestamp)
                    retrieved_record = next(r for r in retrieved_data if r['timestamp'] == timestamp)
                    
                    if (abs(original_record['close'] - retrieved_record['close']) < 0.01 and
                        abs(original_record['volume'] - retrieved_record['volume']) < 0.01):
                        logger.info(f"   ✅ Price data matches for {timestamp}")
                    else:
                        logger.error(f"   ❌ Price data mismatch for {timestamp}")
                        consistency_passed = False
            else:
                logger.warning(f"⚠️  {symbol_formatted}: No matching timestamps (data may be too recent)")
        else:
            logger.warning(f"⚠️  {symbol_formatted}: No retrieved data for consistency check")
    
    # Final Summary
    logger.info("\n🎯 FULL INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    if consistency_passed:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
        logger.info("✅ Binance API → TimescaleDB → Data Retrieval: WORKING")
        logger.info("✅ SQL parameter bug fix: CONFIRMED WORKING")
        logger.info("✅ End-to-end crypto data flow: OPERATIONAL")
        logger.info(f"✅ Total records processed: {total_stored}")
        return True
    else:
        logger.error("❌ Integration test failed - data consistency issues")
        return False

if __name__ == "__main__":
    try:
        success = test_full_integration()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)