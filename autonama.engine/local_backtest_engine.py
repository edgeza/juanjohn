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
        logging.FileHandler("local_backtest_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LocalBacktestEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results"):
        """
        Initialize the local backtesting engine
        
        Args:
            binance_config: Binance API configuration
            output_dir: Directory to store results
        """
        self.binance_config = binance_config
        self.client = Client(binance_config.get('api_key'), binance_config.get('api_secret'))
        self.output_dir = output_dir
        self.cache_dir = 'cache'
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
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
        Fetch historical data from Binance
        
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
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
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
                'regression_line': regression_line.tolist(),
                'upper_band_series': upper_band.tolist(),
                'lower_band_series': lower_band.tolist(),
                'price_series': close_data.tolist(),
                'timestamp': datetime.now().isoformat()
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
    
    def save_results(self, results: List[Dict], filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None
    
    def run_daily_scan(self, save_results: bool = True) -> Tuple[List[Dict], str]:
        """Run daily scan and optionally save results"""
        logger.info("Starting daily scan...")
        
        # Get top 100 assets
        symbols = self.get_top_100_assets()
        logger.info(f"Scanning {len(symbols)} assets")
        
        # Scan all assets
        results = self.scan_all_assets(symbols, interval='1d', days=720)
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        logger.info(f"Scan complete: {len(buy_signals)} BUY signals, {len(sell_signals)} SELL signals")
        
        # Save results if requested
        filepath = None
        if save_results:
            filepath = self.save_results(results)
        
        return results, filepath

# Configuration
BINANCE_CONFIG = {
    'api_key': 'your_api_key_here',  # Replace with your actual API key
    'api_secret': 'your_api_secret_here'  # Replace with your actual API secret
}

if __name__ == "__main__":
    # Initialize engine
    engine = LocalBacktestEngine(BINANCE_CONFIG)
    
    # Run daily scan
    results, filepath = engine.run_daily_scan()
    
    # Print summary
    print(f"\nScan Results:")
    print(f"Total assets scanned: {len(results)}")
    print(f"BUY signals: {len([r for r in results if r['signal'] == 'BUY'])}")
    print(f"SELL signals: {len([r for r in results if r['signal'] == 'SELL'])}")
    print(f"HOLD signals: {len([r for r in results if r['signal'] == 'HOLD'])}")
    
    if filepath:
        print(f"Results saved to: {filepath}")
    
    # Show top BUY signals
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    print(f"\nTop BUY signals:")
    for signal in buy_signals[:10]:
        print(f"{signal['symbol']}: {signal['potential_return']:.2f}% potential return") 
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
        logging.FileHandler("local_backtest_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LocalBacktestEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results"):
        """
        Initialize the local backtesting engine
        
        Args:
            binance_config: Binance API configuration
            output_dir: Directory to store results
        """
        self.binance_config = binance_config
        self.client = Client(binance_config.get('api_key'), binance_config.get('api_secret'))
        self.output_dir = output_dir
        self.cache_dir = 'cache'
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
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
        Fetch historical data from Binance
        
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
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
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
                'regression_line': regression_line.tolist(),
                'upper_band_series': upper_band.tolist(),
                'lower_band_series': lower_band.tolist(),
                'price_series': close_data.tolist(),
                'timestamp': datetime.now().isoformat()
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
    
    def save_results(self, results: List[Dict], filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None
    
    def run_daily_scan(self, save_results: bool = True) -> Tuple[List[Dict], str]:
        """Run daily scan and optionally save results"""
        logger.info("Starting daily scan...")
        
        # Get top 100 assets
        symbols = self.get_top_100_assets()
        logger.info(f"Scanning {len(symbols)} assets")
        
        # Scan all assets
        results = self.scan_all_assets(symbols, interval='1d', days=720)
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        logger.info(f"Scan complete: {len(buy_signals)} BUY signals, {len(sell_signals)} SELL signals")
        
        # Save results if requested
        filepath = None
        if save_results:
            filepath = self.save_results(results)
        
        return results, filepath

# Configuration
BINANCE_CONFIG = {
    'api_key': 'your_api_key_here',  # Replace with your actual API key
    'api_secret': 'your_api_secret_here'  # Replace with your actual API secret
}

if __name__ == "__main__":
    # Initialize engine
    engine = LocalBacktestEngine(BINANCE_CONFIG)
    
    # Run daily scan
    results, filepath = engine.run_daily_scan()
    
    # Print summary
    print(f"\nScan Results:")
    print(f"Total assets scanned: {len(results)}")
    print(f"BUY signals: {len([r for r in results if r['signal'] == 'BUY'])}")
    print(f"SELL signals: {len([r for r in results if r['signal'] == 'SELL'])}")
    print(f"HOLD signals: {len([r for r in results if r['signal'] == 'HOLD'])}")
    
    if filepath:
        print(f"Results saved to: {filepath}")
    
    # Show top BUY signals
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
    
    print(f"\nTop BUY signals:")
    for signal in buy_signals[:10]:
        print(f"{signal['symbol']}: {signal['potential_return']:.2f}% potential return") 
 