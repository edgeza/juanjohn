# 🚀 VectorBTPro Local Analysis Engine

## Overview

The VectorBTPro Local Analysis Engine is a **comprehensive cryptocurrency analysis system** that runs **locally** using VectorBTPro in a conda environment. It performs polynomial regression analysis and generates trading signals that are then ingested into the main system.

## 🎯 Key Features

### 📊 **Polynomial Regression Analysis**
- **VectorBTPro Integration**: Advanced backtesting with VectorBTPro
- **Polynomial Regression**: Degree 2-6 polynomial fitting with confidence bands
- **Signal Generation**: BUY/SELL/HOLD signals based on price position relative to bands
- **Parameter Optimization**: Optuna-based optimization for degree and kstd parameters

### 🔄 **Data Processing**
- **Local SQLite Database**: Stores historical data locally for fast access
- **Smart Caching**: Reduces API calls with 24-hour cache
- **Top 100 Assets**: Analyzes top 100 USDT pairs by volume
- **Parallel Processing**: Multi-threaded analysis for efficiency

### 📈 **Output Generation**
- **CSV Results**: Structured analysis results for ingestion
- **JSON Results**: Alternative format for flexibility
- **Database Integration**: PostgreSQL tables for web application
- **Local Storage**: SQLite database for historical data

## 🏗️ Architecture

```
autonama.engine/
├── vectorbt_local_engine.py      # Main VectorBTPro engine
├── run_vectorbt_analysis.py      # Analysis runner script
├── vectorbt_ingestion.py         # Database ingestion system
├── config.json                   # Configuration file
├── requirements_vectorbt.txt     # Conda environment dependencies
├── results/                      # Generated results
│   ├── vectorbt_analysis_*.csv  # CSV results
│   └── vectorbt_analysis_*.json # JSON results
├── cache/                        # Cached historical data
└── local_data.db                 # Local SQLite database
```

## 🚀 Setup Guide

### **Step 1: Create Conda Environment**

```bash
# Create new conda environment
conda create -n autonama_vectorbt python=3.9

# Activate environment
conda activate autonama_vectorbt

# Install VectorBTPro (requires license)
pip install vectorbtpro

# Install other dependencies
pip install -r requirements_vectorbt.txt
```

### **Step 2: Configure API Credentials**

Edit `config.json` with your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key_here",
    "binance_api_secret": "your_actual_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

### **Step 3: Run Analysis**

```bash
# Analyze core movers
python run_vectorbt_analysis.py --config config.json

# Analyze top 100 assets
python run_vectorbt_analysis.py --config config.json --top-100

# Analyze specific symbols
python run_vectorbt_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Optimize parameters for major coins
python run_vectorbt_analysis.py --config config.json --optimize

# Output only CSV format
python run_vectorbt_analysis.py --config config.json --format csv
```

### **Step 4: Ingest Results**

```bash
# Ingest results into database
python vectorbt_ingestion.py --config config.json --results-dir results
```

## 📊 Analysis Process

### **1. Data Collection**
- Fetches historical data from Binance API
- Stores in local SQLite database for fast access
- Caches data to reduce API calls

### **2. Parameter Optimization**
- Uses Optuna to optimize polynomial degree (2-6) and kstd (1.5-3.0)
- Optimizes on major coins (BTCUSDT, ETHUSDT, SOLUSDT)
- Applies best parameters to all other coins

### **3. Polynomial Regression**
- Fits polynomial regression to price data
- Calculates confidence bands (upper/lower bands)
- Generates BUY/SELL/HOLD signals based on price position

### **4. VectorBTPro Backtesting**
- Creates portfolio with $100,000 initial capital
- Applies 0.15% fees and 0.05% slippage
- Calculates performance metrics (Total Return, Sharpe Ratio, Max Drawdown)

### **5. Signal Generation**
- **BUY**: Price below lower regression band
- **SELL**: Price above upper regression band
- **HOLD**: Price within regression bands

## 📈 Output Format

### **CSV Results Structure**
```csv
symbol,interval,current_price,lower_band,upper_band,signal,potential_return,total_return,sharpe_ratio,max_drawdown,degree,kstd,analysis_date
BTCUSDT,1d,45000.0,44000.0,46000.0,BUY,15.2,12.5,1.8,8.5,4,2.0,2024-01-15T10:30:00
ETHUSDT,1d,2800.0,2750.0,2850.0,HOLD,3.6,8.2,1.2,5.1,4,2.0,2024-01-15T10:30:00
```

### **JSON Results Structure**
```json
[
    {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "current_price": 45000.0,
        "lower_band": 44000.0,
        "upper_band": 46000.0,
        "signal": "BUY",
        "potential_return": 15.2,
        "total_return": 12.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.5,
        "degree": 4,
        "kstd": 2.0,
        "analysis_date": "2024-01-15T10:30:00"
    }
]
```

