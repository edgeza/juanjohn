# 🚀 Autonama Crypto Engine

A comprehensive crypto-focused analysis engine that combines the best features from Autonama Dashboard and CoinScanner, using VectorBTPro for advanced polynomial regression analysis.

## 🎯 Features

- **Crypto-Only Analysis**: Focused on 100+ cryptocurrency pairs
- **VectorBTPro Integration**: Advanced polynomial regression with optimization
- **Real-time Data**: Live Binance API integration with caching
- **Multiple Timeframes**: Support for 1d and 15m intervals
- **Optuna Optimization**: Automatic parameter optimization for major coins
- **Local Database**: SQLite storage for historical data and results
- **Comprehensive Output**: CSV and JSON results for ingestion
- **Parallel Processing**: Multi-threaded analysis for speed

## 📋 Prerequisites

1. **Conda Environment**: Ensure you have the VectorBTPro conda environment activated
   ```bash
   conda activate autonama_vectorbt
   ```

2. **VectorBTPro License**: Valid VectorBTPro license required

3. **Binance API**: API key and secret for data access

## 🔧 Setup

### 1. Configuration

Update `config.json` with your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key_here",
    "binance_api_secret": "your_actual_api_secret_here",
    "default_settings": {
        "interval": "1d",
        "degree": 4,
        "kstd": 2.0,
        "days": 720,
        "output_directory": "results"
    }
}
```

### 2. Test Setup

Run the comprehensive test suite:

```bash
python test_crypto_engine.py
```

### 3. Quick Test

Test the engine with basic functionality:

```bash
python run_crypto_engine.py --test
```

## 🚀 Usage

### Basic Analysis

Analyze core crypto symbols:

```bash
python run_crypto_engine.py --config config.json
```

### Custom Symbols

Analyze specific symbols:

```bash
python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT
```

### Full Analysis with Optimization

Run complete analysis with parameter optimization:

```bash
python run_crypto_engine.py --config config.json --optimize --format both
```

### Top 100 Assets

Analyze top 100 assets by volume:

```bash
python run_crypto_engine.py --config config.json --symbols $(python -c "from crypto_engine import CryptoEngine; e = CryptoEngine('config.json'); print(','.join(e.get_top_100_assets()[:10]))")
```

## 📊 Analysis Process

### 1. Data Collection
- Fetches historical data from Binance API
- Caches data locally to avoid rate limits
- Stores data in SQLite database

### 2. Data Preprocessing
- Removes outliers using Z-score method
- Handles missing values with forward/backward fill
- Applies rolling average smoothing

### 3. Polynomial Regression
- Uses VectorBTPro for polynomial fitting
- Calculates upper and lower bands (kstd standard deviations)
- Generates BUY/SELL/HOLD signals

### 4. Optimization (Major Coins)
- Uses Optuna for parameter optimization
- Optimizes degree (2-6) and kstd (1.5-3.0)
- Maximizes total return while considering risk

### 5. Portfolio Analysis
- Creates VectorBTPro portfolios
- Calculates returns, Sharpe ratio, max drawdown
- Generates comprehensive statistics

## 📁 Output Files

### CSV Results
```
results/crypto_analysis_results_20241201_143022.csv
```

Columns:
- `symbol`: Cryptocurrency symbol
- `interval`: Time interval (1d, 15m)
- `current_price`: Current price
- `lower_band`, `upper_band`: Regression bands
- `signal`: BUY/SELL/HOLD
- `potential_return`: Potential return percentage
- `total_return`: Historical backtest return
- `sharpe_ratio`: Risk-adjusted return
- `max_drawdown`: Maximum drawdown
- `degree`, `kstd`: Parameters used

### JSON Results
```
results/crypto_analysis_results_20241201_143022.json
```

Complete analysis results with metadata and timestamps.

## 🗄️ Database Schema

### crypto_historical_data
- Historical price data from Binance
- Cached for faster subsequent analysis

### crypto_analysis_results
- Analysis results with signals and statistics
- Used for tracking performance over time

### crypto_optimization_results
- Optimization results for major coins
- Parameter history and performance

## 🔍 Signal Generation

### BUY Signal
- Current price < lower band
- Indicates oversold condition
- Potential for upward movement

### SELL Signal
- Current price > upper band
- Indicates overbought condition
- Potential for downward movement

### HOLD Signal
- Current price between bands
- Neutral position
- Wait for clearer signal

## ⚙️ Configuration Options

### Analysis Settings
- `interval`: Time interval (1d, 15m)
- `days`: Historical data period
- `degree`: Polynomial degree (2-6)
- `kstd`: Standard deviation multiplier (1.5-3.0)

### Optimization Settings
- `optimize_major_coins`: Enable for BTC, ETH, SOL
- `optimization_trials`: Number of Optuna trials
- `parallel_workers`: Number of parallel processes

### Output Settings
- `csv_enabled`: Generate CSV files
- `json_enabled`: Generate JSON files
- `include_summary`: Include summary statistics
- `include_metadata`: Include analysis metadata

## 📈 Performance Metrics

### Return Metrics
- **Total Return**: Historical backtest performance
- **Potential Return**: Expected return based on bands
- **Sharpe Ratio**: Risk-adjusted return measure

### Risk Metrics
- **Max Drawdown**: Maximum historical loss
- **Volatility**: Price movement variability
- **Win Rate**: Percentage of profitable trades

## 🔧 Troubleshooting

### Common Issues

1. **VectorBTPro Not Found**
   ```bash
   conda activate autonama_vectorbt
   pip install vectorbtpro
   ```

2. **API Rate Limits**
   - Engine includes automatic rate limiting
   - Caches data to reduce API calls
   - Uses exponential backoff for errors

3. **Insufficient Data**
   - Minimum 50 data points required
   - Check symbol availability on Binance
   - Verify API credentials

4. **Database Errors**
   - Check file permissions
   - Ensure sufficient disk space
   - Verify SQLite installation

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Example Output

```
🚀 STARTING CRYPTO ANALYSIS
============================================================
📊 Analyzing core symbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
⏰ Interval: 1d
📅 Days: 720
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

