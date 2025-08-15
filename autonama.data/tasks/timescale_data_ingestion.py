"""
TimescaleDB-First Data Ingestion System

This module implements the hybrid database architecture where:
1. Data is primarily stored in TimescaleDB
2. DuckDB is used as an analytical engine that queries FROM TimescaleDB
3. Results are stored back to TimescaleDB

Architecture Flow:
Market Data → TimescaleDB → DuckDB (for analysis) → Results back to TimescaleDB
"""

from celery import current_task
from celery_app import celery_app
import pandas as pd
import ccxt
# import duckdb  # REMOVED: No longer needed
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class TimescaleDBManager:
    """Manager for TimescaleDB operations."""
    
    def __init__(self):
        self.db_url = self._get_database_url()
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables with Docker and host network awareness."""
        host = os.getenv('POSTGRES_SERVER', 'localhost')
        port = os.getenv('POSTGRES_PORT', '15432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        database = os.getenv('POSTGRES_DB', 'autonama')
        
        # Check if we have a full DATABASE_URL first
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            logger.info(f"Using DATABASE_URL: {database_url.replace(password, '***')}")
            return database_url
        
        # Docker container adjustments
        if host == '0.0.0.0':
            # From inside Docker container, connect to the postgres service
            host = 'postgres'
            port = '5432'  # Internal PostgreSQL port
            logger.info("Adjusted connection for Docker container: postgres:5432")
        elif host == 'localhost' and os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true':
            # If explicitly running in Docker container
            host = 'postgres'
            port = '5432'
            logger.info("Using Docker service name: postgres:5432")
        elif host == 'localhost':
            # Host network mode or local development
            port = '15432'  # External PostgreSQL port
            logger.info(f"Using host network mode: localhost:{port}")
        
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        logger.info(f"Database URL configured: postgresql://{user}:***@{host}:{port}/{database}")
        return db_url
    
    def insert_ohlc_data(self, data: List[Dict], symbol: str, exchange: str = 'binance', timeframe: str = '1h') -> int:
        """Insert OHLC data into TimescaleDB."""
        if not data:
            return 0
        
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(data)
            
            # Ensure required columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return 0
            
            # Add metadata columns
            df['symbol'] = symbol
            df['exchange'] = exchange
            df['timeframe'] = timeframe
            df['created_at'] = datetime.utcnow()
            
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Insert into TimescaleDB using pandas to_sql method (simpler and more reliable)
            try:
                # Use pandas to_sql with if_exists='append' for bulk insert
                df.to_sql(
                    'ohlc_data',
                    con=self.engine,
                    schema='trading',
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                inserted_count = len(df)
                logger.info(f"Successfully inserted {inserted_count} records for {symbol} into TimescaleDB using pandas")
                
            except Exception as pandas_error:
                logger.warning(f"Pandas bulk insert failed for {symbol}: {pandas_error}")
                
                # Fallback to individual row insertion with proper parameter binding
                inserted_count = 0
                with self.engine.connect() as conn:
                    for _, row in df.iterrows():
                        try:
                            # Use direct parameter binding without string formatting
                            result = conn.execute(
                                text("""
                                    INSERT INTO trading.ohlc_data 
                                    (symbol, exchange, timeframe, timestamp, open, high, low, close, volume, created_at)
                                    VALUES (:symbol, :exchange, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :created_at)
                                """),
                                {
                                    'symbol': row['symbol'],
                                    'exchange': row['exchange'],
                                    'timeframe': row['timeframe'],
                                    'timestamp': row['timestamp'],
                                    'open': float(row['open']),
                                    'high': float(row['high']),
                                    'low': float(row['low']),
                                    'close': float(row['close']),
                                    'volume': float(row['volume']),
                                    'created_at': row['created_at']
                                }
                            )
                            inserted_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to insert individual row for {symbol}: {e}")
                            continue
                    
                    conn.commit()
            
            logger.info(f"Inserted {inserted_count} records for {symbol} into TimescaleDB")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error inserting OHLC data for {symbol}: {e}")
            return 0
    
    def get_ohlc_data(self, symbol: str, exchange: str = 'binance', timeframe: str = '1h', 
                      limit: int = 100, start_time: Optional[datetime] = None) -> pd.DataFrame:
        """Retrieve OHLC data from TimescaleDB."""
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM trading.ohlc_data
                WHERE symbol = :symbol 
                    AND exchange = :exchange 
                    AND timeframe = :timeframe
            """
            
            params = {
                'symbol': symbol,
                'exchange': exchange,
                'timeframe': timeframe
            }
            
            if start_time:
                query += " AND timestamp >= :start_time"
                params['start_time'] = start_time
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params['limit'] = limit
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            
            # Sort by timestamp ascending for proper time series
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Retrieved {len(df)} records for {symbol} from TimescaleDB")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving OHLC data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_timestamp(self, symbol: str, exchange: str = 'binance', timeframe: str = '1h') -> Optional[datetime]:
        """Get the latest timestamp for a symbol."""
        try:
            query = """
                SELECT MAX(timestamp) as latest_timestamp
                FROM trading.ohlc_data
                WHERE symbol = :symbol 
                    AND exchange = :exchange 
                    AND timeframe = :timeframe
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {
                    'symbol': symbol,
                    'exchange': exchange,
                    'timeframe': timeframe
                }).fetchone()
            
            return result[0] if result and result[0] else None
            
        except Exception as e:
            logger.error(f"Error getting latest timestamp for {symbol}: {e}")
            return None

class DuckDBAnalyticalEngine:
    """DuckDB engine - REMOVED: No longer needed."""
    
    def __init__(self, timescale_manager: TimescaleDBManager):
        # DuckDB removed - all calculations done locally
        logger.info("DuckDB analytical engine removed - using local processing only")
    
    def _setup_postgres_connection(self):
        """Setup DuckDB to connect to PostgreSQL/TimescaleDB with improved error handling."""
        try:
            # Install and load postgres extension
            self.conn.execute("INSTALL postgres")
            self.conn.execute("LOAD postgres")
            
            # Get the database URL
            db_url = self.timescale_manager.db_url
            logger.info(f"Attempting to connect DuckDB to TimescaleDB...")
            
            # Test TimescaleDB connection first
            try:
                with self.timescale_manager.engine.connect() as test_conn:
                    result = test_conn.execute(text("SELECT 1")).fetchone()
                    logger.info(f"TimescaleDB connection verified: {result[0]}")
            except Exception as test_error:
                logger.error(f"TimescaleDB connection test failed: {test_error}")
                raise test_error
            
            # Setup connection to TimescaleDB
            self.conn.execute(f"""
                ATTACH '{db_url}' AS timescale (TYPE postgres)
            """)
            
            # Test the DuckDB-TimescaleDB connection
            try:
                result = self.conn.execute("SELECT COUNT(*) FROM timescale.trading.ohlc_data").fetchone()
                logger.info(f"DuckDB connected to TimescaleDB successfully. Found {result[0]} records in ohlc_data")
                self._use_manual_loading = False
            except Exception as query_error:
                logger.warning(f"DuckDB-TimescaleDB query test failed: {query_error}")
                logger.info("Will use manual data loading as fallback")
                self._use_manual_loading = True
            
        except Exception as e:
            logger.error(f"Failed to setup DuckDB-TimescaleDB connection: {e}")
            logger.info("DuckDB will use manual data loading via pandas")
            # Fallback to manual data loading
            self._use_manual_loading = True
    
    def load_data_for_analysis(self, symbol: str, exchange: str = 'binance', 
                              timeframe: str = '1h', limit: int = 1000) -> bool:
        """Load data from TimescaleDB into DuckDB for analysis."""
        try:
            # Check if we should use manual loading
            if hasattr(self, '_use_manual_loading') and self._use_manual_loading:
                logger.info("Using manual data loading (pandas fallback)")
                # Load data manually via pandas
                df = self.timescale_manager.get_ohlc_data(symbol, exchange, timeframe, limit)
                if not df.empty:
                    self.conn.execute("CREATE OR REPLACE TABLE ohlc_data AS SELECT * FROM df")
                    logger.info(f"Loaded {len(df)} records for {symbol} into DuckDB via pandas")
                    return True
                else:
                    logger.warning(f"No data available for {symbol}")
                    return False
            
            # Try direct query first
            try:
                query = """
                    CREATE OR REPLACE TABLE ohlc_data AS 
                    SELECT * FROM timescale.trading.ohlc_data 
                    WHERE symbol = $1 
                        AND exchange = $2 
                        AND timeframe = $3
                    ORDER BY timestamp DESC 
                    LIMIT $4
                """
                self.conn.execute(query, [symbol, exchange, timeframe, limit])
                
                # Verify data was loaded
                count_result = self.conn.execute("SELECT COUNT(*) FROM ohlc_data").fetchone()
                if count_result and count_result[0] > 0:
                    logger.info(f"Loaded {count_result[0]} records for {symbol} into DuckDB via direct connection")
                    return True
                else:
                    logger.warning(f"Direct query returned no data for {symbol}, trying manual loading")
                    raise Exception("No data returned from direct query")
                
            except Exception as direct_error:
                logger.warning(f"Direct connection failed: {direct_error}")
                
                # Fallback: Load data manually via pandas
                logger.info("Falling back to manual data loading")
                df = self.timescale_manager.get_ohlc_data(symbol, exchange, timeframe, limit)
                if not df.empty:
                    self.conn.execute("CREATE OR REPLACE TABLE ohlc_data AS SELECT * FROM df")
                    logger.info(f"Loaded {len(df)} records for {symbol} into DuckDB via pandas fallback")
                    return True
                else:
                    logger.warning(f"No data available for {symbol}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to load data for analysis: {e}")
            return False
    
    def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators using DuckDB's analytical capabilities."""
        try:
            # Ensure data is loaded
            if not self.load_data_for_analysis(symbol):
                return {}
            
            # Calculate various technical indicators using DuckDB SQL
            indicators = {}
            
            # Simple Moving Averages
            sma_query = """
                SELECT 
                    timestamp,
                    AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
                    AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as sma_50
                FROM ohlc_data 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            result = self.conn.execute(sma_query).fetchone()
            if result:
                indicators['sma_20'] = float(result[1]) if result[1] else None
                indicators['sma_50'] = float(result[2]) if result[2] else None
            
            # RSI calculation (simplified)
            rsi_query = """
                WITH price_changes AS (
                    SELECT 
                        timestamp,
                        close,
                        close - LAG(close) OVER (ORDER BY timestamp) as price_change
                    FROM ohlc_data
                    ORDER BY timestamp
                ),
                gains_losses AS (
                    SELECT 
                        timestamp,
                        CASE WHEN price_change > 0 THEN price_change ELSE 0 END as gain,
                        CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END as loss
                    FROM price_changes
                    WHERE price_change IS NOT NULL
                ),
                avg_gains_losses AS (
                    SELECT 
                        timestamp,
                        AVG(gain) OVER (ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_gain,
                        AVG(loss) OVER (ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_loss
                    FROM gains_losses
                )
                SELECT 
                    100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0)))) as rsi
                FROM avg_gains_losses 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            
            try:
                rsi_result = self.conn.execute(rsi_query).fetchone()
                if rsi_result and rsi_result[0]:
                    indicators['rsi'] = float(rsi_result[0])
            except Exception as rsi_error:
                logger.warning(f"RSI calculation failed: {rsi_error}")
            
            # Bollinger Bands
            bb_query = """
                WITH stats AS (
                    SELECT 
                        timestamp,
                        close,
                        AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
                        STDDEV(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as std_20
                    FROM ohlc_data
                )
                SELECT 
                    sma_20 + (2 * std_20) as bb_upper,
                    sma_20 as bb_middle,
                    sma_20 - (2 * std_20) as bb_lower
                FROM stats 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            
            try:
                bb_result = self.conn.execute(bb_query).fetchone()
                if bb_result:
                    indicators['bb_upper'] = float(bb_result[0]) if bb_result[0] else None
                    indicators['bb_middle'] = float(bb_result[1]) if bb_result[1] else None
                    indicators['bb_lower'] = float(bb_result[2]) if bb_result[2] else None
            except Exception as bb_error:
                logger.warning(f"Bollinger Bands calculation failed: {bb_error}")
            
            logger.info(f"Calculated {len(indicators)} technical indicators for {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def store_indicators_to_timescale(self, symbol: str, indicators: Dict[str, Any], 
                                    timeframe: str = '1h') -> bool:
        """Store calculated indicators back to TimescaleDB."""
        try:
            if not indicators:
                return False
            
            timestamp = datetime.utcnow()
            
            with self.timescale_manager.engine.connect() as conn:
                for indicator_name, value in indicators.items():
                    if value is not None:
                        insert_query = """
                            INSERT INTO analytics.indicators 
                            (symbol, timeframe, timestamp, indicator_name, indicator_value, created_at)
                            VALUES (:symbol, :timeframe, :timestamp, :indicator_name, :indicator_value, :created_at)
                            ON CONFLICT (symbol, timeframe, timestamp, indicator_name)
                            DO UPDATE SET 
                                indicator_value = EXCLUDED.indicator_value,
                                created_at = EXCLUDED.created_at
                        """
                        
                        conn.execute(text(insert_query), {
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'timestamp': timestamp,
                            'indicator_name': indicator_name,
                            'indicator_value': float(value),
                            'created_at': timestamp
                        })
                
                conn.commit()
            
            logger.info(f"Stored {len(indicators)} indicators for {symbol} to TimescaleDB")
            return True
            
        except Exception as e:
            logger.error(f"Error storing indicators to TimescaleDB: {e}")
            return False

# Initialize managers
timescale_manager = TimescaleDBManager()
duckdb_engine = DuckDBAnalyticalEngine(timescale_manager)

@celery_app.task(bind=True)
def update_market_data_timescale_first(self, categories: Optional[List[str]] = None, force_update: bool = False):
    """
    Update market data with TimescaleDB-first approach.
    
    Data Flow:
    1. Fetch market data from exchanges
    2. Store in TimescaleDB (primary storage)
    3. Use DuckDB for analytical processing
    4. Store analytical results back to TimescaleDB
    """
    try:
        logger.info("="*60)
        logger.info("TIMESCALEDB-FIRST DATA UPDATE STARTED")
        logger.info("="*60)
        
        # Default to crypto and stocks
        if categories is None:
            categories = ["crypto", "stocks", "forex", "commodities"]
        
        total_categories = len(categories)
        all_stats = {}
        processed_categories = 0
        
        for category in categories:
            try:
                # Update progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed_categories,
                        'total': total_categories,
                        'category': category,
                        'status': f'Processing {category.upper()} with TimescaleDB-first approach'
                    }
                )
                
                if category == "crypto":
                    category_stats = update_crypto_data_timescale(force_update)
                elif category == "stocks":
                    # Import TwelveData tasks
                    from tasks.twelvedata_ingestion import update_stock_data_timescale
                    result = update_stock_data_timescale.apply(args=[None, force_update]).get()
                    category_stats = {
                        "success": result.get("success_count", 0),
                        "failed": result.get("failed_count", 0),
                        "skipped": 0,
                        "total_records": result.get("total_records", 0)
                    }
                elif category == "forex":
                    # Import TwelveData tasks
                    from tasks.twelvedata_ingestion import update_forex_data_timescale
                    result = update_forex_data_timescale.apply(args=[None, force_update]).get()
                    category_stats = {
                        "success": result.get("success_count", 0),
                        "failed": result.get("failed_count", 0),
                        "skipped": 0,
                        "total_records": result.get("total_records", 0)
                    }
                elif category == "commodities":
                    # Import TwelveData tasks
                    from tasks.twelvedata_ingestion import update_commodity_data_timescale
                    result = update_commodity_data_timescale.apply(args=[None, force_update]).get()
                    category_stats = {
                        "success": result.get("success_count", 0),
                        "failed": result.get("failed_count", 0),
                        "skipped": 0,
                        "total_records": result.get("total_records", 0)
                    }
                else:
                    # Placeholder for other categories
                    category_stats = {"success": 0, "failed": 0, "skipped": 1, "message": f"{category} not implemented yet"}
                
                all_stats[category] = category_stats
                
                # Log results
                success = category_stats.get("success", 0)
                failed = category_stats.get("failed", 0)
                skipped = category_stats.get("skipped", 0)
                total_records = category_stats.get("total_records", 0)
                logger.info(f"{category.upper()} Results: {success} success, {failed} failed, {skipped} skipped, {total_records} records")
                
                processed_categories += 1
                
                # Small delay between categories
                if processed_categories < total_categories:
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                all_stats[category] = {"success": 0, "failed": 0, "skipped": 0, "error": str(e)}
                processed_categories += 1
                continue
        
        # Calculate overall summary
        total_success = sum(stats.get("success", 0) for stats in all_stats.values())
        total_failed = sum(stats.get("failed", 0) for stats in all_stats.values())
        total_skipped = sum(stats.get("skipped", 0) for stats in all_stats.values())
        total_records = sum(stats.get("total_records", 0) for stats in all_stats.values())
        
        logger.info("="*60)
        logger.info("TIMESCALEDB-FIRST UPDATE SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Success: {total_success}")
        logger.info(f"Total Failed: {total_failed}")
        logger.info(f"Total Skipped: {total_skipped}")
        logger.info(f"Total Records: {total_records}")
        logger.info("="*60)
        
        return {
            'status': 'completed',
            'approach': 'timescaledb_first',
            'categories_processed': processed_categories,
            'total_categories': total_categories,
            'summary': {
                'total_success': total_success,
                'total_failed': total_failed,
                'total_skipped': total_skipped,
                'total_records': total_records
            },
            'details': all_stats,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in TimescaleDB-first update: {e}")
        raise

def get_top_100_crypto_assets() -> List[str]:
    """Get top 100 crypto assets by 24h volume from Binance."""
    try:
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Get 24hr ticker for all symbols
        tickers = exchange.fetch_tickers()
        
        # Filter for USDT pairs and sort by volume
        usdt_pairs = []
        for symbol, ticker in tickers.items():
            if symbol.endswith('/USDT') and symbol != 'USDT/USDT':
                volume_usd = float(ticker.get('quoteVolume', 0))
                if volume_usd > 0:  # Only include pairs with volume
                    usdt_pairs.append({
                        'symbol': symbol,
                        'volume': volume_usd,
                        'price': float(ticker.get('last', 0))
                    })
        
        # Sort by volume and return top 100
        usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
        top_100_symbols = [pair['symbol'] for pair in usdt_pairs[:100]]
        
        logger.info(f"Found {len(top_100_symbols)} top crypto assets by volume")
        return top_100_symbols
        
    except Exception as e:
        logger.error(f"Error getting top 100 crypto assets: {e}")
        # Fallback to default symbols
        return ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'BNB/USDT', 'SOL/USDT']

def update_crypto_data_timescale(force_update: bool = False) -> Dict[str, int]:
    """Update crypto data using TimescaleDB-first approach."""
    try:
        # Get top 100 crypto assets by volume
        symbols = get_top_100_crypto_assets()
        
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        success_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Processing {symbol}...")
                
                # Check if we need to update (unless forced)
                if not force_update:
                    latest_timestamp = timescale_manager.get_latest_timestamp(symbol, 'binance', '1h')
                    if latest_timestamp and (datetime.utcnow() - latest_timestamp).total_seconds() < 3600:
                        logger.info(f"Skipping {symbol} - data is recent")
                        continue
                
                # Fetch OHLCV data from exchange
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
                
                if ohlcv:
                    # Convert to proper format
                    data = []
                    for candle in ohlcv:
                        data.append({
                            'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                            'open': candle[1],
                            'high': candle[2],
                            'low': candle[3],
                            'close': candle[4],
                            'volume': candle[5]
                        })
                    
                    # Store in TimescaleDB (primary storage)
                    inserted_count = timescale_manager.insert_ohlc_data(data, symbol, 'binance', '1h')
                    
                    if inserted_count > 0:
                        logger.info(f"Stored {inserted_count} records for {symbol} in TimescaleDB")
                        
                        # Calculate technical indicators using DuckDB
                        indicators = duckdb_engine.calculate_technical_indicators(symbol)
                        
                        if indicators:
                            # Store indicators back to TimescaleDB
                            duckdb_engine.store_indicators_to_timescale(symbol, indicators, '1h')
                            logger.info(f"Calculated and stored indicators for {symbol}")
                        
                        # Calculate Autonama Channels signals
                        try:
                            from tasks.autonama_channels_tasks import calculate_autonama_signals_for_symbol
                            autonama_result = calculate_autonama_signals_for_symbol.apply(
                                args=[symbol, 'binance', '1h']
                            ).get()
                            
                            if autonama_result['status'] == 'completed':
                                logger.info(f"Calculated Autonama signals for {symbol}: {autonama_result['signal']}")
                            else:
                                logger.warning(f"Autonama calculation failed for {symbol}: {autonama_result.get('message', 'Unknown error')}")
                        except Exception as e:
                            logger.warning(f"Autonama calculation error for {symbol}: {e}")
                        
                        success_count += 1
                    else:
                        logger.warning(f"No data inserted for {symbol}")
                        failed_count += 1
                else:
                    logger.warning(f"No OHLCV data received for {symbol}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed_count += 1
                
            # Rate limiting
            time.sleep(0.1)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": 0,
            "message": "TimescaleDB-first crypto data update completed"
        }
        
    except Exception as e:
        logger.error(f"Error in TimescaleDB-first crypto update: {e}")
        return {"success": 0, "failed": 1, "skipped": 0, "error": str(e)}

@celery_app.task(bind=True)
def calculate_indicators_for_symbol(self, symbol: str, timeframe: str = '1h'):
    """Calculate technical indicators for a specific symbol using DuckDB analytical engine."""
    try:
        logger.info(f"Calculating indicators for {symbol}")
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'symbol': symbol,
                'status': f'Calculating indicators for {symbol}'
            }
        )
        
        # Calculate indicators using DuckDB
        indicators = duckdb_engine.calculate_technical_indicators(symbol)
        
        if indicators:
            # Store results back to TimescaleDB
            success = duckdb_engine.store_indicators_to_timescale(symbol, indicators, timeframe)
            
            if success:
                logger.info(f"Successfully calculated and stored {len(indicators)} indicators for {symbol}")
                return {
                    'status': 'completed',
                    'symbol': symbol,
                    'indicators_calculated': len(indicators),
                    'indicators': indicators
                }
            else:
                logger.error(f"Failed to store indicators for {symbol}")
                return {
                    'status': 'failed',
                    'symbol': symbol,
                    'error': 'Failed to store indicators'
                }
        else:
            logger.warning(f"No indicators calculated for {symbol}")
            return {
                'status': 'no_data',
                'symbol': symbol,
                'message': 'No indicators calculated'
            }
            
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        raise
