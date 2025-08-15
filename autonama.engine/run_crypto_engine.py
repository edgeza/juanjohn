
#!/usr/bin/env python3
"""
Crypto Engine Runner

Simple script to test and run the crypto engine with VectorBTPro.

Usage:
    python run_crypto_engine.py [--config config.json] [--symbols BTCUSDT,ETHUSDT] [--test]

Example:
    python run_crypto_engine.py --config config.json --test
    python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from crypto_engine import CryptoEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def test_engine_setup():
    """Test if the engine can be initialized and basic functionality works"""
    print("🧪 Testing Crypto Engine Setup...")
    
    try:
        # Test imports
        import vectorbtpro as vbt
        print(f"✅ VectorBTPro detected: {vbt.__version__}")
        
        import optuna
        print(f"✅ Optuna detected: {optuna.__version__}")
        
        from binance.client import Client
        print("✅ Binance client imported successfully")
        
        # Test config loading
        config = load_config("config.json")
        if config.get('binance_api_key') and config.get('binance_api_secret'):
            print("✅ Configuration loaded successfully")
        else:
            print("⚠️  Configuration missing API credentials")
            return False
        
        # Test engine initialization
        engine = CryptoEngine("config.json")
        print("✅ Crypto Engine initialized successfully")
        
        # Test database connection
        import sqlite3
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database initialized with {len(tables)} tables")
        conn.close()
        
        # Test top 100 assets retrieval
        top_100 = engine.get_top_100_assets()
        print(f"✅ Retrieved {len(top_100)} top assets")
        
        print("✅ All tests passed! Engine is ready for analysis.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run Crypto Engine Analysis')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--test', action='store_true', help='Run engine tests only')
    parser.add_argument('--optimize', action='store_true', help='Optimize parameters for major coins')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        success = test_engine_setup()
        sys.exit(0 if success else 1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Check API credentials
    api_key = config.get('binance_api_key')
    api_secret = config.get('binance_api_secret')
    
    if not api_key or not api_secret:
        print("❌ Error: Binance API credentials not found in config.json")
        print("Please update config.json with your Binance API credentials.")
        sys.exit(1)
    
    # Initialize engine
    print("🚀 Initializing Crypto Engine...")
    engine = CryptoEngine(args.config)
    
    # Determine symbols to analyze
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"📊 Analyzing specified symbols: {symbols}")
    else:
        # Use core symbols for quick test
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"📊 Analyzing core symbols: {symbols}")
    
    print(f"⏰ Interval: {args.interval}")
    print(f"📅 Days: {args.days}")
    print(f"🔧 Optimize major coins: {args.optimize}")
    print(f"📁 Output format: {args.format}")
    
    # Run analysis
    print("\n" + "="*60)
    print("🚀 STARTING CRYPTO ANALYSIS")
    print("="*60)
    
    start_time = datetime.now()
    
    try:
        analysis_result = engine.run_complete_analysis(
            symbols=symbols,
            interval=args.interval,
            days=args.days,
            optimize_major_coins=args.optimize,
            output_format=args.format
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print detailed results
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        
        summary = analysis_result['summary']
        print(f"Total assets analyzed: {summary['total_assets']}")
        print(f"BUY signals: {summary['buy_signals']}")
        print(f"SELL signals: {summary['sell_signals']}")
        print(f"HOLD signals: {summary['hold_signals']}")
        print(f"Average potential return: {summary['avg_potential_return']:.2f}%")
        print(f"Average total return: {summary['avg_total_return']:.2f}%")
        print(f"Analysis duration: {duration}")
        
        # Show top signals
        if summary['top_buy_signals']:
            print(f"\n🔥 TOP BUY SIGNALS:")
            for i, signal in enumerate(summary['top_buy_signals'], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        if summary['top_sell_signals']:
            print(f"\n📉 TOP SELL SIGNALS:")
            for i, signal in enumerate(summary['top_sell_signals'], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        # Show file paths
        if analysis_result['csv_filepath']:
            print(f"\n📄 CSV results: {analysis_result['csv_filepath']}")
        if analysis_result['json_filepath']:
            print(f"📄 JSON results: {analysis_result['json_filepath']}")
        
        print("\n✅ Crypto analysis complete!")
        print(f"🗄️  Database: {engine.db_path}")
        print(f"📁 Results directory: {engine.output_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
"""
Crypto Engine Runner

Simple script to test and run the crypto engine with VectorBTPro.

Usage:
    python run_crypto_engine.py [--config config.json] [--symbols BTCUSDT,ETHUSDT] [--test]

