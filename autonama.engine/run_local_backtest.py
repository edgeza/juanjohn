#!/usr/bin/env python3
"""
Local Backtesting Engine Runner

This script runs the local backtesting engine to generate results files
that can be ingested by the main system.

Usage:
    python run_local_backtest.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_local_backtest.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from local_backtest_engine import LocalBacktestEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run local backtesting engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to scan')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--degree', type=int, default=4, help='Polynomial degree (default: 4)')
    parser.add_argument('--kstd', type=float, default=2.0, help='Standard deviation multiplier (default: 2.0)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Scan top 100 assets by volume')
    
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
    
    engine = LocalBacktestEngine(binance_config, args.output)
    
    # Determine symbols to scan
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"Scanning specified symbols: {symbols}")
    elif args.top_100:
        symbols = engine.get_top_100_assets()
        print(f"Scanning top 100 assets by volume")
    else:
        # Default to core movers
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"Scanning core movers: {symbols}")
    
    print(f"Starting backtest scan...")
    print(f"Interval: {args.interval}")
    print(f"Degree: {args.degree}")
    print(f"K-std: {args.kstd}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    
    # Run scan
    start_time = datetime.now()
    results = engine.scan_all_assets(
        symbols=symbols,
        interval=args.interval,
        degree=args.degree,
        kstd=args.kstd,
        days=args.days
    )
    end_time = datetime.now()
    
    # Save results
    filepath = engine.save_results(results)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"BACKTEST SCAN COMPLETE")
    print(f"{'='*50}")
    print(f"Duration: {end_time - start_time}")
    print(f"Total assets scanned: {len(results)}")
    print(f"BUY signals: {len([r for r in results if r['signal'] == 'BUY'])}")
    print(f"SELL signals: {len([r for r in results if r['signal'] == 'SELL'])}")
    print(f"HOLD signals: {len([r for r in results if r['signal'] == 'HOLD'])}")
    
    if filepath:
        print(f"Results saved to: {filepath}")
    
    # Show top BUY signals
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    if buy_signals:
        print(f"\nTop BUY signals:")
        for i, signal in enumerate(buy_signals[:10], 1):
            print(f"{i:2d}. {signal['symbol']:12s} - {signal['potential_return']:6.2f}% potential return")
    
    # Show top SELL signals
    sell_signals = [r for r in results if r['signal'] == 'SELL']
    sell_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    if sell_signals:
        print(f"\nTop SELL signals:")
        for i, signal in enumerate(sell_signals[:10], 1):
            print(f"{i:2d}. {signal['symbol']:12s} - {signal['potential_return']:6.2f}% potential return")
    
    print(f"\n{'='*50}")
    print(f"Next steps:")
    print(f"1. The results file can be ingested into the database using:")
    print(f"   docker-compose exec celery_worker python -c \"from tasks.backtest_ingestion import ingest_backtest_results; result = ingest_backtest_results.delay('{filepath}'); print('Ingestion task submitted:', result.id)\"")
    print(f"2. Or monitor the results directory automatically:")
    print(f"   docker-compose exec celery_worker python -c \"from tasks.backtest_ingestion import monitor_backtest_results_directory; result = monitor_backtest_results_directory.delay('{os.path.abspath(args.output)}'); print('Monitoring task submitted:', result.id)\"")
    print(f"{'='*50}")

if __name__ == "__main__":
    main() 
"""
Local Backtesting Engine Runner

This script runs the local backtesting engine to generate results files
that can be ingested by the main system.

Usage:
    python run_local_backtest.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_local_backtest.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from local_backtest_engine import LocalBacktestEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run local backtesting engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to scan')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--degree', type=int, default=4, help='Polynomial degree (default: 4)')
    parser.add_argument('--kstd', type=float, default=2.0, help='Standard deviation multiplier (default: 2.0)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Scan top 100 assets by volume')
    
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
    
    engine = LocalBacktestEngine(binance_config, args.output)
    
    # Determine symbols to scan
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"Scanning specified symbols: {symbols}")
    elif args.top_100:
        symbols = engine.get_top_100_assets()
        print(f"Scanning top 100 assets by volume")
    else:
        # Default to core movers
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"Scanning core movers: {symbols}")
    
    print(f"Starting backtest scan...")
    print(f"Interval: {args.interval}")
    print(f"Degree: {args.degree}")
    print(f"K-std: {args.kstd}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    
    # Run scan
    start_time = datetime.now()
    results = engine.scan_all_assets(
        symbols=symbols,
        interval=args.interval,
        degree=args.degree,
        kstd=args.kstd,
        days=args.days
    )
    end_time = datetime.now()
    
    # Save results
    filepath = engine.save_results(results)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"BACKTEST SCAN COMPLETE")
    print(f"{'='*50}")
    print(f"Duration: {end_time - start_time}")
    print(f"Total assets scanned: {len(results)}")
    print(f"BUY signals: {len([r for r in results if r['signal'] == 'BUY'])}")
    print(f"SELL signals: {len([r for r in results if r['signal'] == 'SELL'])}")
    print(f"HOLD signals: {len([r for r in results if r['signal'] == 'HOLD'])}")
    
    if filepath:
        print(f"Results saved to: {filepath}")
    
    # Show top BUY signals
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    if buy_signals:
        print(f"\nTop BUY signals:")
        for i, signal in enumerate(buy_signals[:10], 1):
            print(f"{i:2d}. {signal['symbol']:12s} - {signal['potential_return']:6.2f}% potential return")
    
    # Show top SELL signals
    sell_signals = [r for r in results if r['signal'] == 'SELL']
    sell_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    if sell_signals:
        print(f"\nTop SELL signals:")
        for i, signal in enumerate(sell_signals[:10], 1):
            print(f"{i:2d}. {signal['symbol']:12s} - {signal['potential_return']:6.2f}% potential return")
    
    print(f"\n{'='*50}")
    print(f"Next steps:")
    print(f"1. The results file can be ingested into the database using:")
    print(f"   docker-compose exec celery_worker python -c \"from tasks.backtest_ingestion import ingest_backtest_results; result = ingest_backtest_results.delay('{filepath}'); print('Ingestion task submitted:', result.id)\"")
    print(f"2. Or monitor the results directory automatically:")
    print(f"   docker-compose exec celery_worker python -c \"from tasks.backtest_ingestion import monitor_backtest_results_directory; result = monitor_backtest_results_directory.delay('{os.path.abspath(args.output)}'); print('Monitoring task submitted:', result.id)\"")
    print(f"{'='*50}")

if __name__ == "__main__":
    main() 
 