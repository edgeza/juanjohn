from celery import current_task
from celery_app import celery_app
import pandas as pd
import yfinance as yf
import ccxt
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time
import sys
import os

logger = logging.getLogger(__name__)

# Import the new TimescaleDB-first system
try:
    from .timescale_data_ingestion import (
        update_market_data_timescale_first,
        calculate_indicators_for_symbol,
        timescale_manager,
        duckdb_engine
    )
    TIMESCALE_AVAILABLE = True
    logger.info("TimescaleDB-first system available")
except ImportError as e:
    TIMESCALE_AVAILABLE = False
    logger.warning(f"TimescaleDB-first system not available: {e}")

def setup_data_processor():
    """Setup the DuckDBDataProcessor for data operations."""
    try:
        # Add the simple directory to the path to import DuckDBDataProcessor
        simple_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'simple')
        if simple_path not in sys.path:
            sys.path.append(simple_path)
        
        from processors.duckdb_manager import DuckDBManager as DuckDBDataProcessor
        return DuckDBDataProcessor
    except ImportError as e:
        logger.error(f"Failed to import DuckDBDataProcessor: {e}")
        logger.error(f"Make sure the simple directory is accessible at: {simple_path}")
        raise

def create_data_processor(read_only: bool = False):
    """Create a DuckDBDataProcessor instance with proper configuration for Docker environment."""
    try:
        DuckDBDataProcessor = setup_data_processor()
        
        # Configure paths for Docker container environment
        # The DuckDB database should be in the mounted volume
        db_path = os.getenv('DUCKDB_PATH', '/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb')
        
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created DuckDB directory: {db_dir}")
        
        # Initialize the processor
        # Note: We'll need to modify the DuckDBDataProcessor to accept custom paths
        # For now, let's try with the default initialization and see if we can work around it
        processor = DuckDBDataProcessor(read_only=read_only)
        
        return processor
        
    except Exception as e:
        logger.error(f"Failed to create DuckDBDataProcessor: {e}")
        raise

@celery_app.task(bind=True)
def update_market_data(self, categories: Optional[List[str]] = None, force_update: bool = False):
    """
    Update market data using the hybrid TimescaleDB-first approach.
    
    Architecture:
    1. Try TimescaleDB-first approach (primary storage + DuckDB analytics)
    2. Fallback to legacy DuckDB file approach if needed
    3. Final fallback to basic data fetching
    
    Args:
        categories: List of categories to update ['crypto', 'forex', 'stock', 'commodity']
                   If None, updates all categories
        force_update: Whether to force update all data regardless of freshness
    """
    try:
        logger.info("="*60)
        logger.info("HYBRID DATA UPDATE TASK STARTED")
        logger.info("="*60)
        
        # Try TimescaleDB-first approach
        if TIMESCALE_AVAILABLE:
            try:
                logger.info("Using TimescaleDB-first approach (primary storage + DuckDB analytics)")
                result = update_market_data_timescale_first.apply_async(
                    args=[categories, force_update]
                ).get()
                
                # Update our task progress to match the TimescaleDB task
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'approach': 'timescaledb_first',
                        'status': 'Completed TimescaleDB-first update',
                        'details': result
                    }
                )
                
                logger.info("TimescaleDB-first approach completed successfully")
                return result
                
            except Exception as timescale_error:
                logger.warning(f"TimescaleDB-first approach failed: {timescale_error}")
                logger.info("Falling back to legacy approach")
        
        # Fallback to legacy approach
        return update_market_data_legacy(self, categories, force_update)
        
    except Exception as e:
        logger.error(f"Critical error in hybrid update_market_data: {e}")
        raise

