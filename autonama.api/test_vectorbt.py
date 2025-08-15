#!/usr/bin/env python3
"""
Test script to verify VectorBTPro installation in Docker container
"""

import sys
import traceback

def test_vectorbt_import():
    """Test if VectorBTPro can be imported"""
    try:
        import vectorbtpro as vbt
        print("✅ VectorBTPro imported successfully!")
        print(f"Version: {vbt.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import VectorBTPro: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing VectorBTPro: {e}")
        traceback.print_exc()
        return False

def test_vectorbt_functionality():
    """Test basic VectorBTPro functionality"""
    try:
        import vectorbtpro as vbt
        import pandas as pd
        import numpy as np
        
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = pd.Series(np.random.randn(100).cumsum() + 100, index=dates)
        
        # Test basic portfolio creation
        entries = prices > prices.rolling(20).mean()
        exits = prices < prices.rolling(20).mean()
        
        pf = vbt.Portfolio.from_signals(
            close=prices,
            entries=entries,
            exits=exits,
            init_cash=10000,
            fees=0.001
        )
        
        print("✅ VectorBTPro portfolio creation successful!")
        print(f"Total return: {pf.stats()['Total Return [%]']:.2f}%")
        return True
        
    except Exception as e:
        print(f"❌ VectorBTPro functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_optimization_dependencies():
    """Test optimization dependencies"""
    try:
        import optuna
        import matplotlib
        import seaborn
        
        print("✅ Optimization dependencies imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Failed to import optimization dependencies: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing VectorBTPro installation in Docker container...")
    print("=" * 50)
    
    tests = [
        ("VectorBTPro Import", test_vectorbt_import),
        ("VectorBTPro Functionality", test_vectorbt_functionality),
        ("Optimization Dependencies", test_optimization_dependencies)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed!")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! VectorBTPro is ready to use.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        sys.exit(1)

if __name__ == "__main__":
    main() 