"""
Binance Data Fetcher

Real-time data fetching from Binance API to update the database
"""

import requests
import json
import time
from datetime import datetime
from sqlalchemy import text
from src.core.database import get_db
from src.core.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

class BinanceDataFetcher:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Autonama/1.0'
        })
    
    def get_ticker_24hr(self, symbol=None):
        """Get 24hr ticker price change statistics"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            if symbol:
                url += f"?symbol={symbol}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if symbol:
                return data
            else:
                # Filter for USDT pairs only
                return [item for item in data if item['symbol'].endswith('USDT')]
                
        except Exception as e:
            logger.error(f"Error fetching Binance data: {e}")
            return []

    def get_daily_candles(self, symbol, limit=30):
        """Get daily OHLC candle data including current day"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': '1d',
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            candles = []
            
            for candle in data:
                candles.append({
                    'open_time': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'close_time': int(candle[6]),
                    'quote_volume': float(candle[7]),
                    'trades': int(candle[8]),
                    'taker_buy_base': float(candle[9]),
                    'taker_buy_quote': float(candle[10])
                })
            
            return candles
                
        except Exception as e:
            logger.error(f"Error fetching daily candles for {symbol}: {e}")
            return []

    def update_ohlc_database(self, db_session, symbol, candles):
        """Update the database with OHLC candle data"""
        try:
            # Convert Binance symbol format (BTCUSDT) to database format (BTC/USDT)
            if symbol.endswith('USDT'):
                db_symbol = f"{symbol[:-4]}/USDT"
            else:
                db_symbol = symbol

            updated_count = 0
            
            for candle in candles:
                # Convert timestamp to datetime
                open_time = datetime.fromtimestamp(candle['open_time'] / 1000)
                
                # Skip invalid data
                if (candle['open'] <= 0 or candle['high'] <= 0 or candle['low'] <= 0 or 
                    candle['close'] <= 0 or candle['volume'] <= 0):
                    logger.warning(f"Skipping invalid OHLC data for {db_symbol}: open={candle['open']}, high={candle['high']}, low={candle['low']}, close={candle['close']}")
                    continue
                
                # Insert or update OHLC data using the existing table structure
                query = text("""
                    INSERT INTO trading.ohlc_data_enhanced (symbol, timestamp, timeframe, open, high, low, close, volume, volume_quote, trades_count, source)
                    VALUES (:symbol, :timestamp, '1d', :open, :high, :low, :close, :volume, :volume_quote, :trades_count, 'binance')
                    ON CONFLICT (symbol, timestamp, timeframe) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        volume_quote = EXCLUDED.volume_quote,
                        trades_count = EXCLUDED.trades_count,
                        source = 'binance',
                        created_at = NOW()
                """)
                
                try:
                    db_session.execute(query, {
                        'symbol': db_symbol,
                        'timestamp': open_time,
                        'open': candle['open'],
                        'high': candle['high'],
                        'low': candle['low'],
                        'close': candle['close'],
                        'volume': candle['volume'],
                        'volume_quote': candle['quote_volume'],
                        'trades_count': candle['trades']
                    })
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating OHLC data for {db_symbol} at {open_time}: {e}")
                    # Rollback the transaction for this specific symbol and continue
                    db_session.rollback()
                    continue
            
            # Commit the transaction if we have updates
            if updated_count > 0:
                db_session.commit()
            
            logger.info(f"Updated {updated_count} OHLC candles for {db_symbol}")
            return updated_count
                
        except Exception as e:
            logger.error(f"Error updating OHLC database: {e}")
            db_session.rollback()
            return 0
    
    def update_database(self, db_session, ticker_data):
        """Update the database with fresh Binance data"""
        try:
            updated_count = 0
            
            for ticker in ticker_data:
                # Convert Binance symbol format (BTCUSDT) to database format (BTC/USDT)
                binance_symbol = ticker['symbol']
                if binance_symbol.endswith('USDT'):
                    symbol = f"{binance_symbol[:-4]}/USDT"
                else:
                    symbol = binance_symbol  # Keep as is for non-USDT pairs
                
                # Skip symbols that are too long for the database field (max 20 chars)
                if len(symbol) > 20:
                    logger.warning(f"Skipping {symbol} - symbol too long ({len(symbol)} chars)")
                    continue
                
                price = float(ticker['lastPrice'])
                change_24h = float(ticker['priceChange'])
                change_percent_24h = float(ticker['priceChangePercent'])
                volume_24h = float(ticker['quoteVolume'])  # Use quoteVolume (USDT) instead of volume (base asset)
                
                # Skip invalid data
                if price <= 0 or volume_24h < 0:
                    logger.warning(f"Skipping {symbol} due to invalid data: price={price}, volume={volume_24h}")
                    continue
                
                # Check if symbol exists in asset_metadata, if not add it
                check_query = text("SELECT COUNT(*) FROM trading.asset_metadata WHERE symbol = :symbol")
                result = db_session.execute(check_query, {'symbol': symbol})
                count = result.scalar()
                
                if count == 0:
                    # Add the symbol to asset_metadata
                    try:
                        insert_metadata_query = text("""
                            INSERT INTO trading.asset_metadata (symbol, name, asset_type, exchange, base_currency, quote_currency)
                            VALUES (:symbol, :name, 'crypto', 'binance', :base_currency, 'USDT')
                            ON CONFLICT (symbol) DO NOTHING
                        """)
                        
                        # Extract base currency from symbol (e.g., "BTC/USDT" -> "BTC")
                        base_currency = symbol.split('/')[0] if '/' in symbol else symbol
                        # Truncate base_currency to 10 characters to match database field
                        base_currency = base_currency[:10]
                        name = f"{base_currency} / USDT"
                        
                        db_session.execute(insert_metadata_query, {
                            'symbol': symbol,
                            'name': name,
                            'base_currency': base_currency
                        })
                        logger.info(f"Added new symbol to metadata: {symbol}")
                    except Exception as e:
                        logger.error(f"Error adding symbol {symbol} to metadata: {e}")
                        continue
                
                # Update or insert current price
                query = text("""
                    INSERT INTO trading.current_prices (symbol, price, change_24h, change_percent_24h, volume_24h, source, timestamp)
                    VALUES (:symbol, :price, :change_24h, :change_percent_24h, :volume_24h, 'binance', NOW())
                    ON CONFLICT (symbol) DO UPDATE SET
                        price = EXCLUDED.price,
                        change_24h = EXCLUDED.change_24h,
                        change_percent_24h = EXCLUDED.change_percent_24h,
                        volume_24h = EXCLUDED.volume_24h,
                        source = 'binance',
                        timestamp = NOW()
                """)
                
                try:
                    db_session.execute(query, {
                        'symbol': symbol,
                        'price': price,
                        'change_24h': change_24h,
                        'change_percent_24h': change_percent_24h,
                        'volume_24h': volume_24h
                    })
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {e}")
                    continue
            
            db_session.commit()
            logger.info(f"Updated {updated_count} assets in database")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating database: {e}")
            db_session.rollback()
            return 0

