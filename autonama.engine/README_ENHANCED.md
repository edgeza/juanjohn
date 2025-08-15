# 🚀 Enhanced Local Analysis Engine

## Overview

The Enhanced Local Analysis Engine is a comprehensive cryptocurrency analysis system that runs **locally** to avoid cloud computing costs. It performs advanced analytics including polynomial regression, cross-correlation analysis, technical indicators, and signal generation for all major cryptocurrencies.

## 🎯 Key Features

### 📊 Comprehensive Analysis
- **Polynomial Regression Analysis**: Advanced trend analysis with confidence bands
- **Cross-Correlation Analysis**: Identifies highly correlated asset pairs
- **Technical Indicators**: 20+ indicators including RSI, MACD, Bollinger Bands, ATR
- **Signal Generation**: BUY/SELL/HOLD signals with confidence levels
- **Risk Assessment**: Automatic risk level classification

### 🔄 Data Processing
- **Historical Data**: Fetches up to 720 days of daily candlestick data
- **Smart Caching**: Local caching to reduce API calls
- **Top 100 Assets**: Analyzes top 100 USDT pairs by volume
- **Real-time Updates**: Configurable analysis intervals

### 📈 Output Generation
- **JSON Results**: Structured analysis results
- **Charts & Visualizations**: Matplotlib and Plotly charts
- **Database Integration**: PostgreSQL ingestion system
- **Summary Reports**: Comprehensive analysis summaries

## 🏗️ Architecture

```
autonama.engine/
├── enhanced_local_engine.py      # Main analysis engine
├── run_enhanced_analysis.py      # Analysis runner script
├── ingestion_system.py           # Database ingestion system
├── config.json                   # Configuration file
├── requirements.txt              # Python dependencies
├── results/                      # Generated results
│   ├── enhanced_analysis_*.json  # Analysis results
│   ├── charts/                   # Generated charts
│   └── correlations/             # Correlation analysis
└── cache/                        # Cached historical data
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Binance API
cp config.json.example config.json
# Edit config.json with your Binance API credentials
```

### 2. Run Analysis

```bash
# Analyze core movers
python run_enhanced_analysis.py --config config.json

# Analyze top 100 assets
python run_enhanced_analysis.py --config config.json --top-100

# Analyze specific symbols
python run_enhanced_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Generate charts
python run_enhanced_analysis.py --config config.json --generate-charts

# Include correlation analysis
python run_enhanced_analysis.py --config config.json --correlation-analysis
```

### 3. Ingest Results

```bash
# Ingest results into database
python ingestion_system.py --config config.json --results-dir results
```

## 📋 Configuration

### config.json
```json
{
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
        "top_100_enabled": true,
        "custom_symbols": []
    },
    "cache_settings": {
        "enabled": true,
        "cache_duration_hours": 24
    }
}
```

## 🔧 Analysis Parameters

### Polynomial Regression
- **degree**: Polynomial degree (default: 4)
- **kstd**: Standard deviation multiplier for bands (default: 2.0)

### Technical Analysis
- **interval**: Time interval (1d, 4h, 1h, etc.)
- **days**: Historical data period (max: 720 days)

### Signal Generation
- **BUY**: Price below lower regression band
- **SELL**: Price above upper regression band  
- **HOLD**: Price within regression bands

## 📊 Output Format

### Analysis Results (JSON)
```json
{
    "summary": {
        "total_assets_analyzed": 100,
        "buy_signals": 25,
        "sell_signals": 15,
        "hold_signals": 60,
        "avg_potential_return": 12.5,
        "high_risk_assets": 8
    },
    "individual_analyses": [
        {
            "symbol": "BTCUSDT",
            "current_price": 45000.0,
            "signal_analysis": {
                "signal": "BUY",
                "signal_strength": 85.5,
                "potential_return": 15.2,
                "risk_level": "MEDIUM",
                "confirmations": ["RSI oversold", "MACD positive"]
            },
            "technical_indicators": {
                "rsi": 28.5,
                "macd": 0.002,
                "sma_20": 44800.0,
                "sma_50": 44500.0
            },
            "polynomial_regression": {
                "upper_band": 46000.0,
                "lower_band": 44000.0,
                "degree": 4,
                "kstd": 2.0
            }
        }
    ],
    "correlation_analysis": {
        "high_correlation_pairs": [
            {
                "pair": ["BTCUSDT", "ETHUSDT"],
                "correlation": 0.85
            }
        ]
    }
}
```

## 🗄️ Database Integration

### Tables Created
- **trading.alerts**: Signal alerts with technical data
- **trading.asset_analytics**: Detailed asset analytics
- **trading.analysis_summary**: Analysis summaries

### Ingestion Process
1. **Load Results**: Read JSON files from results directory
2. **Validate Data**: Check data integrity and completeness
3. **Database Insert**: Store results in PostgreSQL
4. **Cleanup**: Remove old data (configurable retention)

