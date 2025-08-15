#!/usr/bin/env python3
"""
Test script for the Enhanced Local Analysis Engine

This script tests the basic functionality of the engine without requiring
full Binance API credentials or database connection.
"""

import json
import os
import sys
from datetime import datetime

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_keys = ['binance_api_key', 'binance_api_secret']
        for key in required_keys:
            if key not in config or config[key] == 'your_binance_api_key_here':
                print(f"⚠️  Warning: {key} not configured")
            else:
                print(f"✅ {key} configured")
        
        return True
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    dependencies = [
        'pandas',
        'numpy', 
        'matplotlib',
        'scipy',
        'sklearn',
        'talib',
        'seaborn',
        'psycopg2',
        'plotly',
        'streamlit',
        'aiohttp',
        'binance'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_directory_structure():
    """Test directory structure"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = ['results', 'cache']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ Created {dir_name}/")
        else:
            print(f"✅ {dir_name}/ exists")
    
    return True

def test_engine_import():
    """Test engine import"""
    print("\n🚀 Testing engine import...")
    
    try:
        from enhanced_local_engine import EnhancedLocalEngine
        print("✅ EnhancedLocalEngine imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing EnhancedLocalEngine: {e}")
        return False

def test_runner_import():
    """Test runner import"""
    print("\n🏃 Testing runner import...")
    
    try:
        from run_enhanced_analysis import main
        print("✅ Analysis runner imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing analysis runner: {e}")
        return False

def test_ingestion_import():
    """Test ingestion import"""
    print("\n📥 Testing ingestion import...")
    
    try:
        from ingestion_system import IngestionSystem
        print("✅ IngestionSystem imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing ingestion system: {e}")
        return False

def create_sample_config():
    """Create sample configuration if it doesn't exist"""
    if not os.path.exists('config.json'):
        print("\n📝 Creating sample config.json...")
        
        sample_config = {
            "binance_api_key": "your_binance_api_key_here",
            "binance_api_secret": "your_binance_api_secret_here",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "autonama",
            "database_user": "postgres",
            "database_password": "postgres",
            "default_settings": {
                "interval": "1d",
                "degree": 4,
                "kstd": 2.0,
                "days": 720,
                "output_directory": "results"
            },
            "scan_settings": {
                "core_movers": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "top_100_enabled": True,
                "custom_symbols": []
            },
            "cache_settings": {
                "enabled": True,
                "cache_duration_hours": 24
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print("✅ Sample config.json created")
        print("⚠️  Please edit config.json with your Binance API credentials")

def main():
    """Run all tests"""
    print("🧪 Enhanced Local Engine Test Suite")
    print("=" * 50)
    
    # Create sample config if needed
    create_sample_config()
    
    # Run tests
    tests = [
        test_config,
        test_dependencies,
        test_directory_structure,
        test_engine_import,
        test_runner_import,
        test_ingestion_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Engine is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Edit config.json with your Binance API credentials")
        print("2. Run: python run_enhanced_analysis.py --config config.json")
        print("3. Run: python ingestion_system.py --config config.json")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Configure Binance API credentials in config.json")
        print("3. Ensure PostgreSQL is running for database tests")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 
"""
Test script for the Enhanced Local Analysis Engine

This script tests the basic functionality of the engine without requiring
full Binance API credentials or database connection.
"""

import json
import os
import sys
from datetime import datetime

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_keys = ['binance_api_key', 'binance_api_secret']
        for key in required_keys:
            if key not in config or config[key] == 'your_binance_api_key_here':
                print(f"⚠️  Warning: {key} not configured")
            else:
                print(f"✅ {key} configured")
        
        return True
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    dependencies = [
        'pandas',
        'numpy', 
        'matplotlib',
        'scipy',
        'sklearn',
        'talib',
        'seaborn',
        'psycopg2',
        'plotly',
        'streamlit',
        'aiohttp',
        'binance'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_directory_structure():
    """Test directory structure"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = ['results', 'cache']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ Created {dir_name}/")
        else:
            print(f"✅ {dir_name}/ exists")
    
    return True

def test_engine_import():
    """Test engine import"""
    print("\n🚀 Testing engine import...")
    
    try:
        from enhanced_local_engine import EnhancedLocalEngine
        print("✅ EnhancedLocalEngine imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing EnhancedLocalEngine: {e}")
        return False

def test_runner_import():
    """Test runner import"""
    print("\n🏃 Testing runner import...")
    
    try:
        from run_enhanced_analysis import main
        print("✅ Analysis runner imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing analysis runner: {e}")
        return False

def test_ingestion_import():
    """Test ingestion import"""
    print("\n📥 Testing ingestion import...")
    
    try:
        from ingestion_system import IngestionSystem
        print("✅ IngestionSystem imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing ingestion system: {e}")
        return False

def create_sample_config():
    """Create sample configuration if it doesn't exist"""
    if not os.path.exists('config.json'):
        print("\n📝 Creating sample config.json...")
        
        sample_config = {
            "binance_api_key": "your_binance_api_key_here",
            "binance_api_secret": "your_binance_api_secret_here",
            "database_host": "localhost",
            "database_port": 5432,
            "database_name": "autonama",
            "database_user": "postgres",
            "database_password": "postgres",
            "default_settings": {
                "interval": "1d",
                "degree": 4,
                "kstd": 2.0,
                "days": 720,
                "output_directory": "results"
            },
            "scan_settings": {
                "core_movers": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "top_100_enabled": True,
                "custom_symbols": []
            },
            "cache_settings": {
                "enabled": True,
                "cache_duration_hours": 24
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print("✅ Sample config.json created")
        print("⚠️  Please edit config.json with your Binance API credentials")

def main():
    """Run all tests"""
    print("🧪 Enhanced Local Engine Test Suite")
    print("=" * 50)
    
    # Create sample config if needed
    create_sample_config()
    
    # Run tests
    tests = [
        test_config,
        test_dependencies,
        test_directory_structure,
        test_engine_import,
        test_runner_import,
        test_ingestion_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Engine is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Edit config.json with your Binance API credentials")
        print("2. Run: python run_enhanced_analysis.py --config config.json")
        print("3. Run: python ingestion_system.py --config config.json")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Configure Binance API credentials in config.json")
        print("3. Ensure PostgreSQL is running for database tests")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 
 