@celery_app.task(bind=True)
def fetch_binance_data(self):
    """Fetch fresh data from Binance API and update database"""
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 4, 'status': 'Starting Binance data fetch...'}
        )
        
        fetcher = BinanceDataFetcher()
        
        # Step 1: Fetch ticker data from Binance
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 4, 'status': 'Fetching ticker data from Binance...'}
        )
        
        ticker_data = fetcher.get_ticker_24hr()
        if not ticker_data:
            raise Exception("No ticker data received from Binance API")
        
        # Step 2: Update current prices database
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 4, 'status': 'Updating current prices...'}
        )
        
        db = next(get_db())
        updated_count = fetcher.update_database(db, ticker_data)
        
        # Step 3: Fetch and update OHLC data for top assets
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 4, 'status': 'Fetching daily OHLC candles...'}
        )
        
        # Get top 20 assets by volume for OHLC data
        top_symbols = []
        for ticker in ticker_data[:20]:  # Top 20 by volume
            symbol = ticker['symbol']
            if symbol.endswith('USDT'):
                top_symbols.append(symbol)
        
        ohlc_updated = 0
        for symbol in top_symbols:
            try:
                candles = fetcher.get_daily_candles(symbol, limit=30)  # Last 30 days including current
                if candles:
                    ohlc_count = fetcher.update_ohlc_database(db, symbol, candles)
                    ohlc_updated += ohlc_count
                    logger.info(f"Updated {ohlc_count} OHLC candles for {symbol}")
            except Exception as e:
                logger.error(f"Error updating OHLC for {symbol}: {e}")
                continue
        
        # Step 4: Complete
        self.update_state(
            state='PROGRESS',
            meta={'current': 4, 'total': 4, 'status': 'Data update completed...'}
        )
        
        return {
            "status": "completed",
            "message": f"Binance data updated successfully",
            "assets_updated": updated_count,
            "ohlc_candles_updated": ohlc_updated,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Binance data fetch failed: {e}")
        return {
            "status": "failed",
            "message": f"Binance data fetch failed: {str(e)}"
        }

@celery_app.task(bind=True)
def scheduled_crypto_update(self):
    """Scheduled task to update crypto data from Binance"""
    return fetch_binance_data.delay().id

@celery_app.task(bind=True)
def scheduled_stock_update(self):
    """Scheduled task to update stock data (placeholder for now)"""
    try:
        # For now, just return success - can be expanded for stock data
        return {
            "status": "completed",
            "message": "Stock data update completed (placeholder)",
            "assets_updated": 0
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Stock update failed: {str(e)}"
        }

@celery_app.task(bind=True)
def scheduled_forex_update(self):
    """Scheduled task to update forex data (placeholder for now)"""
    try:
        # For now, just return success - can be expanded for forex data
        return {
            "status": "completed",
            "message": "Forex data update completed (placeholder)",
            "assets_updated": 0
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Forex update failed: {str(e)}"
        }

@celery_app.task(bind=True)
def update_all_asset_types(self):
    """Update all asset types"""
    try:
        # Run crypto update (the main one we have)
        result = fetch_binance_data.delay()
        return {
            "status": "completed",
            "message": "All assets update initiated",
            "task_id": result.id
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"All assets update failed: {str(e)}"
        } 
 
 