def update_market_data_legacy(self, categories: Optional[List[str]] = None, force_update: bool = False):
    """Legacy data update approach with fallback system."""
    try:
        logger.info("Using legacy data update approach")
        
        # Try to setup data processor with proper configuration
        processor = None
        use_fallback = False
        
        try:
            processor = create_data_processor(read_only=False)
            logger.info("DuckDBDataProcessor initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize DuckDBDataProcessor: {e}")
            logger.info("Switching to fallback data update approach")
            use_fallback = True
        
        # Default to all categories if none specified
        if categories is None:
            categories = ["crypto", "forex", "stock", "commodity"]
        
        # Validate categories
        valid_categories = ["crypto", "forex", "stock", "commodity"]
        categories = [cat for cat in categories if cat in valid_categories]
        
        if not categories:
            logger.error("No valid categories specified")
            return {
                'status': 'error',
                'message': 'No valid categories specified'
            }
        
        total_categories = len(categories)
        all_stats = {}
        processed_categories = 0
        
        # Process each category
        for category in categories:
            try:
                # Update progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed_categories,
                        'total': total_categories,
                        'category': category,
                        'status': f'Processing {category.upper()}',
                        'fallback_mode': use_fallback,
                        'approach': 'legacy'
                    }
                )
                
                logger.info(f"Processing {category.upper()} (Priority {categories.index(category) + 1})")
                
                if use_fallback:
                    category_stats = update_category_data_fallback(category, force_update)
                else:
                    category_stats = update_category_data(processor, category, force_update)
                
                all_stats[category] = category_stats
                
                # Log results
                success = category_stats.get("success", 0)
                failed = category_stats.get("failed", 0)
                skipped = category_stats.get("skipped", 0)
                logger.info(f"{category.upper()} Results: {success} success, {failed} failed, {skipped} skipped")
                
                processed_categories += 1
                
                # Small delay between categories to avoid overwhelming APIs
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
        
        logger.info("="*60)
        logger.info("LEGACY UPDATE SUMMARY")
        logger.info("="*60)
        logger.info(f"Mode: {'Fallback' if use_fallback else 'Full DuckDB'}")
        logger.info(f"Total Success: {total_success}")
        logger.info(f"Total Failed: {total_failed}")
        logger.info(f"Total Skipped: {total_skipped}")
        logger.info("="*60)
        
        return {
            'status': 'completed',
            'approach': 'legacy',
            'categories_processed': processed_categories,
            'total_categories': total_categories,
            'fallback_mode': use_fallback,
            'summary': {
                'total_success': total_success,
                'total_failed': total_failed,
                'total_skipped': total_skipped
            },
            'details': all_stats,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in legacy update: {e}")
        raise

def update_category_data_fallback(category: str, force_update: bool = False) -> Dict[str, int]:
    """
    Fallback data update function that uses basic data fetching when DuckDBDataProcessor fails.
    Now enhanced to store data in TimescaleDB when available.
    """
    logger.info(f"Using fallback data update for {category.upper()}")
    
    try:
        if category == "crypto":
            # Try TimescaleDB-aware crypto update first
            if TIMESCALE_AVAILABLE:
                try:
                    from .timescale_data_ingestion import update_crypto_data_timescale
                    return update_crypto_data_timescale(force_update)
                except Exception as e:
                    logger.warning(f"TimescaleDB crypto update failed: {e}")
            
            # Fallback to basic crypto data update
            return update_crypto_data_basic(force_update)
            
        elif category in ["forex", "stock", "commodity"]:
            # For now, return a placeholder response for other categories
            logger.warning(f"Fallback update for {category} not yet implemented")
            return {"success": 0, "failed": 0, "skipped": 1, "message": f"Fallback for {category} not implemented"}
        else:
            logger.error(f"Unknown category: {category}")
            return {"success": 0, "failed": 1, "skipped": 0, "error": f"Unknown category: {category}"}
            
    except Exception as e:
        logger.error(f"Error in fallback update for {category}: {e}")
        return {"success": 0, "failed": 1, "skipped": 0, "error": str(e)}

def update_crypto_data_basic(force_update: bool = False) -> Dict[str, int]:
    """Basic crypto data update using CCXT with optional TimescaleDB storage."""
    try:
        # Basic crypto symbols
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'BNB/USDT', 'SOL/USDT']
        
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        success_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                # Fetch recent OHLCV data
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
                
                if ohlcv:
                    # Convert to DataFrame
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['symbol'] = symbol
                    
                    # Try to store in TimescaleDB if available
                    stored_in_timescale = False
                    if TIMESCALE_AVAILABLE:
                        try:
                            data = []
                            for _, row in df.iterrows():
                                data.append({
                                    'timestamp': row['timestamp'],
                                    'open': row['open'],
                                    'high': row['high'],
                                    'low': row['low'],
                                    'close': row['close'],
                                    'volume': row['volume']
                                })
                            
                            inserted_count = timescale_manager.insert_ohlc_data(data, symbol, 'binance', '1h')
                            if inserted_count > 0:
                                stored_in_timescale = True
                                logger.info(f"Stored {inserted_count} records for {symbol} in TimescaleDB")
                        except Exception as ts_error:
                            logger.warning(f"Failed to store {symbol} in TimescaleDB: {ts_error}")
                    
                    if not stored_in_timescale:
                        # Just log the data (basic fallback)
                        logger.info(f"Fetched {len(df)} records for {symbol} (not stored)")
                    
                    success_count += 1
                else:
                    logger.warning(f"No data received for {symbol}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                failed_count += 1
                
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": 0,
            "message": f"Basic crypto data update completed ({'with TimescaleDB storage' if TIMESCALE_AVAILABLE else 'without storage'})"
        }
        
    except Exception as e:
        logger.error(f"Error in basic crypto data update: {e}")
        return {"success": 0, "failed": 1, "skipped": 0, "error": str(e)}

