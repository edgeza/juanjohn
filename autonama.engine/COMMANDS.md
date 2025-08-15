# 🚀 Crypto Engine Commands Guide

This guide provides all the commands needed to run, test, and visualize the crypto engine.

## 📋 Prerequisites

1. **Activate VectorBTPro Environment**:
   ```bash
   conda activate autonama_vectorbt
   ```

2. **Install Dashboard Dependencies**:
   ```bash
   pip install -r requirements_dashboard.txt
   ```

3. **Update config.json** with your Binance API credentials:
   ```json
   {
       "binance_api_key": "your_actual_api_key_here",
       "binance_api_secret": "your_actual_api_secret_here"
   }
   ```

## 🧪 Testing Commands

### 1. Basic Engine Test
```bash
python test_crypto_engine.py
```
**Purpose**: Tests imports, configuration, engine initialization, and basic functionality.

### 2. Complete Workflow Test
```bash
python test_complete_workflow.py
```
**Purpose**: Tests the complete workflow including database scanning, data collection, analysis, export, and main system compatibility.

### 3. Quick Engine Test
```bash
python run_crypto_engine.py --test
```
**Purpose**: Quick test of engine setup and basic functionality.

## 🚀 Analysis Commands

### 1. Basic Analysis (Core Symbols)
```bash
python run_crypto_engine.py --config config.json
```
**Purpose**: Analyzes BTCUSDT, ETHUSDT, SOLUSDT with default settings.

### 2. Custom Symbols Analysis
```bash
python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,ADAUSDT
```
**Purpose**: Analyzes specific symbols of your choice.

### 3. Full Analysis with Optimization
```bash
python run_crypto_engine.py --config config.json --optimize --format both
```
**Purpose**: Runs analysis with parameter optimization for major coins and exports both CSV and JSON.

### 4. Top 100 Assets Analysis
```bash
python run_crypto_engine.py --config config.json --symbols $(python -c "from crypto_engine import CryptoEngine; e = CryptoEngine('config.json'); print(','.join(e.get_top_100_assets()[:10]))")
```
**Purpose**: Analyzes top 10 assets by volume from Binance.

## 📊 Visualization Commands

### 1. Start Streamlit Dashboard
```bash
python run_dashboard.py
```
**Purpose**: Starts the interactive Streamlit dashboard at http://localhost:8501

### 2. Direct Streamlit Command
```bash
streamlit run crypto_dashboard.py --server.port 8501
```
**Purpose**: Alternative way to start the dashboard directly.

## 🔍 Database Commands

### 1. Check Database Status
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
tables = cursor.fetchall()
print(f'Tables: {tables}')
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'{table[0]}: {count} records')
conn.close()
"
```

### 2. View Latest Analysis Results
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
df = pd.read_sql_query('SELECT * FROM crypto_analysis_results ORDER BY created_at DESC LIMIT 10', conn)
print(df)
conn.close()
"
```

## 📁 Export Commands

### 1. Export Latest Results to CSV
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
import pandas as pd
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
df = pd.read_sql_query('SELECT * FROM crypto_analysis_results', conn)
df.to_csv('latest_export.csv', index=False)
print(f'Exported {len(df)} records to latest_export.csv')
conn.close()
"
```

### 2. Export Latest Results to JSON
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
import json
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('SELECT * FROM crypto_analysis_results')
results = cursor.fetchall()
with open('latest_export.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f'Exported {len(results)} records to latest_export.json')
conn.close()
"
```

## 🔧 Debug Commands

### 1. Check Engine Configuration
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
print(f'Core symbols: {len(engine.core_symbols)}')
print(f'Extended symbols: {len(engine.extended_symbols)}')
print(f'Total symbols: {len(engine.all_symbols)}')
print(f'Database path: {engine.db_path}')
print(f'Output directory: {engine.output_dir}')
"
```

### 2. Test Data Fetching
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
df = engine.fetch_historical_data('BTCUSDT', '1d', 30)
print(f'Fetched {len(df)} records for BTCUSDT')
print(f'Date range: {df.index[0]} to {df.index[-1]}')
print(f'Price range: ${df[\"close\"].min():.2f} to ${df[\"close\"].max():.2f}')
"
```

