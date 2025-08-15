#!/usr/bin/env python3
"""
Full Analysis Runner for Crypto Engine

This script runs comprehensive analysis on all 100 top assets by volume
with maximum available data and stores results for backtesting.
"""

import os
import sys
import json
from datetime import datetime
from crypto_engine import CryptoEngine

def main():
    """Run full analysis on all top assets"""
    print("Crypto Engine - Full Analysis Runner")
    print("="*60)
    
    try:
        # Initialize engine
        print("Initializing Crypto Engine...")
        engine = CryptoEngine("config.json")
        
        # Get top 100 assets
        print("Fetching top 100 assets by volume...")
        symbols = engine.get_top_100_assets()
        print(f"Found {len(symbols)} top assets")
        print(f"Sample symbols: {symbols[:10]}")
        
        # Update all data first
        print("\nUpdating all data in database...")
        print("This ensures we have the latest data before analysis")
        update_success = engine.update_all_data(symbols, '1d', 1000)
        
        if not update_success:
            print("Some data updates failed, but continuing with analysis...")
        
        # Run comprehensive analysis
        print("\nStarting comprehensive analysis...")
        print("Parameters:")
        print("   - Timeframe: 1d (daily)")
        print("   - Data: Maximum available (up to 1000 days)")
        print("   - Assets: All 100 top assets by volume")
        print("   - Optimization: Enabled for major coins")
        print("   - Lookback Mode: Enabled (uses last X candles)")
        print("   - Storage: Local SQLite database")
        
        # Run analysis with lookback mode
        results = engine.analyze_all_assets(
            symbols=symbols,
            interval='1d',
            days=1000,  # Maximum data
            optimize_major_coins=True,
            use_lookback=True  # Use lookback mode
        )
        
        if results:
            print(f"\nAnalysis complete!")
            print(f"Results: {len(results)} successful analyses")
            
            # Generate summary
            summary = engine.get_analysis_summary(results)
            print(f"\nSummary:")
            print(f"   - Total assets: {summary['total_assets']}")
            print(f"   - BUY signals: {summary['buy_signals']}")
            print(f"   - SELL signals: {summary['sell_signals']}")
            print(f"   - HOLD signals: {summary['hold_signals']}")
            print(f"   - Avg potential return: {summary['avg_potential_return']:.2f}%")
            print(f"   - Avg total return: {summary['avg_total_return']:.2f}%")
            
            # Export results
            print(f"\nExporting results...")
            csv_file = engine.save_results_to_csv(results, "full_analysis_results.csv")
            json_file = engine.save_results_to_json(results, "full_analysis_results.json")
            
            print(f"CSV export: {csv_file}")
            print(f"JSON export: {json_file}")
            
            # Show top performers
            print(f"\nTop Performers (by potential return):")
            sorted_results = sorted(results, key=lambda x: x['potential_return'], reverse=True)
            for i, result in enumerate(sorted_results[:10]):
                print(f"   {i+1:2d}. {result['symbol']:10s} - {result['signal']:4s} - {result['potential_return']:6.2f}% potential")
            
            # Show signal distribution
            print(f"\nSignal Distribution:")
            buy_count = len([r for r in results if r['signal'] == 'BUY'])
            sell_count = len([r for r in results if r['signal'] == 'SELL'])
            hold_count = len([r for r in results if r['signal'] == 'HOLD'])
            
            print(f"   - BUY:  {buy_count:3d} ({buy_count/len(results)*100:5.1f}%)")
            print(f"   - SELL: {sell_count:3d} ({sell_count/len(results)*100:5.1f}%)")
            print(f"   - HOLD: {hold_count:3d} ({hold_count/len(results)*100:5.1f}%)")
            
            # Show data usage statistics
            print(f"\nData Usage Statistics:")
            avg_data_points = sum(r.get('data_points', 0) for r in results) / len(results)
            avg_total_available = sum(r.get('total_available', 0) for r in results) / len(results)
            print(f"   - Average data points used: {avg_data_points:.0f}")
            print(f"   - Average total available: {avg_total_available:.0f}")
            print(f"   - Lookback efficiency: {(avg_data_points/avg_total_available)*100:.1f}%")
            
            print(f"\nAnalysis complete! Results saved to database and exported files.")
            print(f"Next steps:")
            print(f"   1. View results in Streamlit dashboard: python run_dashboard.py")
            print(f"   2. Check database for stored data: {engine.db_path}")
            print(f"   3. Review exported files for further analysis")
            
            return True
            
        else:
            print("No results returned from analysis")
            return False
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 