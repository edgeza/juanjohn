import os
import time
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for Matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("backtest_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, db_config: Dict, binance_config: Dict):
        """
        Initialize the backtesting engine
        
        Args:
            db_config: PostgreSQL connection configuration
            binance_config: Binance API configuration
        """
        self.db_config = db_config
        self.binance_config = binance_config
        self.client = Client(binance_config.get('api_key'), binance_config.get('api_secret'))
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_top_100_assets(self) -> List[str]:
        """Get top 100 USDT pairs from Binance by volume"""
        try:
            tickers = self.client.get_ticker()
            usdt_pairs = []
            
            for ticker in tickers:
                if ticker['symbol'].endswith('USDT') and ticker['symbol'] != 'USDTUSDT':
                    volume_usd = float(ticker['quoteVolume'])
                    usdt_pairs.append({
                        'symbol': ticker['symbol'],
                        'volume': volume_usd,
                        'price': float(ticker['lastPrice'])
                    })
            
            # Sort by volume and return top 100
            usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
            return [pair['symbol'] for pair in usdt_pairs[:100]]
            
        except Exception as e:
            logger.error(f"Error fetching top 100 assets: {e}")
            # Return core movers as fallback
            return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
    
    def fetch_historical_data(self, symbol: str, interval: str = '1d', days: int = 720) -> pd.DataFrame:
        """
        Fetch historical data from Binance and store in PostgreSQL
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval ('1d' for daily)
            days: Number of days to fetch (max 720)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=min(days, 720))
            
            # Check if we have recent data in database
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT MAX(timestamp) as latest_timestamp 
                        FROM trading.ohlc_data 
                        WHERE symbol = %s AND interval = %s
                    """, (symbol, interval))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        latest_db_timestamp = result[0]
                        # If we have recent data (within 1 day), use it
                        if latest_db_timestamp > (datetime.now() - timedelta(days=1)):
                            logger.info(f"Using cached data for {symbol}")
                            cursor.execute("""
                                SELECT timestamp, open, high, low, close, volume
                                FROM trading.ohlc_data 
                                WHERE symbol = %s AND interval = %s
                                ORDER BY timestamp DESC
                                LIMIT %s
                            """, (symbol, interval, days))
                            
                            rows = cursor.fetchall()
                            if rows:
                                df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                                df['timestamp'] = pd.to_datetime(df['timestamp'])
                                df.set_index('timestamp', inplace=True)
                                df = df.sort_index()
                                return df.astype(float)
            
            # Fetch fresh data from Binance
            logger.info(f"Fetching fresh data for {symbol} from Binance")
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date.strftime('%Y-%m-%d %H:%M:%S'),
                end_str=end_date.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            if not klines:
                logger.warning(f"No data received for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                "timestamp", "open", "high", "low", "close", "volume", "close_time",
                "quote_asset_volume", "number_of_trades", "taker_buy_base",
                "taker_buy_quote", "ignore"
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            
            # Store in PostgreSQL
            self.store_data_in_db(symbol, interval, df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_data_in_db(self, symbol: str, interval: str, df: pd.DataFrame):
        """Store OHLCV data in PostgreSQL"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert data with conflict resolution
                    for timestamp, row in df.iterrows():
                        cursor.execute("""
                            INSERT INTO trading.ohlc_data 
                            (symbol, interval, timestamp, open, high, low, close, volume)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, interval, timestamp) 
                            DO UPDATE SET
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume
                        """, (
                            symbol, interval, timestamp, 
                            row['open'], row['high'], row['low'], 
                            row['close'], row['volume']
                        ))
                    conn.commit()
                    logger.info(f"Stored {len(df)} records for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error storing data for {symbol}: {e}")
    
    def preprocess_data(self, data: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Preprocess data for analysis"""
        # Remove duplicates
        data = data[~data.index.duplicated(keep='first')]
        # Forward fill and backward fill
        data = data.ffill().bfill()
        
        if len(data) < window:
            return data
        
        # Apply rolling mean for smoothing
        data = data.rolling(window=window, min_periods=1).mean()
        return data
    
    def calculate_polynomial_regression(self, data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate polynomial regression with bands
        
        Args:
            data: Price series
            degree: Polynomial degree
            kstd: Standard deviation multiplier for bands
        
        Returns:
            Tuple of (regression_line, upper_band, lower_band)
        """
        if len(data) < degree + 1:
            return None, None, None
        
        try:
            X = np.arange(len(data))
            y = data.values
            
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coefficients = np.polyfit(X, y, degree)
            
            polynomial = np.poly1d(coefficients)
            regression_line = polynomial(X)
            std_dev = np.std(y - regression_line)
            
            upper_band = regression_line + kstd * std_dev
            lower_band = regression_line - kstd * std_dev
            
            return regression_line, upper_band, lower_band
            
        except Exception as e:
            logger.error(f"Error in polynomial regression: {e}")
            return None, None, None
    
    def generate_signal(self, current_price: float, upper_band: float, lower_band: float) -> Tuple[str, float]:
        """
        Generate trading signal based on price position relative to bands
        
        Args:
            current_price: Current asset price
            upper_band: Upper regression band
            lower_band: Lower regression band
        
        Returns:
            Tuple of (signal, potential_return_percentage)
        """
        if upper_band is None or lower_band is None or lower_band <= 0:
            return 'HOLD', 0.0
        
        signal = 'HOLD'
        potential_return = 0.0
        
        if current_price < lower_band:
            signal = 'BUY'
            # Calculate potential return from lower to upper band
            potential_return = ((upper_band - lower_band) / lower_band) * 100
        elif current_price > upper_band:
            signal = 'SELL'
            # Calculate potential return from upper to lower band
            potential_return = ((upper_band - lower_band) / upper_band) * 100
        
        return signal, potential_return
    
    def scan_asset(self, symbol: str, interval: str = '1d', degree: int = 4, kstd: float = 2.0, days: int = 720) -> Dict:
        """
        Perform complete analysis for a single asset
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days to analyze
        
        Returns:
            Dictionary with analysis results
        """
        try:
            # Fetch historical data
            df = self.fetch_historical_data(symbol, interval, days)
            
            if df.empty or len(df) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return {
                    'symbol': symbol,
                    'interval': interval,
                    'signal': 'HOLD',
                    'current_price': 0.0,
                    'upper_band': None,
                    'lower_band': None,
                    'potential_return': 0.0,
                    'error': 'Insufficient data'
                }
            
            # Preprocess data
            close_data = self.preprocess_data(df['close'])
            
            # Calculate polynomial regression
            regression_line, upper_band, lower_band = self.calculate_polynomial_regression(
                close_data, degree, kstd
            )
            
            if regression_line is None:
                return {
                    'symbol': symbol,
                    'interval': interval,
                    'signal': 'HOLD',
                    'current_price': close_data.iloc[-1] if not close_data.empty else 0.0,
                    'upper_band': None,
                    'lower_band': None,
                    'potential_return': 0.0,
                    'error': 'Regression calculation failed'
                }
            
            # Get current price
            current_price = close_data.iloc[-1]
            
            # Generate signal
            signal, potential_return = self.generate_signal(
                current_price, upper_band[-1], lower_band[-1]
            )
            
            return {
                'symbol': symbol,
                'interval': interval,
                'signal': signal,
                'current_price': current_price,
                'upper_band': upper_band[-1],
                'lower_band': lower_band[-1],
                'potential_return': potential_return,
                'regression_line': regression_line,
                'upper_band_series': upper_band,
                'lower_band_series': lower_band,
                'price_series': close_data,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return {
                'symbol': symbol,
                'interval': interval,
                'signal': 'HOLD',
                'current_price': 0.0,
                'upper_band': None,
                'lower_band': None,
                'potential_return': 0.0,
                'error': str(e)
            }
    
    def scan_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                       degree: int = 4, kstd: float = 2.0, days: int = 720) -> List[Dict]:
        """
        Scan all assets in parallel
        
        Args:
            symbols: List of symbols to scan (if None, uses top 100)
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days to analyze
        
        Returns:
            List of analysis results
        """
        if symbols is None:
            symbols = self.get_top_100_assets()
        
        results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for symbol in symbols:
                future = executor.submit(
                    self.scan_asset, symbol, interval, degree, kstd, days
                )
                futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    result = future.result(timeout=60)  # 60 second timeout
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error in parallel scan: {e}")
        
        return results
    
    def store_alerts(self, results: List[Dict]):
        """Store alerts in PostgreSQL"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for result in results:
                        cursor.execute("""
                            INSERT INTO trading.alerts 
                            (symbol, interval, signal, current_price, upper_band, lower_band, 
                             potential_return, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, interval, created_at::date) 
                            DO UPDATE SET
                                signal = EXCLUDED.signal,
                                current_price = EXCLUDED.current_price,
                                upper_band = EXCLUDED.upper_band,
                                lower_band = EXCLUDED.lower_band,
                                potential_return = EXCLUDED.potential_return,
                                updated_at = NOW()
                        """, (
                            result['symbol'],
                            result['interval'],
                            result['signal'],
                            result['current_price'],
                            result['upper_band'],
                            result['lower_band'],
                            result['potential_return'],
                            result['timestamp']
                        ))
                    conn.commit()
                    logger.info(f"Stored {len(results)} alerts")
                    
        except Exception as e:
            logger.error(f"Error storing alerts: {e}")
    
    def get_alerts(self, signal_type: str = None, min_potential_return: float = 0.0) -> List[Dict]:
        """Get alerts from database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM trading.alerts 
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                    """
                    params = []
                    
                    if signal_type:
                        query += " AND signal = %s"
                        params.append(signal_type)
                    
                    if min_potential_return > 0:
                        query += " AND potential_return >= %s"
                        params.append(min_potential_return)
                    
                    query += " ORDER BY potential_return DESC, created_at DESC"
                    
                    cursor.execute(query, params)
                    return cursor.fetchall()
                    
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def run_daily_scan(self):
        """Run daily scan and store results"""
        logger.info("Starting daily scan...")
        
        # Get top 100 assets
        symbols = self.get_top_100_assets()
        logger.info(f"Scanning {len(symbols)} assets")
        
        # Scan all assets
        results = self.scan_all_assets(symbols, interval='1d', days=720)
        
        # Store alerts
        self.store_alerts(results)
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        logger.info(f"Scan complete: {len(buy_signals)} BUY signals, {len(sell_signals)} SELL signals")
        
        return results

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

BINANCE_CONFIG = {
    'api_key': 'your_api_key_here',
    'api_secret': 'your_api_secret_here'
}

if __name__ == "__main__":
    # Initialize engine
    engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
    
    # Run daily scan
    results = engine.run_daily_scan()
    
    # Print summary
    print(f"\nScan Results:")
    print(f"Total assets scanned: {len(results)}")
    print(f"BUY signals: {len([r for r in results if r['signal'] == 'BUY'])}")
    print(f"SELL signals: {len([r for r in results if r['signal'] == 'SELL'])}")
    print(f"HOLD signals: {len([r for r in results if r['signal'] == 'HOLD'])}")
    
    # Show top BUY signals
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    print(f"\nTop BUY signals:")
    for signal in buy_signals[:10]:
        print(f"{signal['symbol']}: {signal['potential_return']:.2f}% potential return") 
 
 