#!/usr/bin/env python3
"""
VectorBTPro Local Analysis Runner

This script runs the VectorBTPro local analysis engine to generate results files
that can be ingested by the main system.

Usage:
    python run_vectorbt_analysis.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_vectorbt_analysis.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from vectorbt_local_engine import VectorBTLocalEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run VectorBTPro local analysis engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Analyze top 100 assets by volume')
    parser.add_argument('--optimize', action='store_true', help='Optimize parameters for major coins')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Get Binance API credentials
    api_key = config.get('binance_api_key') or os.getenv('BINANCE_API_KEY')
    api_secret = config.get('binance_api_secret') or os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("Error: Binance API credentials not found.")
        print("Please provide them in config.json or set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
        sys.exit(1)
    
    # Initialize engine
    binance_config = {
        'api_key': api_key,
        'api_secret': api_secret
    }
    
    engine = VectorBTLocalEngine(binance_config, args.output)
    
    # Determine symbols to analyze
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"Analyzing specified symbols: {symbols}")
    elif args.top_100:
        symbols = engine.get_top_100_assets()
        print(f"Analyzing top 100 assets by volume")
    else:
        # Default to core movers
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"Analyzing core movers: {symbols}")
    
    print(f"Starting VectorBTPro analysis...")
    print(f"Interval: {args.interval}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    print(f"Optimize major coins: {args.optimize}")
    print(f"Output format: {args.format}")
    
    # Run analysis
    start_time = datetime.now()
    results = engine.analyze_all_assets(
        symbols=symbols,
        interval=args.interval,
        days=args.days,
        optimize_major_coins=args.optimize
    )
    end_time = datetime.now()
    
    # Save results
    csv_filepath = ""
    json_filepath = ""
    
    if args.format in ['csv', 'both']:
        csv_filepath = engine.save_results_to_csv(results)
    
    if args.format in ['json', 'both']:
        json_filepath = engine.save_results_to_json(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"VECTORBTPRO ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Analysis duration: {end_time - start_time}")
    
    if csv_filepath:
        print(f"CSV results saved to: {csv_filepath}")
    if json_filepath:
        print(f"JSON results saved to: {json_filepath}")
    
    # Print analysis summary
    if results:
        buy_signals = [r for r in results if r.get('signal') == 'BUY']
        sell_signals = [r for r in results if r.get('signal') == 'SELL']
        hold_signals = [r for r in results if r.get('signal') == 'HOLD']
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"Total assets analyzed: {len(results)}")
        print(f"BUY signals: {len(buy_signals)}")
        print(f"SELL signals: {len(sell_signals)}")
        print(f"HOLD signals: {len(hold_signals)}")
        
        if results:
            avg_potential_return = sum([r.get('potential_return', 0) or 0 for r in results]) / len(results)
            avg_total_return = sum([r.get('total_return', 0) for r in results]) / len(results)
            print(f"Average potential return: {avg_potential_return:.2f}%")
            print(f"Average total return: {avg_total_return:.2f}%")
        
        # Show top signals
        if buy_signals:
            print(f"\n🔥 TOP BUY SIGNALS:")
            sorted_buy = sorted(buy_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)
            for i, signal in enumerate(sorted_buy[:5], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        if sell_signals:
            print(f"\n📉 TOP SELL SIGNALS:")
            sorted_sell = sorted(sell_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)
            for i, signal in enumerate(sorted_sell[:5], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
    
    print(f"\n✅ VectorBTPro analysis complete! Results ready for ingestion.")
    print(f"📁 Check the '{args.output}' directory for detailed results.")
    print(f"🗄️ Local database: {engine.db_path}")

if __name__ == "__main__":
    main() 
"""
VectorBTPro Local Analysis Runner

This script runs the VectorBTPro local analysis engine to generate results files
that can be ingested by the main system.

Usage:
    python run_vectorbt_analysis.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_vectorbt_analysis.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from vectorbt_local_engine import VectorBTLocalEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run VectorBTPro local analysis engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Analyze top 100 assets by volume')
    parser.add_argument('--optimize', action='store_true', help='Optimize parameters for major coins')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Get Binance API credentials
    api_key = config.get('binance_api_key') or os.getenv('BINANCE_API_KEY')
    api_secret = config.get('binance_api_secret') or os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("Error: Binance API credentials not found.")
        print("Please provide them in config.json or set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
        sys.exit(1)
    
    # Initialize engine
    binance_config = {
        'api_key': api_key,
        'api_secret': api_secret
    }
    
    engine = VectorBTLocalEngine(binance_config, args.output)
    
    # Determine symbols to analyze
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"Analyzing specified symbols: {symbols}")
    elif args.top_100:
        symbols = engine.get_top_100_assets()
        print(f"Analyzing top 100 assets by volume")
    else:
        # Default to core movers
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"Analyzing core movers: {symbols}")
    
    print(f"Starting VectorBTPro analysis...")
    print(f"Interval: {args.interval}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    print(f"Optimize major coins: {args.optimize}")
    print(f"Output format: {args.format}")
    
    # Run analysis
    start_time = datetime.now()
    results = engine.analyze_all_assets(
        symbols=symbols,
        interval=args.interval,
        days=args.days,
        optimize_major_coins=args.optimize
    )
    end_time = datetime.now()
    
    # Save results
    csv_filepath = ""
    json_filepath = ""
    
    if args.format in ['csv', 'both']:
        csv_filepath = engine.save_results_to_csv(results)
    
    if args.format in ['json', 'both']:
        json_filepath = engine.save_results_to_json(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"VECTORBTPRO ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Analysis duration: {end_time - start_time}")
    
    if csv_filepath:
        print(f"CSV results saved to: {csv_filepath}")
    if json_filepath:
        print(f"JSON results saved to: {json_filepath}")
    
    # Print analysis summary
    if results:
        buy_signals = [r for r in results if r.get('signal') == 'BUY']
        sell_signals = [r for r in results if r.get('signal') == 'SELL']
        hold_signals = [r for r in results if r.get('signal') == 'HOLD']
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"Total assets analyzed: {len(results)}")
        print(f"BUY signals: {len(buy_signals)}")
        print(f"SELL signals: {len(sell_signals)}")
        print(f"HOLD signals: {len(hold_signals)}")
        
        if results:
            avg_potential_return = sum([r.get('potential_return', 0) or 0 for r in results]) / len(results)
            avg_total_return = sum([r.get('total_return', 0) for r in results]) / len(results)
            print(f"Average potential return: {avg_potential_return:.2f}%")
            print(f"Average total return: {avg_total_return:.2f}%")
        
        # Show top signals
        if buy_signals:
            print(f"\n🔥 TOP BUY SIGNALS:")
            sorted_buy = sorted(buy_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)
            for i, signal in enumerate(sorted_buy[:5], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        if sell_signals:
            print(f"\n📉 TOP SELL SIGNALS:")
            sorted_sell = sorted(sell_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)
            for i, signal in enumerate(sorted_sell[:5], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
    
    print(f"\n✅ VectorBTPro analysis complete! Results ready for ingestion.")
    print(f"📁 Check the '{args.output}' directory for detailed results.")
    print(f"🗄️ Local database: {engine.db_path}")

if __name__ == "__main__":
    main() 
 