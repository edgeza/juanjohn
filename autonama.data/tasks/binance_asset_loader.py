"""
Binance Asset Loader Tasks

This module provides Celery tasks for loading the top 100 Binance assets
by 24h volume into PostgreSQL/TimescaleDB.
"""

import ccxt
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from celery import Task
from celery.exceptions import Retry

from celery_app import celery_app
from utils.database import get_timescale_connection
from utils.error_handler import handle_processor_error

logger = logging.getLogger(__name__)

class BinanceAssetLoaderTask(Task):
    """Base task class for Binance asset loading with error handling"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_jitter = True

@celery_app.task(bind=True, base=BinanceAssetLoaderTask)
def load_top_100_binance_assets(self) -> Dict[str, Any]:
    """
    Load the top 100 Binance assets by 24h volume into PostgreSQL.
    
    This task:
    1. Fetches all USDT pairs from Binance
    2. Sorts by 24h volume
    3. Takes the top 100
    4. Stores asset metadata in PostgreSQL
    5. Triggers data ingestion for these assets
    
    Returns:
        Dict with loading results and statistics
    """
    start_time = datetime.now()
    
    try:
        logger.info("Starting top 100 Binance assets loading...")
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Get 24hr ticker for all symbols
        logger.info("Fetching all tickers from Binance...")
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
                        'price': float(ticker.get('last', 0) or 0),
                        'change_24h': float(ticker.get('change', 0) or 0),
                        'change_percent_24h': float(ticker.get('percentage', 0) or 0),
                        'high_24h': float(ticker.get('high', 0) or 0),
                        'low_24h': float(ticker.get('low', 0) or 0),
                        'bid': float(ticker.get('bid', 0) or 0),
                        'ask': float(ticker.get('ask', 0) or 0)
                    })
        
        # Sort by volume and get top 100
        usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
        top_100_assets = usdt_pairs[:100]
        
        logger.info(f"Found {len(top_100_assets)} top assets by volume")
        
        # Store asset metadata in PostgreSQL
        stored_count = 0
        failed_count = 0
        
        for asset in top_100_assets:
            try:
                # Parse symbol to get base and quote currencies
                symbol = asset['symbol']
                base_currency = symbol.split('/')[0]
                quote_currency = symbol.split('/')[1]
                
                # Store in PostgreSQL
                with get_timescale_connection() as conn:
                    with conn.cursor() as cursor:
                        # Insert or update asset metadata
                        cursor.execute("""
                            INSERT INTO trading.asset_metadata 
                            (symbol, name, asset_type, exchange, base_currency, quote_currency, 
                             created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol) DO UPDATE SET
                                name = EXCLUDED.name,
                                updated_at = EXCLUDED.updated_at
                        """, (
                            symbol,
                            f"{base_currency} / {quote_currency}",
                            'crypto',
                            'binance',
                            base_currency,
                            quote_currency,
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
                        
                        conn.commit()
                        stored_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to store asset {asset['symbol']}: {e}")
                failed_count += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results = {
            'task_id': self.request.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'assets_processed': len(top_100_assets),
            'assets_stored': stored_count,
            'assets_failed': failed_count,
            'top_assets': [
                {
                    'symbol': asset['symbol'],
                    'volume': asset['volume'],
                    'price': asset['price'],
                    'rank': idx + 1
                }
                for idx, asset in enumerate(top_100_assets[:10])  # Top 10 for summary
            ],
            'success': True
        }
        
        logger.info(f"Top 100 Binance assets loading completed in {duration:.2f} seconds")
        logger.info(f"Stored {stored_count}/{len(top_100_assets)} assets in PostgreSQL")
        
        return results
        
    except Exception as e:
        error_msg = f"Failed to load top 100 Binance assets: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return handle_processor_error(
            e,
            'binance_asset_loader',
            context={
                'task_id': self.request.id,
                'operation': 'load_top_100_assets'
            }
        )

@celery_app.task(bind=True, base=BinanceAssetLoaderTask)
def refresh_top_100_assets(self) -> Dict[str, Any]:
    """
    Refresh the top 100 assets list and update their data.
    
    This task runs periodically to ensure we're always tracking
    the most relevant assets by volume.
    """
    try:
        logger.info("Refreshing top 100 Binance assets...")
        
        # Load top 100 assets
        load_result = load_top_100_binance_assets.apply().get()
        
        return {
            'task_id': self.request.id,
            'load_result': load_result,
            'success': True
        }
        
    except Exception as e:
        error_msg = f"Failed to refresh top 100 assets: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return handle_processor_error(
            e,
            'binance_asset_loader',
            context={
                'task_id': self.request.id,
                'operation': 'refresh_top_100_assets'
            }
        )

@celery_app.task(bind=True)
def get_current_top_100_assets(self) -> Dict[str, Any]:
    """
    Get the current list of top 100 assets from PostgreSQL.
    
    Returns:
        Dict with current top 100 assets and their metadata
    """
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT symbol, name, current_price, price_change_24h, 
                           price_change_percent_24h, volume_24h, updated_at
                    FROM trading.asset_metadata 
                    WHERE asset_type = 'crypto' AND exchange = 'binance'
                    ORDER BY volume_24h DESC 
                    LIMIT 100
                """)
                
                assets = []
                for row in cursor.fetchall():
                    assets.append({
                        'symbol': row[0],
                        'name': row[1],
                        'current_price': float(row[2]) if row[2] else 0,
                        'price_change_24h': float(row[3]) if row[3] else 0,
                        'price_change_percent_24h': float(row[4]) if row[4] else 0,
                        'volume_24h': float(row[5]) if row[5] else 0,
                        'updated_at': row[6].isoformat() if row[6] else None
                    })
        
        return {
            'task_id': self.request.id,
            'assets': assets,
            'total_count': len(assets),
            'success': True
        }
        
    except Exception as e:
        error_msg = f"Failed to get current top 100 assets: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return handle_processor_error(
            e,
            'binance_asset_loader',
            context={
                'task_id': self.request.id,
                'operation': 'get_current_top_100_assets'
            }
        ) 

