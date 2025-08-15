# TimescaleDB-First Architecture Implementation

This document describes the implementation of the hybrid database architecture where TimescaleDB serves as the primary storage and DuckDB as the analytical engine.

## Overview

Based on the MIGRATION_PLAN.md and README.md specifications, we have implemented the intended hybrid database architecture:

### **Architecture Flow**
```
Market Data → TimescaleDB (Primary Storage) → DuckDB (Analytics) → Results back to TimescaleDB
```

### **Key Components**
1. **TimescaleDB**: Primary time-series database for market data storage
2. **DuckDB**: In-process analytical engine that queries FROM TimescaleDB
3. **Hybrid Task System**: Intelligent fallback between approaches

## Implementation Details

### **1. TimescaleDB Manager (`TimescaleDBManager`)**

**Purpose**: Handles all TimescaleDB operations for primary data storage.

**Key Methods**:
- `insert_ohlc_data()`: Store market data in trading.ohlc_data hypertable
- `get_ohlc_data()`: Retrieve market data for analysis
- `get_latest_timestamp()`: Check data freshness

**Database Schema Used**:
- `trading.ohlc_data`: Main hypertable for OHLC market data
- `analytics.indicators`: Technical indicators storage
- Continuous aggregates for 1h and 1d data
- Retention policies and performance optimizations

### **2. DuckDB Analytical Engine (`DuckDBAnalyticalEngine`)**

**Purpose**: High-performance analytical processing using data FROM TimescaleDB.

**Key Features**:
- **Direct Connection**: Uses DuckDB's PostgreSQL extension to query TimescaleDB
- **Fallback Loading**: Manual data loading via pandas if direct connection fails
- **Technical Indicators**: Calculates SMA, RSI, Bollinger Bands using SQL
- **Result Storage**: Stores calculated indicators back to TimescaleDB

**Analytical Capabilities**:
```sql
-- Simple Moving Averages
AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20

-- RSI Calculation
100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0)))) as rsi

-- Bollinger Bands
sma_20 + (2 * std_20) as bb_upper
```

### **3. Hybrid Task System**

**Primary Task**: `update_market_data()`
- **First**: Attempts TimescaleDB-first approach
- **Fallback**: Legacy DuckDB file approach
- **Final Fallback**: Basic data fetching

**Task Flow**:
```python
try:
    # TimescaleDB-first approach
    result = update_market_data_timescale_first()
except Exception:
    # Legacy approach
    result = update_market_data_legacy()
```

## New Tasks and Functions

### **Core Tasks**

#### `update_market_data_timescale_first()`
- **Purpose**: Main data ingestion using TimescaleDB-first approach
- **Flow**: Fetch data → Store in TimescaleDB → Calculate indicators with DuckDB → Store results
- **Categories**: Currently supports crypto (extensible to forex, stock, commodity)

#### `calculate_indicators_for_symbol()`
- **Purpose**: Calculate technical indicators for specific symbols
- **Process**: Load data from TimescaleDB → DuckDB analysis → Store results back
- **Indicators**: SMA, RSI, Bollinger Bands (extensible)

#### `update_crypto_data_timescale()`
- **Purpose**: Crypto-specific data update with TimescaleDB storage
- **Symbols**: BTC/USDT, ETH/USDT, ADA/USDT, BNB/USDT, SOL/USDT
- **Features**: Smart updates (checks data freshness), indicator calculation

### **Enhanced Fallback System**

The fallback system has been enhanced to support TimescaleDB when available:

```python
def update_category_data_fallback(category: str, force_update: bool = False):
    if category == "crypto":
        if TIMESCALE_AVAILABLE:
            return update_crypto_data_timescale(force_update)
        else:
            return update_crypto_data_basic(force_update)
```

## Configuration and Setup

### **Environment Variables**
```bash
# PostgreSQL/TimescaleDB Configuration
POSTGRES_SERVER=localhost
POSTGRES_PORT=15432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=autonama

# DuckDB Configuration (for fallback)
DUCKDB_PATH=/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb
```