Example:
    python run_crypto_engine.py --config config.json --test
    python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""

import argparse
import json
import os
import sys
from datetime import datetime
from crypto_engine import CryptoEngine

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def test_engine_setup():
    """Test if the engine can be initialized and basic functionality works"""
    print("🧪 Testing Crypto Engine Setup...")
    
    try:
        # Test imports
        import vectorbtpro as vbt
        print(f"✅ VectorBTPro detected: {vbt.__version__}")
        
        import optuna
        print(f"✅ Optuna detected: {optuna.__version__}")
        
        from binance.client import Client
        print("✅ Binance client imported successfully")
        
        # Test config loading
        config = load_config("config.json")
        if config.get('binance_api_key') and config.get('binance_api_secret'):
            print("✅ Configuration loaded successfully")
        else:
            print("⚠️  Configuration missing API credentials")
            return False
        
        # Test engine initialization
        engine = CryptoEngine("config.json")
        print("✅ Crypto Engine initialized successfully")
        
        # Test database connection
        import sqlite3
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database initialized with {len(tables)} tables")
        conn.close()
        
        # Test top 100 assets retrieval
        top_100 = engine.get_top_100_assets()
        print(f"✅ Retrieved {len(top_100)} top assets")
        
        print("✅ All tests passed! Engine is ready for analysis.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run Crypto Engine Analysis')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--symbols', help='Comma-separated list of symbols to analyze')
    parser.add_argument('--interval', default='1d', help='Time interval (default: 1d)')
    parser.add_argument('--days', type=int, default=720, help='Number of days to analyze (default: 720)')
    parser.add_argument('--test', action='store_true', help='Run engine tests only')
    parser.add_argument('--optimize', action='store_true', help='Optimize parameters for major coins')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        success = test_engine_setup()
        sys.exit(0 if success else 1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Check API credentials
    api_key = config.get('binance_api_key')
    api_secret = config.get('binance_api_secret')
    
    if not api_key or not api_secret:
        print("❌ Error: Binance API credentials not found in config.json")
        print("Please update config.json with your Binance API credentials.")
        sys.exit(1)
    
    # Initialize engine
    print("🚀 Initializing Crypto Engine...")
    engine = CryptoEngine(args.config)
    
    # Determine symbols to analyze
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"📊 Analyzing specified symbols: {symbols}")
    else:
        # Use core symbols for quick test
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        print(f"📊 Analyzing core symbols: {symbols}")
    
    print(f"⏰ Interval: {args.interval}")
    print(f"📅 Days: {args.days}")
    print(f"🔧 Optimize major coins: {args.optimize}")
    print(f"📁 Output format: {args.format}")
    
    # Run analysis
    print("\n" + "="*60)
    print("🚀 STARTING CRYPTO ANALYSIS")
    print("="*60)
    
    start_time = datetime.now()
    
    try:
        analysis_result = engine.run_complete_analysis(
            symbols=symbols,
            interval=args.interval,
            days=args.days,
            optimize_major_coins=args.optimize,
            output_format=args.format
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print detailed results
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        
        summary = analysis_result['summary']
        print(f"Total assets analyzed: {summary['total_assets']}")
        print(f"BUY signals: {summary['buy_signals']}")
        print(f"SELL signals: {summary['sell_signals']}")
        print(f"HOLD signals: {summary['hold_signals']}")
        print(f"Average potential return: {summary['avg_potential_return']:.2f}%")
        print(f"Average total return: {summary['avg_total_return']:.2f}%")
        print(f"Analysis duration: {duration}")
        
        # Show top signals
        if summary['top_buy_signals']:
            print(f"\n🔥 TOP BUY SIGNALS:")
            for i, signal in enumerate(summary['top_buy_signals'], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        if summary['top_sell_signals']:
            print(f"\n📉 TOP SELL SIGNALS:")
            for i, signal in enumerate(summary['top_sell_signals'], 1):
                symbol = signal['symbol']
                potential_return = signal.get('potential_return', 0) or 0
                total_return = signal.get('total_return', 0)
                print(f"{i}. {symbol}: {potential_return:.2f}% potential, {total_return:.2f}% total return")
        
        # Show file paths
        if analysis_result['csv_filepath']:
            print(f"\n📄 CSV results: {analysis_result['csv_filepath']}")
        if analysis_result['json_filepath']:
            print(f"📄 JSON results: {analysis_result['json_filepath']}")
        
        print("\n✅ Crypto analysis complete!")
        print(f"🗄️  Database: {engine.db_path}")
        print(f"📁 Results directory: {engine.output_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
 