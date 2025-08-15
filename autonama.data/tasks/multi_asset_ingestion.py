"""
Enhanced Multi-Asset Data Ingestion Tasks

This module provides Celery tasks for ingesting data from multiple asset types
using the new processor architecture from Phase 2.

Features:
- Multi-asset coordination (crypto, stocks, forex, commodities)
- Intelligent error handling and retries
- Rate limiting compliance
- Performance monitoring
- Parallel processing with resource management
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from celery import Task
from celery.exceptions import Retry

from celery_app import celery_app
from processors.unified_processor import UnifiedDataProcessor
from processors.duckdb_manager import DuckDBManager
from models.asset_models import AssetConfig, AssetType, Exchange
from utils.database import get_timescale_connection
from utils.error_handler import handle_processor_error
from config.processor_config import ProcessorConfig

# Configure logging
logger = logging.getLogger(__name__)

class MultiAssetIngestionTask(Task):
    """Base task class for multi-asset ingestion with error handling"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_jitter = True

@celery_app.task(bind=True, base=MultiAssetIngestionTask)
def ingest_multi_asset_data(self, asset_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingest data for multiple asset types using the unified processor
    
    Args:
        asset_configs: List of asset configuration dictionaries
        
    Returns:
        Dict with ingestion results and statistics
    """
    start_time = datetime.now()
    results = {
        'task_id': self.request.id,
        'start_time': start_time.isoformat(),
        'assets_processed': 0,
        'assets_failed': 0,
        'errors': [],
        'performance_stats': {}
    }
    
    try:
        # Initialize unified processor
        unified_processor = UnifiedDataProcessor()
        
        # Convert dict configs to AssetConfig objects
        assets = []
        for config in asset_configs:
            try:
                asset = AssetConfig(
                    symbol=config['symbol'],
                    asset_type=AssetType(config['asset_type']),
                    exchange=Exchange(config['exchange']),
                    priority=config.get('priority', 1)
                )
                assets.append(asset)
            except Exception as e:
                logger.error(f"Invalid asset config {config}: {e}")
                results['errors'].append(f"Invalid config {config}: {str(e)}")
        
        if not assets:
            raise ValueError("No valid asset configurations provided")
        
        # Process assets using unified processor
        logger.info(f"Starting ingestion for {len(assets)} assets")
        
        ingestion_results = unified_processor.update_all_assets(assets)
        
        # Process results
        for asset_symbol, result in ingestion_results.items():
            if result.get('success', False):
                results['assets_processed'] += 1
                logger.info(f"Successfully processed {asset_symbol}")
            else:
                results['assets_failed'] += 1
                error_msg = f"Failed to process {asset_symbol}: {result.get('error', 'Unknown error')}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Add performance statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results.update({
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'success_rate': results['assets_processed'] / len(assets) if assets else 0,
            'performance_stats': unified_processor.get_performance_stats()
        })
        
        logger.info(f"Multi-asset ingestion completed: {results['assets_processed']}/{len(assets)} successful")
        
        return results
        
    except Exception as e:
        error_msg = f"Multi-asset ingestion failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        results['errors'].append(error_msg)
        
        # Handle specific error types
        if isinstance(e, ConnectionError):
            # Retry on connection errors
            raise self.retry(countdown=120, max_retries=5)
        
        return results

@celery_app.task(bind=True, base=MultiAssetIngestionTask)
def ingest_crypto_assets(self, symbols: List[str] = None) -> Dict[str, Any]:
    """
    Ingest cryptocurrency data using Binance and CCXT processors
    
    Args:
        symbols: List of crypto symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
        
    Returns:
        Dict with ingestion results
    """
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'BNB/USDT', 'SOL/USDT']
    
    # Convert to asset configs
    asset_configs = [
        {
            'symbol': symbol,
            'asset_type': 'crypto',
            'exchange': 'binance',
            'priority': 1
        }
        for symbol in symbols
    ]
    
    return ingest_multi_asset_data.apply_async(args=[asset_configs]).get()

@celery_app.task(bind=True, base=MultiAssetIngestionTask)
def ingest_stock_assets(self, symbols: List[str] = None) -> Dict[str, Any]:
    """
    Ingest stock market data using TwelveData processor
    
    Args:
        symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL', 'MSFT'])
        
    Returns:
        Dict with ingestion results
    """
    if symbols is None:
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    # Convert to asset configs
    asset_configs = [
        {
            'symbol': symbol,
            'asset_type': 'stock',
            'exchange': 'nasdaq',
            'priority': 2
        }
        for symbol in symbols
    ]
    
    return ingest_multi_asset_data.apply_async(args=[asset_configs]).get()

@celery_app.task(bind=True, base=MultiAssetIngestionTask)
def ingest_forex_assets(self, pairs: List[str] = None) -> Dict[str, Any]:
    """
    Ingest forex data using TwelveData processor
    
    Args:
        pairs: List of forex pairs (e.g., ['EUR/USD', 'GBP/USD'])
        
    Returns:
        Dict with ingestion results
    """
    if pairs is None:
        pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD']
    
    # Convert to asset configs
    asset_configs = [
        {
            'symbol': pair,
            'asset_type': 'forex',
            'exchange': 'forex',
            'priority': 3
        }
        for pair in pairs
    ]
    
    return ingest_multi_asset_data.apply_async(args=[asset_configs]).get()

@celery_app.task(bind=True, base=MultiAssetIngestionTask)
def ingest_commodity_assets(self, symbols: List[str] = None) -> Dict[str, Any]:
    """
    Ingest commodity data using TwelveData processor
    
    Args:
        symbols: List of commodity symbols (e.g., ['GOLD', 'OIL', 'SILVER'])
        
    Returns:
        Dict with ingestion results
    """
    if symbols is None:
        symbols = ['GOLD', 'OIL', 'SILVER', 'COPPER', 'PLATINUM']
    
    # Convert to asset configs
    asset_configs = [
        {
            'symbol': symbol,
            'asset_type': 'commodity',
            'exchange': 'commodity',
            'priority': 4
        }
        for symbol in symbols
    ]
    
    return ingest_multi_asset_data.apply_async(args=[asset_configs]).get()

@celery_app.task(bind=True)
def update_all_asset_types(self) -> Dict[str, Any]:
    """
    Comprehensive update of all asset types in parallel
    
    Returns:
        Dict with results from all asset type updates
    """
    start_time = datetime.now()
    
    try:
        # Launch parallel tasks for each asset type
        crypto_task = ingest_crypto_assets.delay()
        stock_task = ingest_stock_assets.delay()
        forex_task = ingest_forex_assets.delay()
        commodity_task = ingest_commodity_assets.delay()
        
        # Collect results
        results = {
            'task_id': self.request.id,
            'start_time': start_time.isoformat(),
            'crypto_results': crypto_task.get(timeout=300),
            'stock_results': stock_task.get(timeout=300),
            'forex_results': forex_task.get(timeout=300),
            'commodity_results': commodity_task.get(timeout=300)
        }
        
        # Calculate overall statistics
        total_processed = sum([
            results['crypto_results']['assets_processed'],
            results['stock_results']['assets_processed'],
            results['forex_results']['assets_processed'],
            results['commodity_results']['assets_processed']
        ])
        
        total_failed = sum([
            results['crypto_results']['assets_failed'],
            results['stock_results']['assets_failed'],
            results['forex_results']['assets_failed'],
            results['commodity_results']['assets_failed']
        ])
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results.update({
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_assets_processed': total_processed,
            'total_assets_failed': total_failed,
            'overall_success_rate': total_processed / (total_processed + total_failed) if (total_processed + total_failed) > 0 else 0
        })
        
        logger.info(f"All asset types update completed: {total_processed} successful, {total_failed} failed")
        
        return results
        
    except Exception as e:
        logger.error(f"All asset types update failed: {e}", exc_info=True)
        return {
            'task_id': self.request.id,
            'error': str(e),
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }

@celery_app.task(bind=True)
def sync_data_to_analytics(self, symbols: List[str] = None) -> Dict[str, Any]:
    """
    Sync data from TimescaleDB to DuckDB for analytics
    
    Args:
        symbols: List of symbols to sync (None for all)
        
    Returns:
        Dict with sync results
    """
    start_time = datetime.now()
    
    try:
        duckdb_manager = DuckDBManager()
        
        if symbols is None:
            # Get all symbols from TimescaleDB
            with get_timescale_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM trading.ohlc_data")
                symbols = [row[0] for row in cursor.fetchall()]
        
        sync_results = {}
        
        for symbol in symbols:
            try:
                # Sync symbol data to DuckDB
                rows_synced = duckdb_manager.sync_from_timescale('ohlc_data', symbol)
                sync_results[symbol] = {
                    'success': True,
                    'rows_synced': rows_synced
                }
                logger.info(f"Synced {rows_synced} rows for {symbol}")
                
            except Exception as e:
                sync_results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Failed to sync {symbol}: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful_syncs = sum(1 for result in sync_results.values() if result['success'])
        total_rows_synced = sum(result.get('rows_synced', 0) for result in sync_results.values() if result['success'])
        
        return {
            'task_id': self.request.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'symbols_processed': len(symbols),
            'successful_syncs': successful_syncs,
            'total_rows_synced': total_rows_synced,
            'sync_results': sync_results
        }
        
    except Exception as e:
        logger.error(f"Data sync to analytics failed: {e}", exc_info=True)
        return {
            'task_id': self.request.id,
            'error': str(e),
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }

# Periodic tasks for scheduled data updates
@celery_app.task(bind=True)
def scheduled_crypto_update(self):
    """Scheduled task for crypto data updates (every 5 minutes)"""
    return ingest_crypto_assets.delay().get()

@celery_app.task(bind=True)
def scheduled_stock_update(self):
    """Scheduled task for stock data updates (every 15 minutes during market hours)"""
    return ingest_stock_assets.delay().get()

@celery_app.task(bind=True)
def scheduled_forex_update(self):
    """Scheduled task for forex data updates (every 10 minutes)"""
    return ingest_forex_assets.delay().get()

@celery_app.task(bind=True)
def scheduled_analytics_sync(self):
    """Scheduled task for analytics data sync (every hour)"""
    return sync_data_to_analytics.delay().get()