## 🗄️ Database Integration

### **Tables Created**
- **trading.alerts**: Signal alerts with VectorBTPro metrics
- **trading.vectorbt_analysis**: Detailed VectorBTPro analysis results

### **Ingestion Process**
1. **Load Results**: Read CSV/JSON files from results directory
2. **Validate Data**: Check data integrity and completeness
3. **Database Insert**: Store results in PostgreSQL
4. **Cleanup**: Remove old data (configurable retention)

## 🔧 Configuration

### **config.json**
```json
{
    "binance_api_key": "your_api_key",
    "binance_api_secret": "your_api_secret",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

## 🚨 Important Notes

### **VectorBTPro License**
- **Requires VectorBTPro License**: This engine requires a VectorBTPro license
- **Local Installation**: Must be installed in a local conda environment, NOT in Docker
- **License Activation**: Ensure VectorBTPro is properly licensed and activated

### **Local Processing**
- All intensive computation runs locally using VectorBTPro
- No cloud costs for analysis processing
- Results are stored in cloud database for display

### **API Limits**
- Binance API has rate limits
- Use caching to minimize API calls
- Process assets in batches if needed

### **Data Retention**
- Historical data cached locally for 24 hours
- Database cleanup removes old data after 30 days
- Local SQLite database for historical data storage

## 🔄 Integration with Main System

### **Data Flow**
```
Local VectorBTPro Engine → CSV/JSON Results → Ingestion System → PostgreSQL → Web Application
```

### **Schedule Recommendations**
- **Daily Analysis**: Run analysis once per day
- **Weekly Optimization**: Re-optimize parameters weekly
- **Monthly Cleanup**: Database cleanup monthly

### **Automation Scripts**
```bash
#!/bin/bash
# daily_vectorbt_analysis.sh

cd autonama.engine
conda activate autonama_vectorbt

# Run analysis
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
python vectorbt_ingestion.py --config config.json --results-dir results

echo "Daily VectorBTPro analysis complete!"
```

## 🛠️ Advanced Usage

### **Custom Analysis Parameters**
```python
from vectorbt_local_engine import VectorBTLocalEngine

# Initialize engine
engine = VectorBTLocalEngine(binance_config)

# Analyze specific asset with custom parameters
result = engine.analyze_asset('BTCUSDT', degree=5, kstd=2.5)

# Run optimization
results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT'], optimize_major_coins=True)
```

### **Batch Processing**
```python
# Analyze multiple symbols
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
results = engine.analyze_all_assets(symbols)

# Save results
engine.save_results_to_csv(results)
engine.save_results_to_json(results)
```

## 🔍 Monitoring and Logs

### **Log Files**
- `vectorbt_local_engine.log`: Main engine logs
- `vectorbt_ingestion.log`: Ingestion system logs

### **Key Metrics**
- Analysis duration
- Assets processed successfully
- Signals generated
- Database operations
- Error rates

### **Success Indicators**
- CSV/JSON files generated in results/
- Database records inserted
- Web dashboard showing alerts

## 🚨 Troubleshooting

### **Common Issues**

#### **VectorBTPro License**
```bash
# Check VectorBTPro installation
python -c "import vectorbtpro; print(vectorbtpro.__version__)"

