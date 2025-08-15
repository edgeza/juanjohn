# Complete Optimization and Data Export

This directory contains scripts to run optimization on all 100 assets and export data in formats ready for Docker ingestion.

## Quick Start

### Option 1: Windows Batch File
```cmd
run_optimization.bat
```

### Option 2: PowerShell Script
```powershell
.\run_optimization.ps1
```

### Option 3: Direct Python
```bash
python run_complete_optimization.py
```

## What the Script Does

1. **Runs Optimization on All 100 Assets**
   - Uses Optuna to find optimal parameters for each asset
   - Optimizes degree, kstd, and lookback parameters
   - Processes all top 100 assets by volume

2. **Exports Data in Multiple Formats**
   - **CSV**: Raw analysis results
   - **JSON**: Detailed analysis with optimization data
   - **Alerts**: Real-time alert data for actionable signals
   - **Analytics**: Comprehensive analytics data
   - **Summary**: Dashboard overview data
   - **Plots**: Data for generating charts and visualizations

3. **Creates Docker-Ready Files**
   - All files formatted for easy ingestion into Docker system
   - Includes manifest file explaining each file's purpose
   - Timestamped files for version control

## Output Files

After running the script, check the `export_results/` folder for:

### Core Files
- `alerts_YYYYMMDD_HHMMSS.json` - Real-time alerts for BUY/SELL signals
- `analytics_YYYYMMDD_HHMMSS.json` - Detailed analytics and optimization results
- `summary_YYYYMMDD_HHMMSS.json` - Dashboard summary and top performers
- `plots_data_YYYYMMDD_HHMMSS.json` - Data for generating charts

### Original Exports
- `vectorbt_analysis_results_YYYYMMDD_HHMMSS.csv` - Raw CSV export
- `vectorbt_analysis_results_YYYYMMDD_HHMMSS.json` - Raw JSON export

### Manifest
- `ingestion_manifest.json` - Complete file listing and instructions

## File Formats for Docker Ingestion

### Alerts File Structure
```json
[
  {
    "symbol": "BTCUSDT",
    "signal": "BUY",
    "current_price": 45000.0,
    "potential_return": 15.2,
    "signal_strength": 85.5,
    "risk_level": "MEDIUM",
    "timestamp": "2024-01-15T10:30:00",
    "interval": "1d",
    "optimized_degree": 1,
    "optimized_kstd": 2.1,
    "optimized_lookback": 180
  }
]
```

### Analytics File Structure
```json
{
  "metadata": {
    "analysis_date": "2024-01-15T10:30:00",
    "total_assets": 100,
    "optimization_enabled": true,
    "interval": "1d"
  },
  "summary": {
    "total_assets": 100,
    "buy_signals": 25,
    "sell_signals": 15,
    "hold_signals": 60,
    "avg_potential_return": 12.5
  },
  "individual_analyses": [...],
  "optimization_results": [...]
}
```

### Summary File Structure
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_assets_analyzed": 100,
  "optimization_enabled": true,
  "analysis_summary": {...},
  "top_performers": {
    "buy_signals": [...],
    "sell_signals": [...]
  },
  "optimization_stats": {
    "assets_optimized": 100,
    "avg_optimization_improvement": 12.5
  }
}
```

## Docker Integration

### Step 1: Run Optimization
```bash
cd autonama.engine
python run_complete_optimization.py
```

### Step 2: Copy Files to Docker
Copy all files from `export_results/` to your Docker ingestion system.

### Step 3: Process in Docker
- Use `alerts_*.json` for real-time alerting
- Use `analytics_*.json` for detailed analytics
- Use `summary_*.json` for dashboard overview
- Use `plots_data_*.json` for chart generation

## Configuration

The script uses the same `config.json` file as the crypto engine. Make sure it contains:

```json
{
  "binance_api_key": "your_api_key",
  "binance_secret_key": "your_secret_key",
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "autonama",
    "user": "postgres",
    "password": "postgres"
  },
  "optimization": {
    "n_trials": 50,
    "degree_range": [1, 5],
    "kstd_range": [1.0, 3.0],
    "lookback_range": [50, 350]
  }
}
```

## Performance

- **Processing Time**: ~2-3 hours for 100 assets
- **Memory Usage**: ~4-8 GB RAM
- **Storage**: ~100-200 MB for all export files
- **CPU**: Multi-core optimization using Optuna

## Troubleshooting

### Common Issues

1. **NumPy Version Error**
   ```bash
   pip install numpy==2.2.0
   ```

2. **Memory Issues**
   - Reduce `n_trials` in config.json
   - Process fewer assets at once

3. **Database Connection Issues**
   - Check PostgreSQL is running
   - Verify database credentials in config.json

### Logs
Check `complete_optimization.log` for detailed execution logs.

## Next Steps

After running the optimization:

1. **Copy files to Docker system**
2. **Process alerts for real-time notifications**
3. **Generate analytics dashboards**
4. **Create charts and visualizations**
5. **Set up automated scheduling**

The exported files are ready for immediate use in your Docker-based alerting, analytics, and visualization systems. 