## 🔄 Integration with Autonama System

The crypto engine is designed to integrate seamlessly with the Autonama system:

1. **Results Generation**: Creates files ready for ingestion
2. **Database Storage**: Local SQLite for historical tracking
3. **API Compatibility**: JSON format matches API expectations
4. **Real-time Updates**: Can be scheduled for regular analysis

## 📝 License

This engine is part of the Autonama system and requires a valid VectorBTPro license for operation.

## 🤝 Contributing

When contributing to the crypto engine:

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure compatibility with the main Autonama system

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Run the test suite to identify problems
3. Review logs in `crypto_engine.log`
4. Verify VectorBTPro license status 

A comprehensive crypto-focused analysis engine that combines the best features from Autonama Dashboard and CoinScanner, using VectorBTPro for advanced polynomial regression analysis.

## 🎯 Features

- **Crypto-Only Analysis**: Focused on 100+ cryptocurrency pairs
- **VectorBTPro Integration**: Advanced polynomial regression with optimization
- **Real-time Data**: Live Binance API integration with caching
- **Multiple Timeframes**: Support for 1d and 15m intervals
- **Optuna Optimization**: Automatic parameter optimization for major coins
- **Local Database**: SQLite storage for historical data and results
- **Comprehensive Output**: CSV and JSON results for ingestion
- **Parallel Processing**: Multi-threaded analysis for speed

## 📋 Prerequisites

1. **Conda Environment**: Ensure you have the VectorBTPro conda environment activated
   ```bash
   conda activate autonama_vectorbt
   ```

2. **VectorBTPro License**: Valid VectorBTPro license required

3. **Binance API**: API key and secret for data access

## 🔧 Setup

### 1. Configuration

