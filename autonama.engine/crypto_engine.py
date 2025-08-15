#!/usr/bin/env python3
"""
Autonama Crypto Engine - Custom Backtesting Engine

This engine provides a complete in-house analysis and backtesting pipeline
tailored for the Autonama app, without external backtesting dependencies.

Key Features:
- Crypto-only analysis with top 100+ assets
- Polynomial regression bands with optimization (Optuna)
- Local SQLite database for historical data caching
- Real-time Binance data integration
- Comprehensive signal generation and custom portfolio backtesting
- Multiple timeframe analysis (1d, 15m)
- Results export for ingestion system
"""

# NumPy 2.0 compatibility layer - MUST BE FIRST
import numpy as np
try:
    # Handle NumPy 2.0 changes
    if not hasattr(np, 'float_'):
        np.float_ = np.float64
    if not hasattr(np, 'int_'):
        np.int_ = np.int64
    # Add RankWarning if missing
    if not hasattr(np, 'RankWarning'):
        import warnings
        np.RankWarning = RuntimeWarning
except:
    pass

import os
import time
import pickle
import logging
import warnings
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from typing import Dict, List, Optional, Tuple, Any
import optuna
from tqdm import tqdm
import os

# Optional acceleration for the backtest loop
try:
    from numba import njit  # type: ignore
    NUMBA_AVAILABLE = True
except Exception:
    NUMBA_AVAILABLE = False
    def njit(*args, **kwargs):  # type: ignore
        def _wrap(func):
            return func
        return _wrap

@njit(cache=True)
def _compute_equity_numba(close_arr, entries_exec, exits_exec, fees, slippage):
    init_cash = 100000.0
    cash = init_cash
    units = 0.0
    in_pos = False
    n = close_arr.shape[0]
    equity = np.empty(n, dtype=np.float64)
    for i in range(n):
        price = float(close_arr[i])
        if (not in_pos) and entries_exec[i]:
            buy_price = price * (1.0 + slippage + fees)
            if buy_price > 0.0:
                units = cash / buy_price
                cash = 0.0
                in_pos = True
        elif in_pos and exits_exec[i]:
            sell_price = price * (1.0 - slippage - fees)
            cash = units * sell_price
            units = 0.0
            in_pos = False
        if in_pos:
            equity[i] = cash + units * price
        else:
            equity[i] = cash
    if in_pos and n > 0:
        last_price = float(close_arr[-1])
        sell_price = last_price * (1.0 - slippage - fees)
        cash = units * sell_price
        equity[-1] = cash
    return equity