### 3. Test Analysis for Single Asset
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
result = engine.analyze_asset('BTCUSDT', '1d', 365, optimize=True)
if result:
    print(f'Analysis complete for {result[\"symbol\"]}')
    print(f'Signal: {result[\"signal\"]}')
    print(f'Current price: ${result[\"current_price\"]:,.2f}')
    print(f'Potential return: {result[\"potential_return\"]:.2f}%')
    print(f'Total return: {result[\"total_return\"]:.2f}%')
else:
    print('Analysis failed')
"
```

## 📈 Performance Monitoring

### 1. Monitor Analysis Progress
```bash
python -c "
from crypto_engine import CryptoEngine
import time
engine = CryptoEngine('config.json')
start_time = time.time()
results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], '1d', 365)
end_time = time.time()
print(f'Analysis completed in {end_time - start_time:.2f} seconds')
print(f'Processed {len(results)} assets')
"
```

### 2. Check Cache Status
```bash
python -c "
import os
cache_dir = 'cache'
if os.path.exists(cache_dir):
    files = os.listdir(cache_dir)
    print(f'Cache directory: {cache_dir}')
    print(f'Cached files: {len(files)}')
    for file in files[:5]:
        print(f'  - {file}')
else:
    print('Cache directory not found')
"
```

## 🎯 Complete Workflow Example

Here's a complete workflow to test everything:

```bash
# 1. Test basic setup
python test_crypto_engine.py

# 2. Test complete workflow
python test_complete_workflow.py

# 3. Run analysis on core symbols
python run_crypto_engine.py --config config.json --optimize

# 4. Start dashboard to visualize results
python run_dashboard.py

# 5. In dashboard, click "Run Analysis" to test the interface
```

## 🔍 Troubleshooting Commands

### 1. Check VectorBTPro Installation
```bash
python -c "import vectorbtpro as vbt; print(f'VectorBTPro version: {vbt.__version__}')"
```

### 2. Check Binance API Connection
```bash
python -c "
from binance.client import Client
client = Client('test_key', 'test_secret')
try:
    info = client.get_exchange_info()
    print(f'Connected to Binance API')
    print(f'Available symbols: {len(info[\"symbols\"])}')
except Exception as e:
    print(f'Binance API error: {e}')
"
```

### 3. Check Database Integrity
```bash
python -c "
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
result = cursor.fetchone()
print(f'Database integrity: {result[0]}')
conn.close()
"
```

## 📊 Expected Output Examples

### Successful Analysis Output:
```
🚀 Starting Crypto Engine Analysis
============================================================
📊 Analyzing core symbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
⏰ Interval: 1d
📅 Days: 365
🔧 Optimize major coins: True
📁 Output format: both

📊 ANALYSIS RESULTS
============================================================
Total assets analyzed: 3
BUY signals: 1
SELL signals: 0
HOLD signals: 2
Average potential return: 8.45%
Average total return: 12.34%
Analysis duration: 0:02:15

🔥 TOP BUY SIGNALS:
1. BTCUSDT: 12.34% potential, 15.67% total return

✅ Crypto analysis complete!
🗄️  Database: crypto_data.db
📁 Results directory: results
```

### Successful Test Output:
```
🚀 Crypto Engine Test Suite
==================================================
🧪 Testing imports...
✅ VectorBTPro: 1.0.0
✅ Optuna: 3.4.0
✅ Binance client
✅ Pandas: 2.0.0
✅ NumPy: 1.24.0

🧪 Testing configuration...
✅ Configuration structure is valid
⚠️  API credentials not configured (using placeholder values)

🧪 Testing engine initialization...
✅ Engine initialized successfully
✅ Database file created