def update_category_data(processor, category: str, force_update: bool = False) -> Dict[str, int]:
    """Update a specific category of data using the legacy DuckDB processor."""
    logger.info(f"Updating {category.upper()} data...")
    
    try:
        if category == "crypto":
            # Get crypto symbols and update
            crypto_symbols = processor._get_crypto_symbols()
            logger.info(f"Updating {len(crypto_symbols)} crypto symbols")
            return processor.hybrid_processor.update_data("crypto", crypto_symbols, force_update=force_update)
            
        elif category == "forex":
            # Get forex symbols and update
            forex_symbols = processor._get_forex_symbols()
            logger.info(f"Updating {len(forex_symbols)} forex symbols")
            return processor.twelvedata_processor.update_category_data("forex", forex_symbols, force_update=force_update)
            
        elif category == "stock":
            # Get stock symbols and update
            stock_symbols = processor._get_stock_symbols()
            logger.info(f"Updating {len(stock_symbols)} stock symbols")
            return processor.twelvedata_processor.update_category_data("stock", stock_symbols, force_update=force_update)
            
        elif category == "commodity":
            # Get commodity symbols and update
            commodity_symbols = processor._get_commodity_symbols()
            logger.info(f"Updating {len(commodity_symbols)} commodity symbols")
            return processor.twelvedata_processor.update_category_data("commodity", commodity_symbols, force_update=force_update)
            
        else:
            logger.error(f"Unknown category: {category}")
            return {"success": 0, "failed": 0, "skipped": 0}
            
    except Exception as e:
        logger.error(f"Error updating {category} data: {e}")
        return {"success": 0, "failed": 0, "skipped": 0}

@celery_app.task(bind=True)
def update_single_category(self, category: str, force_update: bool = False):
    """
    Update market data for a single category using hybrid approach.
    
    Args:
        category: Category to update ('crypto', 'forex', 'stock', 'commodity')
        force_update: Whether to force update all data regardless of freshness
    """
    try:
        logger.info(f"Starting single category update for {category.upper()}")
        
        # Validate category
        valid_categories = ["crypto", "forex", "stock", "commodity"]
        if category not in valid_categories:
            logger.error(f"Invalid category: {category}")
            return {
                'status': 'error',
                'message': f'Invalid category: {category}. Valid categories: {valid_categories}'
            }
        
        # Try TimescaleDB-first approach for crypto
        if category == "crypto" and TIMESCALE_AVAILABLE:
            try:
                logger.info("Using TimescaleDB-first approach for crypto")
                
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'category': category,
                        'status': f'Processing {category.upper()} with TimescaleDB-first approach',
                        'approach': 'timescaledb_first'
                    }
                )
                
                from .timescale_data_ingestion import update_crypto_data_timescale
                category_stats = update_crypto_data_timescale(force_update)
                
                # Log results
                success = category_stats.get("success", 0)
                failed = category_stats.get("failed", 0)
                skipped = category_stats.get("skipped", 0)
                logger.info(f"{category.upper()} Results: {success} success, {failed} failed, {skipped} skipped")
                logger.info("Mode: TimescaleDB-first")
                
                return {
                    'status': 'completed',
                    'category': category,
                    'approach': 'timescaledb_first',
                    'stats': category_stats,
                    'force_update': force_update
                }
                
            except Exception as timescale_error:
                logger.warning(f"TimescaleDB-first approach failed: {timescale_error}")
                logger.info("Falling back to legacy approach")
        
        # Fallback to legacy approach
        return update_single_category_legacy(self, category, force_update)
        
    except Exception as e:
        logger.error(f"Error in hybrid update_single_category for {category}: {e}")
        raise