### **Database Schema**
The system uses the existing TimescaleDB schema from `init-db.sql`:
- **trading.ohlc_data**: Hypertable for market data
- **analytics.indicators**: Technical indicators
- **optimization.results**: Optimization results
- **Continuous aggregates**: 1h and 1d data views

### **Dependencies**
```python
# New dependencies for TimescaleDB integration
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
duckdb>=0.9.0  # With PostgreSQL extension support
```

## Data Flow Examples

### **1. Market Data Ingestion**
```
1. Fetch OHLCV from Binance API
2. Store in TimescaleDB trading.ohlc_data
3. Load data into DuckDB for analysis
4. Calculate technical indicators
5. Store indicators in analytics.indicators
```

### **2. Analytical Processing**
```
1. DuckDB connects to TimescaleDB
2. Query: SELECT * FROM timescale.trading.ohlc_data WHERE symbol = 'BTC/USDT'
3. Perform analytical calculations in DuckDB
4. Store results back to TimescaleDB
```

### **3. API Data Serving**
```
1. FastAPI receives request for market data
2. Query TimescaleDB directly for OHLC data
3. Query analytics.indicators for technical indicators
4. Return combined response to frontend
```

## Performance Benefits

### **TimescaleDB (Primary Storage)**
- **High Write Throughput**: Optimized for time-series data ingestion
- **Efficient Queries**: Time-based indexing and continuous aggregates
- **Data Retention**: Automatic data lifecycle management
- **Scalability**: Horizontal scaling capabilities

### **DuckDB (Analytics)**
- **In-Memory Processing**: Fast analytical computations
- **Columnar Storage**: Efficient for analytical workloads
- **SQL Interface**: Familiar query language for complex calculations
- **Zero-Copy Integration**: Seamless data sharing with pandas

### **Hybrid Benefits**
- **Best of Both Worlds**: Persistent storage + fast analytics
- **Reduced Data Movement**: DuckDB queries TimescaleDB directly
- **Scalable Architecture**: Each component optimized for its purpose

## Monitoring and Observability

### **Task Monitoring**
```python
# Progress updates include approach information
current_task.update_state(
    state='PROGRESS',
    meta={
        'approach': 'timescaledb_first',
        'status': 'Processing CRYPTO with TimescaleDB-first approach'
    }
)
```

### **Logging**
```
INFO: Using TimescaleDB-first approach (primary storage + DuckDB analytics)
INFO: Stored 100 records for BTC/USDT in TimescaleDB
INFO: Calculated and stored indicators for BTC/USDT
INFO: TIMESCALEDB-FIRST UPDATE SUMMARY
```

### **Health Checks**
The maintenance system now includes TimescaleDB health checks:
- Connection validation
- Schema accessibility
- Data freshness checks

## Testing

### **Test Script**: `test_timescale_ingestion.py`

**Test Coverage**:
1. **TimescaleDB Connection**: Verify database connectivity
2. **DuckDB Integration**: Test DuckDB-TimescaleDB connection
3. **Data Insertion**: Test OHLC data storage
4. **Indicator Calculation**: Test analytical processing
5. **Crypto Data Update**: Test end-to-end crypto update
6. **Hybrid Task**: Test complete hybrid system

**Running Tests**:
```bash
cd /home/tawanda/dev/autonama/v2/data
python test_timescale_ingestion.py
```

## Migration from File-Based DuckDB

### **Before (File-Based)**
```
Market Data → DuckDB Files → Local Storage → API Serving
```

### **After (TimescaleDB-First)**
```
Market Data → TimescaleDB → DuckDB (Analytics) → Results to TimescaleDB → API Serving
```

### **Migration Benefits**
1. **Persistent Storage**: Data survives container restarts
2. **Concurrent Access**: Multiple processes can access data safely
3. **ACID Compliance**: Transactional data integrity
4. **Backup/Recovery**: Standard database backup procedures
5. **Monitoring**: Database-level monitoring and alerting

## Celery Integration

