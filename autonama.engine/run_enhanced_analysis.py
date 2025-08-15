#!/usr/bin/env python3
"""
Enhanced Local Analysis Runner

This script runs the comprehensive local analysis engine to generate all analytics
and results that can be ingested by the main system.

Usage:
    python run_enhanced_analysis.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_enhanced_analysis.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from enhanced_local_engine import EnhancedLocalEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run enhanced local analysis engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--degree', type=int, default=4, help='Polynomial degree (default: 4)')
    parser.add_argument('--kstd', type=float, default=2.0, help='Standard deviation multiplier (default: 2.0)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Analyze top 100 assets by volume')
    parser.add_argument('--generate-charts', action='store_true', help='Generate analysis charts')
    parser.add_argument('--correlation-analysis', action='store_true', help='Include cross-correlation analysis')
    
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
    
    engine = EnhancedLocalEngine(binance_config, args.output)
    
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
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        print(f"Analyzing core movers: {symbols}")
    
    print(f"Starting enhanced analysis...")
    print(f"Interval: {args.interval}")
    print(f"Degree: {args.degree}")
    print(f"K-std: {args.kstd}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    print(f"Generate charts: {args.generate_charts}")
    print(f"Correlation analysis: {args.correlation_analysis}")
    
    # Run comprehensive analysis
    start_time = datetime.now()
    results = engine.analyze_all_assets(
        symbols=symbols,
        interval=args.interval,
        degree=args.degree,
        kstd=args.kstd,
        days=args.days
    )
    end_time = datetime.now()
    
    # Save results
    filepath = engine.save_results(results)
    
    # Generate charts if requested
    if args.generate_charts:
        print("Generating analysis charts...")
        engine.generate_charts(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ENHANCED ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Analysis duration: {end_time - start_time}")
    print(f"Results saved to: {filepath}")
    
    if 'summary' in results:
        summary = results['summary']
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"Total assets analyzed: {summary['total_assets_analyzed']}")
        print(f"BUY signals: {summary['buy_signals']}")
        print(f"SELL signals: {summary['sell_signals']}")
        print(f"HOLD signals: {summary['hold_signals']}")
        print(f"Average potential return: {summary['avg_potential_return']:.2f}%")
        print(f"High-risk assets: {summary['high_risk_assets']}")
    
    if 'top_buy_signals' in results and results['top_buy_signals']:
        print(f"\n🔥 TOP BUY SIGNALS:")
        for i, signal in enumerate(results['top_buy_signals'][:5], 1):
            symbol = signal['symbol']
            potential_return = signal['signal_analysis']['potential_return']
            risk_level = signal['signal_analysis']['risk_level']
            print(f"{i}. {symbol}: {potential_return:.2f}% return ({risk_level} risk)")
    
    if 'top_sell_signals' in results and results['top_sell_signals']:
        print(f"\n📉 TOP SELL SIGNALS:")
        for i, signal in enumerate(results['top_sell_signals'][:5], 1):
            symbol = signal['symbol']
            potential_return = signal['signal_analysis']['potential_return']
            risk_level = signal['signal_analysis']['risk_level']
            print(f"{i}. {symbol}: {potential_return:.2f}% return ({risk_level} risk)")
    
    if 'correlation_analysis' in results and results['correlation_analysis']:
        corr_analysis = results['correlation_analysis']
        if 'high_correlation_pairs' in corr_analysis:
            print(f"\n🔗 HIGH CORRELATION PAIRS:")
            for i, pair in enumerate(corr_analysis['high_correlation_pairs'][:5], 1):
                symbols = pair['pair']
                correlation = pair['correlation']
                print(f"{i}. {symbols[0]} ↔ {symbols[1]}: {correlation:.3f}")
    
    print(f"\n✅ Analysis complete! Results ready for ingestion.")
    print(f"📁 Check the '{args.output}' directory for detailed results and charts.")

if __name__ == "__main__":
    main() 
 
"""
Enhanced Local Analysis Runner

