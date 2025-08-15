#!/usr/bin/env python3
"""
Crypto Engine Dashboard Runner

Simple script to run the Streamlit dashboard for testing and visualization.
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard"""
    print("🚀 Starting Crypto Engine Dashboard...")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists("crypto_dashboard.py"):
        print("❌ Error: crypto_dashboard.py not found in current directory")
        print("Please run this script from the autonama.engine directory")
        sys.exit(1)
    
    # Check if config.json exists
    if not os.path.exists("config.json"):
        print("❌ Error: config.json not found")
        print("Please create config.json with your Binance API credentials")
        sys.exit(1)
    
    # Check if crypto_engine.py exists
    if not os.path.exists("crypto_engine.py"):
        print("❌ Error: crypto_engine.py not found")
        print("Please ensure the crypto engine is properly set up")
        sys.exit(1)
    
    print("✅ All required files found")
    print("🌐 Starting Streamlit dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🔧 Press Ctrl+C to stop the dashboard")
    print("="*50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "crypto_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
"""
Crypto Engine Dashboard Runner

Simple script to run the Streamlit dashboard for testing and visualization.
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard"""
    print("🚀 Starting Crypto Engine Dashboard...")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists("crypto_dashboard.py"):
        print("❌ Error: crypto_dashboard.py not found in current directory")
        print("Please run this script from the autonama.engine directory")
        sys.exit(1)
    
    # Check if config.json exists
    if not os.path.exists("config.json"):
        print("❌ Error: config.json not found")
        print("Please create config.json with your Binance API credentials")
        sys.exit(1)
    
    # Check if crypto_engine.py exists
    if not os.path.exists("crypto_engine.py"):
        print("❌ Error: crypto_engine.py not found")
        print("Please ensure the crypto engine is properly set up")
        sys.exit(1)
    
    print("✅ All required files found")
    print("🌐 Starting Streamlit dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🔧 Press Ctrl+C to stop the dashboard")
    print("="*50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "crypto_dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
 