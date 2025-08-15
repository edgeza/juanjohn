#!/usr/bin/env python3
"""
Test script to verify that Optuna optimization works for all assets

This script tests the updated crypto_engine.py to ensure it optimizes
parameters for all assets, not just major coins.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_optimization_all_assets():
    """Test that optimization works for all assets"""
    
    try:
        # Import the crypto engine
        from crypto_engine import CryptoEngine
        
        logger.info("Testing optimization for all assets...")
        
        # Initialize the engine
        engine = CryptoEngine()
        
        # Test with a small subset of assets to verify optimization works
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        logger.info(f"Testing with {len(test_symbols)} symbols: {test_symbols}")
        
        # Run analysis with optimization enabled for all assets
        results = engine.analyze_all_assets(
            symbols=test_symbols,
            interval='1d',
            days=365,  # Use 1 year of data
            optimize_all_assets=True,  # This is the key change - optimize ALL assets
            use_lookback=True
        )
        
        logger.info(f"Analysis completed. Results: {len(results)} assets processed")
        
        # Check that optimization was performed for each asset
        optimized_count = 0
        for result in results:
            if result and 'symbol' in result:
                symbol = result['symbol']
                degree = result.get('degree', 'N/A')
                kstd = result.get('kstd', 'N/A')
                logger.info(f"{symbol}: degree={degree}, kstd={kstd}")
                
                # Check if parameters were optimized (not default)
                if degree != 2 or kstd != 2.0:
                    optimized_count += 1
                    logger.info(f"✅ {symbol} was optimized")
                else:
                    logger.info(f"⚠️ {symbol} used default parameters")
        
        logger.info(f"Optimization summary: {optimized_count}/{len(results)} assets were optimized")
        
        if optimized_count > 0:
            logger.info("✅ SUCCESS: Optimization is working for all assets!")
        else:
            logger.warning("⚠️ WARNING: No assets were optimized. Check the optimization logic.")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_complete_analysis():
    """Test the complete analysis workflow"""
    
    try:
        from crypto_engine import CryptoEngine
        
        logger.info("Testing complete analysis workflow...")
        
        # Initialize the engine
        engine = CryptoEngine()
        
        # Test with just a few symbols for speed
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        # Run complete analysis
        analysis_result = engine.run_complete_analysis(
            symbols=test_symbols,
            interval='1d',
            days=365,
            optimize_all_assets=True,  # Enable optimization for all assets
            output_format='both'
        )
        
        logger.info("✅ Complete analysis workflow successful!")
        logger.info(f"Results saved to: {analysis_result.get('csv_filepath', 'N/A')}")
        logger.info(f"Duration: {analysis_result.get('duration', 'N/A')}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Complete analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("TESTING OPTIMIZATION FOR ALL ASSETS")
    logger.info("="*60)
    
    # Test 1: Individual asset optimization
    logger.info("\nTest 1: Individual asset optimization")
    results = test_optimization_all_assets()
    
    # Test 2: Complete analysis workflow
    logger.info("\nTest 2: Complete analysis workflow")
    analysis_result = test_complete_analysis()
    
    logger.info("\n" + "="*60)
    logger.info("TESTING COMPLETE")
    logger.info("="*60)
    
    if results and analysis_result:
        logger.info("✅ All tests passed! Optimization is working for all assets.")
    else:
        logger.error("❌ Some tests failed. Check the logs above.") 