## 📈 Charts and Visualizations

### Generated Charts
- **Price Action**: Price with regression bands
- **Technical Indicators**: RSI, MACD, Bollinger Bands
- **Correlation Matrix**: Asset correlation heatmap
- **Signal Distribution**: Pie chart of signal types
- **Risk Analysis**: Risk level distribution

### Chart Locations
- `results/charts/analysis_summary.png`
- `results/charts/{symbol}_analysis.png`

## 🔄 Integration with Main System

### Data Flow
```
Local Engine → JSON Results → Ingestion System → PostgreSQL → Web Application
```

### Schedule Recommendations
- **Daily Analysis**: Run analysis once per day
- **Weekly Correlation**: Full correlation analysis weekly
- **Monthly Cleanup**: Database cleanup monthly

### Automation Scripts
```bash
# Daily analysis script
#!/bin/bash
cd autonama.engine
python run_enhanced_analysis.py --config config.json --top-100 --generate-charts
python ingestion_system.py --config config.json --results-dir results
```

## 🛠️ Advanced Usage

### Custom Analysis
```python
from enhanced_local_engine import EnhancedLocalEngine

# Initialize engine
engine = EnhancedLocalEngine(binance_config)

# Analyze specific asset
result = engine.analyze_asset('BTCUSDT', degree=5, kstd=2.5)

# Cross-correlation analysis
corr_results = engine.calculate_cross_correlation(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
```

### Batch Processing
```python
# Analyze multiple symbols
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
results = engine.analyze_all_assets(symbols)

# Save results
engine.save_results(results)
engine.generate_charts(results)
```

## 🔍 Monitoring and Logging

### Log Files
- `enhanced_local_engine.log`: Main engine logs
- `ingestion_system.log`: Ingestion system logs

### Key Metrics
- Analysis duration
- Assets processed
- Signals generated
- Database operations
- Error rates

## 🚨 Troubleshooting

### Common Issues
1. **API Rate Limits**: Use caching and reasonable intervals
2. **Memory Usage**: Process assets in batches
3. **Database Connection**: Check PostgreSQL configuration
4. **Missing Dependencies**: Install TA-Lib and other requirements

### Performance Tips
- Use SSD storage for cache
- Increase database connection pool
- Enable parallel processing
- Optimize chart generation

## 📝 License

This project is part of the Autonama Research platform. All analysis results are for educational and research purposes only.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

**Note**: This engine runs locally to avoid cloud computing costs. All intensive processing is done on your local machine, and only the results are stored in the cloud database for the web application to display. 
 

## Overview

The Enhanced Local Analysis Engine is a comprehensive cryptocurrency analysis system that runs **locally** to avoid cloud computing costs. It performs advanced analytics including polynomial regression, cross-correlation analysis, technical indicators, and signal generation for all major cryptocurrencies.

## 🎯 Key Features

### 📊 Comprehensive Analysis
- **Polynomial Regression Analysis**: Advanced trend analysis with confidence bands
- **Cross-Correlation Analysis**: Identifies highly correlated asset pairs
- **Technical Indicators**: 20+ indicators including RSI, MACD, Bollinger Bands, ATR
- **Signal Generation**: BUY/SELL/HOLD signals with confidence levels
- **Risk Assessment**: Automatic risk level classification

### 🔄 Data Processing
- **Historical Data**: Fetches up to 720 days of daily candlestick data
- **Smart Caching**: Local caching to reduce API calls
- **Top 100 Assets**: Analyzes top 100 USDT pairs by volume
- **Real-time Updates**: Configurable analysis intervals

### 📈 Output Generation
- **JSON Results**: Structured analysis results
- **Charts & Visualizations**: Matplotlib and Plotly charts
- **Database Integration**: PostgreSQL ingestion system
- **Summary Reports**: Comprehensive analysis summaries

## 🏗️ Architecture

```
autonama.engine/
├── enhanced_local_engine.py      # Main analysis engine
├── run_enhanced_analysis.py      # Analysis runner script
├── ingestion_system.py           # Database ingestion system
├── config.json                   # Configuration file
├── requirements.txt              # Python dependencies
├── results/                      # Generated results
│   ├── enhanced_analysis_*.json  # Analysis results
│   ├── charts/                   # Generated charts
│   └── correlations/             # Correlation analysis
└── cache/                        # Cached historical data
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Binance API
cp config.json.example config.json
# Edit config.json with your Binance API credentials
```

### 2. Run Analysis

```bash
# Analyze core movers
python run_enhanced_analysis.py --config config.json

# Analyze top 100 assets
python run_enhanced_analysis.py --config config.json --top-100

# Analyze specific symbols
python run_enhanced_analysis.py --config config.json --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Generate charts
python run_enhanced_analysis.py --config config.json --generate-charts

# Include correlation analysis
python run_enhanced_analysis.py --config config.json --correlation-analysis
```

### 3. Ingest Results