# Activate license if needed
# Follow VectorBTPro license activation instructions
```

#### **Missing Dependencies**
```bash
# Install in conda environment
conda activate autonama_vectorbt
pip install -r requirements_vectorbt.txt
```

#### **API Rate Limits**
```bash
# Use caching (enabled by default)
# Process fewer assets at once
python run_vectorbt_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT
```

#### **Database Connection**
```bash
# Check PostgreSQL is running
# Verify database credentials in config.json
# Test connection manually
```

### **Performance Tips**
- Use SSD storage for cache directory
- Increase system memory if analyzing many assets
- Run analysis during off-peak hours
- Use parallel processing (enabled by default)

## 🎯 Next Steps

1. **Setup Environment**: Create conda environment and install VectorBTPro
2. **Configure API**: Edit `config.json` with your credentials
3. **Run Analysis**: `python run_vectorbt_analysis.py --config config.json --top-100`
4. **Ingest Results**: `python vectorbt_ingestion.py --config config.json --results-dir results`
5. **View Dashboard**: http://localhost:3001

## 📞 Support

If you encounter issues:
1. Check the log files for error messages
2. Verify VectorBTPro license is active
3. Ensure all dependencies are installed in conda environment
4. Check Binance API credentials
5. Verify database connection settings

---

**This system provides comprehensive cryptocurrency analysis using VectorBTPro while keeping intensive processing costs local and only storing results in the cloud for display. The web application will show real-time alerts and analytics based on your local VectorBTPro analysis results.** 

## Overview

The VectorBTPro Local Analysis Engine is a **comprehensive cryptocurrency analysis system** that runs **locally** using VectorBTPro in a conda environment. It performs polynomial regression analysis and generates trading signals that are then ingested into the main system.

## 🎯 Key Features

### 📊 **Polynomial Regression Analysis**
- **VectorBTPro Integration**: Advanced backtesting with VectorBTPro
- **Polynomial Regression**: Degree 2-6 polynomial fitting with confidence bands
- **Signal Generation**: BUY/SELL/HOLD signals based on price position relative to bands
- **Parameter Optimization**: Optuna-based optimization for degree and kstd parameters

### 🔄 **Data Processing**
- **Local SQLite Database**: Stores historical data locally for fast access
- **Smart Caching**: Reduces API calls with 24-hour cache
- **Top 100 Assets**: Analyzes top 100 USDT pairs by volume
- **Parallel Processing**: Multi-threaded analysis for efficiency

### 📈 **Output Generation**
- **CSV Results**: Structured analysis results for ingestion
- **JSON Results**: Alternative format for flexibility
- **Database Integration**: PostgreSQL tables for web application
- **Local Storage**: SQLite database for historical data

## 🏗️ Architecture

```
autonama.engine/
├── vectorbt_local_engine.py      # Main VectorBTPro engine
├── run_vectorbt_analysis.py      # Analysis runner script
├── vectorbt_ingestion.py         # Database ingestion system
├── config.json                   # Configuration file
├── requirements_vectorbt.txt     # Conda environment dependencies
├── results/                      # Generated results
│   ├── vectorbt_analysis_*.csv  # CSV results
│   └── vectorbt_analysis_*.json # JSON results
├── cache/                        # Cached historical data
└── local_data.db                 # Local SQLite database
```

## 🚀 Setup Guide

### **Step 1: Create Conda Environment**

```bash
# Create new conda environment
conda create -n autonama_vectorbt python=3.9

# Activate environment
conda activate autonama_vectorbt

# Install VectorBTPro (requires license)
pip install vectorbtpro

# Install other dependencies
pip install -r requirements_vectorbt.txt
```

### **Step 2: Configure API Credentials**

Edit `config.json` with your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key_here",
    "binance_api_secret": "your_actual_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

### **Step 3: Run Analysis**

```bash
# Analyze core movers
python run_vectorbt_analysis.py --config config.json

# Analyze top 100 assets
python run_vectorbt_analysis.py --config config.json --top-100

# Analyze specific symbols
python run_vectorbt_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Optimize parameters for major coins
python run_vectorbt_analysis.py --config config.json --optimize

