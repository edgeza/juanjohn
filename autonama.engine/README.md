# Autonama Local Backtesting Engine

This directory contains the local backtesting engine that runs offline to generate trading signals and alerts. The engine uses polynomial regression analysis to identify BUY, SELL, and HOLD signals for cryptocurrency assets.

## Architecture

The system works as follows:

1. **Local Backtesting Engine** (offline) - Runs on your local machine
   - Fetches historical data from Binance API
   - Performs polynomial regression analysis
   - Generates trading signals (BUY/SELL/HOLD)
   - Saves results to JSON files

2. **Ingestion System** (online) - Runs in Docker containers
   - Monitors for new result files
   - Ingests results into PostgreSQL database
   - Makes data available to web application

3. **Web Application** (online) - Runs in Docker containers
   - Displays alerts and signals
   - Shows charts and analysis
   - Provides real-time updates

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- python-binance
- pandas
- numpy
- matplotlib
- psycopg2-binary

### 2. Configure Binance API

Edit `config.json` and add your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key",
    "binance_api_secret": "your_actual_api_secret"
}
```

Or set environment variables:
```bash
export BINANCE_API_KEY="your_actual_api_key"
export BINANCE_API_SECRET="your_actual_api_secret"
```

### 3. Run Local Backtesting

#### Basic Usage

```bash
# Scan core movers (BTC, ETH, SOL)
python run_local_backtest.py

# Scan top 100 assets by volume
python run_local_backtest.py --top-100

# Scan specific symbols
python run_local_backtest.py --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Custom parameters
python run_local_backtest.py --interval 1d --degree 4 --kstd 2.0 --days 720
```

#### Advanced Usage

```bash
# Use custom config file
python run_local_backtest.py --config my_config.json

# Specify output directory
python run_local_backtest.py --output /path/to/results

# Full example
python run_local_backtest.py \
    --config config.json \
    --output results/ \
    --top-100 \
    --interval 1d \
    --degree 4 \
    --kstd 2.0 \
    --days 720
```

## Signal Generation

The engine generates signals based on polynomial regression analysis:

- **BUY Signal**: Current price is below the lower regression band
- **SELL Signal**: Current price is above the upper regression band  
- **HOLD Signal**: Current price is within the regression bands

### Potential Return Calculation

- **BUY**: Percentage distance from lower to upper band
- **SELL**: Percentage distance from upper to lower band
- **HOLD**: 0% (no action recommended)

## Integration with Main System

### 1. Manual Ingestion

After running the local backtest, ingest results into the database:

```bash
# Ingest a specific results file
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import ingest_backtest_results
result = ingest_backtest_results.delay('/path/to/backtest_results_20240730_143022.json')
print('Ingestion task submitted:', result.id)
"
```

### 2. Automatic Monitoring

Set up automatic monitoring of the results directory:

```bash
# Start monitoring a directory for new result files
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import monitor_backtest_results_directory
result = monitor_backtest_results_directory.delay('/path/to/results/')
print('Monitoring task submitted:', result.id)
"
```

### 3. Check Ingestion Status

```bash
# Check recent ingestion activity
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import get_ingestion_status
result = get_ingestion_status.delay()
print('Status task submitted:', result.id)
"
```

## API Endpoints

Once ingested, alerts are available via the API:

- `GET /v1/alerts` - Get all alerts
- `GET /v1/alerts/summary` - Get alert summary
- `GET /v1/alerts/top-buy` - Get top BUY signals
- `GET /v1/alerts/top-sell` - Get top SELL signals

## Workflow Example

1. **Run Local Backtest** (daily or as needed):
   ```bash
   python run_local_backtest.py --top-100
   ```

2. **Ingest Results** (automatic or manual):
   ```bash
   # Manual ingestion
   docker-compose exec celery_worker python -c "
   from tasks.backtest_ingestion import ingest_backtest_results
   result = ingest_backtest_results.delay('results/backtest_results_20240730_143022.json')
   print('Task submitted:', result.id)
   "
   ```

3. **View Alerts** (via web interface):
   - Navigate to `http://localhost:3001/alerts`
   - View BUY/SELL signals with potential returns
   - See charts and analysis

## Configuration Options

### Backtest Parameters

- `interval`: Time interval (1d, 4h, 1h, etc.)
- `degree`: Polynomial degree (2-10, default: 4)
- `kstd`: Standard deviation multiplier (1.0-3.0, default: 2.0)
- `days`: Number of days to analyze (max: 720)

### Cache Settings

- Data is cached locally to avoid repeated API calls
- Cache expires after 24 hours
- Cache files stored in `cache/` directory

### Output Settings

- Results saved as JSON files in `results/` directory
- Filename format: `backtest_results_YYYYMMDD_HHMMSS.json`
- Contains all analysis data including regression bands

## Troubleshooting

### Common Issues

1. **Binance API Errors**
   - Check API credentials in config.json
   - Verify API key has correct permissions
   - Check rate limits

2. **Insufficient Data**
   - Some symbols may not have enough historical data
   - Engine will mark these as HOLD with error message

3. **Ingestion Errors**
   - Check file paths are correct
   - Verify database connection
   - Check file permissions

### Logs

- Local engine logs: `local_backtest_engine.log`
- Ingestion logs: Check Celery worker logs
- API logs: Check API container logs

## Performance Tips

1. **Parallel Processing**: Engine uses ThreadPoolExecutor for parallel asset scanning
2. **Caching**: Historical data is cached to avoid repeated API calls
3. **Batch Processing**: Process multiple assets simultaneously
4. **Memory Management**: Large datasets are processed in chunks

## Security Notes

- Keep API credentials secure
- Don't commit config.json with real credentials
- Use environment variables for production
- Monitor API usage to stay within rate limits 

