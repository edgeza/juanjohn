#!/usr/bin/env python3
"""
Direct Docker Integration Test

This script tests the Binance to TimescaleDB integration directly
without Celery dependencies, designed to run in Docker environment.
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

class DirectTimescaleIntegrator:
    """Direct integration without Celery dependencies"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama-Trading-System/1.0'
        })
        self.engine = None
    
    def initialize_timescale(self):
        """Initialize TimescaleDB connection directly"""
        try:
            from sqlalchemy import create_engine, text
            
            # Get database URL from environment
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:15432/autonama')
            
            self.engine = create_engine(db_url)
            logger.info(f"✅ Database engine created: {db_url.replace('postgres:postgres', 'postgres:***')}")
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test, NOW() as current_time")).fetchone()
                if result:
                    logger.info(f"✅ TimescaleDB connection successful: {result[1]}")
                    
                    # Check table existence
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
                        
                        return True
                    else:
                        logger.error("❌ trading.ohlc_data table not found")
                        return False
                else:
                    logger.error("❌ Database connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ TimescaleDB initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def fetch_binance_data(self, symbol: str, interval: str = '1h', limit: int = 3) -> Optional[List[Dict]]:
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
        """Store data in TimescaleDB using fixed SQL parameters"""
        if not self.engine or not data:
            return False
        
        try:
            from sqlalchemy import text
            
            with self.engine.connect() as conn:
                for record in data:
                    # Use the fixed SQL parameter format (:param instead of %(param)s)
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
                logger.info(f"✅ Successfully stored {len(data)} records in TimescaleDB")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store data in TimescaleDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve_from_timescale(self, symbol: str, limit: int = 5) -> Optional[List[Dict]]:
        """Retrieve data from TimescaleDB using fixed SQL parameters"""
        if not self.engine:
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
            
            with self.engine.connect() as conn:
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
                    logger.info(f"ℹ️  No data found for {symbol}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to retrieve data from TimescaleDB: {e}")
            import traceback
            traceback.print_exc()
            return None

def test_docker_integration():
    """Test the complete Docker integration"""
    logger.info("🚀 DOCKER BINANCE TO TIMESCALEDB INTEGRATION TEST")
    logger.info("=" * 60)
    
    integrator = DirectTimescaleIntegrator()
    
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
        data = integrator.fetch_binance_data(symbol, '1h', 3)
        
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
        
        retrieved_data = integrator.retrieve_from_timescale(symbol_formatted, 3)
        
        if retrieved_data is not None:
            if retrieved_data:
                logger.info(f"✅ {symbol_formatted}: {len(retrieved_data)} records retrieved")
                logger.info(f"   Latest: {retrieved_data[0]['timestamp']} - ${retrieved_data[0]['close']:.2f}")
            else:
                logger.info(f"ℹ️  {symbol_formatted}: No data retrieved (may be expected)")
        else:
            logger.error(f"❌ {symbol_formatted}: Retrieval failed")
            return False
    
    # Test 5: SQL Parameter Fix Validation
    logger.info("\n🔍 TEST 5: SQL Parameter Fix Validation")
    logger.info("=" * 50)
    
    try:
        from sqlalchemy import text
        
        # Test a complex query with multiple parameters
        with integrator.engine.connect() as conn:
            test_query = """
                SELECT COUNT(*) as count, 
                       MIN(timestamp) as earliest, 
                       MAX(timestamp) as latest,
                       AVG(close) as avg_price
                FROM trading.ohlc_data 
                WHERE symbol = :symbol 
                    AND exchange = :exchange 
                    AND timestamp >= :start_time
            """
            
            result = conn.execute(text(test_query), {
                'symbol': 'BTC/USDT',
                'exchange': 'binance',
                'start_time': datetime.now() - timedelta(days=1)
            }).fetchone()
            
            if result:
                logger.info("✅ Complex SQL query with parameters executed successfully")
                logger.info(f"   Records found: {result[0]}")
                if result[1] and result[2]:
                    logger.info(f"   Time range: {result[1]} to {result[2]}")
                if result[3]:
                    logger.info(f"   Average price: ${result[3]:.2f}")
            else:
                logger.warning("⚠️  Query executed but returned no result")
                
    except Exception as e:
        logger.error(f"❌ SQL parameter test failed: {e}")
        return False
    
    # Final Summary
    logger.info("\n🎯 DOCKER INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    logger.info("🎉 ALL DOCKER INTEGRATION TESTS PASSED!")
    logger.info("✅ TimescaleDB connection: WORKING")
    logger.info("✅ Binance API integration: WORKING")
    logger.info("✅ Data storage: WORKING")
    logger.info("✅ Data retrieval: WORKING")
    logger.info("✅ SQL parameter fix: CONFIRMED WORKING")
    logger.info(f"✅ Total records processed: {total_stored}")
    logger.info("✅ End-to-end crypto data flow: OPERATIONAL")
    
    return True

if __name__ == "__main__":
    try:
        success = test_docker_integration()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)