This script runs the comprehensive local analysis engine to generate all analytics
and results that can be ingested by the main system.

Usage:
    python run_enhanced_analysis.py [--config config.json] [--output results/] [--symbols BTCUSDT,ETHUSDT]

Example:
    python run_enhanced_analysis.py --config config.json --output results/ --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from enhanced_local_engine import EnhancedLocalEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Run enhanced local analysis engine')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', default='results', help='Output directory for results')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--degree', type=int, default=4, help='Polynomial degree (default: 4)')
    parser.add_argument('--kstd', type=float, default=2.0, help='Standard deviation multiplier (default: 2.0)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--top-100', action='store_true', help='Analyze top 100 assets by volume')
    parser.add_argument('--generate-charts', action='store_true', help='Generate analysis charts')
    parser.add_argument('--correlation-analysis', action='store_true', help='Include cross-correlation analysis')
    
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
    
    engine = EnhancedLocalEngine(binance_config, args.output)
    
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
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        print(f"Analyzing core movers: {symbols}")
    
    print(f"Starting enhanced analysis...")
    print(f"Interval: {args.interval}")
    print(f"Degree: {args.degree}")
    print(f"K-std: {args.kstd}")
    print(f"Days: {args.days}")
    print(f"Output directory: {args.output}")
    print(f"Generate charts: {args.generate_charts}")
    print(f"Correlation analysis: {args.correlation_analysis}")
    
    # Run comprehensive analysis
    start_time = datetime.now()
    results = engine.analyze_all_assets(
        symbols=symbols,
        interval=args.interval,
        degree=args.degree,
        kstd=args.kstd,
        days=args.days
    )
    end_time = datetime.now()
    
    # Save results
    filepath = engine.save_results(results)
    
    # Generate charts if requested
    if args.generate_charts:
        print("Generating analysis charts...")
        engine.generate_charts(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ENHANCED ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Analysis duration: {end_time - start_time}")
    print(f"Results saved to: {filepath}")
    
    if 'summary' in results:
        summary = results['summary']
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"Total assets analyzed: {summary['total_assets_analyzed']}")
        print(f"BUY signals: {summary['buy_signals']}")
        print(f"SELL signals: {summary['sell_signals']}")
        print(f"HOLD signals: {summary['hold_signals']}")
        print(f"Average potential return: {summary['avg_potential_return']:.2f}%")
        print(f"High-risk assets: {summary['high_risk_assets']}")
    
    if 'top_buy_signals' in results and results['top_buy_signals']:
        print(f"\n🔥 TOP BUY SIGNALS:")
        for i, signal in enumerate(results['top_buy_signals'][:5], 1):
            symbol = signal['symbol']
            potential_return = signal['signal_analysis']['potential_return']
            risk_level = signal['signal_analysis']['risk_level']
            print(f"{i}. {symbol}: {potential_return:.2f}% return ({risk_level} risk)")
    
    if 'top_sell_signals' in results and results['top_sell_signals']:
        print(f"\n📉 TOP SELL SIGNALS:")
        for i, signal in enumerate(results['top_sell_signals'][:5], 1):
            symbol = signal['symbol']
            potential_return = signal['signal_analysis']['potential_return']
            risk_level = signal['signal_analysis']['risk_level']
            print(f"{i}. {symbol}: {potential_return:.2f}% return ({risk_level} risk)")
    
    if 'correlation_analysis' in results and results['correlation_analysis']:
        corr_analysis = results['correlation_analysis']
        if 'high_correlation_pairs' in corr_analysis:
            print(f"\n🔗 HIGH CORRELATION PAIRS:")
            for i, pair in enumerate(corr_analysis['high_correlation_pairs'][:5], 1):
                symbols = pair['pair']
                correlation = pair['correlation']
                print(f"{i}. {symbols[0]} ↔ {symbols[1]}: {correlation:.3f}")
    
    print(f"\n✅ Analysis complete! Results ready for ingestion.")
    print(f"📁 Check the '{args.output}' directory for detailed results and charts.")

if __name__ == "__main__":
    main() 
 
 