```bash
# Ingest results into database
python ingestion_system.py --config config.json --results-dir results
```

## 📋 Configuration

### config.json
```json
{
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
        "top_100_enabled": true,
        "custom_symbols": []
    },
    "cache_settings": {
        "enabled": true,
        "cache_duration_hours": 24
    }
}
```

## 🔧 Analysis Parameters

### Polynomial Regression
- **degree**: Polynomial degree (default: 4)
- **kstd**: Standard deviation multiplier for bands (default: 2.0)

### Technical Analysis
- **interval**: Time interval (1d, 4h, 1h, etc.)
- **days**: Historical data period (max: 720 days)

### Signal Generation
- **BUY**: Price below lower regression band
- **SELL**: Price above upper regression band  
- **HOLD**: Price within regression bands

## 📊 Output Format

### Analysis Results (JSON)
```json
{
    "summary": {
        "total_assets_analyzed": 100,
        "buy_signals": 25,
        "sell_signals": 15,
        "hold_signals": 60,
        "avg_potential_return": 12.5,
        "high_risk_assets": 8
    },
    "individual_analyses": [
        {
            "symbol": "BTCUSDT",
            "current_price": 45000.0,
            "signal_analysis": {
                "signal": "BUY",
                "signal_strength": 85.5,
                "potential_return": 15.2,
                "risk_level": "MEDIUM",
                "confirmations": ["RSI oversold", "MACD positive"]
            },
            "technical_indicators": {
                "rsi": 28.5,
                "macd": 0.002,
                "sma_20": 44800.0,
                "sma_50": 44500.0
            },
            "polynomial_regression": {
                "upper_band": 46000.0,
                "lower_band": 44000.0,
                "degree": 4,
                "kstd": 2.0
            }
        }
    ],
    "correlation_analysis": {
        "high_correlation_pairs": [
            {
                "pair": ["BTCUSDT", "ETHUSDT"],
                "correlation": 0.85
            }
        ]
    }
}
```

## 🗄️ Database Integration

### Tables Created
- **trading.alerts**: Signal alerts with technical data
- **trading.asset_analytics**: Detailed asset analytics
- **trading.analysis_summary**: Analysis summaries

### Ingestion Process
1. **Load Results**: Read JSON files from results directory
2. **Validate Data**: Check data integrity and completeness
3. **Database Insert**: Store results in PostgreSQL
4. **Cleanup**: Remove old data (configurable retention)

## 📈 Charts and Visualizations

### Generated Charts
- **Price Action**: Price with regression bands
- **Technical Indicators**: RSI, MACD, Bollinger Bands
- **Correlation Matrix**: Asset correlation heatmap
- **Signal Distribution**: Pie chart of signal types
- **Risk Analysis**: Risk level distribution

### Chart Locations
- `results/charts/analysis_summary.png`
- `results/charts/{symbol}_analysis.png`

## 🔄 Integration with Main System

### Data Flow
```
Local Engine → JSON Results → Ingestion System → PostgreSQL → Web Application
```

### Schedule Recommendations
- **Daily Analysis**: Run analysis once per day
- **Weekly Correlation**: Full correlation analysis weekly
- **Monthly Cleanup**: Database cleanup monthly

### Automation Scripts
```bash
# Daily analysis script
#!/bin/bash
cd autonama.engine
python run_enhanced_analysis.py --config config.json --top-100 --generate-charts
python ingestion_system.py --config config.json --results-dir results
```

## 🛠️ Advanced Usage

### Custom Analysis
```python
from enhanced_local_engine import EnhancedLocalEngine

# Initialize engine
engine = EnhancedLocalEngine(binance_config)

# Analyze specific asset
result = engine.analyze_asset('BTCUSDT', degree=5, kstd=2.5)

# Cross-correlation analysis
corr_results = engine.calculate_cross_correlation(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
```

### Batch Processing
```python
# Analyze multiple symbols
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
results = engine.analyze_all_assets(symbols)

# Save results
engine.save_results(results)
engine.generate_charts(results)
```

## 🔍 Monitoring and Logging

### Log Files
- `enhanced_local_engine.log`: Main engine logs
- `ingestion_system.log`: Ingestion system logs

### Key Metrics
- Analysis duration
- Assets processed
- Signals generated
- Database operations
- Error rates

## 🚨 Troubleshooting

### Common Issues
1. **API Rate Limits**: Use caching and reasonable intervals
2. **Memory Usage**: Process assets in batches
3. **Database Connection**: Check PostgreSQL configuration
4. **Missing Dependencies**: Install TA-Lib and other requirements

### Performance Tips
- Use SSD storage for cache
- Increase database connection pool
- Enable parallel processing
- Optimize chart generation

## 📝 License

This project is part of the Autonama Research platform. All analysis results are for educational and research purposes only.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

**Note**: This engine runs locally to avoid cloud computing costs. All intensive processing is done on your local machine, and only the results are stored in the cloud database for the web application to display. 
 
 