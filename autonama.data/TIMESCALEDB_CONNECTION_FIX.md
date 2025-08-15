# TimescaleDB Connection Fix

This document describes the fix for the TimescaleDB connection issue that was causing the error:

```
IO Error: Unable to connect to Postgres at postgresql://autonama:password@0.0.0.0:15432/autonama: connection to server at "0.0.0.0", port 15432 failed: Connection refused
```

## Problem Analysis

### Root Cause
The TimescaleDB connection was failing because:

1. **Incorrect Host Configuration**: Using `0.0.0.0:15432` from inside Docker container
2. **Port Mapping Confusion**: External port `15432` vs internal port `5432`
3. **Docker Networking**: Container needs to use service name `postgres` not `0.0.0.0`
4. **Missing Fallback Handling**: DuckDB-TimescaleDB integration had insufficient error handling

### Error Context
The error occurred in the `DuckDBAnalyticalEngine` when trying to establish a connection between DuckDB and TimescaleDB using the PostgreSQL extension.

## Solutions Implemented

### 1. **Fixed Database Connection Configuration**

#### Before (Problematic)
```python
def _get_database_url(self) -> str:
    host = os.getenv('POSTGRES_SERVER', 'localhost')  # 0.0.0.0
    port = os.getenv('POSTGRES_PORT', '15432')        # External port
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
```

#### After (Fixed)
```python
def _get_database_url(self) -> str:
    host = os.getenv('POSTGRES_SERVER', 'localhost')
    port = os.getenv('POSTGRES_PORT', '15432')
    
    # Docker container adjustments
    if host == '0.0.0.0':
        host = 'postgres'  # Docker service name
        port = '5432'      # Internal PostgreSQL port
    elif host == 'localhost' and os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true':
        host = 'postgres'
        port = '5432'
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
```

### 2. **Enhanced Error Handling**

#### Improved DuckDB-TimescaleDB Connection Setup
```python
def _setup_postgres_connection(self):
    try:
        # Test TimescaleDB connection first
        with self.timescale_manager.engine.connect() as test_conn:
            test_conn.execute("SELECT 1")
        logger.info("TimescaleDB connection verified")
        
        # Setup DuckDB connection
        self.conn.execute("INSTALL postgres")
        self.conn.execute("LOAD postgres")
        self.conn.execute(f"ATTACH '{db_url}' AS timescale (TYPE postgres)")
        
        # Test the connection
        result = self.conn.execute("SELECT COUNT(*) FROM timescale.trading.ohlc_data").fetchone()
        logger.info(f"DuckDB connected successfully. Found {result[0]} records")
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        logger.info("Will use manual data loading as fallback")
        self._use_manual_loading = True
```

#### Robust Data Loading with Fallback
```python
def load_data_for_analysis(self, symbol: str, ...):
    # Check if manual loading is required
    if hasattr(self, '_use_manual_loading') and self._use_manual_loading:
        # Use pandas fallback
        df = self.timescale_manager.get_ohlc_data(symbol, exchange, timeframe, limit)
        self.conn.execute("CREATE OR REPLACE TABLE ohlc_data AS SELECT * FROM df")
        return True
    
    # Try direct query, fallback to manual if needed
    try:
        self.conn.execute(f"CREATE OR REPLACE TABLE ohlc_data AS SELECT * FROM timescale.trading.ohlc_data WHERE ...")
    except Exception:
        # Automatic fallback to pandas
        df = self.timescale_manager.get_ohlc_data(...)
        self.conn.execute("CREATE OR REPLACE TABLE ohlc_data AS SELECT * FROM df")
```

### 3. **Updated Environment Configuration**

#### Docker-Aware .env Configuration
```bash
# Database Configuration (Docker)
POSTGRES_SERVER=postgres      # Docker service name
POSTGRES_USER=autonama
POSTGRES_PASSWORD=password
POSTGRES_DB=autonama
POSTGRES_PORT=5432           # Internal PostgreSQL port

# Docker Configuration
DOCKER_CONTAINER=true        # Explicit Docker detection
```

#### .env.example with Both Configurations
```bash
# Database Configuration (Docker)
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432

# Database Configuration (Local Development)
# POSTGRES_SERVER=localhost
# POSTGRES_PORT=15432
```

### 4. **Connection Test Script**

