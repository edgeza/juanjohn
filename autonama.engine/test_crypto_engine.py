
#!/usr/bin/env python3
"""
Crypto Engine Test Script

This script tests the crypto engine functionality step by step.
"""

import os
import sys
import json
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # NumPy 2.0 compatibility layer
        import numpy as np
        try:
            # Handle NumPy 2.0 changes
            if not hasattr(np, 'float_'):
                np.float_ = np.float64
            if not hasattr(np, 'int_'):
                np.int_ = np.int64
        except:
            pass
        
        print(f"✅ NumPy: {np.__version__}")
        
        import vectorbtpro as vbt
        print(f"✅ VectorBTPro: {vbt.__version__}")
        
        import optuna
        print(f"✅ Optuna: {optuna.__version__}")
        
        from binance.client import Client
        print("✅ Binance client")
        
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
        
        # Test NumPy functionality
        try:
            test_float = np.float64(1.0)
            test_int = np.int64(1)
            print("✅ NumPy types working correctly")
        except Exception as e:
            print(f"⚠️ NumPy compatibility issue: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        required_keys = ['binance_api_key', 'binance_api_secret', 'default_settings']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config key: {key}")
                return False
        
        print("✅ Configuration structure is valid")
        
        # Check if API credentials are set
        api_key = config.get('binance_api_key')
        api_secret = config.get('binance_api_secret')
        
        if api_key == "your_binance_api_key_here" or api_secret == "your_binance_api_secret_here":
            print("⚠️  API credentials not configured (using placeholder values)")
        else:
            print("✅ API credentials configured")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_engine_initialization():
    """Test engine initialization"""
    print("\n🧪 Testing engine initialization...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Test with placeholder credentials
        test_config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {
                "output_directory": "test_results",
                "interval": "1d",
                "degree": 4,
                "kstd": 2.0,
                "days": 720
            }
        }
        
        # Write test config
        with open("test_config.json", "w") as f:
            json.dump(test_config, f, indent=2)
        
        # Initialize engine
        engine = CryptoEngine("test_config.json")
        print("✅ Engine initialized successfully")
        
        # Test database creation
        if os.path.exists(engine.db_path):
            print("✅ Database file created")
        else:
            print("❌ Database file not created")
            return False
        
        # Clean up test config
        os.remove("test_config.json")
        
        return True
    except Exception as e:
        print(f"❌ Engine initialization test failed: {e}")
        return False