# Output only CSV format
python run_vectorbt_analysis.py --config config.json --format csv
```

### **Step 4: Ingest Results**

```bash
# Ingest results into database
python vectorbt_ingestion.py --config config.json --results-dir results
```

## 📊 Analysis Process

### **1. Data Collection**
- Fetches historical data from Binance API
- Stores in local SQLite database for fast access
- Caches data to reduce API calls

### **2. Parameter Optimization**
- Uses Optuna to optimize polynomial degree (2-6) and kstd (1.5-3.0)
- Optimizes on major coins (BTCUSDT, ETHUSDT, SOLUSDT)
- Applies best parameters to all other coins

### **3. Polynomial Regression**
- Fits polynomial regression to price data
- Calculates confidence bands (upper/lower bands)
- Generates BUY/SELL/HOLD signals based on price position

### **4. VectorBTPro Backtesting**
- Creates portfolio with $100,000 initial capital
- Applies 0.15% fees and 0.05% slippage
- Calculates performance metrics (Total Return, Sharpe Ratio, Max Drawdown)

### **5. Signal Generation**
- **BUY**: Price below lower regression band
- **SELL**: Price above upper regression band
- **HOLD**: Price within regression bands

## 📈 Output Format

### **CSV Results Structure**
```csv
symbol,interval,current_price,lower_band,upper_band,signal,potential_return,total_return,sharpe_ratio,max_drawdown,degree,kstd,analysis_date
BTCUSDT,1d,45000.0,44000.0,46000.0,BUY,15.2,12.5,1.8,8.5,4,2.0,2024-01-15T10:30:00
ETHUSDT,1d,2800.0,2750.0,2850.0,HOLD,3.6,8.2,1.2,5.1,4,2.0,2024-01-15T10:30:00
```

### **JSON Results Structure**
```json
[
    {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "current_price": 45000.0,
        "lower_band": 44000.0,
        "upper_band": 46000.0,
        "signal": "BUY",
        "potential_return": 15.2,
        "total_return": 12.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.5,
        "degree": 4,
        "kstd": 2.0,
        "analysis_date": "2024-01-15T10:30:00"
    }
]
```

## 🗄️ Database Integration

### **Tables Created**
- **trading.alerts**: Signal alerts with VectorBTPro metrics
- **trading.vectorbt_analysis**: Detailed VectorBTPro analysis results

### **Ingestion Process**
1. **Load Results**: Read CSV/JSON files from results directory
2. **Validate Data**: Check data integrity and completeness
3. **Database Insert**: Store results in PostgreSQL
4. **Cleanup**: Remove old data (configurable retention)

## 🔧 Configuration

### **config.json**
```json
{
    "binance_api_key": "your_api_key",
    "binance_api_secret": "your_api_secret",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

## 🚨 Important Notes

### **VectorBTPro License**
- **Requires VectorBTPro License**: This engine requires a VectorBTPro license
- **Local Installation**: Must be installed in a local conda environment, NOT in Docker
- **License Activation**: Ensure VectorBTPro is properly licensed and activated

### **Local Processing**
- All intensive computation runs locally using VectorBTPro
- No cloud costs for analysis processing
- Results are stored in cloud database for display

### **API Limits**
- Binance API has rate limits
- Use caching to minimize API calls
- Process assets in batches if needed

### **Data Retention**
- Historical data cached locally for 24 hours
- Database cleanup removes old data after 30 days
- Local SQLite database for historical data storage

## 🔄 Integration with Main System

### **Data Flow**
```
Local VectorBTPro Engine → CSV/JSON Results → Ingestion System → PostgreSQL → Web Application
```

### **Schedule Recommendations**
- **Daily Analysis**: Run analysis once per day
- **Weekly Optimization**: Re-optimize parameters weekly
- **Monthly Cleanup**: Database cleanup monthly

### **Automation Scripts**
```bash
#!/bin/bash
# daily_vectorbt_analysis.sh

cd autonama.engine
conda activate autonama_vectorbt

# Run analysis
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
python vectorbt_ingestion.py --config config.json --results-dir results

echo "Daily VectorBTPro analysis complete!"
```

## 🛠️ Advanced Usage

### **Custom Analysis Parameters**
```python
from vectorbt_local_engine import VectorBTLocalEngine

# Initialize engine
engine = VectorBTLocalEngine(binance_config)

# Analyze specific asset with custom parameters
result = engine.analyze_asset('BTCUSDT', degree=5, kstd=2.5)

# Run optimization
results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT'], optimize_major_coins=True)
```

### **Batch Processing**
```python
# Analyze multiple symbols
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
results = engine.analyze_all_assets(symbols)

# Save results
engine.save_results_to_csv(results)
engine.save_results_to_json(results)
```

## 🔍 Monitoring and Logs

### **Log Files**
- `vectorbt_local_engine.log`: Main engine logs
- `vectorbt_ingestion.log`: Ingestion system logs

### **Key Metrics**
- Analysis duration
- Assets processed successfully
- Signals generated
- Database operations
- Error rates

### **Success Indicators**
- CSV/JSON files generated in results/
- Database records inserted
- Web dashboard showing alerts

## 🚨 Troubleshooting

### **Common Issues**

#### **VectorBTPro License**
```bash
# Check VectorBTPro installation
python -c "import vectorbtpro; print(vectorbtpro.__version__)"

# Activate license if needed
# Follow VectorBTPro license activation instructions
```

#### **Missing Dependencies**
```bash
# Install in conda environment
conda activate autonama_vectorbt
pip install -r requirements_vectorbt.txt
```

#### **API Rate Limits**
```bash
# Use caching (enabled by default)
# Process fewer assets at once
python run_vectorbt_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT
```

#### **Database Connection**
```bash
# Check PostgreSQL is running
# Verify database credentials in config.json
# Test connection manually
```

### **Performance Tips**
- Use SSD storage for cache directory
- Increase system memory if analyzing many assets
- Run analysis during off-peak hours
- Use parallel processing (enabled by default)

## 🎯 Next Steps

1. **Setup Environment**: Create conda environment and install VectorBTPro
2. **Configure API**: Edit `config.json` with your credentials
3. **Run Analysis**: `python run_vectorbt_analysis.py --config config.json --top-100`
4. **Ingest Results**: `python vectorbt_ingestion.py --config config.json --results-dir results`
5. **View Dashboard**: http://localhost:3001

## 📞 Support

If you encounter issues:
1. Check the log files for error messages
2. Verify VectorBTPro license is active
3. Ensure all dependencies are installed in conda environment
4. Check Binance API credentials
5. Verify database connection settings

---

**This system provides comprehensive cryptocurrency analysis using VectorBTPro while keeping intensive processing costs local and only storing results in the cloud for display. The web application will show real-time alerts and analytics based on your local VectorBTPro analysis results.** 
 