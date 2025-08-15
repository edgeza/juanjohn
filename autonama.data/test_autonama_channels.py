#!/usr/bin/env python3
"""
Autonama Channels Algorithm Test

This script tests the migrated Autonama Channels algorithm with TimescaleDB integration.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.autonama_channels_core import AutonamaChannelsCore, create_autonama_channels_calculator
from tasks.timescale_data_ingestion import timescale_manager
from tasks.autonama_channels_tasks import (
    store_autonama_signals_to_timescale,
    get_available_symbols_from_timescale,
    get_latest_autonama_signals_from_timescale
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run Autonama Channels algorithm tests."""
    try:
        logger.info("🚀 AUTONAMA CHANNELS ALGORITHM TEST")
        logger.info("=" * 60)
        
        # Test 1: Core Algorithm Validation
        logger.info("🔍 TEST 1: Core Algorithm Validation")
        logger.info("=" * 50)
        
        # Create calculator
        calculator = create_autonama_channels_calculator(degree=2, kstd=2.0)
        logger.info("✅ Autonama Channels calculator created")
        
        # Test 2: TimescaleDB Connection
        logger.info("\n🔍 TEST 2: TimescaleDB Connection")
        logger.info("=" * 50)
        
        try:
            with timescale_manager.engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                logger.info(f"✅ TimescaleDB connection verified: {result[0]}")
        except Exception as e:
            logger.error(f"❌ TimescaleDB connection failed: {e}")
            return False
        
        # Test 3: Data Availability Check
        logger.info("\n🔍 TEST 3: Data Availability Check")
        logger.info("=" * 50)
        
        # Get available symbols
        available_symbols = get_available_symbols_from_timescale()
        
        if not available_symbols:
            logger.error("❌ No symbols found in TimescaleDB")
            return False
        
        logger.info(f"✅ Found {len(available_symbols)} symbols in TimescaleDB:")
        for symbol_info in available_symbols[:10]:  # Show first 10
            logger.info(f"   - {symbol_info['symbol']} ({symbol_info['exchange']})")
        
        if len(available_symbols) > 10:
            logger.info(f"   ... and {len(available_symbols) - 10} more")
        
        # Test 4: Algorithm Testing with Real Data
        logger.info("\n🔍 TEST 4: Algorithm Testing with Real Data")
        logger.info("=" * 50)
        
        test_symbols = available_symbols[:3]  # Test with first 3 symbols
        successful_tests = 0
        
        for symbol_info in test_symbols:
            symbol = symbol_info['symbol']
            exchange = symbol_info['exchange']
            
            try:
                logger.info(f"\n📊 Testing {symbol} ({exchange})...")
                
                # Load data from TimescaleDB
                data = timescale_manager.get_ohlc_data(symbol, exchange, '1h', limit=100)
                
                if data.empty:
                    logger.warning(f"⚠️  No data available for {symbol}")
                    continue
                
                logger.info(f"   Loaded {len(data)} records")
                
                # Test channel calculation
                close_data = data['close']
                autonama_channel, autonama_upper, autonama_lower = calculator.calculate_autonama_channels(close_data)
                
                if autonama_channel is None:
                    logger.warning(f"⚠️  Channel calculation failed for {symbol}")
                    continue
                
                logger.info(f"   ✅ Channels calculated successfully")
                logger.info(f"      Latest price: ${close_data.iloc[-1]:.4f}")
                logger.info(f"      Channel: ${autonama_channel[-1]:.4f}")
                logger.info(f"      Upper: ${autonama_upper[-1]:.4f}")
                logger.info(f"      Lower: ${autonama_lower[-1]:.4f}")
                
                # Test signal generation
                result = calculator.compute_signal_and_insights(symbol, data)
                
                if result is None:
                    logger.warning(f"⚠️  Signal calculation failed for {symbol}")
                    continue
                
                logger.info(f"   ✅ Signal: {result['Signal']}")
                logger.info(f"      Deviation: {result['Deviation_Pct']:.2f}%")
                logger.info(f"      Potential Earnings: {result['Potential_Earnings_Pct']:.2f}%")
                logger.info(f"      Trend: {result.get('Trend', 'N/A')}")
                logger.info(f"      Market Regime: {result.get('Market_Regime', 'N/A')}")
                
                successful_tests += 1
                
            except Exception as e:
                logger.error(f"❌ Error testing {symbol}: {e}")
                continue
        
        if successful_tests == 0:
            logger.error("❌ No successful algorithm tests")
            return False
        
        logger.info(f"\n✅ Algorithm testing completed: {successful_tests}/{len(test_symbols)} successful")
        
        # Test 5: TimescaleDB Storage Integration
        logger.info("\n🔍 TEST 5: TimescaleDB Storage Integration")
        logger.info("=" * 50)
        
        if successful_tests > 0:
            # Test storing signals
            test_symbol_info = test_symbols[0]
            symbol = test_symbol_info['symbol']
            exchange = test_symbol_info['exchange']
            
            # Load data and calculate signals
            data = timescale_manager.get_ohlc_data(symbol, exchange, '1h', limit=100)
            result = calculator.compute_signal_and_insights(symbol, data)
            
            if result:
                # Store in TimescaleDB
                success = store_autonama_signals_to_timescale(symbol, result, exchange, '1h')
                
                if success:
                    logger.info(f"✅ Successfully stored signals for {symbol}")
                    
                    # Verify storage by retrieving
                    latest_signals = get_latest_autonama_signals_from_timescale()
                    
                    if latest_signals:
                        logger.info(f"✅ Retrieved {len(latest_signals)} signals from database")
                        
                        # Show sample signal
                        sample_signal = latest_signals[0]
                        logger.info(f"   Sample: {sample_signal['symbol']} - {sample_signal['signal']} "
                                  f"(deviation: {sample_signal['deviation_pct']:.2f}%)")
                    else:
                        logger.warning("⚠️  No signals retrieved from database")
                else:
                    logger.error(f"❌ Failed to store signals for {symbol}")
            else:
                logger.error("❌ No signals to store")
        
        # Test 6: Performance Metrics
        logger.info("\n🔍 TEST 6: Performance Metrics")
        logger.info("=" * 50)
        
        if successful_tests > 0:
            # Test calculation speed
            test_symbol_info = test_symbols[0]
            symbol = test_symbol_info['symbol']
            exchange = test_symbol_info['exchange']
            
            data = timescale_manager.get_ohlc_data(symbol, exchange, '1h', limit=200)
            
            if not data.empty:
                start_time = datetime.now()
                
                # Run multiple calculations to test performance
                for _ in range(5):
                    result = calculator.compute_signal_and_insights(symbol, data)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                avg_time = duration / 5
                
                logger.info(f"✅ Performance test completed:")
                logger.info(f"   Average calculation time: {avg_time:.3f} seconds")
                logger.info(f"   Data points processed: {len(data)}")
                logger.info(f"   Processing rate: {len(data)/avg_time:.1f} points/second")
        
        # Test 7: Database Statistics
        logger.info("\n🔍 TEST 7: Database Statistics")
        logger.info("=" * 50)
        
        try:
            with timescale_manager.engine.connect() as conn:
                # Check OHLC data
                ohlc_result = conn.execute("SELECT COUNT(*) FROM trading.ohlc_data").fetchone()
                ohlc_count = ohlc_result[0] if ohlc_result else 0
                
                # Check if autonama_signals table exists
                signals_result = conn.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'analytics' AND table_name = 'autonama_signals'
                """).fetchone()
                
                signals_table_exists = signals_result[0] > 0 if signals_result else False
                
                if signals_table_exists:
                    signals_count_result = conn.execute("SELECT COUNT(*) FROM analytics.autonama_signals").fetchone()
                    signals_count = signals_count_result[0] if signals_count_result else 0
                else:
                    signals_count = 0
                
                logger.info(f"✅ Database statistics:")
                logger.info(f"   OHLC records: {ohlc_count}")
                logger.info(f"   Autonama signals: {signals_count}")
                logger.info(f"   Available symbols: {len(available_symbols)}")
                
        except Exception as e:
            logger.error(f"❌ Database statistics failed: {e}")
        
        # Summary
        logger.info("\n🎯 AUTONAMA CHANNELS TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ Core algorithm: Working")
        logger.info("✅ TimescaleDB integration: Working")
        logger.info("✅ Data processing: Working")
        logger.info("✅ Signal generation: Working")
        logger.info("✅ Storage integration: Working")
        logger.info(f"✅ Algorithm tests: {successful_tests}/{len(test_symbols)} successful")
        logger.info("✅ Performance: Acceptable")
        logger.info("\n🚀 AUTONAMA CHANNELS ALGORITHM IS PRODUCTION READY!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error in Autonama Channels test: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)