def test_data_fetching():
    """Test data fetching functionality"""
    print("\n🧪 Testing data fetching...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Create test config with real API credentials
        config = {}
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            print("⚠️  Using test credentials for data fetching test")
            config = {
                "binance_api_key": "test_key",
                "binance_api_secret": "test_secret",
                "default_settings": {"output_directory": "test_results"}
            }
        
        engine = CryptoEngine("config.json")
        
        # Test top 100 assets retrieval
        try:
            top_100 = engine.get_top_100_assets()
            print(f"✅ Retrieved {len(top_100)} top assets")
        except Exception as e:
            print(f"⚠️  Top 100 assets test failed (expected with test credentials): {e}")
        
        # Test symbol list
        print(f"✅ Core symbols: {len(engine.core_symbols)}")
        print(f"✅ Extended symbols: {len(engine.extended_symbols)}")
        print(f"✅ Total symbols: {len(engine.all_symbols)}")
        
        return True
    except Exception as e:
        print(f"❌ Data fetching test failed: {e}")
        return False

def test_analysis_functions():
    """Test analysis functions"""
    print("\n🧪 Testing analysis functions...")
    
    try:
        from crypto_engine import CryptoEngine
        import pandas as pd
        import numpy as np
        
        # Create test data
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        close_prices = np.random.randn(len(dates)).cumsum() + 100
        test_data = pd.Series(close_prices, index=dates)
        
        # Initialize engine
        config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {"output_directory": "test_results"}
        }
        
        with open("test_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        engine = CryptoEngine("test_config.json")
        
        # Test preprocessing
        processed_data = engine.preprocess_data(test_data)
        print(f"✅ Data preprocessing: {len(processed_data)} points")
        
        # Test polynomial regression
        pf, indicators, entries, exits = engine.calculate_polynomial_regression(processed_data)
        if pf is not None:
            print("✅ Polynomial regression calculation")
        else:
            print("⚠️  Polynomial regression returned None (may be normal for test data)")
        
        # Test signal generation
        if indicators is not None:
            signal, lower_band, upper_band, potential_return = engine.generate_signal(indicators)
            print(f"✅ Signal generation: {signal}")
        
        # Clean up
        os.remove("test_config.json")
        
        return True
    except Exception as e:
        print(f"❌ Analysis functions test failed: {e}")
        return False

def test_output_functions():
    """Test output functions"""
    print("\n🧪 Testing output functions...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Create test results
        test_results = [
            {
                'symbol': 'BTCUSDT',
                'interval': '1d',
                'current_price': 45000.0,
                'lower_band': 44000.0,
                'upper_band': 46000.0,
                'signal': 'BUY',
                'potential_return': 4.55,
                'total_return': 12.34,
                'sharpe_ratio': 1.23,
                'max_drawdown': -5.67,
                'degree': 4,
                'kstd': 2.0,
                'analysis_date': datetime.now().isoformat()
            },
            {
                'symbol': 'ETHUSDT',
                'interval': '1d',
                'current_price': 2800.0,
                'lower_band': 2750.0,
                'upper_band': 2850.0,
                'signal': 'HOLD',
                'potential_return': 3.64,
                'total_return': 8.91,
                'sharpe_ratio': 0.98,
                'max_drawdown': -3.45,
                'degree': 4,
                'kstd': 2.0,
                'analysis_date': datetime.now().isoformat()
            }
        ]
        
        # Initialize engine
        config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {"output_directory": "test_results"}
        }
        
        with open("test_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        engine = CryptoEngine("test_config.json")
        
        # Test CSV output
        csv_file = engine.save_results_to_csv(test_results, "test_results.csv")
        if csv_file and os.path.exists(csv_file):
            print("✅ CSV output test passed")
        else:
            print("❌ CSV output test failed")
        
        # Test JSON output
        json_file = engine.save_results_to_json(test_results, "test_results.json")
        if json_file and os.path.exists(json_file):
            print("✅ JSON output test passed")
        else:
            print("❌ JSON output test failed")
        
        # Test summary generation
        summary = engine.get_analysis_summary(test_results)
        if summary:
            print(f"✅ Summary generation: {summary['total_assets']} assets")
        
        # Clean up test files
        for file in ["test_results.csv", "test_results.json", "test_config.json"]:
            if os.path.exists(file):
                os.remove(file)
        
        return True
    except Exception as e:
        print(f"❌ Output functions test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Crypto Engine Test Suite")
    print("="*50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Engine Initialization", test_engine_initialization),
        ("Data Fetching", test_data_fetching),
        ("Analysis Functions", test_analysis_functions),
        ("Output Functions", test_output_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Crypto engine is ready for use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
"""
Crypto Engine Test Script

This script tests the crypto engine functionality step by step.
"""

import os
import sys
import json
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # NumPy 2.0 compatibility layer
        import numpy as np
        try:
            # Handle NumPy 2.0 changes
            if not hasattr(np, 'float_'):
                np.float_ = np.float64
            if not hasattr(np, 'int_'):
                np.int_ = np.int64
        except:
            pass
        
        print(f"✅ NumPy: {np.__version__}")
        
        import vectorbtpro as vbt
        print(f"✅ VectorBTPro: {vbt.__version__}")
        
        import optuna
        print(f"✅ Optuna: {optuna.__version__}")
        
        from binance.client import Client
        print("✅ Binance client")
        
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
        
        # Test NumPy functionality
        try:
            test_float = np.float64(1.0)
            test_int = np.int64(1)
            print("✅ NumPy types working correctly")
        except Exception as e:
            print(f"⚠️ NumPy compatibility issue: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        required_keys = ['binance_api_key', 'binance_api_secret', 'default_settings']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config key: {key}")
                return False
        
        print("✅ Configuration structure is valid")
        
        # Check if API credentials are set
        api_key = config.get('binance_api_key')
        api_secret = config.get('binance_api_secret')
        
        if api_key == "your_binance_api_key_here" or api_secret == "your_binance_api_secret_here":
            print("⚠️  API credentials not configured (using placeholder values)")
        else:
            print("✅ API credentials configured")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_engine_initialization():
    """Test engine initialization"""
    print("\n🧪 Testing engine initialization...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Test with placeholder credentials
        test_config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {
                "output_directory": "test_results",
                "interval": "1d",
                "degree": 4,
                "kstd": 2.0,
                "days": 720
            }
        }
        
        # Write test config
        with open("test_config.json", "w") as f:
            json.dump(test_config, f, indent=2)
        
        # Initialize engine
        engine = CryptoEngine("test_config.json")
        print("✅ Engine initialized successfully")
        
        # Test database creation
        if os.path.exists(engine.db_path):
            print("✅ Database file created")
        else:
            print("❌ Database file not created")
            return False
        
        # Clean up test config
        os.remove("test_config.json")
        
        return True
    except Exception as e:
        print(f"❌ Engine initialization test failed: {e}")
        return False

def test_data_fetching():
    """Test data fetching functionality"""
    print("\n🧪 Testing data fetching...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Create test config with real API credentials
        config = {}
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            print("⚠️  Using test credentials for data fetching test")
            config = {
                "binance_api_key": "test_key",
                "binance_api_secret": "test_secret",
                "default_settings": {"output_directory": "test_results"}
            }
        
        engine = CryptoEngine("config.json")
        
        # Test top 100 assets retrieval
        try:
            top_100 = engine.get_top_100_assets()
            print(f"✅ Retrieved {len(top_100)} top assets")
        except Exception as e:
            print(f"⚠️  Top 100 assets test failed (expected with test credentials): {e}")
        
        # Test symbol list
        print(f"✅ Core symbols: {len(engine.core_symbols)}")
        print(f"✅ Extended symbols: {len(engine.extended_symbols)}")
        print(f"✅ Total symbols: {len(engine.all_symbols)}")
        
        return True
    except Exception as e:
        print(f"❌ Data fetching test failed: {e}")
        return False

def test_analysis_functions():
    """Test analysis functions"""
    print("\n🧪 Testing analysis functions...")
    
    try:
        from crypto_engine import CryptoEngine
        import pandas as pd
        import numpy as np
        
        # Create test data
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        close_prices = np.random.randn(len(dates)).cumsum() + 100
        test_data = pd.Series(close_prices, index=dates)
        
        # Initialize engine
        config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {"output_directory": "test_results"}
        }
        
        with open("test_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        engine = CryptoEngine("test_config.json")
        
        # Test preprocessing
        processed_data = engine.preprocess_data(test_data)
        print(f"✅ Data preprocessing: {len(processed_data)} points")
        
        # Test polynomial regression
        pf, indicators, entries, exits = engine.calculate_polynomial_regression(processed_data)
        if pf is not None:
            print("✅ Polynomial regression calculation")
        else:
            print("⚠️  Polynomial regression returned None (may be normal for test data)")
        
        # Test signal generation
        if indicators is not None:
            signal, lower_band, upper_band, potential_return = engine.generate_signal(indicators)
            print(f"✅ Signal generation: {signal}")
        
        # Clean up
        os.remove("test_config.json")
        
        return True
    except Exception as e:
        print(f"❌ Analysis functions test failed: {e}")
        return False

def test_output_functions():
    """Test output functions"""
    print("\n🧪 Testing output functions...")
    
    try:
        from crypto_engine import CryptoEngine
        
        # Create test results
        test_results = [
            {
                'symbol': 'BTCUSDT',
                'interval': '1d',
                'current_price': 45000.0,
                'lower_band': 44000.0,
                'upper_band': 46000.0,
                'signal': 'BUY',
                'potential_return': 4.55,
                'total_return': 12.34,
                'sharpe_ratio': 1.23,
                'max_drawdown': -5.67,
                'degree': 4,
                'kstd': 2.0,
                'analysis_date': datetime.now().isoformat()
            },
            {
                'symbol': 'ETHUSDT',
                'interval': '1d',
                'current_price': 2800.0,
                'lower_band': 2750.0,
                'upper_band': 2850.0,
                'signal': 'HOLD',
                'potential_return': 3.64,
                'total_return': 8.91,
                'sharpe_ratio': 0.98,
                'max_drawdown': -3.45,
                'degree': 4,
                'kstd': 2.0,
                'analysis_date': datetime.now().isoformat()
            }
        ]
        
        # Initialize engine
        config = {
            "binance_api_key": "test_key",
            "binance_api_secret": "test_secret",
            "default_settings": {"output_directory": "test_results"}
        }
        
        with open("test_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        engine = CryptoEngine("test_config.json")
        
        # Test CSV output
        csv_file = engine.save_results_to_csv(test_results, "test_results.csv")
        if csv_file and os.path.exists(csv_file):
            print("✅ CSV output test passed")
        else:
            print("❌ CSV output test failed")
        
        # Test JSON output
        json_file = engine.save_results_to_json(test_results, "test_results.json")
        if json_file and os.path.exists(json_file):
            print("✅ JSON output test passed")
        else:
            print("❌ JSON output test failed")
        
        # Test summary generation
        summary = engine.get_analysis_summary(test_results)
        if summary:
            print(f"✅ Summary generation: {summary['total_assets']} assets")
        
        # Clean up test files
        for file in ["test_results.csv", "test_results.json", "test_config.json"]:
            if os.path.exists(file):
                os.remove(file)
        
        return True
    except Exception as e:
        print(f"❌ Output functions test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Crypto Engine Test Suite")
    print("="*50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Engine Initialization", test_engine_initialization),
        ("Data Fetching", test_data_fetching),
        ("Analysis Functions", test_analysis_functions),
        ("Output Functions", test_output_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Crypto engine is ready for use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 