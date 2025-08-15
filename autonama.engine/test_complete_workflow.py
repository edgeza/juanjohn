#!/usr/bin/env python3
"""
Complete Workflow Test for Crypto Engine

This script tests the entire workflow from data fetching to export.
"""

# NumPy 2.0 compatibility layer - MUST BE FIRST
import numpy as np
try:
    # Handle NumPy 2.0 changes
    if not hasattr(np, 'float_'):
        np.float_ = np.float64
    if not hasattr(np, 'int_'):
        np.int_ = np.int64
except:
    pass

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from crypto_engine import CryptoEngine

def test_database_scanning():
    """Test local database scanning functionality"""
    print("🧪 Testing Database Scanning...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Check if database exists
        if os.path.exists(engine.db_path):
            print(f"✅ Database found: {engine.db_path}")
            
            # Get database info
            conn = sqlite3.connect(engine.db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            # Check historical data
            if 'crypto_historical_data' in tables:
                cursor.execute("SELECT COUNT(*) FROM crypto_historical_data")
                hist_count = cursor.fetchone()[0]
                print(f"✅ Historical data records: {hist_count}")
                
                # Check symbols in database
                cursor.execute("SELECT DISTINCT symbol FROM crypto_historical_data LIMIT 10")
                symbols = [row[0] for row in cursor.fetchall()]
                print(f"✅ Symbols in database: {symbols}")
            else:
                print("⚠️ No historical data table found")
            
            # Check analysis results
            if 'crypto_analysis_results' in tables:
                cursor.execute("SELECT COUNT(*) FROM crypto_analysis_results")
                analysis_count = cursor.fetchone()[0]
                print(f"✅ Analysis results: {analysis_count}")
            else:
                print("⚠️ No analysis results table found")
            
            conn.close()
            return True
            
        else:
            print("⚠️ Database not found, will be created on first run")
            return True
            
    except Exception as e:
        print(f"❌ Database scanning test failed: {e}")
        return False

def test_data_collection():
    """Test data collection from Binance"""
    print("\n🧪 Testing Data Collection...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test symbol list
        print(f"✅ Core symbols: {len(engine.core_symbols)}")
        print(f"✅ Extended symbols: {len(engine.extended_symbols)}")
        print(f"✅ Total symbols: {len(engine.all_symbols)}")
        
        # Test top 100 assets
        try:
            top_100 = engine.get_top_100_assets()
            print(f"✅ Retrieved {len(top_100)} top assets")
            print(f"✅ Sample: {top_100[:5]}")
        except Exception as e:
            print(f"⚠️ Top 100 test failed (expected with test credentials): {e}")
        
        # Test data fetching for a single symbol
        test_symbol = "BTCUSDT"
        print(f"✅ Testing data fetch for {test_symbol}")
        
        df = engine.fetch_historical_data(test_symbol, "1d", 30)
        if not df.empty:
            print(f"✅ Fetched {len(df)} records for {test_symbol}")
            print(f"✅ Date range: {df.index[0]} to {df.index[-1]}")
            print(f"✅ Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
        else:
            print(f"⚠️ No data fetched for {test_symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data collection test failed: {e}")
        return False

def test_analysis_workflow():
    """Test complete analysis workflow"""
    print("\n🧪 Testing Analysis Workflow...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test with a small set of symbols
        test_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        print(f"✅ Testing analysis for {len(test_symbols)} symbols")
        
        # Run analysis
        results = engine.analyze_all_assets(
            symbols=test_symbols,
            interval="1d",
            days=365,
            optimize_major_coins=True
        )
        
        if results:
            print(f"✅ Analysis completed for {len(results)} assets")
            
            # Check results structure
            required_fields = ['symbol', 'signal', 'current_price', 'potential_return', 'total_return']
            for field in required_fields:
                if all(field in result for result in results):
                    print(f"✅ Field '{field}' present in all results")
                else:
                    print(f"❌ Field '{field}' missing from some results")
            
            # Check signal distribution
            signals = [r['signal'] for r in results]
            signal_counts = pd.Series(signals).value_counts()
            print(f"✅ Signal distribution: {dict(signal_counts)}")
            
            # Check return statistics
            potential_returns = [r.get('potential_return', 0) or 0 for r in results]
            total_returns = [r.get('total_return', 0) for r in results]
            
            print(f"✅ Potential return range: {min(potential_returns):.2f}% to {max(potential_returns):.2f}%")
            print(f"✅ Total return range: {min(total_returns):.2f}% to {max(total_returns):.2f}%")
            
            return results
        else:
            print("❌ No results returned from analysis")
            return None
            
    except Exception as e:
        print(f"❌ Analysis workflow test failed: {e}")
        return None

def test_export_functionality(results):
    """Test export functionality"""
    print("\n🧪 Testing Export Functionality...")
    
    if not results:
        print("⚠️ No results to export")
        return False
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test CSV export
        csv_file = engine.save_results_to_csv(results, "test_export.csv")
        if csv_file and os.path.exists(csv_file):
            print(f"✅ CSV export successful: {csv_file}")
            
            # Verify CSV content
            df = pd.read_csv(csv_file)
            print(f"✅ CSV contains {len(df)} rows and {len(df.columns)} columns")
        else:
            print("❌ CSV export failed")
        
        # Test JSON export
        json_file = engine.save_results_to_json(results, "test_export.json")
        if json_file and os.path.exists(json_file):
            print(f"✅ JSON export successful: {json_file}")
            
            # Verify JSON content
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            print(f"✅ JSON contains {len(json_data)} records")
        else:
            print("❌ JSON export failed")
        
        # Test summary generation
        summary = engine.get_analysis_summary(results)
        if summary:
            print(f"✅ Summary generated: {summary['total_assets']} assets")
            print(f"✅ BUY signals: {summary['buy_signals']}")
            print(f"✅ SELL signals: {summary['sell_signals']}")
            print(f"✅ HOLD signals: {summary['hold_signals']}")
        
        # Clean up test files
        for file in ["test_export.csv", "test_export.json"]:
            if os.path.exists(file):
                os.remove(file)
                print(f"✅ Cleaned up {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export functionality test failed: {e}")
        return False

def test_visualization_data(results):
    """Test that results contain data needed for visualization"""
    print("\n🧪 Testing Visualization Data...")
    
    if not results:
        print("⚠️ No results to test visualization data")
        return False
    
    try:
        # Convert to DataFrame for easier testing
        df = pd.DataFrame(results)
        
        # Check required fields for visualization
        viz_fields = {
            'symbol': 'Asset symbols for identification',
            'signal': 'BUY/SELL/HOLD signals for color coding',
            'current_price': 'Current price for price charts',
            'potential_return': 'Potential return for analysis',
            'total_return': 'Historical return for comparison',
            'sharpe_ratio': 'Risk-adjusted return metric',
            'max_drawdown': 'Risk metric for charts'
        }
        
        missing_fields = []
        for field, description in viz_fields.items():
            if field in df.columns:
                print(f"✅ {field}: {description}")
            else:
                print(f"❌ {field}: Missing - {description}")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Missing {len(missing_fields)} fields for visualization")
            return False
        else:
            print("✅ All visualization fields present")
        
        # Test data quality
        print(f"✅ Data quality check:")
        print(f"   - No null values in key fields: {not df[['symbol', 'signal', 'current_price']].isnull().any().any()}")
        print(f"   - Valid signals: {set(df['signal'].unique())}")
        print(f"   - Price range: ${df['current_price'].min():.2f} to ${df['current_price'].max():.2f}")
        print(f"   - Return range: {df['potential_return'].min():.2f}% to {df['potential_return'].max():.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization data test failed: {e}")
        return False

def test_main_system_compatibility(results):
    """Test that results are compatible with main system expectations"""
    print("\n🧪 Testing Main System Compatibility...")
    
    if not results:
        print("⚠️ No results to test compatibility")
        return False
    
    try:
        # Check that results match expected format for main system
        expected_format = {
            'symbol': str,
            'interval': str,
            'current_price': (int, float),
            'lower_band': (int, float),
            'upper_band': (int, float),
            'signal': str,
            'potential_return': (int, float),
            'total_return': (int, float),
            'sharpe_ratio': (int, float),
            'max_drawdown': (int, float),
            'degree': int,
            'kstd': (int, float),
            'analysis_date': str
        }
        
        compatibility_issues = []
        
        for result in results:
            for field, expected_type in expected_format.items():
                if field not in result:
                    compatibility_issues.append(f"Missing field: {field}")
                elif not isinstance(result[field], expected_type):
                    compatibility_issues.append(f"Wrong type for {field}: expected {expected_type}, got {type(result[field])}")
        
        if compatibility_issues:
            print("❌ Compatibility issues found:")
            for issue in compatibility_issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ All results compatible with main system format")
        
        # Test signal values
        valid_signals = {'BUY', 'SELL', 'HOLD'}
        actual_signals = set(result['signal'] for result in results)
        if actual_signals.issubset(valid_signals):
            print("✅ All signals are valid")
        else:
            print(f"❌ Invalid signals found: {actual_signals - valid_signals}")
            return False
        
        # Test numeric ranges
        for result in results:
            if result['potential_return'] < -100 or result['potential_return'] > 1000:
                print(f"❌ Unrealistic potential return: {result['potential_return']}%")
                return False
            if result['total_return'] < -100 or result['total_return'] > 1000:
                print(f"❌ Unrealistic total return: {result['total_return']}%")
                return False
        
        print("✅ All numeric values within reasonable ranges")
        return True
        
    except Exception as e:
        print(f"❌ Main system compatibility test failed: {e}")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 Crypto Engine Complete Workflow Test")
    print("="*60)
    
    tests = [
        ("Database Scanning", test_database_scanning),
        ("Data Collection", test_data_collection),
        ("Analysis Workflow", test_analysis_workflow),
        ("Export Functionality", lambda: test_export_functionality(results) if 'results' in locals() else False),
        ("Visualization Data", lambda: test_visualization_data(results) if 'results' in locals() else False),
        ("Main System Compatibility", lambda: test_main_system_compatibility(results) if 'results' in locals() else False)
    ]
    
    passed = 0
    total = len(tests)
    results = None
    
    for test_name, test_func in tests:
        try:
            if test_name == "Analysis Workflow":
                result = test_func()
                if result:
                    results = result
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
            else:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Crypto engine is ready for production use.")
        print("\n🎯 Next Steps:")
        print("1. Run the Streamlit dashboard: python run_dashboard.py")
        print("2. Test with real API credentials in config.json")
        print("3. Integrate with main Autonama system")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
"""
Complete Workflow Test for Crypto Engine

This script tests the entire workflow from data fetching to export.
"""

# NumPy 2.0 compatibility layer - MUST BE FIRST
import numpy as np
try:
    # Handle NumPy 2.0 changes
    if not hasattr(np, 'float_'):
        np.float_ = np.float64
    if not hasattr(np, 'int_'):
        np.int_ = np.int64
except:
    pass

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from crypto_engine import CryptoEngine

def test_database_scanning():
    """Test local database scanning functionality"""
    print("🧪 Testing Database Scanning...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Check if database exists
        if os.path.exists(engine.db_path):
            print(f"✅ Database found: {engine.db_path}")
            
            # Get database info
            conn = sqlite3.connect(engine.db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            # Check historical data
            if 'crypto_historical_data' in tables:
                cursor.execute("SELECT COUNT(*) FROM crypto_historical_data")
                hist_count = cursor.fetchone()[0]
                print(f"✅ Historical data records: {hist_count}")
                
                # Check symbols in database
                cursor.execute("SELECT DISTINCT symbol FROM crypto_historical_data LIMIT 10")
                symbols = [row[0] for row in cursor.fetchall()]
                print(f"✅ Symbols in database: {symbols}")
            else:
                print("⚠️ No historical data table found")
            
            # Check analysis results
            if 'crypto_analysis_results' in tables:
                cursor.execute("SELECT COUNT(*) FROM crypto_analysis_results")
                analysis_count = cursor.fetchone()[0]
                print(f"✅ Analysis results: {analysis_count}")
            else:
                print("⚠️ No analysis results table found")
            
            conn.close()
            return True
            
        else:
            print("⚠️ Database not found, will be created on first run")
            return True
            
    except Exception as e:
        print(f"❌ Database scanning test failed: {e}")
        return False

def test_data_collection():
    """Test data collection from Binance"""
    print("\n🧪 Testing Data Collection...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test symbol list
        print(f"✅ Core symbols: {len(engine.core_symbols)}")
        print(f"✅ Extended symbols: {len(engine.extended_symbols)}")
        print(f"✅ Total symbols: {len(engine.all_symbols)}")
        
        # Test top 100 assets
        try:
            top_100 = engine.get_top_100_assets()
            print(f"✅ Retrieved {len(top_100)} top assets")
            print(f"✅ Sample: {top_100[:5]}")
        except Exception as e:
            print(f"⚠️ Top 100 test failed (expected with test credentials): {e}")
        
        # Test data fetching for a single symbol
        test_symbol = "BTCUSDT"
        print(f"✅ Testing data fetch for {test_symbol}")
        
        df = engine.fetch_historical_data(test_symbol, "1d", 30)
        if not df.empty:
            print(f"✅ Fetched {len(df)} records for {test_symbol}")
            print(f"✅ Date range: {df.index[0]} to {df.index[-1]}")
            print(f"✅ Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
        else:
            print(f"⚠️ No data fetched for {test_symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data collection test failed: {e}")
        return False

def test_analysis_workflow():
    """Test complete analysis workflow"""
    print("\n🧪 Testing Analysis Workflow...")
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test with a small set of symbols
        test_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        print(f"✅ Testing analysis for {len(test_symbols)} symbols")
        
        # Run analysis
        results = engine.analyze_all_assets(
            symbols=test_symbols,
            interval="1d",
            days=365,
            optimize_major_coins=True
        )
        
        if results:
            print(f"✅ Analysis completed for {len(results)} assets")
            
            # Check results structure
            required_fields = ['symbol', 'signal', 'current_price', 'potential_return', 'total_return']
            for field in required_fields:
                if all(field in result for result in results):
                    print(f"✅ Field '{field}' present in all results")
                else:
                    print(f"❌ Field '{field}' missing from some results")
            
            # Check signal distribution
            signals = [r['signal'] for r in results]
            signal_counts = pd.Series(signals).value_counts()
            print(f"✅ Signal distribution: {dict(signal_counts)}")
            
            # Check return statistics
            potential_returns = [r.get('potential_return', 0) or 0 for r in results]
            total_returns = [r.get('total_return', 0) for r in results]
            
            print(f"✅ Potential return range: {min(potential_returns):.2f}% to {max(potential_returns):.2f}%")
            print(f"✅ Total return range: {min(total_returns):.2f}% to {max(total_returns):.2f}%")
            
            return results
        else:
            print("❌ No results returned from analysis")
            return None
            
    except Exception as e:
        print(f"❌ Analysis workflow test failed: {e}")
        return None

def test_export_functionality(results):
    """Test export functionality"""
    print("\n🧪 Testing Export Functionality...")
    
    if not results:
        print("⚠️ No results to export")
        return False
    
    try:
        engine = CryptoEngine("config.json")
        
        # Test CSV export
        csv_file = engine.save_results_to_csv(results, "test_export.csv")
        if csv_file and os.path.exists(csv_file):
            print(f"✅ CSV export successful: {csv_file}")
            
            # Verify CSV content
            df = pd.read_csv(csv_file)
            print(f"✅ CSV contains {len(df)} rows and {len(df.columns)} columns")
        else:
            print("❌ CSV export failed")
        
        # Test JSON export
        json_file = engine.save_results_to_json(results, "test_export.json")
        if json_file and os.path.exists(json_file):
            print(f"✅ JSON export successful: {json_file}")
            
            # Verify JSON content
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            print(f"✅ JSON contains {len(json_data)} records")
        else:
            print("❌ JSON export failed")
        
        # Test summary generation
        summary = engine.get_analysis_summary(results)
        if summary:
            print(f"✅ Summary generated: {summary['total_assets']} assets")
            print(f"✅ BUY signals: {summary['buy_signals']}")
            print(f"✅ SELL signals: {summary['sell_signals']}")
            print(f"✅ HOLD signals: {summary['hold_signals']}")
        
        # Clean up test files
        for file in ["test_export.csv", "test_export.json"]:
            if os.path.exists(file):
                os.remove(file)
                print(f"✅ Cleaned up {file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export functionality test failed: {e}")
        return False

def test_visualization_data(results):
    """Test that results contain data needed for visualization"""
    print("\n🧪 Testing Visualization Data...")
    
    if not results:
        print("⚠️ No results to test visualization data")
        return False
    
    try:
        # Convert to DataFrame for easier testing
        df = pd.DataFrame(results)
        
        # Check required fields for visualization
        viz_fields = {
            'symbol': 'Asset symbols for identification',
            'signal': 'BUY/SELL/HOLD signals for color coding',
            'current_price': 'Current price for price charts',
            'potential_return': 'Potential return for analysis',
            'total_return': 'Historical return for comparison',
            'sharpe_ratio': 'Risk-adjusted return metric',
            'max_drawdown': 'Risk metric for charts'
        }
        
        missing_fields = []
        for field, description in viz_fields.items():
            if field in df.columns:
                print(f"✅ {field}: {description}")
            else:
                print(f"❌ {field}: Missing - {description}")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Missing {len(missing_fields)} fields for visualization")
            return False
        else:
            print("✅ All visualization fields present")
        
        # Test data quality
        print(f"✅ Data quality check:")
        print(f"   - No null values in key fields: {not df[['symbol', 'signal', 'current_price']].isnull().any().any()}")
        print(f"   - Valid signals: {set(df['signal'].unique())}")
        print(f"   - Price range: ${df['current_price'].min():.2f} to ${df['current_price'].max():.2f}")
        print(f"   - Return range: {df['potential_return'].min():.2f}% to {df['potential_return'].max():.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization data test failed: {e}")
        return False

def test_main_system_compatibility(results):
    """Test that results are compatible with main system expectations"""
    print("\n🧪 Testing Main System Compatibility...")
    
    if not results:
        print("⚠️ No results to test compatibility")
        return False
    
    try:
        # Check that results match expected format for main system
        expected_format = {
            'symbol': str,
            'interval': str,
            'current_price': (int, float),
            'lower_band': (int, float),
            'upper_band': (int, float),
            'signal': str,
            'potential_return': (int, float),
            'total_return': (int, float),
            'sharpe_ratio': (int, float),
            'max_drawdown': (int, float),
            'degree': int,
            'kstd': (int, float),
            'analysis_date': str
        }
        
        compatibility_issues = []
        
        for result in results:
            for field, expected_type in expected_format.items():
                if field not in result:
                    compatibility_issues.append(f"Missing field: {field}")
                elif not isinstance(result[field], expected_type):
                    compatibility_issues.append(f"Wrong type for {field}: expected {expected_type}, got {type(result[field])}")
        
        if compatibility_issues:
            print("❌ Compatibility issues found:")
            for issue in compatibility_issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ All results compatible with main system format")
        
        # Test signal values
        valid_signals = {'BUY', 'SELL', 'HOLD'}
        actual_signals = set(result['signal'] for result in results)
        if actual_signals.issubset(valid_signals):
            print("✅ All signals are valid")
        else:
            print(f"❌ Invalid signals found: {actual_signals - valid_signals}")
            return False
        
        # Test numeric ranges
        for result in results:
            if result['potential_return'] < -100 or result['potential_return'] > 1000:
                print(f"❌ Unrealistic potential return: {result['potential_return']}%")
                return False
            if result['total_return'] < -100 or result['total_return'] > 1000:
                print(f"❌ Unrealistic total return: {result['total_return']}%")
                return False
        
        print("✅ All numeric values within reasonable ranges")
        return True
        
    except Exception as e:
        print(f"❌ Main system compatibility test failed: {e}")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 Crypto Engine Complete Workflow Test")
    print("="*60)
    
    tests = [
        ("Database Scanning", test_database_scanning),
        ("Data Collection", test_data_collection),
        ("Analysis Workflow", test_analysis_workflow),
        ("Export Functionality", lambda: test_export_functionality(results) if 'results' in locals() else False),
        ("Visualization Data", lambda: test_visualization_data(results) if 'results' in locals() else False),
        ("Main System Compatibility", lambda: test_main_system_compatibility(results) if 'results' in locals() else False)
    ]
    
    passed = 0
    total = len(tests)
    results = None
    
    for test_name, test_func in tests:
        try:
            if test_name == "Analysis Workflow":
                result = test_func()
                if result:
                    results = result
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
            else:
                if test_func():
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Crypto engine is ready for production use.")
        print("\n🎯 Next Steps:")
        print("1. Run the Streamlit dashboard: python run_dashboard.py")
        print("2. Test with real API credentials in config.json")
        print("3. Integrate with main Autonama system")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 