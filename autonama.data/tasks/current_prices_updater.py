"""
Current Prices Updater

This module handles updating current prices from Binance and storing them
in the trading.current_prices table for real-time price display.
"""

import ccxt
import logging
from datetime import datetime
from typing import Dict, List, Any
from celery import Task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from celery_app import celery_app
from utils.database import get_timescale_connection
from utils.error_handler import handle_processor_error

logger = logging.getLogger(__name__)

def get_top_100_crypto_assets() -> List[str]:
    """Get top 100 crypto assets by 24h volume from Binance."""
    try:
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        tickers = exchange.fetch_tickers()
        usdt_pairs = []
        for symbol, ticker in tickers.items():
            if symbol.endswith('/USDT') and symbol != 'USDT/USDT':
                volume_usd = float(ticker.get('quoteVolume', 0))
                if volume_usd > 0:
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
        usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
        top_100_symbols = [pair['symbol'] for pair in usdt_pairs[:100]]
        logger.info(f"Found {len(top_100_symbols)} top crypto assets by volume")
        return top_100_symbols
    except Exception as e:
        logger.error(f"Error getting top 100 crypto assets: {e}")
        return ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'BNB/USDT', 'SOL/USDT']

@celery_app.task(bind=True)
def update_current_prices(self):
    """Update current prices for all crypto assets from Binance."""
    try:
        logger.info("Starting current prices update from Binance")
        
        # Get top 100 crypto assets
        symbols = get_top_100_crypto_assets()
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Get database connection
        engine = get_timescale_connection()
        
        # First, ensure all top 100 assets exist in asset_metadata table
        with engine as conn:
            for symbol in symbols:
                try:
                    base_currency = symbol.split('/')[0]
                    quote_currency = symbol.split('/')[1]
                    
                    # Insert asset metadata if it doesn't exist
                    conn.execute(text("""
                        INSERT INTO trading.asset_metadata 
                        (symbol, name, asset_type, exchange, base_currency, quote_currency, created_at, updated_at)
                        VALUES (:symbol, :name, :asset_type, :exchange, :base_currency, :quote_currency, :created_at, :updated_at)
                        ON CONFLICT (symbol) DO NOTHING
                    """), {
                        'symbol': symbol,
                        'name': f"{base_currency} / {quote_currency}",
                        'asset_type': 'crypto',
                        'exchange': 'binance',
                        'base_currency': base_currency,
                        'quote_currency': quote_currency,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to ensure asset metadata for {symbol}: {e}")
        
        success_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                # Fetch current ticker data
                ticker = exchange.fetch_ticker(symbol)
                
                if ticker and ticker.get('last'):
                    # Prepare data for insertion
                    price_data = {
                        'symbol': symbol,
                        'price': float(ticker.get('last', 0)),
                        'bid': float(ticker.get('bid', 0)),
                        'ask': float(ticker.get('ask', 0)),
                        'spread': float(ticker.get('ask', 0) - ticker.get('bid', 0)),
                        'volume_24h': float(ticker.get('quoteVolume', 0)),
                        'change_24h': float(ticker.get('change', 0)),
                        'change_percent_24h': float(ticker.get('percentage', 0)),
                        'high_24h': float(ticker.get('high', 0)),
                        'low_24h': float(ticker.get('low', 0)),
                        'timestamp': datetime.utcnow(),
                        'source': 'binance'
                    }
                    
                    # Insert or update current price
                    with engine as conn:
                        query = """
                        INSERT INTO trading.current_prices (
                            symbol, price, bid, ask, spread, volume_24h, 
                            change_24h, change_percent_24h, high_24h, low_24h, 
                            timestamp, source
                        ) VALUES (
                            :symbol, :price, :bid, :ask, :spread, :volume_24h,
                            :change_24h, :change_percent_24h, :high_24h, :low_24h,
                            :timestamp, :source
                        ) ON CONFLICT (symbol) DO UPDATE SET
                            price = EXCLUDED.price,
                            bid = EXCLUDED.bid,
                            ask = EXCLUDED.ask,
                            spread = EXCLUDED.spread,
                            volume_24h = EXCLUDED.volume_24h,
                            change_24h = EXCLUDED.change_24h,
                            change_percent_24h = EXCLUDED.change_percent_24h,
                            high_24h = EXCLUDED.high_24h,
                            low_24h = EXCLUDED.low_24h,
                            timestamp = EXCLUDED.timestamp,
                            source = EXCLUDED.source
                        """
                        
                        conn.execute(text(query), price_data)
                        conn.commit()
                        
                        success_count += 1
                        logger.debug(f"Updated current price for {symbol}: ${price_data['price']:.4f}")
                else:
                    logger.warning(f"No valid ticker data for {symbol}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating current price for {symbol}: {e}")
                failed_count += 1
                
            # Rate limiting
            import time
            time.sleep(0.1)
        
        logger.info(f"Current prices update completed: {success_count} successful, {failed_count} failed")
        return {
            "success": success_count,
            "failed": failed_count,
            "message": "Current prices updated from Binance"
        }
        
    except Exception as e:
        error_msg = f"Error in current prices update: {str(e)}"
        logger.error(error_msg)
        return {
            "success": 0,
            "failed": 1,
            "error": error_msg
        }

@celery_app.task(bind=True)
def force_update_current_prices(self):
    """Force update current prices for all assets."""
    return update_current_prices.apply().get() 
Current Prices Updater

This module handles updating current prices from Binance and storing them
in the trading.current_prices table for real-time price display.
"""

import ccxt
import logging
from datetime import datetime
from typing import Dict, List, Any
from celery import Task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from celery_app import celery_app
from utils.database import get_timescale_connection
from utils.error_handler import handle_processor_error

logger = logging.getLogger(__name__)

def get_top_100_crypto_assets() -> List[str]:
    """Get top 100 crypto assets by 24h volume from Binance."""
    try:
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        tickers = exchange.fetch_tickers()
        usdt_pairs = []
        for symbol, ticker in tickers.items():
            if symbol.endswith('/USDT') and symbol != 'USDT/USDT':
                volume_usd = float(ticker.get('quoteVolume', 0))
                if volume_usd > 0:
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
        usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
        top_100_symbols = [pair['symbol'] for pair in usdt_pairs[:100]]
        logger.info(f"Found {len(top_100_symbols)} top crypto assets by volume")
        return top_100_symbols
    except Exception as e:
        logger.error(f"Error getting top 100 crypto assets: {e}")
        return ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'BNB/USDT', 'SOL/USDT']

@celery_app.task(bind=True)
def update_current_prices(self):
    """Update current prices for all crypto assets from Binance."""
    try:
        logger.info("Starting current prices update from Binance")
        
        # Get top 100 crypto assets
        symbols = get_top_100_crypto_assets()
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Get database connection
        engine = get_timescale_connection()
        
        # First, ensure all top 100 assets exist in asset_metadata table
        with engine as conn:
            for symbol in symbols:
                try:
                    base_currency = symbol.split('/')[0]
                    quote_currency = symbol.split('/')[1]
                    
                    # Insert asset metadata if it doesn't exist
                    conn.execute(text("""
                        INSERT INTO trading.asset_metadata 
                        (symbol, name, asset_type, exchange, base_currency, quote_currency, created_at, updated_at)
                        VALUES (:symbol, :name, :asset_type, :exchange, :base_currency, :quote_currency, :created_at, :updated_at)
                        ON CONFLICT (symbol) DO NOTHING
                    """), {
                        'symbol': symbol,
                        'name': f"{base_currency} / {quote_currency}",
                        'asset_type': 'crypto',
                        'exchange': 'binance',
                        'base_currency': base_currency,
                        'quote_currency': quote_currency,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to ensure asset metadata for {symbol}: {e}")
        
        success_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                # Fetch current ticker data
                ticker = exchange.fetch_ticker(symbol)
                
                if ticker and ticker.get('last'):
                    # Prepare data for insertion
                    price_data = {
                        'symbol': symbol,
                        'price': float(ticker.get('last', 0)),
                        'bid': float(ticker.get('bid', 0)),
                        'ask': float(ticker.get('ask', 0)),
                        'spread': float(ticker.get('ask', 0) - ticker.get('bid', 0)),
                        'volume_24h': float(ticker.get('quoteVolume', 0)),
                        'change_24h': float(ticker.get('change', 0)),
                        'change_percent_24h': float(ticker.get('percentage', 0)),
                        'high_24h': float(ticker.get('high', 0)),
                        'low_24h': float(ticker.get('low', 0)),
                        'timestamp': datetime.utcnow(),
                        'source': 'binance'
                    }
                    
                    # Insert or update current price
                    with engine as conn:
                        query = """
                        INSERT INTO trading.current_prices (
                            symbol, price, bid, ask, spread, volume_24h, 
                            change_24h, change_percent_24h, high_24h, low_24h, 
                            timestamp, source
                        ) VALUES (
                            :symbol, :price, :bid, :ask, :spread, :volume_24h,
                            :change_24h, :change_percent_24h, :high_24h, :low_24h,
                            :timestamp, :source
                        ) ON CONFLICT (symbol) DO UPDATE SET
                            price = EXCLUDED.price,
                            bid = EXCLUDED.bid,
                            ask = EXCLUDED.ask,
                            spread = EXCLUDED.spread,
                            volume_24h = EXCLUDED.volume_24h,
                            change_24h = EXCLUDED.change_24h,
                            change_percent_24h = EXCLUDED.change_percent_24h,
                            high_24h = EXCLUDED.high_24h,
                            low_24h = EXCLUDED.low_24h,
                            timestamp = EXCLUDED.timestamp,
                            source = EXCLUDED.source
                        """
                        
                        conn.execute(text(query), price_data)
                        conn.commit()
                        
                        success_count += 1
                        logger.debug(f"Updated current price for {symbol}: ${price_data['price']:.4f}")
                else:
                    logger.warning(f"No valid ticker data for {symbol}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating current price for {symbol}: {e}")
                failed_count += 1
                
            # Rate limiting
            import time
            time.sleep(0.1)
        
        logger.info(f"Current prices update completed: {success_count} successful, {failed_count} failed")
        return {
            "success": success_count,
            "failed": failed_count,
            "message": "Current prices updated from Binance"
        }
        
    except Exception as e:
        error_msg = f"Error in current prices update: {str(e)}"
        logger.error(error_msg)
        return {
            "success": 0,
            "failed": 1,
            "error": error_msg
        }

@celery_app.task(bind=True)
def force_update_current_prices(self):
    """Force update current prices for all assets."""
    return update_current_prices.apply().get() 
 