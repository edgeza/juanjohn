#!/usr/bin/env python3
"""
VectorBTPro Local Analysis Engine

This engine uses VectorBTPro in a local conda environment to perform
polynomial regression analysis and generate output files for ingestion.

Key Features:
- Only uses polynomial regression (no other indicators)
- Local SQLite database for historical data
- VectorBTPro for backtesting and portfolio analysis
- Output files designed for ingestion into main system
- Follows exact pattern from CoinScanner system
"""

import os
import time
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import json
from typing import Dict, List, Optional, Tuple, Any
import optuna
import vectorbtpro as vbt
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("vectorbt_local_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VectorBTLocalEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results", db_path: str = "local_data.db"):
        """
        Initialize the VectorBTPro local analysis engine
        
        Args:
            binance_config: Binance API configuration
            output_dir: Directory to store results
            db_path: SQLite database path for local historical data
        """
        self.binance_config = binance_config
        self.client = Client(binance_config.get('api_key'), binance_config.get('api_secret'))
        self.output_dir = output_dir
        self.cache_dir = 'cache'
        self.db_path = db_path
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize local database
        self.init_local_database()
        
    def init_local_database(self):
        """Initialize local SQLite database for historical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create historical data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
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
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    analysis_date DATETIME NOT NULL,
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
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_interval ON historical_data(symbol, interval)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON historical_data(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_results(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date)")
            
            conn.commit()
            conn.close()
            logger.info(f"Local database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing local database: {e}")
            raise
    
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
    
    def fetch_and_store_historical_data(self, symbol: str, interval: str = '1d', days: int = 720) -> pd.DataFrame:
        """
        Fetch historical data from Binance and store in local database
        
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
            
            # Check cache first
            cache_file = os.path.join(self.cache_dir, f"{symbol}_{interval}_{days}d.pkl")
            if os.path.exists(cache_file):
                # Check if cache is recent (within 1 day)
                cache_time = os.path.getmtime(cache_file)
                if time.time() - cache_time < 86400:  # 24 hours
                    logger.info(f"Using cached data for {symbol}")
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            
            # Fetch from Binance
            logger.info(f"Fetching {days} days of {interval} data for {symbol}")
            klines = self.client.get_historical_klines(
                symbol, interval, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Set index
            df.set_index('timestamp', inplace=True)
            
            # Store in local database
            self.store_historical_data(symbol, interval, df)
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_historical_data(self, symbol: str, interval: str, df: pd.DataFrame):
        """Store historical data in local SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data for insertion
            data_to_insert = []
            for timestamp, row in df.iterrows():
                data_to_insert.append((
                    symbol,
                    interval,
                    timestamp,
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume']
                ))
            
            # Insert data (ignore duplicates)
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO historical_data 
                (symbol, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            conn.commit()
            conn.close()
            logger.info(f"Stored {len(data_to_insert)} records for {symbol} in local database")
            
        except Exception as e:
            logger.error(f"Error storing historical data for {symbol}: {e}")
    
    def get_historical_data_from_db(self, symbol: str, interval: str, days: int = 720) -> pd.DataFrame:
        """Get historical data from local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = ? AND interval = ? AND timestamp >= ?
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol, interval, start_date))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            conn.close()
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data from DB for {symbol}: {e}")
            return pd.DataFrame()
    
    def preprocess_data(self, data: pd.Series, window: int = 5) -> pd.Series:
        """
        Preprocess data for polynomial regression
        
        Args:
            data: Price series
            window: Rolling window for smoothing
        
        Returns:
            Preprocessed price series
        """
        # Remove duplicates
        data = data.drop_duplicates()
        
        # Remove NaN values
        data = data.dropna()
        
        # Apply rolling mean for smoothing
        if len(data) > window:
            data = data.rolling(window=window, center=True).mean()
            data = data.dropna()
        
        return data
    
    def calculate_and_trade_with_vectorbt(self, close_data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple:
        """
        Calculate polynomial regression and perform VectorBTPro backtesting
        
        Args:
            close_data: Close price series
            degree: Polynomial degree
            kstd: Standard deviation multiplier
        
        Returns:
            Tuple of (portfolio, indicators, entries, exits)
        """
        try:
            close_data = self.preprocess_data(close_data)
            
            if len(close_data) < degree + 1:
                logger.warning(f"Insufficient data for polynomial regression: {len(close_data)} points")
                return None, None, None, None
            
            X = np.arange(len(close_data))
            y = close_data.values
            
            # Fit polynomial
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coefficients = np.polyfit(X, y, degree)
            
            polynomial = np.poly1d(coefficients)
            regression_line = polynomial(X)
            std_dev = np.std(y - regression_line)
            
            # Calculate bands
            upper_band = regression_line + kstd * std_dev
            lower_band = regression_line - kstd * std_dev
            
            # Create indicators DataFrame
            indicators = pd.DataFrame({
                'Close': close_data,
                'regression_line': regression_line,
                'upper_band': upper_band,
                'lower_band': lower_band
            }, index=close_data.index)
            
            # Generate signals
            entries = indicators['Close'] < indicators['lower_band']
            exits = indicators['Close'] > indicators['upper_band']
            
            if entries.empty or exits.empty:
                return None, None, None, None
            
            # Create VectorBTPro portfolio
            pf = vbt.Portfolio.from_signals(
                close=indicators['Close'],
                entries=entries,
                exits=exits,
                init_cash=100_000,  # Start with $100,000
                fees=0.0015,  # 0.15% fee
                slippage=0.0005  # 0.05% slippage
            )
            
            return pf, indicators, entries, exits
            
        except Exception as e:
            logger.error(f"Error in VectorBTPro calculation: {e}")
            return None, None, None, None
    
    def generate_signal(self, indicators: pd.DataFrame) -> Tuple:
        """
        Generate trading signal based on current price position
        
        Args:
            indicators: DataFrame with regression bands
        
        Returns:
            Tuple of (signal, lower_band, upper_band, potential_return)
        """
        try:
            last_close = indicators['Close'].iloc[-1]
            last_lower_band = indicators['lower_band'].iloc[-1]
            last_upper_band = indicators['upper_band'].iloc[-1]
            
            # Determine signal
            if last_close < last_lower_band:
                signal = 'BUY'
            elif last_close > last_upper_band:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Calculate potential return
            if last_lower_band != 0:
                potential_return = ((last_upper_band - last_lower_band) / last_lower_band) * 100
            else:
                potential_return = None
            
            return signal, last_lower_band, last_upper_band, potential_return
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return 'HOLD', None, None, None
    
    def optimize_with_optuna(self, close_data: pd.Series, n_trials: int = 15) -> Tuple:
        """
        Optimize polynomial regression parameters using Optuna
        
        Args:
            close_data: Close price series
            n_trials: Number of optimization trials
        
        Returns:
            Tuple of (best_degree, best_kstd)
        """
        def objective(trial):
            try:
                degree = trial.suggest_int('degree', 2, 6)
                kstd = trial.suggest_float('kstd', 1.5, 3.0)
                
                pf, _, _, _ = self.calculate_and_trade_with_vectorbt(close_data, degree, kstd)
                
                if pf is None:
                    return float('inf')
                
                stats = pf.stats()
                return -stats['Total Return [%]']  # Minimize negative return
                
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                return float('inf')
        
        try:
            study = optuna.create_study(direction='minimize')
            study.optimize(objective, n_trials=n_trials)
            
            best_trial = study.best_trial
            return best_trial.params['degree'], best_trial.params['kstd']
            
        except Exception as e:
            logger.error(f"Error in Optuna optimization: {e}")
            return 4, 2.0  # Default values
    
    def analyze_asset(self, symbol: str, interval: str = '1d', days: int = 720, 
                     optimize: bool = True, degree: int = 4, kstd: float = 2.0) -> Dict:
        """
        Analyze a single asset using VectorBTPro and polynomial regression
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            days: Number of days to analyze
            optimize: Whether to optimize parameters
            degree: Polynomial degree (if not optimizing)
            kstd: Standard deviation multiplier (if not optimizing)
        
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing {symbol} with VectorBTPro...")
            
            # Get historical data
            df = self.fetch_and_store_historical_data(symbol, interval, days)
            if df.empty:
                return {'error': f'No data available for {symbol}'}
            
            close_data = df['close']
            
            # Optimize parameters if requested
            if optimize:
                logger.info(f"Optimizing parameters for {symbol}")
                degree, kstd = self.optimize_with_optuna(close_data, n_trials=50)
                logger.info(f"Best parameters for {symbol}: degree={degree}, kstd={kstd}")
            
            # Perform analysis
            pf, indicators, entries, exits = self.calculate_and_trade_with_vectorbt(close_data, degree, kstd)
            
            if pf is None:
                return {'error': f'Failed to create portfolio for {symbol}'}
            
            # Get portfolio statistics
            stats = pf.stats()
            
            # Generate signal
            signal, lower_band, upper_band, potential_return = self.generate_signal(indicators)
            
            # Store results in local database
            self.store_analysis_result(symbol, interval, df['close'].iloc[-1], lower_band, upper_band,
                                    signal, potential_return, stats['Total Return [%]'],
                                    stats['Sharpe Ratio'], stats['Max Drawdown [%]'], degree, kstd)
            
            return {
                'symbol': symbol,
                'interval': interval,
                'current_price': float(df['close'].iloc[-1]),
                'signal': signal,
                'lower_band': float(lower_band) if lower_band is not None else None,
                'upper_band': float(upper_band) if upper_band is not None else None,
                'potential_return': float(potential_return) if potential_return is not None else None,
                'total_return': float(stats['Total Return [%]']),
                'sharpe_ratio': float(stats['Sharpe Ratio']),
                'max_drawdown': float(stats['Max Drawdown [%]']),
                'degree': degree,
                'kstd': kstd,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': f'Analysis failed for {symbol}: {str(e)}'}
    
    def store_analysis_result(self, symbol: str, interval: str, current_price: float,
                            lower_band: float, upper_band: float, signal: str,
                            potential_return: float, total_return: float, sharpe_ratio: float,
                            max_drawdown: float, degree: int, kstd: float):
        """Store analysis result in local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO analysis_results 
                (symbol, interval, analysis_date, current_price, lower_band, upper_band,
                 signal, potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, interval, datetime.now(), current_price, lower_band, upper_band,
                  signal, potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis result for {symbol}: {e}")
    
    def analyze_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                          days: int = 720, optimize_major_coins: bool = True) -> List[Dict]:
        """
        Analyze all assets using VectorBTPro
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            days: Number of days to analyze
            optimize_major_coins: Whether to optimize parameters for major coins
        
        Returns:
            List of analysis results
        """
        try:
            if symbols is None:
                symbols = self.get_top_100_assets()
            
            logger.info(f"Starting VectorBTPro analysis of {len(symbols)} assets...")
            
            results = []
            major_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            
            # First, optimize parameters on major coins
            best_params = {}
            if optimize_major_coins:
                for coin in major_coins:
                    if coin in symbols:
                        logger.info(f"Optimizing parameters for major coin: {coin}")
                        df = self.fetch_and_store_historical_data(coin, interval, days)
                        if not df.empty:
                            close_data = df['close']
                            degree, kstd = self.optimize_with_optuna(close_data, n_trials=50)
                            best_params[coin] = {'degree': degree, 'kstd': kstd}
                            logger.info(f"Best parameters for {coin}: degree={degree}, kstd={kstd}")
            
            # Analyze all assets
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {}
                
                for symbol in symbols:
                    # Use optimized parameters for major coins, default for others
                    if symbol in best_params:
                        params = best_params[symbol]
                        future = executor.submit(self.analyze_asset, symbol, interval, days, 
                                              False, params['degree'], params['kstd'])
                    else:
                        # Use BTCUSDT parameters for other coins if available
                        if 'BTCUSDT' in best_params:
                            params = best_params['BTCUSDT']
                            future = executor.submit(self.analyze_asset, symbol, interval, days,
                                                  False, params['degree'], params['kstd'])
                        else:
                            future = executor.submit(self.analyze_asset, symbol, interval, days,
                                                  False, 4, 2.0)
                    
                    future_to_symbol[future] = symbol
                
                # Collect results
                for future in tqdm(as_completed(future_to_symbol), total=len(symbols), desc="Analyzing assets"):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if 'error' not in result:
                            results.append(result)
                        else:
                            logger.warning(f"Skipping {symbol}: {result['error']}")
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")
            
            logger.info(f"VectorBTPro analysis complete. {len(results)} assets analyzed successfully.")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return []
    
    def save_results_to_csv(self, results: List[Dict], filename: str = None) -> str:
        """
        Save analysis results to CSV file for ingestion
        
        Args:
            results: List of analysis results
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"vectorbt_analysis_results_{timestamp}.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Reorder columns to match expected format
            column_order = [
                'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
                'signal', 'potential_return', 'total_return', 'sharpe_ratio', 'max_drawdown',
                'degree', 'kstd', 'analysis_date'
            ]
            
            # Only include columns that exist
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def save_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """
        Save analysis results to JSON file for ingestion
        
        Args:
            results: List of analysis results
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"vectorbt_analysis_results_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            # Convert results for JSON serialization
            json_results = []
            for result in results:
                json_result = {}
                for key, value in result.items():
                    json_result[key] = convert_numpy(value)
                json_results.append(json_result)
            
            # Save to JSON
            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""

if __name__ == "__main__":
    # Example usage
    config = {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    engine = VectorBTLocalEngine(config)
    results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    engine.save_results_to_csv(results)
    engine.save_results_to_json(results) 
"""
VectorBTPro Local Analysis Engine

This engine uses VectorBTPro in a local conda environment to perform
polynomial regression analysis and generate output files for ingestion.

Key Features:
- Only uses polynomial regression (no other indicators)
- Local SQLite database for historical data
- VectorBTPro for backtesting and portfolio analysis
- Output files designed for ingestion into main system
- Follows exact pattern from CoinScanner system
"""

import os
import time
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import json
from typing import Dict, List, Optional, Tuple, Any
import optuna
import vectorbtpro as vbt
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("vectorbt_local_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VectorBTLocalEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results", db_path: str = "local_data.db"):
        """
        Initialize the VectorBTPro local analysis engine
        
        Args:
            binance_config: Binance API configuration
            output_dir: Directory to store results
            db_path: SQLite database path for local historical data
        """
        self.binance_config = binance_config
        self.client = Client(binance_config.get('api_key'), binance_config.get('api_secret'))
        self.output_dir = output_dir
        self.cache_dir = 'cache'
        self.db_path = db_path
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize local database
        self.init_local_database()
        
    def init_local_database(self):
        """Initialize local SQLite database for historical data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create historical data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
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
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    analysis_date DATETIME NOT NULL,
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
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_interval ON historical_data(symbol, interval)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON historical_data(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_results(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date)")
            
            conn.commit()
            conn.close()
            logger.info(f"Local database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing local database: {e}")
            raise
    
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
    
    def fetch_and_store_historical_data(self, symbol: str, interval: str = '1d', days: int = 720) -> pd.DataFrame:
        """
        Fetch historical data from Binance and store in local database
        
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
            
            # Check cache first
            cache_file = os.path.join(self.cache_dir, f"{symbol}_{interval}_{days}d.pkl")
            if os.path.exists(cache_file):
                # Check if cache is recent (within 1 day)
                cache_time = os.path.getmtime(cache_file)
                if time.time() - cache_time < 86400:  # 24 hours
                    logger.info(f"Using cached data for {symbol}")
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            
            # Fetch from Binance
            logger.info(f"Fetching {days} days of {interval} data for {symbol}")
            klines = self.client.get_historical_klines(
                symbol, interval, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Set index
            df.set_index('timestamp', inplace=True)
            
            # Store in local database
            self.store_historical_data(symbol, interval, df)
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_historical_data(self, symbol: str, interval: str, df: pd.DataFrame):
        """Store historical data in local SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data for insertion
            data_to_insert = []
            for timestamp, row in df.iterrows():
                data_to_insert.append((
                    symbol,
                    interval,
                    timestamp,
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume']
                ))
            
            # Insert data (ignore duplicates)
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO historical_data 
                (symbol, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            conn.commit()
            conn.close()
            logger.info(f"Stored {len(data_to_insert)} records for {symbol} in local database")
            
        except Exception as e:
            logger.error(f"Error storing historical data for {symbol}: {e}")
    
    def get_historical_data_from_db(self, symbol: str, interval: str, days: int = 720) -> pd.DataFrame:
        """Get historical data from local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = ? AND interval = ? AND timestamp >= ?
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol, interval, start_date))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            conn.close()
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data from DB for {symbol}: {e}")
            return pd.DataFrame()
    
    def preprocess_data(self, data: pd.Series, window: int = 5) -> pd.Series:
        """
        Preprocess data for polynomial regression
        
        Args:
            data: Price series
            window: Rolling window for smoothing
        
        Returns:
            Preprocessed price series
        """
        # Remove duplicates
        data = data.drop_duplicates()
        
        # Remove NaN values
        data = data.dropna()
        
        # Apply rolling mean for smoothing
        if len(data) > window:
            data = data.rolling(window=window, center=True).mean()
            data = data.dropna()
        
        return data
    
    def calculate_and_trade_with_vectorbt(self, close_data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple:
        """
        Calculate polynomial regression and perform VectorBTPro backtesting
        
        Args:
            close_data: Close price series
            degree: Polynomial degree
            kstd: Standard deviation multiplier
        
        Returns:
            Tuple of (portfolio, indicators, entries, exits)
        """
        try:
            close_data = self.preprocess_data(close_data)
            
            if len(close_data) < degree + 1:
                logger.warning(f"Insufficient data for polynomial regression: {len(close_data)} points")
                return None, None, None, None
            
            X = np.arange(len(close_data))
            y = close_data.values
            
            # Fit polynomial
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coefficients = np.polyfit(X, y, degree)
            
            polynomial = np.poly1d(coefficients)
            regression_line = polynomial(X)
            std_dev = np.std(y - regression_line)
            
            # Calculate bands
            upper_band = regression_line + kstd * std_dev
            lower_band = regression_line - kstd * std_dev
            
            # Create indicators DataFrame
            indicators = pd.DataFrame({
                'Close': close_data,
                'regression_line': regression_line,
                'upper_band': upper_band,
                'lower_band': lower_band
            }, index=close_data.index)
            
            # Generate signals
            entries = indicators['Close'] < indicators['lower_band']
            exits = indicators['Close'] > indicators['upper_band']
            
            if entries.empty or exits.empty:
                return None, None, None, None
            
            # Create VectorBTPro portfolio
            pf = vbt.Portfolio.from_signals(
                close=indicators['Close'],
                entries=entries,
                exits=exits,
                init_cash=100_000,  # Start with $100,000
                fees=0.0015,  # 0.15% fee
                slippage=0.0005  # 0.05% slippage
            )
            
            return pf, indicators, entries, exits
            
        except Exception as e:
            logger.error(f"Error in VectorBTPro calculation: {e}")
            return None, None, None, None
    
    def generate_signal(self, indicators: pd.DataFrame) -> Tuple:
        """
        Generate trading signal based on current price position
        
        Args:
            indicators: DataFrame with regression bands
        
        Returns:
            Tuple of (signal, lower_band, upper_band, potential_return)
        """
        try:
            last_close = indicators['Close'].iloc[-1]
            last_lower_band = indicators['lower_band'].iloc[-1]
            last_upper_band = indicators['upper_band'].iloc[-1]
            
            # Determine signal
            if last_close < last_lower_band:
                signal = 'BUY'
            elif last_close > last_upper_band:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Calculate potential return
            if last_lower_band != 0:
                potential_return = ((last_upper_band - last_lower_band) / last_lower_band) * 100
            else:
                potential_return = None
            
            return signal, last_lower_band, last_upper_band, potential_return
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return 'HOLD', None, None, None
    
    def optimize_with_optuna(self, close_data: pd.Series, n_trials: int = 15) -> Tuple:
        """
        Optimize polynomial regression parameters using Optuna
        
        Args:
            close_data: Close price series
            n_trials: Number of optimization trials
        
        Returns:
            Tuple of (best_degree, best_kstd)
        """
        def objective(trial):
            try:
                degree = trial.suggest_int('degree', 2, 6)
                kstd = trial.suggest_float('kstd', 1.5, 3.0)
                
                pf, _, _, _ = self.calculate_and_trade_with_vectorbt(close_data, degree, kstd)
                
                if pf is None:
                    return float('inf')
                
                stats = pf.stats()
                return -stats['Total Return [%]']  # Minimize negative return
                
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                return float('inf')
        
        try:
            study = optuna.create_study(direction='minimize')
            study.optimize(objective, n_trials=n_trials)
            
            best_trial = study.best_trial
            return best_trial.params['degree'], best_trial.params['kstd']
            
        except Exception as e:
            logger.error(f"Error in Optuna optimization: {e}")
            return 4, 2.0  # Default values
    
    def analyze_asset(self, symbol: str, interval: str = '1d', days: int = 720, 
                     optimize: bool = True, degree: int = 4, kstd: float = 2.0) -> Dict:
        """
        Analyze a single asset using VectorBTPro and polynomial regression
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            days: Number of days to analyze
            optimize: Whether to optimize parameters
            degree: Polynomial degree (if not optimizing)
            kstd: Standard deviation multiplier (if not optimizing)
        
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing {symbol} with VectorBTPro...")
            
            # Get historical data
            df = self.fetch_and_store_historical_data(symbol, interval, days)
            if df.empty:
                return {'error': f'No data available for {symbol}'}
            
            close_data = df['close']
            
            # Optimize parameters if requested
            if optimize:
                logger.info(f"Optimizing parameters for {symbol}")
                degree, kstd = self.optimize_with_optuna(close_data, n_trials=50)
                logger.info(f"Best parameters for {symbol}: degree={degree}, kstd={kstd}")
            
            # Perform analysis
            pf, indicators, entries, exits = self.calculate_and_trade_with_vectorbt(close_data, degree, kstd)
            
            if pf is None:
                return {'error': f'Failed to create portfolio for {symbol}'}
            
            # Get portfolio statistics
            stats = pf.stats()
            
            # Generate signal
            signal, lower_band, upper_band, potential_return = self.generate_signal(indicators)
            
            # Store results in local database
            self.store_analysis_result(symbol, interval, df['close'].iloc[-1], lower_band, upper_band,
                                    signal, potential_return, stats['Total Return [%]'],
                                    stats['Sharpe Ratio'], stats['Max Drawdown [%]'], degree, kstd)
            
            return {
                'symbol': symbol,
                'interval': interval,
                'current_price': float(df['close'].iloc[-1]),
                'signal': signal,
                'lower_band': float(lower_band) if lower_band is not None else None,
                'upper_band': float(upper_band) if upper_band is not None else None,
                'potential_return': float(potential_return) if potential_return is not None else None,
                'total_return': float(stats['Total Return [%]']),
                'sharpe_ratio': float(stats['Sharpe Ratio']),
                'max_drawdown': float(stats['Max Drawdown [%]']),
                'degree': degree,
                'kstd': kstd,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': f'Analysis failed for {symbol}: {str(e)}'}
    
    def store_analysis_result(self, symbol: str, interval: str, current_price: float,
                            lower_band: float, upper_band: float, signal: str,
                            potential_return: float, total_return: float, sharpe_ratio: float,
                            max_drawdown: float, degree: int, kstd: float):
        """Store analysis result in local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO analysis_results 
                (symbol, interval, analysis_date, current_price, lower_band, upper_band,
                 signal, potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, interval, datetime.now(), current_price, lower_band, upper_band,
                  signal, potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis result for {symbol}: {e}")
    
    def analyze_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                          days: int = 720, optimize_major_coins: bool = True) -> List[Dict]:
        """
        Analyze all assets using VectorBTPro
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            days: Number of days to analyze
            optimize_major_coins: Whether to optimize parameters for major coins
        
        Returns:
            List of analysis results
        """
        try:
            if symbols is None:
                symbols = self.get_top_100_assets()
            
            logger.info(f"Starting VectorBTPro analysis of {len(symbols)} assets...")
            
            results = []
            major_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            
            # First, optimize parameters on major coins
            best_params = {}
            if optimize_major_coins:
                for coin in major_coins:
                    if coin in symbols:
                        logger.info(f"Optimizing parameters for major coin: {coin}")
                        df = self.fetch_and_store_historical_data(coin, interval, days)
                        if not df.empty:
                            close_data = df['close']
                            degree, kstd = self.optimize_with_optuna(close_data, n_trials=50)
                            best_params[coin] = {'degree': degree, 'kstd': kstd}
                            logger.info(f"Best parameters for {coin}: degree={degree}, kstd={kstd}")
            
            # Analyze all assets
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {}
                
                for symbol in symbols:
                    # Use optimized parameters for major coins, default for others
                    if symbol in best_params:
                        params = best_params[symbol]
                        future = executor.submit(self.analyze_asset, symbol, interval, days, 
                                              False, params['degree'], params['kstd'])
                    else:
                        # Use BTCUSDT parameters for other coins if available
                        if 'BTCUSDT' in best_params:
                            params = best_params['BTCUSDT']
                            future = executor.submit(self.analyze_asset, symbol, interval, days,
                                                  False, params['degree'], params['kstd'])
                        else:
                            future = executor.submit(self.analyze_asset, symbol, interval, days,
                                                  False, 4, 2.0)
                    
                    future_to_symbol[future] = symbol
                
                # Collect results
                for future in tqdm(as_completed(future_to_symbol), total=len(symbols), desc="Analyzing assets"):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if 'error' not in result:
                            results.append(result)
                        else:
                            logger.warning(f"Skipping {symbol}: {result['error']}")
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")
            
            logger.info(f"VectorBTPro analysis complete. {len(results)} assets analyzed successfully.")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return []
    
    def save_results_to_csv(self, results: List[Dict], filename: str = None) -> str:
        """
        Save analysis results to CSV file for ingestion
        
        Args:
            results: List of analysis results
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"vectorbt_analysis_results_{timestamp}.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Reorder columns to match expected format
            column_order = [
                'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
                'signal', 'potential_return', 'total_return', 'sharpe_ratio', 'max_drawdown',
                'degree', 'kstd', 'analysis_date'
            ]
            
            # Only include columns that exist
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def save_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """
        Save analysis results to JSON file for ingestion
        
        Args:
            results: List of analysis results
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"vectorbt_analysis_results_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            # Convert results for JSON serialization
            json_results = []
            for result in results:
                json_result = {}
                for key, value in result.items():
                    json_result[key] = convert_numpy(value)
                json_results.append(json_result)
            
            # Save to JSON
            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""

if __name__ == "__main__":
    # Example usage
    config = {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    engine = VectorBTLocalEngine(config)
    results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    engine.save_results_to_csv(results)
    engine.save_results_to_json(results) 
 