📊 Test Results: 6/6 tests passed
✅ All tests passed! Crypto engine is ready for use.
```

## 🎯 Next Steps After Testing

1. **Update config.json** with real Binance API credentials
2. **Run complete analysis**: `python run_crypto_engine.py --config config.json --optimize`
3. **Start dashboard**: `python run_dashboard.py`
4. **Test visualization**: Use the dashboard to run analysis and view results
5. **Export results**: Use dashboard export functions to generate files for main system
6. **Integrate with main system**: Use exported JSON/CSV files in the main Autonama system

## 📝 Notes

- All commands should be run from the `autonama.engine` directory
- Ensure VectorBTPro conda environment is activated
- The engine prioritizes local database data before fetching from Binance
- Analysis results are stored in both database and exported files
- Dashboard provides real-time visualization and testing capabilities 

This guide provides all the commands needed to run, test, and visualize the crypto engine.

## 📋 Prerequisites

1. **Activate VectorBTPro Environment**:
   ```bash
   conda activate autonama_vectorbt
   ```

2. **Install Dashboard Dependencies**:
   ```bash
   pip install -r requirements_dashboard.txt
   ```

3. **Update config.json** with your Binance API credentials:
   ```json
   {
       "binance_api_key": "your_actual_api_key_here",
       "binance_api_secret": "your_actual_api_secret_here"
   }
   ```

## 🧪 Testing Commands

### 1. Basic Engine Test
```bash
python test_crypto_engine.py
```
**Purpose**: Tests imports, configuration, engine initialization, and basic functionality.

### 2. Complete Workflow Test
```bash
python test_complete_workflow.py
```
**Purpose**: Tests the complete workflow including database scanning, data collection, analysis, export, and main system compatibility.

### 3. Quick Engine Test
```bash
python run_crypto_engine.py --test
```
**Purpose**: Quick test of engine setup and basic functionality.

## 🚀 Analysis Commands

### 1. Basic Analysis (Core Symbols)
```bash
python run_crypto_engine.py --config config.json
```
**Purpose**: Analyzes BTCUSDT, ETHUSDT, SOLUSDT with default settings.

### 2. Custom Symbols Analysis
```bash
python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,ADAUSDT
```
**Purpose**: Analyzes specific symbols of your choice.

### 3. Full Analysis with Optimization
```bash
python run_crypto_engine.py --config config.json --optimize --format both
```
**Purpose**: Runs analysis with parameter optimization for major coins and exports both CSV and JSON.

### 4. Top 100 Assets Analysis
```bash
python run_crypto_engine.py --config config.json --symbols $(python -c "from crypto_engine import CryptoEngine; e = CryptoEngine('config.json'); print(','.join(e.get_top_100_assets()[:10]))")
```
**Purpose**: Analyzes top 10 assets by volume from Binance.

## 📊 Visualization Commands

### 1. Start Streamlit Dashboard
```bash
python run_dashboard.py
```
**Purpose**: Starts the interactive Streamlit dashboard at http://localhost:8501

### 2. Direct Streamlit Command
```bash
streamlit run crypto_dashboard.py --server.port 8501
```
**Purpose**: Alternative way to start the dashboard directly.

## 🔍 Database Commands

### 1. Check Database Status
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
tables = cursor.fetchall()
print(f'Tables: {tables}')
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    print(f'{table[0]}: {count} records')
conn.close()
"
```

### 2. View Latest Analysis Results
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
df = pd.read_sql_query('SELECT * FROM crypto_analysis_results ORDER BY created_at DESC LIMIT 10', conn)
print(df)
conn.close()
"
```

## 📁 Export Commands

### 1. Export Latest Results to CSV
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
import pandas as pd
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
df = pd.read_sql_query('SELECT * FROM crypto_analysis_results', conn)
df.to_csv('latest_export.csv', index=False)
print(f'Exported {len(df)} records to latest_export.csv')
conn.close()
"
```

### 2. Export Latest Results to JSON
```bash
python -c "
from crypto_engine import CryptoEngine
import sqlite3
import json
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('SELECT * FROM crypto_analysis_results')
results = cursor.fetchall()
with open('latest_export.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f'Exported {len(results)} records to latest_export.json')
conn.close()
"
```

## 🔧 Debug Commands

### 1. Check Engine Configuration
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
print(f'Core symbols: {len(engine.core_symbols)}')
print(f'Extended symbols: {len(engine.extended_symbols)}')
print(f'Total symbols: {len(engine.all_symbols)}')
print(f'Database path: {engine.db_path}')
print(f'Output directory: {engine.output_dir}')
"
```

### 2. Test Data Fetching
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
df = engine.fetch_historical_data('BTCUSDT', '1d', 30)
print(f'Fetched {len(df)} records for BTCUSDT')
print(f'Date range: {df.index[0]} to {df.index[-1]}')
print(f'Price range: ${df[\"close\"].min():.2f} to ${df[\"close\"].max():.2f}')
"
```