Update `config.json` with your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key_here",
    "binance_api_secret": "your_actual_api_secret_here",
    "default_settings": {
        "interval": "1d",
        "degree": 4,
        "kstd": 2.0,
        "days": 720,
        "output_directory": "results"
    }
}
```

### 2. Test Setup

Run the comprehensive test suite:

```bash
python test_crypto_engine.py
```

### 3. Quick Test

Test the engine with basic functionality:

```bash
python run_crypto_engine.py --test
```

## 🚀 Usage

### Basic Analysis

Analyze core crypto symbols:

```bash
python run_crypto_engine.py --config config.json
```

### Custom Symbols

Analyze specific symbols:

```bash
python run_crypto_engine.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT
```

### Full Analysis with Optimization

Run complete analysis with parameter optimization:

```bash
python run_crypto_engine.py --config config.json --optimize --format both
```

### Top 100 Assets

Analyze top 100 assets by volume:

```bash
python run_crypto_engine.py --config config.json --symbols $(python -c "from crypto_engine import CryptoEngine; e = CryptoEngine('config.json'); print(','.join(e.get_top_100_assets()[:10]))")
```

## 📊 Analysis Process

### 1. Data Collection
- Fetches historical data from Binance API
- Caches data locally to avoid rate limits
- Stores data in SQLite database

### 2. Data Preprocessing
- Removes outliers using Z-score method
- Handles missing values with forward/backward fill
- Applies rolling average smoothing

### 3. Polynomial Regression
- Uses VectorBTPro for polynomial fitting
- Calculates upper and lower bands (kstd standard deviations)
- Generates BUY/SELL/HOLD signals

### 4. Optimization (Major Coins)
- Uses Optuna for parameter optimization
- Optimizes degree (2-6) and kstd (1.5-3.0)
- Maximizes total return while considering risk

### 5. Portfolio Analysis
- Creates VectorBTPro portfolios
- Calculates returns, Sharpe ratio, max drawdown
- Generates comprehensive statistics

## 📁 Output Files

### CSV Results
```
results/crypto_analysis_results_20241201_143022.csv
```

Columns:
- `symbol`: Cryptocurrency symbol
- `interval`: Time interval (1d, 15m)
- `current_price`: Current price
- `lower_band`, `upper_band`: Regression bands
- `signal`: BUY/SELL/HOLD
- `potential_return`: Potential return percentage
- `total_return`: Historical backtest return
- `sharpe_ratio`: Risk-adjusted return
- `max_drawdown`: Maximum drawdown
- `degree`, `kstd`: Parameters used

### JSON Results
```
results/crypto_analysis_results_20241201_143022.json
```

Complete analysis results with metadata and timestamps.

## 🗄️ Database Schema

### crypto_historical_data
- Historical price data from Binance
- Cached for faster subsequent analysis

### crypto_analysis_results
- Analysis results with signals and statistics
- Used for tracking performance over time

### crypto_optimization_results
- Optimization results for major coins
- Parameter history and performance

## 🔍 Signal Generation

### BUY Signal
- Current price < lower band
- Indicates oversold condition
- Potential for upward movement

### SELL Signal
- Current price > upper band
- Indicates overbought condition
- Potential for downward movement

### HOLD Signal
- Current price between bands
- Neutral position
- Wait for clearer signal

## ⚙️ Configuration Options

### Analysis Settings
- `interval`: Time interval (1d, 15m)
- `days`: Historical data period
- `degree`: Polynomial degree (2-6)
- `kstd`: Standard deviation multiplier (1.5-3.0)

### Optimization Settings
- `optimize_major_coins`: Enable for BTC, ETH, SOL
- `optimization_trials`: Number of Optuna trials
- `parallel_workers`: Number of parallel processes

### Output Settings
- `csv_enabled`: Generate CSV files
- `json_enabled`: Generate JSON files
- `include_summary`: Include summary statistics
- `include_metadata`: Include analysis metadata

## 📈 Performance Metrics

### Return Metrics
- **Total Return**: Historical backtest performance
- **Potential Return**: Expected return based on bands
- **Sharpe Ratio**: Risk-adjusted return measure

### Risk Metrics
- **Max Drawdown**: Maximum historical loss
- **Volatility**: Price movement variability
- **Win Rate**: Percentage of profitable trades

## 🔧 Troubleshooting

### Common Issues

1. **VectorBTPro Not Found**
   ```bash
   conda activate autonama_vectorbt
   pip install vectorbtpro
   ```

2. **API Rate Limits**
   - Engine includes automatic rate limiting
   - Caches data to reduce API calls
   - Uses exponential backoff for errors

3. **Insufficient Data**
   - Minimum 50 data points required
   - Check symbol availability on Binance
   - Verify API credentials

4. **Database Errors**
   - Check file permissions
   - Ensure sufficient disk space
   - Verify SQLite installation

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Example Output

```
🚀 STARTING CRYPTO ANALYSIS
============================================================
📊 Analyzing core symbols: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
⏰ Interval: 1d
📅 Days: 720
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

## 🔄 Integration with Autonama System

The crypto engine is designed to integrate seamlessly with the Autonama system:

1. **Results Generation**: Creates files ready for ingestion
2. **Database Storage**: Local SQLite for historical tracking
3. **API Compatibility**: JSON format matches API expectations
4. **Real-time Updates**: Can be scheduled for regular analysis

## 📝 License

This engine is part of the Autonama system and requires a valid VectorBTPro license for operation.

## 🤝 Contributing

When contributing to the crypto engine:

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure compatibility with the main Autonama system

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Run the test suite to identify problems
3. Review logs in `crypto_engine.log`
4. Verify VectorBTPro license status 
 