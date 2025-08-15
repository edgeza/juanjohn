#!/usr/bin/env python3
"""
Enhanced Local Backtesting & Analytics Engine

This is the main local engine that performs comprehensive analysis including:
- Polynomial regression analysis
- Cross-correlation analysis
- Technical indicators
- Signal generation
- Risk assessment
- Portfolio optimization insights

All processing is done locally to avoid cloud costs.
"""

import os
import time
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import json
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
from scipy import stats
from scipy.signal import savgol_filter
import talib
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("enhanced_local_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedLocalEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results"):
        """
        Initialize the enhanced local analytics engine
        
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
        os.makedirs(os.path.join(self.output_dir, 'charts'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'correlations'), exist_ok=True)
        
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
        Fetch historical data from Binance with caching
        
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
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added technical indicators
        """
        try:
            # Moving averages
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['sma_200'] = talib.SMA(df['close'], timeperiod=200)
            df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
                df['close'], fastperiod=12, slowperiod=26, signalperiod=9
            )
            
            # RSI
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
                df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
            )
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(
                df['high'], df['low'], df['close'], 
                fastk_period=14, slowk_period=3, slowd_period=3
            )
            
            # ATR (Average True Range)
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Volume indicators
            df['obv'] = talib.OBV(df['close'], df['volume'])
            df['ad'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
            
            # Momentum indicators
            df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
            df['williams_r'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Trend indicators
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Price patterns
            df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def calculate_polynomial_regression(self, data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate polynomial regression with confidence bands
        
        Args:
            data: Price series
            degree: Polynomial degree
            kstd: Standard deviation multiplier for bands
        
        Returns:
            Tuple of (x_values, regression_line, upper_band, lower_band)
        """
        try:
            # Remove NaN values
            clean_data = data.dropna()
            if len(clean_data) < degree + 1:
                return np.array([]), np.array([]), np.array([]), np.array([])
            
            # Create x values (time index)
            x = np.arange(len(clean_data))
            y = clean_data.values
            
            # Fit polynomial
            coeffs = np.polyfit(x, y, degree)
            poly = np.poly1d(coeffs)
            
            # Calculate regression line
            regression_line = poly(x)
            
            # Calculate residuals and standard deviation
            residuals = y - regression_line
            std_residuals = np.std(residuals)
            
            # Calculate confidence bands
            upper_band = regression_line + (kstd * std_residuals)
            lower_band = regression_line - (kstd * std_residuals)
            
            return x, regression_line, upper_band, lower_band
            
        except Exception as e:
            logger.error(f"Error in polynomial regression: {e}")
            return np.array([]), np.array([]), np.array([]), np.array([])
    
    def calculate_cross_correlation(self, symbols: List[str], interval: str = '1d', days: int = 720) -> Dict:
        """
        Calculate cross-correlation between assets
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            days: Number of days
        
        Returns:
            Dictionary with correlation matrix and analysis
        """
        try:
            # Fetch data for all symbols
            price_data = {}
            for symbol in symbols:
                df = self.fetch_historical_data(symbol, interval, days)
                if not df.empty:
                    price_data[symbol] = df['close']
            
            # Create price matrix
            price_df = pd.DataFrame(price_data)
            price_df = price_df.dropna()
            
            # Calculate correlation matrix
            correlation_matrix = price_df.corr()
            
            # Calculate rolling correlations (30-day window)
            rolling_corr = price_df.rolling(window=30).corr()
            
            # Find highly correlated pairs
            high_corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_corr_pairs.append({
                            'pair': (correlation_matrix.columns[i], correlation_matrix.columns[j]),
                            'correlation': corr_value
                        })
            
            # Sort by absolute correlation
            high_corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            return {
                'correlation_matrix': correlation_matrix,
                'rolling_correlation': rolling_corr,
                'high_correlation_pairs': high_corr_pairs,
                'symbols': symbols,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating cross-correlation: {e}")
            return {}
    
    def generate_signal(self, current_price: float, upper_band: float, lower_band: float, 
                       rsi: float = None, macd: float = None, volume_ratio: float = None) -> Dict:
        """
        Generate comprehensive trading signal
        
        Args:
            current_price: Current asset price
            upper_band: Upper polynomial regression band
            lower_band: Lower polynomial regression band
            rsi: RSI value
            macd: MACD value
            volume_ratio: Volume ratio
        
        Returns:
            Dictionary with signal analysis
        """
        try:
            # Calculate potential return
            band_width = upper_band - lower_band
            if band_width > 0:
                potential_return = (band_width / current_price) * 100
            else:
                potential_return = 0
            
            # Determine signal based on price position relative to bands
            if current_price > upper_band:
                signal = 'SELL'
                signal_strength = min((current_price - upper_band) / band_width * 100, 100) if band_width > 0 else 50
            elif current_price < lower_band:
                signal = 'BUY'
                signal_strength = min((lower_band - current_price) / band_width * 100, 100) if band_width > 0 else 50
            else:
                signal = 'HOLD'
                signal_strength = 50
            
            # Additional signal confirmation
            confirmations = []
            if rsi is not None:
                if signal == 'BUY' and rsi < 30:
                    confirmations.append('RSI oversold')
                elif signal == 'SELL' and rsi > 70:
                    confirmations.append('RSI overbought')
            
            if macd is not None:
                if signal == 'BUY' and macd > 0:
                    confirmations.append('MACD positive')
                elif signal == 'SELL' and macd < 0:
                    confirmations.append('MACD negative')
            
            if volume_ratio is not None and volume_ratio > 1.5:
                confirmations.append('High volume')
            
            # Risk assessment
            risk_level = 'LOW'
            if abs(potential_return) > 20:
                risk_level = 'HIGH'
            elif abs(potential_return) > 10:
                risk_level = 'MEDIUM'
            
            return {
                'signal': signal,
                'signal_strength': signal_strength,
                'potential_return': potential_return,
                'confirmations': confirmations,
                'risk_level': risk_level,
                'current_price': current_price,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'band_width': band_width
            }
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {
                'signal': 'HOLD',
                'signal_strength': 0,
                'potential_return': 0,
                'confirmations': [],
                'risk_level': 'UNKNOWN',
                'current_price': current_price,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'band_width': 0
            }
    
    def analyze_asset(self, symbol: str, interval: str = '1d', degree: int = 4, 
                     kstd: float = 2.0, days: int = 720) -> Dict:
        """
        Comprehensive asset analysis
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days to analyze
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            logger.info(f"Analyzing {symbol}...")
            
            # Fetch historical data
            df = self.fetch_historical_data(symbol, interval, days)
            if df.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)
            
            # Get current values
            current_price = float(df['close'].iloc[-1])
            current_rsi = float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else None
            current_macd = float(df['macd'].iloc[-1]) if not pd.isna(df['macd'].iloc[-1]) else None
            
            # Calculate volume ratio (current volume vs 20-day average)
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume'].rolling(20).mean().iloc[-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Polynomial regression analysis
            x, regression_line, upper_band, lower_band = self.calculate_polynomial_regression(
                df['close'], degree, kstd
            )
            
            if len(x) == 0:
                return {'error': f'Insufficient data for polynomial regression on {symbol}'}
            
            # Get current band values
            current_upper_band = float(upper_band[-1])
            current_lower_band = float(lower_band[-1])
            
            # Generate signal
            signal_analysis = self.generate_signal(
                current_price, current_upper_band, current_lower_band,
                current_rsi, current_macd, volume_ratio
            )
            
            # Calculate additional metrics
            price_change_24h = ((current_price - float(df['close'].iloc[-2])) / float(df['close'].iloc[-2])) * 100
            volatility = float(df['close'].pct_change().std() * 100)
            
            # Trend analysis
            sma_20 = float(df['sma_20'].iloc[-1]) if not pd.isna(df['sma_20'].iloc[-1]) else current_price
            sma_50 = float(df['sma_50'].iloc[-1]) if not pd.isna(df['sma_50'].iloc[-1]) else current_price
            trend = 'BULLISH' if sma_20 > sma_50 else 'BEARISH'
            
            # Support and resistance levels
            recent_high = float(df['high'].tail(20).max())
            recent_low = float(df['low'].tail(20).min())
            
            return {
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'current_price': current_price,
                'price_change_24h': price_change_24h,
                'volatility': volatility,
                'trend': trend,
                'support_level': recent_low,
                'resistance_level': recent_high,
                'volume_ratio': volume_ratio,
                'technical_indicators': {
                    'rsi': current_rsi,
                    'macd': current_macd,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'bb_upper': float(df['bb_upper'].iloc[-1]) if not pd.isna(df['bb_upper'].iloc[-1]) else None,
                    'bb_lower': float(df['bb_lower'].iloc[-1]) if not pd.isna(df['bb_lower'].iloc[-1]) else None,
                    'atr': float(df['atr'].iloc[-1]) if not pd.isna(df['atr'].iloc[-1]) else None
                },
                'polynomial_regression': {
                    'upper_band': current_upper_band,
                    'lower_band': current_lower_band,
                    'regression_line': float(regression_line[-1]),
                    'degree': degree,
                    'kstd': kstd
                },
                'signal_analysis': signal_analysis,
                'data_points': len(df),
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': f'Analysis failed for {symbol}: {str(e)}'}
    
    def analyze_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                          degree: int = 4, kstd: float = 2.0, days: int = 720) -> Dict:
        """
        Analyze all assets with cross-correlation
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            if symbols is None:
                symbols = self.get_top_100_assets()
            
            logger.info(f"Starting comprehensive analysis of {len(symbols)} assets...")
            
            # Analyze individual assets
            individual_results = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {
                    executor.submit(self.analyze_asset, symbol, interval, degree, kstd, days): symbol 
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if 'error' not in result:
                            individual_results.append(result)
                        else:
                            logger.warning(f"Skipping {symbol}: {result['error']}")
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")
            
            # Calculate cross-correlation
            correlation_analysis = self.calculate_cross_correlation(symbols, interval, days)
            
            # Generate summary statistics
            buy_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'BUY']
            sell_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'SELL']
            hold_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'HOLD']
            
            summary = {
                'total_assets_analyzed': len(individual_results),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'hold_signals': len(hold_signals),
                'avg_potential_return': np.mean([r['signal_analysis']['potential_return'] for r in individual_results]),
                'high_risk_assets': len([r for r in individual_results if r['signal_analysis']['risk_level'] == 'HIGH']),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return {
                'summary': summary,
                'individual_analyses': individual_results,
                'correlation_analysis': correlation_analysis,
                'top_buy_signals': sorted(buy_signals, key=lambda x: x['signal_analysis']['potential_return'], reverse=True)[:10],
                'top_sell_signals': sorted(sell_signals, key=lambda x: x['signal_analysis']['potential_return'], reverse=True)[:10],
                'high_risk_assets': [r for r in individual_results if r['signal_analysis']['risk_level'] == 'HIGH']
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': f'Comprehensive analysis failed: {str(e)}'}
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """
        Save analysis results to JSON file
        
        Args:
            results: Analysis results dictionary
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_analysis_results_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert numpy arrays to lists for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {key: convert_numpy(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                else:
                    return obj
            
            # Convert results for JSON serialization
            json_results = convert_numpy(results)
            
            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def generate_charts(self, results: Dict, symbol: str = None):
        """
        Generate analysis charts
        
        Args:
            results: Analysis results
            symbol: Specific symbol for detailed charts
        """
        try:
            if symbol:
                # Generate detailed charts for specific symbol
                asset_result = next((r for r in results['individual_analyses'] if r['symbol'] == symbol), None)
                if asset_result:
                    self._generate_symbol_charts(asset_result)
            else:
                # Generate summary charts
                self._generate_summary_charts(results)
                
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_symbol_charts(self, asset_result: Dict):
        """Generate detailed charts for a specific symbol"""
        try:
            symbol = asset_result['symbol']
            
            # Create figure with subplots
            fig, axes = plt.subplots(3, 1, figsize=(15, 12))
            fig.suptitle(f'Detailed Analysis: {symbol}', fontsize=16)
            
            # Price and bands chart
            axes[0].set_title('Price Action with Polynomial Regression Bands')
            # Add price data here if available
            
            # Technical indicators
            axes[1].set_title('Technical Indicators')
            # Add RSI, MACD, etc.
            
            # Volume analysis
            axes[2].set_title('Volume Analysis')
            # Add volume data
            
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, 'charts', f'{symbol}_analysis.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Charts saved for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating symbol charts: {e}")
    
    def _generate_summary_charts(self, results: Dict):
        """Generate summary charts for all assets"""
        try:
            # Signal distribution pie chart
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Analysis Summary', fontsize=16)
            
            # Signal distribution
            signals = [results['summary']['buy_signals'], 
                      results['summary']['sell_signals'], 
                      results['summary']['hold_signals']]
            labels = ['BUY', 'SELL', 'HOLD']
            axes[0, 0].pie(signals, labels=labels, autopct='%1.1f%%')
            axes[0, 0].set_title('Signal Distribution')
            
            # Potential return distribution
            returns = [r['signal_analysis']['potential_return'] for r in results['individual_analyses']]
            axes[0, 1].hist(returns, bins=20, alpha=0.7)
            axes[0, 1].set_title('Potential Return Distribution')
            axes[0, 1].set_xlabel('Potential Return (%)')
            axes[0, 1].set_ylabel('Frequency')
            
            # Risk level distribution
            risk_levels = [r['signal_analysis']['risk_level'] for r in results['individual_analyses']]
            risk_counts = pd.Series(risk_levels).value_counts()
            axes[1, 0].bar(risk_counts.index, risk_counts.values)
            axes[1, 0].set_title('Risk Level Distribution')
            
            # Correlation heatmap (if available)
            if 'correlation_analysis' in results and 'correlation_matrix' in results['correlation_analysis']:
                corr_matrix = results['correlation_analysis']['correlation_matrix']
                sns.heatmap(corr_matrix, ax=axes[1, 1], cmap='coolwarm', center=0)
                axes[1, 1].set_title('Asset Correlation Matrix')
            
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, 'charts', 'analysis_summary.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Summary charts generated")
            
        except Exception as e:
            logger.error(f"Error generating summary charts: {e}")

if __name__ == "__main__":
    # Example usage
    config = {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    engine = EnhancedLocalEngine(config)
    results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    engine.save_results(results)
    engine.generate_charts(results) 
 
"""
Enhanced Local Backtesting & Analytics Engine

This is the main local engine that performs comprehensive analysis including:
- Polynomial regression analysis
- Cross-correlation analysis
- Technical indicators
- Signal generation
- Risk assessment
- Portfolio optimization insights

All processing is done locally to avoid cloud costs.
"""

import os
import time
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import json
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
from scipy import stats
from scipy.signal import savgol_filter
import talib
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns

# Suppress warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("enhanced_local_engine.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedLocalEngine:
    def __init__(self, binance_config: Dict, output_dir: str = "results"):
        """
        Initialize the enhanced local analytics engine
        
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
        os.makedirs(os.path.join(self.output_dir, 'charts'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'correlations'), exist_ok=True)
        
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
        Fetch historical data from Binance with caching
        
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
            
            # Cache the data
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added technical indicators
        """
        try:
            # Moving averages
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['sma_200'] = talib.SMA(df['close'], timeperiod=200)
            df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
                df['close'], fastperiod=12, slowperiod=26, signalperiod=9
            )
            
            # RSI
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
                df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
            )
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(
                df['high'], df['low'], df['close'], 
                fastk_period=14, slowk_period=3, slowd_period=3
            )
            
            # ATR (Average True Range)
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Volume indicators
            df['obv'] = talib.OBV(df['close'], df['volume'])
            df['ad'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
            
            # Momentum indicators
            df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
            df['williams_r'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Trend indicators
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Price patterns
            df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def calculate_polynomial_regression(self, data: pd.Series, degree: int = 4, kstd: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate polynomial regression with confidence bands
        
        Args:
            data: Price series
            degree: Polynomial degree
            kstd: Standard deviation multiplier for bands
        
        Returns:
            Tuple of (x_values, regression_line, upper_band, lower_band)
        """
        try:
            # Remove NaN values
            clean_data = data.dropna()
            if len(clean_data) < degree + 1:
                return np.array([]), np.array([]), np.array([]), np.array([])
            
            # Create x values (time index)
            x = np.arange(len(clean_data))
            y = clean_data.values
            
            # Fit polynomial
            coeffs = np.polyfit(x, y, degree)
            poly = np.poly1d(coeffs)
            
            # Calculate regression line
            regression_line = poly(x)
            
            # Calculate residuals and standard deviation
            residuals = y - regression_line
            std_residuals = np.std(residuals)
            
            # Calculate confidence bands
            upper_band = regression_line + (kstd * std_residuals)
            lower_band = regression_line - (kstd * std_residuals)
            
            return x, regression_line, upper_band, lower_band
            
        except Exception as e:
            logger.error(f"Error in polynomial regression: {e}")
            return np.array([]), np.array([]), np.array([]), np.array([])
    
    def calculate_cross_correlation(self, symbols: List[str], interval: str = '1d', days: int = 720) -> Dict:
        """
        Calculate cross-correlation between assets
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            days: Number of days
        
        Returns:
            Dictionary with correlation matrix and analysis
        """
        try:
            # Fetch data for all symbols
            price_data = {}
            for symbol in symbols:
                df = self.fetch_historical_data(symbol, interval, days)
                if not df.empty:
                    price_data[symbol] = df['close']
            
            # Create price matrix
            price_df = pd.DataFrame(price_data)
            price_df = price_df.dropna()
            
            # Calculate correlation matrix
            correlation_matrix = price_df.corr()
            
            # Calculate rolling correlations (30-day window)
            rolling_corr = price_df.rolling(window=30).corr()
            
            # Find highly correlated pairs
            high_corr_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_corr_pairs.append({
                            'pair': (correlation_matrix.columns[i], correlation_matrix.columns[j]),
                            'correlation': corr_value
                        })
            
            # Sort by absolute correlation
            high_corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            return {
                'correlation_matrix': correlation_matrix,
                'rolling_correlation': rolling_corr,
                'high_correlation_pairs': high_corr_pairs,
                'symbols': symbols,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating cross-correlation: {e}")
            return {}
    
    def generate_signal(self, current_price: float, upper_band: float, lower_band: float, 
                       rsi: float = None, macd: float = None, volume_ratio: float = None) -> Dict:
        """
        Generate comprehensive trading signal
        
        Args:
            current_price: Current asset price
            upper_band: Upper polynomial regression band
            lower_band: Lower polynomial regression band
            rsi: RSI value
            macd: MACD value
            volume_ratio: Volume ratio
        
        Returns:
            Dictionary with signal analysis
        """
        try:
            # Calculate potential return
            band_width = upper_band - lower_band
            if band_width > 0:
                potential_return = (band_width / current_price) * 100
            else:
                potential_return = 0
            
            # Determine signal based on price position relative to bands
            if current_price > upper_band:
                signal = 'SELL'
                signal_strength = min((current_price - upper_band) / band_width * 100, 100) if band_width > 0 else 50
            elif current_price < lower_band:
                signal = 'BUY'
                signal_strength = min((lower_band - current_price) / band_width * 100, 100) if band_width > 0 else 50
            else:
                signal = 'HOLD'
                signal_strength = 50
            
            # Additional signal confirmation
            confirmations = []
            if rsi is not None:
                if signal == 'BUY' and rsi < 30:
                    confirmations.append('RSI oversold')
                elif signal == 'SELL' and rsi > 70:
                    confirmations.append('RSI overbought')
            
            if macd is not None:
                if signal == 'BUY' and macd > 0:
                    confirmations.append('MACD positive')
                elif signal == 'SELL' and macd < 0:
                    confirmations.append('MACD negative')
            
            if volume_ratio is not None and volume_ratio > 1.5:
                confirmations.append('High volume')
            
            # Risk assessment
            risk_level = 'LOW'
            if abs(potential_return) > 20:
                risk_level = 'HIGH'
            elif abs(potential_return) > 10:
                risk_level = 'MEDIUM'
            
            return {
                'signal': signal,
                'signal_strength': signal_strength,
                'potential_return': potential_return,
                'confirmations': confirmations,
                'risk_level': risk_level,
                'current_price': current_price,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'band_width': band_width
            }
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {
                'signal': 'HOLD',
                'signal_strength': 0,
                'potential_return': 0,
                'confirmations': [],
                'risk_level': 'UNKNOWN',
                'current_price': current_price,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'band_width': 0
            }
    
    def analyze_asset(self, symbol: str, interval: str = '1d', degree: int = 4, 
                     kstd: float = 2.0, days: int = 720) -> Dict:
        """
        Comprehensive asset analysis
        
        Args:
            symbol: Trading symbol
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days to analyze
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            logger.info(f"Analyzing {symbol}...")
            
            # Fetch historical data
            df = self.fetch_historical_data(symbol, interval, days)
            if df.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)
            
            # Get current values
            current_price = float(df['close'].iloc[-1])
            current_rsi = float(df['rsi'].iloc[-1]) if not pd.isna(df['rsi'].iloc[-1]) else None
            current_macd = float(df['macd'].iloc[-1]) if not pd.isna(df['macd'].iloc[-1]) else None
            
            # Calculate volume ratio (current volume vs 20-day average)
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume'].rolling(20).mean().iloc[-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Polynomial regression analysis
            x, regression_line, upper_band, lower_band = self.calculate_polynomial_regression(
                df['close'], degree, kstd
            )
            
            if len(x) == 0:
                return {'error': f'Insufficient data for polynomial regression on {symbol}'}
            
            # Get current band values
            current_upper_band = float(upper_band[-1])
            current_lower_band = float(lower_band[-1])
            
            # Generate signal
            signal_analysis = self.generate_signal(
                current_price, current_upper_band, current_lower_band,
                current_rsi, current_macd, volume_ratio
            )
            
            # Calculate additional metrics
            price_change_24h = ((current_price - float(df['close'].iloc[-2])) / float(df['close'].iloc[-2])) * 100
            volatility = float(df['close'].pct_change().std() * 100)
            
            # Trend analysis
            sma_20 = float(df['sma_20'].iloc[-1]) if not pd.isna(df['sma_20'].iloc[-1]) else current_price
            sma_50 = float(df['sma_50'].iloc[-1]) if not pd.isna(df['sma_50'].iloc[-1]) else current_price
            trend = 'BULLISH' if sma_20 > sma_50 else 'BEARISH'
            
            # Support and resistance levels
            recent_high = float(df['high'].tail(20).max())
            recent_low = float(df['low'].tail(20).min())
            
            return {
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'current_price': current_price,
                'price_change_24h': price_change_24h,
                'volatility': volatility,
                'trend': trend,
                'support_level': recent_low,
                'resistance_level': recent_high,
                'volume_ratio': volume_ratio,
                'technical_indicators': {
                    'rsi': current_rsi,
                    'macd': current_macd,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'bb_upper': float(df['bb_upper'].iloc[-1]) if not pd.isna(df['bb_upper'].iloc[-1]) else None,
                    'bb_lower': float(df['bb_lower'].iloc[-1]) if not pd.isna(df['bb_lower'].iloc[-1]) else None,
                    'atr': float(df['atr'].iloc[-1]) if not pd.isna(df['atr'].iloc[-1]) else None
                },
                'polynomial_regression': {
                    'upper_band': current_upper_band,
                    'lower_band': current_lower_band,
                    'regression_line': float(regression_line[-1]),
                    'degree': degree,
                    'kstd': kstd
                },
                'signal_analysis': signal_analysis,
                'data_points': len(df),
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': f'Analysis failed for {symbol}: {str(e)}'}
    
    def analyze_all_assets(self, symbols: List[str] = None, interval: str = '1d', 
                          degree: int = 4, kstd: float = 2.0, days: int = 720) -> Dict:
        """
        Analyze all assets with cross-correlation
        
        Args:
            symbols: List of symbols to analyze
            interval: Time interval
            degree: Polynomial degree
            kstd: Standard deviation multiplier
            days: Number of days
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            if symbols is None:
                symbols = self.get_top_100_assets()
            
            logger.info(f"Starting comprehensive analysis of {len(symbols)} assets...")
            
            # Analyze individual assets
            individual_results = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {
                    executor.submit(self.analyze_asset, symbol, interval, degree, kstd, days): symbol 
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if 'error' not in result:
                            individual_results.append(result)
                        else:
                            logger.warning(f"Skipping {symbol}: {result['error']}")
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")
            
            # Calculate cross-correlation
            correlation_analysis = self.calculate_cross_correlation(symbols, interval, days)
            
            # Generate summary statistics
            buy_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'BUY']
            sell_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'SELL']
            hold_signals = [r for r in individual_results if r['signal_analysis']['signal'] == 'HOLD']
            
            summary = {
                'total_assets_analyzed': len(individual_results),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'hold_signals': len(hold_signals),
                'avg_potential_return': np.mean([r['signal_analysis']['potential_return'] for r in individual_results]),
                'high_risk_assets': len([r for r in individual_results if r['signal_analysis']['risk_level'] == 'HIGH']),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return {
                'summary': summary,
                'individual_analyses': individual_results,
                'correlation_analysis': correlation_analysis,
                'top_buy_signals': sorted(buy_signals, key=lambda x: x['signal_analysis']['potential_return'], reverse=True)[:10],
                'top_sell_signals': sorted(sell_signals, key=lambda x: x['signal_analysis']['potential_return'], reverse=True)[:10],
                'high_risk_assets': [r for r in individual_results if r['signal_analysis']['risk_level'] == 'HIGH']
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': f'Comprehensive analysis failed: {str(e)}'}
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """
        Save analysis results to JSON file
        
        Args:
            results: Analysis results dictionary
            filename: Optional filename
        
        Returns:
            Path to saved file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"enhanced_analysis_results_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Convert numpy arrays to lists for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {key: convert_numpy(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                else:
                    return obj
            
            # Convert results for JSON serialization
            json_results = convert_numpy(results)
            
            with open(filepath, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def generate_charts(self, results: Dict, symbol: str = None):
        """
        Generate analysis charts
        
        Args:
            results: Analysis results
            symbol: Specific symbol for detailed charts
        """
        try:
            if symbol:
                # Generate detailed charts for specific symbol
                asset_result = next((r for r in results['individual_analyses'] if r['symbol'] == symbol), None)
                if asset_result:
                    self._generate_symbol_charts(asset_result)
            else:
                # Generate summary charts
                self._generate_summary_charts(results)
                
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _generate_symbol_charts(self, asset_result: Dict):
        """Generate detailed charts for a specific symbol"""
        try:
            symbol = asset_result['symbol']
            
            # Create figure with subplots
            fig, axes = plt.subplots(3, 1, figsize=(15, 12))
            fig.suptitle(f'Detailed Analysis: {symbol}', fontsize=16)
            
            # Price and bands chart
            axes[0].set_title('Price Action with Polynomial Regression Bands')
            # Add price data here if available
            
            # Technical indicators
            axes[1].set_title('Technical Indicators')
            # Add RSI, MACD, etc.
            
            # Volume analysis
            axes[2].set_title('Volume Analysis')
            # Add volume data
            
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, 'charts', f'{symbol}_analysis.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Charts saved for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating symbol charts: {e}")
    
    def _generate_summary_charts(self, results: Dict):
        """Generate summary charts for all assets"""
        try:
            # Signal distribution pie chart
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Analysis Summary', fontsize=16)
            
            # Signal distribution
            signals = [results['summary']['buy_signals'], 
                      results['summary']['sell_signals'], 
                      results['summary']['hold_signals']]
            labels = ['BUY', 'SELL', 'HOLD']
            axes[0, 0].pie(signals, labels=labels, autopct='%1.1f%%')
            axes[0, 0].set_title('Signal Distribution')
            
            # Potential return distribution
            returns = [r['signal_analysis']['potential_return'] for r in results['individual_analyses']]
            axes[0, 1].hist(returns, bins=20, alpha=0.7)
            axes[0, 1].set_title('Potential Return Distribution')
            axes[0, 1].set_xlabel('Potential Return (%)')
            axes[0, 1].set_ylabel('Frequency')
            
            # Risk level distribution
            risk_levels = [r['signal_analysis']['risk_level'] for r in results['individual_analyses']]
            risk_counts = pd.Series(risk_levels).value_counts()
            axes[1, 0].bar(risk_counts.index, risk_counts.values)
            axes[1, 0].set_title('Risk Level Distribution')
            
            # Correlation heatmap (if available)
            if 'correlation_analysis' in results and 'correlation_matrix' in results['correlation_analysis']:
                corr_matrix = results['correlation_analysis']['correlation_matrix']
                sns.heatmap(corr_matrix, ax=axes[1, 1], cmap='coolwarm', center=0)
                axes[1, 1].set_title('Asset Correlation Matrix')
            
            plt.tight_layout()
            chart_path = os.path.join(self.output_dir, 'charts', 'analysis_summary.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Summary charts generated")
            
        except Exception as e:
            logger.error(f"Error generating summary charts: {e}")

if __name__ == "__main__":
    # Example usage
    config = {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    engine = EnhancedLocalEngine(config)
    results = engine.analyze_all_assets(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    engine.save_results(results)
    engine.generate_charts(results) 
 
 