### 3. Test Analysis for Single Asset
```bash
python -c "
from crypto_engine import CryptoEngine
engine = CryptoEngine('config.json')
result = engine.analyze_asset('BTCUSDT', '1d', 365, optimize=True)
if result:
    print(f'Analysis complete for {result[\"symbol\"]}')
    print(f'Signal: {result[\"signal\"]}')
    print(f'Current price: ${result[\"current_price\"]:,.2f}')
    print(f'Potential return: {result[\"potential_return\"]:.2f}%')
    print(f'Total return: {result[\"total_return\"]:.2f}%')
else:
    print('Analysis failed')
"
```

## 📈 Performance Monitoring

### 1. Monitor Analysis Progress
```bash
python -c "
from crypto_engine import CryptoEngine
import time
engine = CryptoEngine('config.json')
start_time = time.time()
results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], '1d', 365)
end_time = time.time()
print(f'Analysis completed in {end_time - start_time:.2f} seconds')
print(f'Processed {len(results)} assets')
"
```

### 2. Check Cache Status
```bash
python -c "
import os
cache_dir = 'cache'
if os.path.exists(cache_dir):
    files = os.listdir(cache_dir)
    print(f'Cache directory: {cache_dir}')
    print(f'Cached files: {len(files)}')
    for file in files[:5]:
        print(f'  - {file}')
else:
    print('Cache directory not found')
"
```

## 🎯 Complete Workflow Example

Here's a complete workflow to test everything:

```bash
# 1. Test basic setup
python test_crypto_engine.py

# 2. Test complete workflow
python test_complete_workflow.py

# 3. Run analysis on core symbols
python run_crypto_engine.py --config config.json --optimize

# 4. Start dashboard to visualize results
python run_dashboard.py

# 5. In dashboard, click "Run Analysis" to test the interface
```

## 🔍 Troubleshooting Commands

### 1. Check VectorBTPro Installation
```bash
python -c "import vectorbtpro as vbt; print(f'VectorBTPro version: {vbt.__version__}')"
```

### 2. Check Binance API Connection
```bash
python -c "
from binance.client import Client
client = Client('test_key', 'test_secret')
try:
    info = client.get_exchange_info()
    print(f'Connected to Binance API')
    print(f'Available symbols: {len(info[\"symbols\"])}')
except Exception as e:
    print(f'Binance API error: {e}')
"
```

### 3. Check Database Integrity
```bash
python -c "
import sqlite3
engine = CryptoEngine('config.json')
conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
result = cursor.fetchone()
print(f'Database integrity: {result[0]}')
conn.close()
"
```

## 📊 Expected Output Examples

### Successful Analysis Output:
```
🚀 Starting Crypto Engine Analysis
============================================================
📊 Analyzing core symbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
⏰ Interval: 1d
📅 Days: 365
🔧 Optimize major coins: True
📁 Output format: both

📊 ANALYSIS RESULTS
============================================================
Total assets analyzed: 3
BUY signals: 1
SELL signals: 0
HOLD signals: 2
Average potential return: 8.45%
Average total return: 12.34%
Analysis duration: 0:02:15

🔥 TOP BUY SIGNALS:
1. BTCUSDT: 12.34% potential, 15.67% total return

✅ Crypto analysis complete!
🗄️  Database: crypto_data.db
📁 Results directory: results
```

### Successful Test Output:
```
🚀 Crypto Engine Test Suite
==================================================
🧪 Testing imports...
✅ VectorBTPro: 1.0.0
✅ Optuna: 3.4.0
✅ Binance client
✅ Pandas: 2.0.0
✅ NumPy: 1.24.0

🧪 Testing configuration...
✅ Configuration structure is valid
⚠️  API credentials not configured (using placeholder values)

🧪 Testing engine initialization...
✅ Engine initialized successfully
✅ Database file created

📊 Test Results: 6/6 tests passed
✅ All tests passed! Crypto engine is ready for use.
```

## 🎯 Next Steps After Testing

1. **Update config.json** with real Binance API credentials
2. **Run complete analysis**: `python run_crypto_engine.py --config config.json --optimize`
3. **Start dashboard**: `python run_dashboard.py`
4. **Test visualization**: Use the dashboard to run analysis and view results
5. **Export results**: Use dashboard export functions to generate files for main system
6. **Integrate with main system**: Use exported JSON/CSV files in the main Autonama system

## 📝 Notes

- All commands should be run from the `autonama.engine` directory
- Ensure VectorBTPro conda environment is activated
- The engine prioritizes local database data before fetching from Binance
- Analysis results are stored in both database and exported files
- Dashboard provides real-time visualization and testing capabilities 
 