import os

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("crypto_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CryptoEngine:
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the Crypto Engine
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self.load_config(config_file)
        # Control whether to use numba-accelerated backtester
        # Default to False for maximum stability on Windows unless explicitly enabled
        self.numba_enabled = bool(
            self.config.get('backtest_settings', {}).get('numba_enabled', False)
        )
        self.client = Client(
            self.config['binance_api_key'], 
            self.config['binance_api_secret']
        )
        # Backtest settings (custom backtester only)
        bt_cfg = self.config.get('backtest_settings', {})
        self.bt_fees = float(bt_cfg.get('fees', 0.0015))
        self.bt_slippage = float(bt_cfg.get('slippage', 0.0005))
        self.bt_order_delay_bars = int(bt_cfg.get('order_delay_bars', 0))
        
        # Setup directories and database
        self.output_dir = self.config['default_settings']['output_directory']
        self.cache_dir = 'cache'
        self.db_path = 'crypto_data.db'
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Core crypto symbols (major coins + top 100)
        self.core_symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'AVAXUSDT',
            'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT',
            'XRPUSDT', 'BCHUSDT', 'ETCUSDT', 'FILUSDT', 'NEARUSDT', 'ALGOUSDT',
            'VETUSDT', 'ICPUSDT', 'FLOWUSDT', 'THETAUSDT', 'XLMUSDT', 'TRXUSDT'
        ]
        
        # Extended crypto symbols (from CoinScanner)
        self.extended_symbols = [
            '1INCHUSDT', 'AAVEUSDT', 'ACAUSDT', 'ACHUSDT', 'ADXUSDT', 'AEVOUSDT', 
            'AGLDUSDT', 'ALCXUSDT', 'ALICEUSDT', 'ALPHAUSDT', 'ALTUSDT', 'ANKRUSDT',
            'APEUSDT', 'API3USDT', 'APTUSDT', 'ARBUSDT', 'ARKMUSDT', 'ARPAUSDT',
            'ASTRUSDT', 'ATOMUSDT', 'AUCTIONUSDT', 'AUDIOUSDT', 'AXSUSDT', 'BADGERUSDT',
            'BALUSDT', 'BANDUSDT', 'BATUSDT', 'BCHUSDT', 'BICOUSDT', 'BLURUSDT',
            'BLZUSDT', 'BNTUSDT', 'BONDUSDT', 'BONKUSDT', 'C98USDT', 'CELRUSDT',
            'CHRUSDT', 'COMPUSDT', 'CRVUSDT', 'CVXUSDT', 'DASHUSDT', 'DOGEUSDT',
            'DYDXUSDT', 'EGLDUSDT', 'ENJUSDT', 'ENSUSDT', 'EOSUSDT', 'ETCUSDT',
            'FARMUSDT', 'FETUSDT', 'FILUSDT', 'FLOKIUSDT', 'FLOWUSDT', 'FTMUSDT',
            'FXSUSDT', 'GALAUSDT', 'GALUSDT', 'GMTUSDT', 'GMXUSDT', 'GRTUSDT',
            'HFTUSDT', 'ICPUSDT', 'IMXUSDT', 'INJUSDT', 'JUPUSDT', 'LDOUSDT',
            'LITUSDT', 'LPTUSDT', 'LRCUSDT', 'MANAUSDT', 'MASKUSDT', 'MATICUSDT',
            'MKRUSDT', 'NEARUSDT', 'NMRUSDT', 'OCEANUSDT', 'OPUSDT', 'PEPEUSDT',
            'PERPUSDT', 'POLUSDT', 'PONDUSDT', 'QNTUSDT', 'RADUSDT', 'RAREUSDT',
            'RAYUSDT', 'RENUSDT', 'RENDERUSDT', 'RLCUSDT', 'RNDRUSDT', 'ROOKUSDT',
            'RUNEUSDT', 'SANDUSDT', 'SHIBUSDT', 'SNXUSDT', 'SPELLUSDT', 'SRMUSDT',
            'STEPUSDT', 'STORJUSDT', 'STRKUSDT', 'STXUSDT', 'SUIUSDT', 'SUSHIUSDT',
            'SYNUSDT', 'UMAUSDT', 'UNIUSDT', 'WAVESUSDT', 'WBTCUSDT', 'WOOUSDT',
            'XLMUSDT', 'XMRUSDT', 'YFIUSDT', 'ZECUSDT', 'ZRXUSDT'
        ]
        
        # Combine all symbols and remove duplicates
        self.all_symbols = list(set(self.core_symbols + self.extended_symbols))
        
        logger.info(f"Crypto Engine initialized with {len(self.all_symbols)} symbols")
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            raise
    
    def init_database(self):
        """Initialize SQLite database for crypto data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create historical data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_historical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, timestamp)
                )
            """)
            
            # Create analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    current_price REAL,
                    lower_band REAL,
                    upper_band REAL,
                    signal TEXT,
                    potential_return REAL,
                    total_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    degree INTEGER,
                    kstd REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create optimization results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    best_degree INTEGER,
                    best_kstd REAL,
                    best_total_return REAL,
                    best_sharpe_ratio REAL,
                    optimization_trials INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_top_100_assets(self) -> List[str]:
        """Get top 100 crypto assets by volume from Binance"""
        try:
            # Get 24hr ticker for all symbols
            tickers = self.client.get_ticker()
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Get top 100 symbols
            top_100 = [pair['symbol'] for pair in sorted_pairs[:100]]
            
            logger.info(f"Retrieved top 100 assets by volume")
            return top_100
            
        except Exception as e:
            logger.error(f"Error getting top 100 assets: {e}")
            return self.all_symbols[:100]  # Fallback to predefined list
    
    def fetch_historical_data(self, symbol: str, interval: str = '1d', days: int = 1000) -> pd.DataFrame:
        """Fetch historical data from Binance with caching - maximum data available"""
        cache_dir = self.cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        def format_time_for_filename(dt):
            if dt:
                return dt.strftime("%Y-%m-%d_%H-%M-%S")
            else:
                return 'None'
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        start_str_fname = format_time_for_filename(start_time)
        end_str_fname = format_time_for_filename(end_time)
        
        cache_filename = os.path.join(
            cache_dir,
            f"cache_{symbol}_{interval}_{start_str_fname}_{end_str_fname}.pkl"
        )

        # Check cache first
        if os.path.exists(cache_filename):
            try:
                with open(cache_filename, 'rb') as f:
                    df = pickle.load(f)
                logger.debug(f"Loaded cached data for {symbol}")
                return df
            except Exception as e:
                logger.warning(f"Failed to load cache for {symbol}: {e}")
        
        # Fetch from Binance with maximum data
        retries = 3
        for attempt in range(retries):
            try:
                start_str = start_time.strftime("%d %b %Y %H:%M:%S")
                end_str = end_time.strftime("%d %b %Y %H:%M:%S")
                klines = self.client.get_historical_klines(symbol, interval, start_str, end_str)
                
                if not klines:
                    logger.warning(f"No data available for {symbol}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(klines, columns=[
                    "timestamp", "open", "high", "low", "close", "volume", "close_time",
                    "quote_asset_volume", "number_of_trades", "taker_buy_base",
                    "taker_buy_quote", "ignore"
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                
                # Cache the data
                try:
                    with open(cache_filename, 'wb') as f:
                        pickle.dump(df, f)
                except Exception as e:
                    logger.warning(f"Failed to cache data for {symbol}: {e}")
                
                logger.debug(f"Fetched {len(df)} records for {symbol} (max data available)")
                return df
                
            except (BinanceAPIException, BinanceRequestException) as e:
                logger.error(f"Binance API error for {symbol} - {interval}: {e}")
                if hasattr(e, 'code') and e.code == -1003:
                    logger.info("Rate limit exceeded. Sleeping for 60 seconds.")
                    time.sleep(60)
                else:
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error fetching data for {symbol} - {interval}: {e}")
                time.sleep(5)
        
        logger.error(f"Failed to fetch data for {symbol} after {retries} attempts")
        return pd.DataFrame()
    
    def store_historical_data(self, symbol: str, interval: str, df: pd.DataFrame):
        """Store historical data in local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data for insertion
            data_to_insert = []
            for timestamp, row in df.iterrows():
                # Convert timestamp to string for SQLite compatibility
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)
                data_to_insert.append((
                    symbol, interval, timestamp_str,
                    row['open'], row['high'], row['low'], row['close'], row['volume']
                ))
            
            # Insert data
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO crypto_historical_data 
                (symbol, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            conn.commit()
            conn.close()
            logger.debug(f"Stored {len(data_to_insert)} records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing historical data for {symbol}: {e}")
    
    def get_historical_data_from_db(self, symbol: str, interval: str, days: int = 720) -> pd.DataFrame:
        """Get historical data from local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM crypto_historical_data
                WHERE symbol = ? AND interval = ? AND timestamp >= ?
                ORDER BY timestamp
            """
            # Ensure we compare using the same string format as stored in DB
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.cursor()
            cursor.execute(query, (symbol, interval, start_time_str))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                logger.debug(f"No data found for {symbol} in database")
                return pd.DataFrame()
            # Build DataFrame manually to avoid numpy conversion quirks in pandas read_sql
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            # Normalize types
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df = df.set_index('timestamp')
            df = df.dropna()
            logger.debug(f"Retrieved {len(df)} records for {symbol} from database")
            return df
                
        except Exception as e:
            logger.error(f"Error retrieving data from database for {symbol}: {e}")
            return pd.DataFrame()
    
    def preprocess_data(self, data: pd.Series, window: int = 5) -> pd.Series:
        """Preprocess data by removing outliers and smoothing"""
        # Remove duplicates
        data = data[~data.index.duplicated(keep='first')]
        
        # Handle missing values
        data = data.ffill().bfill()
        
        # Remove outliers using Z-score
        mean = data.mean()
        std = data.std()
        z_scores = np.abs((data - mean) / std)
        data = data[z_scores < 3]
        
        # Fill missing values after outlier removal
        data = data.ffill().bfill()
        
        # Apply smoothing using a rolling average
        data = data.rolling(window=window, min_periods=1).mean()
        
        return data
    
    def calculate_polynomial_regression(self, close_data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple:
        """Calculate polynomial regression and trading signals using VectorBTPro"""
        close_data = self.preprocess_data(close_data)
        
        if len(close_data) < 50:
            logger.warning(f"Insufficient data for analysis: {len(close_data)} points")
            return None, None, None, None
        
        # Validate input data
        if close_data.isnull().any() or (close_data <= 0).any():
            logger.warning("Invalid data detected: null values or non-positive prices")
            return None, None, None, None
        
        # Use a simpler approach without normalization to avoid overflow issues
        X = np.arange(len(close_data))
        y = close_data.values
        
        # Ensure degree within 1-4 as specified
        degree = max(1, min(int(degree), 4))
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                warnings.simplefilter('ignore', UserWarning)
                coefficients = np.polyfit(X, y, degree)
        except Exception as e:
            logger.warning(f"Polyfit failed for degree {degree}: {e}")
            return None, None, None, None
        
        # Check for extreme coefficients that could cause overflow
        if np.any(np.abs(coefficients) > 1e6):
            logger.warning("Extreme polynomial coefficients detected, trying lower degree")
            try:
                coefficients = np.polyfit(X, y, min(degree, 2))
                if np.any(np.abs(coefficients) > 1e6):
                    logger.warning("Still extreme coefficients, skipping")
                    return None, None, None, None
            except Exception as e:
                logger.warning(f"Lower degree polyfit also failed: {e}")
                return None, None, None, None
        
        polynomial = np.poly1d(coefficients)
        regression_line = polynomial(X)
        
        # Validate regression line
        if np.any(regression_line <= 0) or np.any(regression_line > 1e8):
            logger.warning("Invalid regression line values")
            return None, None, None, None
        
        # Calculate residuals and standard deviation
        residuals = y - regression_line
        std_dev = np.std(residuals)
        
        # Validate standard deviation
        if std_dev == 0 or not np.isfinite(std_dev) or std_dev > np.mean(y) * 0.5:
            logger.warning("Invalid standard deviation calculated")
            return None, None, None, None
        
        # Calculate bands with more conservative approach
        upper_band = regression_line + kstd * std_dev
        lower_band = regression_line - kstd * std_dev
        
        # Validate bands to prevent extreme values
        current_price = close_data.iloc[-1]
        
        # More conservative bounds to prevent overflow
        max_multiplier = 1.5  # Maximum 150% of current price
        min_multiplier = 0.2  # Minimum 20% of current price
        
        # Ensure bands are within reasonable bounds
        upper_band = np.maximum(upper_band, current_price * min_multiplier)
        upper_band = np.minimum(upper_band, current_price * max_multiplier)
        
        lower_band = np.maximum(lower_band, current_price * min_multiplier)
        lower_band = np.minimum(lower_band, current_price * max_multiplier)
        
        # Ensure lower band is not higher than upper band
        lower_band = np.minimum(lower_band, upper_band * 0.95)
        
        # Final validation of bands
        if np.any(upper_band <= 0) or np.any(lower_band <= 0):
            logger.warning("Invalid band values (non-positive)")
            return None, None, None, None
        
        if np.any(upper_band < lower_band):
            logger.warning("Upper band is lower than lower band")
            return None, None, None, None
        
        # Check for extreme values that could cause overflow
        if np.any(upper_band > 1e6) or np.any(lower_band > 1e6):
            logger.warning("Extreme band values detected")
            return None, None, None, None
        
        indicators = pd.DataFrame({
            'Close': close_data,
            'regression_line': regression_line,
            'upper_band': upper_band,
            'lower_band': lower_band
        }, index=close_data.index)

        # Ensure clean boolean masks and contiguous arrays to avoid numpy flags overflow
        entries = np.ascontiguousarray(
            (indicators['Close'].values < indicators['lower_band'].values), dtype=np.bool_
        )
        exits = np.ascontiguousarray(
            (indicators['Close'].values > indicators['upper_band'].values), dtype=np.bool_
        )
        
        # entries/exits are numpy arrays; validate lengths instead of DataFrame emptiness
        if entries.size == 0 or exits.size == 0:
            return None, None, None, None
        
        # Additional validation before creating portfolio
        if np.any(indicators['Close'] <= 0):
            logger.warning("Non-positive close prices detected")
            return None, None, None, None
        
        if np.any(indicators['upper_band'] <= 0) or np.any(indicators['lower_band'] <= 0):
            logger.warning("Non-positive band values detected")
            return None, None, None, None
        
        # Additional validation for extreme values that could cause overflow
        if np.any(indicators['Close'] > 1e6) or np.any(indicators['upper_band'] > 1e6) or np.any(indicators['lower_band'] > 1e6):
            logger.warning("Extreme price values detected (> 1e6)")
            return None, None, None, None
        
        # Check for reasonable price ranges
        price_range = indicators['Close'].max() / indicators['Close'].min()
        if price_range > 100:  # If price varies by more than 100x, it's likely problematic
            logger.warning(f"Extreme price range detected: {price_range:.2f}")
            return None, None, None, None
        
        # Validate signal quality
        entry_count = entries.sum()
        exit_count = exits.sum()
        total_periods = len(entries)
        
        # More lenient signal validation
        if entry_count == 0 and exit_count == 0:
            logger.warning("No entry or exit signals generated")
            return None, None, None, None
        
        # Allow more signals if we have at least some of each type
        if entry_count > 0 and exit_count > 0:
            # If we have both types of signals, be more lenient
            if entry_count > total_periods * 0.8 or exit_count > total_periods * 0.8:
                logger.warning("Too many signals generated (> 80% of periods)")
                return None, None, None, None
        else:
            # If we only have one type of signal, be more restrictive
            if entry_count > total_periods * 0.6 or exit_count > total_periods * 0.6:
                logger.warning("Too many signals generated (> 60% of periods)")
                return None, None, None, None
        
        # Build portfolio using minimal custom backtester only
        # Use contiguous float64 close array to match contiguous boolean masks
        close_arr = np.ascontiguousarray(indicators['Close'].values, dtype=np.float64)
        # Optionally delay orders to avoid lookahead bias
        if self.bt_order_delay_bars > 0:
            entries_exec = np.roll(entries, self.bt_order_delay_bars)
            exits_exec = np.roll(exits, self.bt_order_delay_bars)
            entries_exec[: self.bt_order_delay_bars] = False
            exits_exec[: self.bt_order_delay_bars] = False
        else:
            entries_exec = entries
            exits_exec = exits
        # High-performance backtest engine using numba if explicitly enabled; otherwise safe Python fallback
        use_numba = bool(self.numba_enabled and NUMBA_AVAILABLE)
        if use_numba:
            try:
                equity = _compute_equity_numba(
                    close_arr,
                    entries_exec.astype(np.bool_),
                    exits_exec.astype(np.bool_),
                    float(self.bt_fees),
                    float(self.bt_slippage)
                )
            except Exception as e:
                logger.info(f"Numba backtester failed, falling back to Python implementation: {e}")
                use_numba = False

        if not use_numba:
            # Safe Python fallback
            init_cash = 100_000.0
            cash = init_cash
            units = 0.0
            in_pos = False
            equity = np.empty_like(close_arr, dtype=np.float64)
            for i in range(close_arr.shape[0]):
                price = float(close_arr[i])
                if not in_pos and entries_exec[i]:
                    buy_price = price * (1.0 + self.bt_slippage + self.bt_fees)
                    if buy_price > 0:
                        units = cash / buy_price
                        cash = 0.0
                        in_pos = True
                elif in_pos and exits_exec[i]:
                    sell_price = price * (1.0 - self.bt_slippage - self.bt_fees)
                    cash = units * sell_price
                    units = 0.0
                    in_pos = False
                equity[i] = cash + (units * price if in_pos else 0.0)
            if in_pos and close_arr.size > 0:
                last_price = float(close_arr[-1])
                sell_price = last_price * (1.0 - self.bt_slippage - self.bt_fees)
                cash = units * sell_price
                equity[-1] = cash

        eq = pd.Series(equity, index=indicators.index)
        total_return_pct = (eq.iloc[-1] / init_cash - 1.0) * 100.0 if len(eq) > 0 else 0.0
        rets = eq.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        r_mean = float(rets.mean())
        r_std = float(rets.std())
        sharpe = (r_mean / r_std * np.sqrt(252.0)) if r_std > 0 else 0.0
        dd = (eq / eq.cummax() - 1.0)
        max_dd = float(dd.min() * 100.0) if len(dd) > 0 else 0.0

        class CustomPortfolio:
            def stats(self_inner):
                return {
                    'Total Return [%]': total_return_pct,
                    'Sharpe Ratio': sharpe,
                    'Max Drawdown [%]': max_dd
                }

        pf = CustomPortfolio()
        
        return pf, indicators, entries, exits
    
    def generate_signal(self, indicators: pd.DataFrame) -> Tuple:
        """Generate trading signal based on current price position"""
        last_close = indicators['Close'].iloc[-1]
        last_lower_band = indicators['lower_band'].iloc[-1]
        last_upper_band = indicators['upper_band'].iloc[-1]
        
        if last_close < last_lower_band:
            signal = 'BUY'
        elif last_close > last_upper_band:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        # Fix potential return calculation to be more realistic
        if signal == 'BUY':
            # For BUY signals, calculate return from current price to upper band
            if last_lower_band > 0 and last_upper_band > last_close:
                potential_return = ((last_upper_band - last_close) / last_close) * 100
            else:
                potential_return = 0
        elif signal == 'SELL':
            # For SELL signals, calculate return from current price to lower band
            if last_upper_band > 0 and last_close > last_lower_band:
                potential_return = ((last_close - last_lower_band) / last_close) * 100
            else:
                potential_return = 0
        else:
            # For HOLD signals, calculate the smaller of the two potential moves
            if last_lower_band > 0 and last_upper_band > last_close:
                up_potential = ((last_upper_band - last_close) / last_close) * 100
                down_potential = ((last_close - last_lower_band) / last_close) * 100 if last_close > last_lower_band else 0
                potential_return = min(up_potential, down_potential) if down_potential > 0 else up_potential
            else:
                potential_return = 0
        
        # Ensure potential return is reasonable (not more than 1000%)
        if potential_return > 1000:
            potential_return = 1000
        elif potential_return < -1000:
            potential_return = -1000
        
        # Additional validation for NaN or infinite values
        if not np.isfinite(potential_return):
            potential_return = 0
        
        return signal, last_lower_band, last_upper_band, potential_return
    
    def optimize_parameters(self, close_data: pd.Series, n_trials: int = 100) -> Tuple:
        """Optimize polynomial regression parameters using Optuna"""
        def objective(trial):
            # User-specified broader search space
            degree = trial.suggest_int('degree', 1, 4, step=1)
            kstd = trial.suggest_float('kstd', 1.0, 3.0, step=0.1)
            # Lookback: 0 (full dataset) or 50..len(close_data)
            max_len = max(1, len(close_data))
            high_lb = max(50, max_len)
            lookback_choice = trial.suggest_int('lookback', 0, high_lb, step=10)
            
            try:
                # Apply lookback to data (0 means use full dataset)
                if lookback_choice == 0:
                    data_for_optimization = close_data
                    effective_lookback = len(close_data)
                else:
                    effective_lookback = min(lookback_choice, len(close_data))
                    data_for_optimization = close_data.tail(effective_lookback)
                
                # Validate data before optimization
                if len(data_for_optimization) < 50:
                    return float('inf')
                
                if data_for_optimization.isnull().any() or (data_for_optimization <= 0).any():
                    return float('inf')
                
                # Calculate regression with suggested parameters
                pf, indicators, entries, exits = self.calculate_polynomial_regression(data_for_optimization, degree, kstd)
                if pf is None or indicators is None:
                    return float('inf')
                
                # Get total return as objective
                stats = pf.stats()
                total_return = stats['Total Return [%]']
                
                # Check if return is finite
                if not np.isfinite(total_return):
                    return float('inf')
                
                # Additional validation to prevent extreme values
                if abs(total_return) > 1000:  # More than 1000% return is unrealistic per user cap
                    return float('inf')
                
                # Prefer positive returns but allow negative returns
                if total_return > 0:
                    return -total_return  # Negative because we want to maximize return
                else:
                    return abs(total_return)  # For negative returns, minimize the loss
                
            except Exception as e:
                logger.warning(f"Optimization trial failed: {e}")
                return float('inf')
        
        try:
            study = optuna.create_study(direction='minimize')
            study.optimize(objective, n_trials=n_trials)
            
            # Check if optimization found valid parameters
            if study.best_value == float('inf'):
                logger.warning("Optimization failed to find valid parameters, using defaults")
                return 1, 1.5, 150  # Conservative defaults
            
            best_params = study.best_params
            degree = best_params['degree']
            kstd = best_params['kstd']
            lookback = best_params.get('lookback', 0)
            
            logger.info(f"Best parameters: degree={degree}, kstd={kstd}, lookback={lookback}")
            return degree, kstd, lookback
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            # Return default parameters
            degree_range = self.config.get('analysis_settings', {}).get('degree_range', {'min': 1, 'max': 3, 'step': 1})
            std_range = self.config.get('analysis_settings', {}).get('std_range', {'min': 1.0, 'max': 3.0, 'step': 0.1})
            lookback_range = self.config.get('analysis_settings', {}).get('lookback_range', {'min': 50, 'max': 350, 'step': 10})
            
            return degree_range['min'], std_range['min'], lookback_range['min']
    
    def get_asset_parameters(self, symbol: str) -> Dict:
        """Get asset-specific parameters from config"""
        asset_settings = self.config.get('analysis_settings', {}).get('asset_specific_settings', {})
        
        if symbol in asset_settings:
            return asset_settings[symbol]
        else:
            # Return more conservative default parameters
            return {
                'degree': 1,  # Reduced from 2 to 1
                'std': 1.5,   # Reduced from 2.0 to 1.5
                'lookback': 100  # Reduced from 200 to 100
            }
    
    def analyze_asset(self, symbol: str, interval: str = '1d', days: int = 720, 
                     optimize: bool = True, degree: int = None, kstd: float = None, lookback: int = None) -> Dict:
        """Analyze a single crypto asset with configurable parameters"""
        try:
            logger.info(f"Analyzing {symbol} - {interval}")
            
            # Get asset-specific parameters
            asset_params = self.get_asset_parameters(symbol)
            if degree is None:
                degree = asset_params['degree']
            if kstd is None:
                kstd = asset_params['std']
            if lookback is None:
                lookback = asset_params['lookback']
            
            # Fetch data with lookback
            df = self.fetch_historical_data(symbol, interval, days)
            if df.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Store data in database
            self.store_historical_data(symbol, interval, df)
            
            # Apply lookback to close data
            close_data = df['close'].tail(lookback)
            
            # Optimize parameters if requested (default True)
            if optimize:
                logger.info(f"Optimizing parameters for {symbol}")
                try:
                    degree, kstd, optimized_lookback = self.optimize_parameters(close_data, n_trials=100)
                    # optimized_lookback==0 means use full dataset
                    if optimized_lookback == 0:
                        close_data = df['close']
                        lookback = len(close_data)
                        logger.info(f"Using full dataset ({lookback} candles) for {symbol} (optimized lookback=full)")
                    elif optimized_lookback != lookback:
                        lookback = optimized_lookback
                        close_data = df['close'].tail(lookback)
                        logger.info(f"Using last {lookback} candles for {symbol} (optimized lookback)")
                except Exception as e:
                    logger.warning(f"Optimization failed for {symbol}: {e}")
                    # fallback to asset params already set
            else:
                logger.info(f"Using provided/default parameters for {symbol}: degree={degree}, kstd={kstd}, lookback={lookback}")
            
            # Calculate regression and signals
            pf, indicators, entries, exits = self.calculate_polynomial_regression(close_data, degree, kstd)
            
            if pf is None:
                logger.warning(f"Failed to create portfolio for {symbol}")
                # Try with default parameters as fallback
                pf, indicators, entries, exits = self.calculate_polynomial_regression(close_data, 2, 2.0)
                if pf is None:
                    # Try with very conservative parameters as final fallback
                    logger.warning(f"Trying with very conservative parameters for {symbol}")
                    pf, indicators, entries, exits = self.calculate_polynomial_regression(close_data, 1, 1.0)
                    if pf is None:
                        logger.error(f"Failed to create portfolio for {symbol} even with conservative parameters")
                        return None
                    else:
                        degree, kstd = 1, 1.0  # Use very conservative parameters
                        logger.info(f"Using very conservative parameters for {symbol}: degree={degree}, kstd={kstd}")
                else:
                    degree, kstd = 2, 2.0  # Use default parameters
                    logger.info(f"Using default parameters for {symbol}: degree={degree}, kstd={kstd}")
            
            # Get portfolio statistics with error handling
            try:
                stats = pf.stats()
                
                # Validate portfolio stats
                if not np.isfinite(stats['Total Return [%]']):
                    logger.warning(f"Portfolio returned infinite values for {symbol}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error getting portfolio stats for {symbol}: {e}")
                return None
            
            # Generate signal
            signal, lower_band, upper_band, potential_return = self.generate_signal(indicators)
            
            # Get current price
            current_price = close_data.iloc[-1]
            
            # Store analysis result
            self.store_analysis_result(
                symbol, interval, current_price, lower_band, upper_band,
                signal, potential_return, stats['Total Return [%]'],
                stats['Sharpe Ratio'], stats['Max Drawdown [%]'], degree, kstd
            )
            
            result = {
                'symbol': symbol,
                'interval': interval,
                'current_price': current_price,
                'lower_band': lower_band,
                'upper_band': upper_band,
                'signal': signal,
                'potential_return': potential_return,
                'total_return': stats['Total Return [%]'],
                'sharpe_ratio': stats['Sharpe Ratio'],
                'max_drawdown': stats['Max Drawdown [%]'],
                'degree': degree,
                'kstd': kstd,
                'lookback': lookback,
                'analysis_date': datetime.now().isoformat()
            }
            
            logger.info(f"Analysis complete for {symbol}: {signal} signal, {potential_return:.2f}% potential")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def store_analysis_result(self, symbol: str, interval: str, current_price: float,
                            lower_band: float, upper_band: float, signal: str,
                            potential_return: float, total_return: float, sharpe_ratio: float,
                            max_drawdown: float, degree: int, kstd: float):
        """Store analysis result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO crypto_analysis_results
                (symbol, interval, current_price, lower_band, upper_band, signal,
                 potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, interval, current_price, lower_band, upper_band, signal,
                  potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis result for {symbol}: {e}")
    
    def analyze_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                          days: int = 720, optimize_all_assets: bool = True,
                          use_lookback: bool = True) -> List[Dict]:
        """Analyze all crypto assets with comprehensive data collection and optimization for all assets"""
        try:
            # Get top 100 assets if no symbols specified
            if symbols is None:
                symbols = self.get_top_100_assets()
                logger.info(f"Using top 100 assets by volume: {len(symbols)} symbols")
            
            logger.info(f"Starting analysis of {len(symbols)} crypto assets")
            logger.info(f"Interval: {interval}, Days: {days}, Optimize All Assets: {optimize_all_assets}, Use Lookback: {use_lookback}")
            
            results = []
            failed_symbols = []
            
            # Process all symbols with progress bar (Windows-safe rendering)
            is_windows = (os.name == 'nt')
            for symbol in tqdm(
                symbols,
                desc="Analyzing assets",
                ascii=is_windows,
                dynamic_ncols=True,
                mininterval=0.2,
                unit="asset"
            ):
                try:
                    logger.info(f"Analyzing {symbol} - {interval}")
                    
                    # Get asset-specific parameters
                    asset_params = self.get_asset_parameters(symbol)
                    degree = asset_params['degree']
                    kstd = asset_params['std']
                    lookback = asset_params['lookback']
                    
                    # Fetch maximum data available
                    df = self.fetch_historical_data(symbol, interval, days)
                    if df.empty:
                        logger.warning(f"No data available for {symbol}")
                        failed_symbols.append(symbol)
                        continue
                    
                    # Store data in database
                    self.store_historical_data(symbol, interval, df)
                    
                    # Apply lookback to close data
                    if use_lookback and lookback > 0:
                        # Use only the last X candles
                        close_data = df['close'].tail(lookback)
                        logger.info(f"Using last {lookback} candles for {symbol} (lookback mode)")
                    else:
                        # Use all available data from start
                        close_data = df['close']
                        logger.info(f"Using all {len(close_data)} candles for {symbol} (full data mode)")
                    
                    # Optimize parameters for ALL assets (not just major coins)
                    if optimize_all_assets:
                        logger.info(f"Optimizing parameters for {symbol}")
                        try:
                            degree, kstd, optimized_lookback = self.optimize_parameters(close_data, n_trials=100)
                            logger.info(f"Best parameters for {symbol}: degree={degree}, kstd={kstd}, lookback={optimized_lookback}")
                            # Use optimized lookback if it's different from the original
                            if optimized_lookback != lookback:
                                logger.info(f"Using optimized lookback: {optimized_lookback} instead of {lookback}")
                                lookback = optimized_lookback
                                # Re-apply lookback with optimized value
                                if use_lookback and lookback > 0:
                                    close_data = df['close'].tail(lookback)
                                    logger.info(f"Using last {lookback} candles for {symbol} (optimized lookback)")
                        except Exception as e:
                            logger.warning(f"Optimization failed for {symbol}: {e}")
                            # Use default parameters
                            degree = asset_params['degree']
                            kstd = asset_params['std']
                            lookback = asset_params['lookback']
                    
                    # Calculate regression and signals
                    pf, indicators, entries, exits = self.calculate_polynomial_regression(close_data, degree, kstd)
                    
                    if pf is None:
                        logger.warning(f"Failed to create portfolio for {symbol}")
                        # Try with default parameters as fallback
                        pf, indicators, entries, exits = self.calculate_polynomial_regression(close_data, 2, 2.0)
                        if pf is None:
                            logger.error(f"Failed to create portfolio for {symbol} even with default parameters")
                            failed_symbols.append(symbol)
                            continue
                        else:
                            degree, kstd = 2, 2.0  # Use default parameters
                            logger.info(f"Using default parameters for {symbol}: degree={degree}, kstd={kstd}")
                    
                    # Get portfolio statistics
                    stats = pf.stats()
                    
                    # Generate signal
                    signal, lower_band, upper_band, potential_return = self.generate_signal(indicators)
                    
                    # Get current price
                    current_price = close_data.iloc[-1]
                    
                    # Store analysis result
                    self.store_analysis_result(
                        symbol, interval, current_price, lower_band, upper_band,
                        signal, potential_return, stats['Total Return [%]'],
                        stats['Sharpe Ratio'], stats['Max Drawdown [%]'], degree, kstd
                    )
                    
                    result = {
                        'symbol': symbol,
                        'interval': interval,
                        'current_price': current_price,
                        'lower_band': lower_band,
                        'upper_band': upper_band,
                        'signal': signal,
                        'potential_return': potential_return,
                        'total_return': stats['Total Return [%]'],
                        'sharpe_ratio': stats['Sharpe Ratio'],
                        'max_drawdown': stats['Max Drawdown [%]'],
                        'degree': degree,
                        'kstd': kstd,
                        'lookback': lookback,
                        'use_lookback': use_lookback,
                        'data_points': len(close_data),
                        'total_available': len(df['close']),
                        'analysis_date': datetime.now().isoformat()
                    }
                    
                    results.append(result)
                    logger.info(f"Analysis complete for {symbol}: {signal} signal, {potential_return:.2f}% potential")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    failed_symbols.append(symbol)
                    continue
            
            logger.info(f"Analysis complete: {len(results)} successful, {len(failed_symbols)} failed")
            if failed_symbols:
                logger.warning(f"Failed symbols: {failed_symbols}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_all_assets: {e}")
            return []
    
    def save_results_to_csv(self, results: List[Dict], filename: str = None) -> str:
        """Save results to CSV file"""
        if not results:
            logger.warning("No results to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_analysis_results_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            df = pd.DataFrame(results)
            df.to_csv(filepath, index=False)
            logger.info(f"Results saved to CSV: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving CSV results: {e}")
            return ""
    
    def save_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """Save results to JSON file"""
        if not results:
            logger.warning("No results to save")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_analysis_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif hasattr(obj, 'item'):  # Handle numpy scalars
                    return obj.item()
                return obj
            
            # Convert results
            json_results = []
            for result in results:
                json_result = {}
                for key, value in result.items():
                    json_result[key] = convert_numpy(value)
                json_results.append(json_result)
            
            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            logger.info(f"Results saved to JSON: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving JSON results: {e}")
            return ""
    
    def get_analysis_summary(self, results: List[Dict]) -> Dict:
        """Get summary statistics from analysis results"""
        if not results:
            return {}
        
        buy_signals = [r for r in results if r.get('signal') == 'BUY']
        sell_signals = [r for r in results if r.get('signal') == 'SELL']
        hold_signals = [r for r in results if r.get('signal') == 'HOLD']
        
        avg_potential_return = sum([r.get('potential_return', 0) or 0 for r in results]) / len(results)
        avg_total_return = sum([r.get('total_return', 0) for r in results]) / len(results)
        
        summary = {
            'total_assets': len(results),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'hold_signals': len(hold_signals),
            'avg_potential_return': avg_potential_return,
            'avg_total_return': avg_total_return,
            'top_buy_signals': sorted(buy_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)[:5],
            'top_sell_signals': sorted(sell_signals, key=lambda x: x.get('potential_return', 0) or 0, reverse=True)[:5]
        }
        
        return summary
    
    def run_complete_analysis(self, symbols: List[str] = None, interval: str = '1d', 
                            days: int = 720, optimize_all_assets: bool = True,
                            output_format: str = 'both', update_data_first: bool = False) -> Dict:
        """Run complete crypto analysis"""
        start_time = datetime.now()
        
        logger.info("Starting Crypto Engine Analysis")
        logger.info(f"Symbols: {len(symbols) if symbols else 'all'}")
        logger.info(f"Interval: {interval}")
        logger.info(f"Days: {days}")
        logger.info(f"Optimize all assets: {optimize_all_assets}")
        logger.info(f"Update data first: {update_data_first}")
        
        # Ensure data is downloaded and stored before analysis if requested
        if update_data_first:
            try:
                self.update_all_data(symbols=symbols, interval=interval, days=days)
            except Exception as e:
                logger.warning(f"Pre-analysis data update encountered an issue: {e}")
        
        # Run analysis
        results = self.analyze_all_assets(symbols, interval, days, optimize_all_assets)
        
        # Save results
        csv_filepath = ""
        json_filepath = ""
        
        if output_format in ['csv', 'both']:
            csv_filepath = self.save_results_to_csv(results)
        
        if output_format in ['json', 'both']:
            json_filepath = self.save_results_to_json(results)
        
        # Get summary
        summary = self.get_analysis_summary(results)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        analysis_result = {
            'results': results,
            'summary': summary,
            'csv_filepath': csv_filepath,
            'json_filepath': json_filepath,
            'duration': str(duration),
            'analysis_date': end_time.isoformat()
        }
        
        # Log summary
        logger.info("="*60)
        logger.info("CRYPTO ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Total assets: {summary['total_assets']}")
        logger.info(f"BUY signals: {summary['buy_signals']}")
        logger.info(f"SELL signals: {summary['sell_signals']}")
        logger.info(f"HOLD signals: {summary['hold_signals']}")
        logger.info(f"Average potential return: {summary['avg_potential_return']:.2f}%")
        logger.info(f"Average total return: {summary['avg_total_return']:.2f}%")
        
        if csv_filepath:
            logger.info(f"CSV results: {csv_filepath}")
        if json_filepath:
            logger.info(f"JSON results: {json_filepath}")
        
        return analysis_result 

    def update_all_data(self, symbols: List[str] = None, interval: str = '1d', days: int = 1000) -> bool:
        """Update all data in the database efficiently - only fetch missing data"""
        try:
            logger.info("Starting efficient data update process...")
            
            # Get symbols to update
            if symbols is None:
                symbols = self.get_top_100_assets()
                logger.info(f"Updating data for {len(symbols)} top assets")
            
            updated_count = 0
            failed_symbols = []
            total_new_records = 0
            total_updated_records = 0
            
            # Update each symbol's data (Windows-safe tqdm)
            is_windows = (os.name == 'nt')
            for symbol in tqdm(
                symbols,
                desc="Updating data",
                ascii=is_windows,
                dynamic_ncols=True,
                mininterval=0.2,
                unit="symbol"
            ):
                try:
                    logger.info(f"Checking data for {symbol}")
                    
                    # Get existing data from database
                    existing_df = self.get_historical_data_from_db(symbol, interval, days=days)
                    
                    # Determine what data we need to fetch
                    if existing_df.empty:
                        # No existing data, fetch everything
                        logger.info(f"No existing data for {symbol}, fetching all {days} days")
                        df = self.fetch_historical_data(symbol, interval, days)
                        new_records = len(df) if not df.empty else 0
                        updated_records = 0
                    else:
                        # Check what's missing
                        latest_existing = existing_df.index.max()
                        current_time = datetime.now()
                        
                        # Calculate how many days we need to fetch
                        if isinstance(latest_existing, str):
                            latest_existing = datetime.strptime(latest_existing, '%Y-%m-%d %H:%M:%S')
                        
                        days_since_last = (current_time - latest_existing).days
                        
                        if days_since_last <= 0:
                            # Data is up to date (within same day)
                            logger.info(f"{symbol} data is up to date (last update: {latest_existing})")
                            updated_count += 1
                            continue
                        else:
                            # Need to fetch missing days
                            logger.info(f"{symbol} needs {days_since_last} days of updates (last: {latest_existing})")
                            df = self.fetch_historical_data(symbol, interval, days=days_since_last + 1)
                            new_records = len(df) if not df.empty else 0
                            updated_records = 0
                    
                    if df.empty:
                        logger.warning(f"No data available for {symbol}")
                        failed_symbols.append(symbol)
                        continue
                    
                    # Store in database (INSERT OR REPLACE handles duplicates)
                    self.store_historical_data(symbol, interval, df)
                    updated_count += 1
                    total_new_records += new_records
                    total_updated_records += updated_records
                    
                    logger.info(f"Updated {symbol}: {new_records} new records, {updated_records} updated records")
                    
                except Exception as e:
                    logger.error(f"Failed to update {symbol}: {e}")
                    failed_symbols.append(symbol)
                    continue
            
            logger.info(f"Data update complete: {updated_count} successful, {len(failed_symbols)} failed")
            logger.info(f"Total new records: {total_new_records}, Total updated records: {total_updated_records}")
            if failed_symbols:
                logger.warning(f"Failed symbols: {failed_symbols}")
            
            return len(failed_symbols) == 0
            
        except Exception as e:
            logger.error(f"Error in update_all_data: {e}")
            return False
    
    def get_data_status(self, symbols: List[str] = None, interval: str = '1d') -> Dict:
        """Get status of data for all symbols"""
        try:
            if symbols is None:
                symbols = self.get_top_100_assets()
            
            status = {
                'total_symbols': len(symbols),
                'symbols_with_data': 0,
                'symbols_up_to_date': 0,
                'symbols_needing_update': 0,
                'symbols_no_data': 0,
                'details': {}
            }
            
            current_time = datetime.now()
            
            for symbol in symbols:
                existing_df = self.get_historical_data_from_db(symbol, interval, days=1)
                
                if existing_df.empty:
                    status['symbols_no_data'] += 1
                    status['details'][symbol] = 'no_data'
                else:
                    status['symbols_with_data'] += 1
                    latest_existing = existing_df.index.max()
                    
                    if isinstance(latest_existing, str):
                        latest_existing = datetime.strptime(latest_existing, '%Y-%m-%d %H:%M:%S')
                    
                    days_since_last = (current_time - latest_existing).days
                    
                    if days_since_last <= 0:
                        status['symbols_up_to_date'] += 1
                        status['details'][symbol] = 'up_to_date'
                    else:
                        status['symbols_needing_update'] += 1
                        status['details'][symbol] = f'needs_update_{days_since_last}_days'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting data status: {e}")
            return {} 