def update_single_category_legacy(self, category: str, force_update: bool = False):
    """Legacy single category update with fallback system."""
    try:
        # Try to setup data processor with proper configuration
        processor = None
        use_fallback = False
        
        try:
            processor = create_data_processor(read_only=False)
            logger.info("DuckDBDataProcessor initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize DuckDBDataProcessor: {e}")
            logger.info("Switching to fallback data update approach")
            use_fallback = True
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'category': category,
                'status': f'Processing {category.upper()}',
                'fallback_mode': use_fallback,
                'approach': 'legacy'
            }
        )
        
        # Update the category
        if use_fallback:
            category_stats = update_category_data_fallback(category, force_update)
        else:
            category_stats = update_category_data(processor, category, force_update)
        
        # Log results
        success = category_stats.get("success", 0)
        failed = category_stats.get("failed", 0)
        skipped = category_stats.get("skipped", 0)
        logger.info(f"{category.upper()} Results: {success} success, {failed} failed, {skipped} skipped")
        logger.info(f"Mode: {'Fallback' if use_fallback else 'Full DuckDB'}")
        
        return {
            'status': 'completed',
            'category': category,
            'approach': 'legacy',
            'fallback_mode': use_fallback,
            'stats': category_stats,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Error in legacy update_single_category for {category}: {e}")
        raise


# Legacy functions for backward compatibility and historical data fetching

def fetch_binance_data(symbol: str, interval: str = '1h', limit: int = 1000) -> pd.DataFrame:
    """
    Legacy function: Fetch OHLCV data from Binance
    Note: This is kept for backward compatibility. New data updates use DuckDBDataProcessor.
    """
    try:
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, interval, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching Binance data for {symbol}: {str(e)}")
        return pd.DataFrame()

def store_market_data(df: pd.DataFrame, symbol: str):
    """
    Legacy function: Store market data in TimescaleDB
    Note: This is kept for backward compatibility. New data updates use DuckDBDataProcessor.
    """
    try:
        from utils.database import db_manager
        
        # Prepare data for insertion
        df_clean = df.copy()
        df_clean = df_clean.dropna()
        
        # Insert into TimescaleDB
        db_manager.insert_dataframe_to_postgres(
            df_clean, 
            'market_data', 
            if_exists='append'
        )
        
        # Cache latest data in Redis
        latest_data = df_clean.tail(100).to_dict('records')
        cache_key = f"market_data:{symbol}:latest"
        db_manager.cache_data(cache_key, latest_data, expire=300)  # 5 minutes
        
    except Exception as e:
        logger.error(f"Error storing market data for {symbol}: {str(e)}")
        raise


@celery_app.task(bind=True)
def fetch_historical_data(self, symbol: str, start_date: str, end_date: str):
    """Fetch historical data for backtesting"""
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': f'Fetching historical data for {symbol}'}
        )
        
        # Convert dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Fetch data in chunks to avoid rate limits
        all_data = []
        current_date = start
        
        while current_date < end:
            chunk_end = min(current_date + timedelta(days=30), end)
            
            # Fetch chunk
            chunk_data = fetch_binance_historical_chunk(symbol, current_date, chunk_end)
            if not chunk_data.empty:
                all_data.append(chunk_data)
            
            current_date = chunk_end
        
        if all_data:
            # Combine all chunks
            df = pd.concat(all_data, ignore_index=True)
            df = df.drop_duplicates(subset=['timestamp', 'symbol'])
            
            # Store in database
            store_market_data(df, symbol)
            
            return {
                'status': 'completed',
                'symbol': symbol,
                'records': len(df),
                'start_date': start_date,
                'end_date': end_date
            }
        else:
            return {
                'status': 'no_data',
                'symbol': symbol
            }
            
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        raise


def fetch_binance_historical_chunk(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Fetch historical data chunk from Binance"""
    try:
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        since = int(start_date.timestamp() * 1000)
        until = int(end_date.timestamp() * 1000)
        
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', since=since, limit=1000)
        
        # Filter by end date
        ohlcv = [candle for candle in ohlcv if candle[0] <= until]
        
        if ohlcv:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching historical chunk: {str(e)}")
        return pd.DataFrame()


@celery_app.task
def update_symbol_list():
    """Update the list of available trading symbols"""
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        
        # Filter for USDT pairs
        usdt_symbols = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
        
        # Store in Redis
        db_manager.cache_data('available_symbols', usdt_symbols, expire=86400)  # 24 hours
        
        logger.info(f"Updated symbol list: {len(usdt_symbols)} symbols")
        
        return {
            'status': 'completed',
            'symbols_count': len(usdt_symbols)
        }
        
    except Exception as e:
        logger.error(f"Error updating symbol list: {str(e)}")
        raise