### **Updated Beat Schedule**
```python
beat_schedule={
    'update-market-data': {
        'task': 'tasks.data_ingestion.update_market_data',
        'schedule': 900.0,  # Every 15 minutes - now uses hybrid approach
    },
    'calculate-indicators': {
        'task': 'tasks.timescale_data_ingestion.calculate_indicators_for_symbol',
        'schedule': 1800.0,  # Every 30 minutes - DuckDB analytics
        'args': ['BTC/USDT'],
    },
}
```

### **Task Results**
```python
{
    'status': 'completed',
    'approach': 'timescaledb_first',  # Indicates which approach was used
    'categories_processed': 1,
    'summary': {
        'total_success': 5,
        'total_failed': 0,
        'total_skipped': 0
    }
}
```

## API Integration

### **Updated API Endpoints**
The existing API endpoints now serve data from TimescaleDB:

```python
# GET /api/v1/data/ohlc
# Now queries TimescaleDB directly instead of DuckDB files
SELECT timestamp, open, high, low, close, volume
FROM trading.ohlc_data
WHERE symbol = %s AND timeframe = %s
ORDER BY timestamp DESC
LIMIT %s
```

### **Technical Indicators**
```python
# GET /api/v1/data/indicators
# Serves pre-calculated indicators from analytics.indicators
SELECT indicator_name, indicator_value, timestamp
FROM analytics.indicators
WHERE symbol = %s AND timeframe = %s
ORDER BY timestamp DESC
```

## Troubleshooting

### **Common Issues**

#### 1. TimescaleDB Connection Failed
**Symptoms**: "TimescaleDB-first approach failed" messages
**Solutions**:
- Check PostgreSQL/TimescaleDB is running
- Verify connection parameters in .env
- Check network connectivity

#### 2. DuckDB-TimescaleDB Integration Failed
**Symptoms**: "DuckDB query failed" or "Direct connection failed"
**Solutions**:
- Ensure DuckDB PostgreSQL extension is available
- Check TimescaleDB permissions
- Verify schema access

#### 3. Always Using Fallback Mode
**Symptoms**: Always seeing "Switching to fallback" messages
**Solutions**:
- Check TimescaleDB availability
- Verify import paths for timescale_data_ingestion module
- Check Python dependencies

### **Debug Commands**
```bash
# Test TimescaleDB connection
python -c "
from tasks.timescale_data_ingestion import TimescaleDBManager
manager = TimescaleDBManager()
print('TimescaleDB connection successful')
"

# Test DuckDB integration
python test_timescale_ingestion.py

# Check task logs
docker logs autonama_celery_worker | grep -E "(timescale|duckdb|approach)"
```

## Future Enhancements

### **Short Term**
1. **Forex/Stock/Commodity Support**: Extend TimescaleDB-first approach to all categories
2. **Real-time Indicators**: WebSocket-based real-time indicator updates
3. **Advanced Analytics**: More sophisticated DuckDB analytical functions

### **Medium Term**
1. **Distributed Analytics**: DuckDB cluster for large-scale analytics
2. **Streaming Data**: Real-time data ingestion with Kafka/TimescaleDB
3. **ML Integration**: Machine learning models using DuckDB analytics

### **Long Term**
1. **Multi-Tenant Architecture**: Separate schemas per user/organization
2. **Global Distribution**: TimescaleDB replication across regions
3. **Advanced Optimization**: Query optimization and caching strategies

## Summary

The TimescaleDB-first architecture successfully implements the intended hybrid database design:

✅ **TimescaleDB as Primary Storage**: All market data stored in time-series optimized database
✅ **DuckDB as Analytical Engine**: High-performance analytics querying FROM TimescaleDB  
✅ **Hybrid Task System**: Intelligent fallback between approaches
✅ **Backward Compatibility**: Existing functionality preserved
✅ **Performance Optimized**: Each database used for its strengths
✅ **Scalable Design**: Ready for production deployment

The system now aligns with the MIGRATION_PLAN.md specifications and provides a solid foundation for the modern trading optimization dashboard.