This directory contains the local backtesting engine that runs offline to generate trading signals and alerts. The engine uses polynomial regression analysis to identify BUY, SELL, and HOLD signals for cryptocurrency assets.

## Architecture

The system works as follows:

1. **Local Backtesting Engine** (offline) - Runs on your local machine
   - Fetches historical data from Binance API
   - Performs polynomial regression analysis
   - Generates trading signals (BUY/SELL/HOLD)
   - Saves results to JSON files

2. **Ingestion System** (online) - Runs in Docker containers
   - Monitors for new result files
   - Ingests results into PostgreSQL database
   - Makes data available to web application

3. **Web Application** (online) - Runs in Docker containers
   - Displays alerts and signals
   - Shows charts and analysis
   - Provides real-time updates

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- python-binance
- pandas
- numpy
- matplotlib
- psycopg2-binary

### 2. Configure Binance API

Edit `config.json` and add your Binance API credentials:

```json
{
    "binance_api_key": "your_actual_api_key",
    "binance_api_secret": "your_actual_api_secret"
}
```

Or set environment variables:
```bash
export BINANCE_API_KEY="your_actual_api_key"
export BINANCE_API_SECRET="your_actual_api_secret"
```

### 3. Run Local Backtesting

#### Basic Usage

```bash
# Scan core movers (BTC, ETH, SOL)
python run_local_backtest.py

# Scan top 100 assets by volume
python run_local_backtest.py --top-100

# Scan specific symbols
python run_local_backtest.py --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Custom parameters
python run_local_backtest.py --interval 1d --degree 4 --kstd 2.0 --days 720
```

#### Advanced Usage

```bash
# Use custom config file
python run_local_backtest.py --config my_config.json

# Specify output directory
python run_local_backtest.py --output /path/to/results

# Full example
python run_local_backtest.py \
    --config config.json \
    --output results/ \
    --top-100 \
    --interval 1d \
    --degree 4 \
    --kstd 2.0 \
    --days 720
```

## Signal Generation

The engine generates signals based on polynomial regression analysis:

- **BUY Signal**: Current price is below the lower regression band
- **SELL Signal**: Current price is above the upper regression band  
- **HOLD Signal**: Current price is within the regression bands

### Potential Return Calculation

- **BUY**: Percentage distance from lower to upper band
- **SELL**: Percentage distance from upper to lower band
- **HOLD**: 0% (no action recommended)

## Integration with Main System

### 1. Manual Ingestion

After running the local backtest, ingest results into the database:

```bash
# Ingest a specific results file
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import ingest_backtest_results
result = ingest_backtest_results.delay('/path/to/backtest_results_20240730_143022.json')
print('Ingestion task submitted:', result.id)
"
```

### 2. Automatic Monitoring

Set up automatic monitoring of the results directory:

```bash
# Start monitoring a directory for new result files
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import monitor_backtest_results_directory
result = monitor_backtest_results_directory.delay('/path/to/results/')
print('Monitoring task submitted:', result.id)
"
```

### 3. Check Ingestion Status

```bash
# Check recent ingestion activity
docker-compose exec celery_worker python -c "
from tasks.backtest_ingestion import get_ingestion_status
result = get_ingestion_status.delay()
print('Status task submitted:', result.id)
"
```

## API Endpoints

Once ingested, alerts are available via the API:

- `GET /v1/alerts` - Get all alerts
- `GET /v1/alerts/summary` - Get alert summary
- `GET /v1/alerts/top-buy` - Get top BUY signals
- `GET /v1/alerts/top-sell` - Get top SELL signals

## Workflow Example

1. **Run Local Backtest** (daily or as needed):
   ```bash
   python run_local_backtest.py --top-100
   ```

2. **Ingest Results** (automatic or manual):
   ```bash
   # Manual ingestion
   docker-compose exec celery_worker python -c "
   from tasks.backtest_ingestion import ingest_backtest_results
   result = ingest_backtest_results.delay('results/backtest_results_20240730_143022.json')
   print('Task submitted:', result.id)
   "
   ```

3. **View Alerts** (via web interface):
   - Navigate to `http://localhost:3001/alerts`
   - View BUY/SELL signals with potential returns
   - See charts and analysis

## Configuration Options

### Backtest Parameters

- `interval`: Time interval (1d, 4h, 1h, etc.)
- `degree`: Polynomial degree (2-10, default: 4)
- `kstd`: Standard deviation multiplier (1.0-3.0, default: 2.0)
- `days`: Number of days to analyze (max: 720)

### Cache Settings

- Data is cached locally to avoid repeated API calls
- Cache expires after 24 hours
- Cache files stored in `cache/` directory

### Output Settings

- Results saved as JSON files in `results/` directory
- Filename format: `backtest_results_YYYYMMDD_HHMMSS.json`
- Contains all analysis data including regression bands

## Troubleshooting

### Common Issues

1. **Binance API Errors**
   - Check API credentials in config.json
   - Verify API key has correct permissions
   - Check rate limits

2. **Insufficient Data**
   - Some symbols may not have enough historical data
   - Engine will mark these as HOLD with error message

3. **Ingestion Errors**
   - Check file paths are correct
   - Verify database connection
   - Check file permissions

### Logs

- Local engine logs: `local_backtest_engine.log`
- Ingestion logs: Check Celery worker logs
- API logs: Check API container logs

## Performance Tips

1. **Parallel Processing**: Engine uses ThreadPoolExecutor for parallel asset scanning
2. **Caching**: Historical data is cached to avoid repeated API calls
3. **Batch Processing**: Process multiple assets simultaneously
4. **Memory Management**: Large datasets are processed in chunks

## Security Notes

- Keep API credentials secure
- Don't commit config.json with real credentials
- Use environment variables for production
- Monitor API usage to stay within rate limits 
 