Created `test_timescale_connection.py` to verify:
- Environment variable setup
- DuckDB PostgreSQL extension availability
- TimescaleDB connection and schema access
- Table accessibility

## Docker Networking Explanation

### Port Mapping
```yaml
# docker-compose.yml
postgres:
  ports:
    - "15432:5432"  # External:Internal
```

### Connection Contexts
- **From Host Machine**: `localhost:15432`
- **From Docker Container**: `postgres:5432`
- **Service Discovery**: Docker Compose creates internal DNS for service names

### Why the Fix Works
1. **Service Name Resolution**: `postgres` resolves to the PostgreSQL container IP
2. **Internal Port**: `5432` is the actual PostgreSQL port inside the container
3. **Docker Network**: Containers communicate via internal Docker network

## Testing the Fix

### 1. **Connection Test**
```bash
cd /home/tawanda/dev/autonama/v2/data
python test_timescale_connection.py
```

### 2. **Full System Test**
```bash
python test_timescale_ingestion.py
```

### 3. **Celery Task Test**
```bash
# Check Celery logs for successful connections
docker logs autonama_celery_worker | grep -E "(TimescaleDB|DuckDB|connection)"
```

## Expected Log Messages

### Successful Connection
```
INFO: Database URL configured: postgresql://autonama:***@postgres:5432/autonama
INFO: TimescaleDB connection verified
INFO: DuckDB connected to TimescaleDB successfully. Found 1234 records in ohlc_data
INFO: Using TimescaleDB-first approach (primary storage + DuckDB analytics)
```

### Fallback Mode (If Direct Connection Fails)
```
WARNING: DuckDB-TimescaleDB query test failed: [error details]
INFO: Will use manual data loading as fallback
INFO: Using manual data loading (pandas fallback)
INFO: Loaded 100 records for BTC/USDT into DuckDB via pandas
```

## Verification Steps

### 1. **Environment Variables**
```bash
# Check if variables are set correctly
echo $POSTGRES_SERVER  # Should be 'postgres' in Docker
echo $POSTGRES_PORT    # Should be '5432' in Docker
echo $DOCKER_CONTAINER # Should be 'true'
```

### 2. **PostgreSQL Service**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres
docker logs autonama_postgres
```

### 3. **Network Connectivity**
```bash
# Test from inside Celery container
docker exec -it autonama_celery_worker ping postgres
docker exec -it autonama_celery_worker nc -zv postgres 5432
```

## Troubleshooting

### Common Issues

#### 1. Still Getting Connection Refused
**Check**: 
- PostgreSQL container is running: `docker ps | grep postgres`
- Environment variables are loaded: `docker exec autonama_celery_worker env | grep POSTGRES`

#### 2. DuckDB PostgreSQL Extension Not Found
**Solution**: 
- Ensure DuckDB version supports PostgreSQL extension
- Check if extension can be installed: `docker exec autonama_celery_worker python -c "import duckdb; duckdb.connect().execute('INSTALL postgres')"`

#### 3. Manual Loading Always Used
**Check**:
- TimescaleDB connection works: Run `test_timescale_connection.py`
- DuckDB can connect to PostgreSQL: Check logs for connection test results

### Debug Commands

```bash
# Test TimescaleDB connection from container
docker exec -it autonama_celery_worker python -c "
from tasks.timescale_data_ingestion import TimescaleDBManager
manager = TimescaleDBManager()
print('Connection URL:', manager.db_url)
with manager.engine.connect() as conn:
    result = conn.execute('SELECT 1').fetchone()
    print('Connection successful:', result[0])
"

# Test DuckDB PostgreSQL extension
docker exec -it autonama_celery_worker python -c "
import duckdb
conn = duckdb.connect()
conn.execute('INSTALL postgres')
conn.execute('LOAD postgres')
print('PostgreSQL extension loaded successfully')
"
```

## Summary

The fix addresses the TimescaleDB connection issue by:

✅ **Correct Docker Networking**: Uses `postgres:5432` instead of `0.0.0.0:15432`
✅ **Environment Detection**: Automatically detects Docker container environment
✅ **Robust Fallback**: Manual data loading when direct connection fails
✅ **Better Error Handling**: Graceful degradation with informative logging
✅ **Connection Testing**: Comprehensive test scripts for verification

The system now properly implements the TimescaleDB-first architecture with reliable connection handling and fallback mechanisms.
