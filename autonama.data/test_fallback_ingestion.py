#!/usr/bin/env python3
"""
Test script for the fallback data ingestion functionality.

This script tests the basic data fetching without requiring the full DuckDBDataProcessor.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_fallback_crypto_update():
    """Test the fallback crypto data update"""
    try:
        from tasks.data_ingestion import update_crypto_data_basic
        
        print("Testing fallback crypto data update...")
        stats = update_crypto_data_basic(force_update=False)
        
        print(f"✅ Fallback crypto update completed:")
        print(f"   Success: {stats.get('success', 0)}")
        print(f"   Failed: {stats.get('failed', 0)}")
        print(f"   Skipped: {stats.get('skipped', 0)}")
        print(f"   Message: {stats.get('message', 'N/A')}")
        
        return stats.get('success', 0) > 0
        
    except Exception as e:
        print(f"❌ Error testing fallback crypto update: {e}")
        return False

def test_fallback_category_update():
    """Test the fallback category update function"""
    try:
        from tasks.data_ingestion import update_category_data_fallback
        
        print("\nTesting fallback category updates...")
        
        categories = ["crypto", "forex", "stock", "commodity"]
        results = {}
        
        for category in categories:
            print(f"\nTesting {category.upper()}...")
            stats = update_category_data_fallback(category, force_update=False)
            results[category] = stats
            
            success = stats.get("success", 0)
            failed = stats.get("failed", 0)
            skipped = stats.get("skipped", 0)
            message = stats.get("message", "N/A")
            
            print(f"   Results: {success} success, {failed} failed, {skipped} skipped")
            print(f"   Message: {message}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing fallback category updates: {e}")
        return {}

def test_ccxt_connection():
    """Test basic CCXT connection"""
    try:
        import ccxt
        
        print("\nTesting CCXT Binance connection...")
        
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Test basic connection
        markets = exchange.load_markets()
        print(f"✅ Connected to Binance. Found {len(markets)} markets")
        
        # Test fetching OHLCV data
        symbol = 'BTC/USDT'
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=5)
        print(f"✅ Fetched {len(ohlcv)} OHLCV records for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CCXT connection: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("FALLBACK DATA INGESTION TEST")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Test CCXT connection first
    if not test_ccxt_connection():
        print("❌ CCXT connection test failed. Cannot proceed with data tests.")
        return 1
    
    # Test fallback crypto update
    if not test_fallback_crypto_update():
        print("❌ Fallback crypto update test failed.")
        return 1
    
    # Test fallback category updates
    results = test_fallback_category_update()
    if not results:
        print("❌ Fallback category update tests failed.")
        return 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_success = sum(stats.get("success", 0) for stats in results.values())
    total_failed = sum(stats.get("failed", 0) for stats in results.values())
    total_skipped = sum(stats.get("skipped", 0) for stats in results.values())
    
    print(f"Total Success: {total_success}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Skipped: {total_skipped}")
    
    if total_success > 0:
        print("\n✅ Fallback data ingestion is working!")
        print("The Celery tasks should now run without DuckDBDataProcessor initialization errors.")
        return 0
    else:
        print("\n⚠️  Fallback tests completed but no successful data updates.")
        print("This may be normal if API keys are not configured or rate limits are hit.")
        return 0

if __name__ == "__main__":
    exit(main())
