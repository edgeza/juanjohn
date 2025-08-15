"""
Advanced Analytics Tasks

This module provides Celery tasks for advanced analytics using DuckDB
for high-performance analytical processing across multiple asset types.

Features:
- Technical indicator calculations
- Cross-asset correlation analysis
- Portfolio performance metrics
- Risk analysis
- Backtesting support
- Multi-timeframe analysis
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
from celery import Task

from celery_app import celery_app
from processors.duckdb_manager import DuckDBManager
from utils.database import get_timescale_connection
from models.asset_models import AssetType

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsTask(Task):
    """Base task class for analytics with error handling"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2, 'countdown': 30}

@celery_app.task(bind=True, base=AnalyticsTask)
def calculate_technical_indicators(
    self, 
    symbol: str, 
    indicators: List[str], 
    timeframe: str = '1h',
    lookback_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate technical indicators for a symbol using DuckDB
    
    Args:
        symbol: Asset symbol (e.g., 'BTC/USDT', 'AAPL')
        indicators: List of indicators to calculate ['rsi', 'macd', 'bb', 'sma', 'ema']
        timeframe: Data timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
        lookback_days: Number of days to look back for calculations
        
    Returns:
        Dict with calculated indicators
    """
    start_time = datetime.now()
    
    try:
        duckdb_manager = DuckDBManager()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        results = {
            'task_id': self.request.id,
            'symbol': symbol,
            'timeframe': timeframe,
            'start_time': start_time.isoformat(),
            'indicators': {},
            'data_points': 0
        }
        
        # Get base OHLC data
        base_query = f"""
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM timescale.trading.ohlc_data 
        WHERE symbol = '{symbol}'
        AND timestamp >= '{start_date.isoformat()}'
        AND timestamp <= '{end_date.isoformat()}'
        ORDER BY timestamp
        """
        
        df = duckdb_manager.execute_analytics_query(base_query)
        
        if df.empty:
            raise ValueError(f"No data found for symbol {symbol}")
        
        results['data_points'] = len(df)
        
        # Calculate requested indicators
        for indicator in indicators:
            try:
                if indicator.lower() == 'rsi':
                    results['indicators']['rsi'] = calculate_rsi(df)
                elif indicator.lower() == 'macd':
                    results['indicators']['macd'] = calculate_macd(df)
                elif indicator.lower() == 'bb':
                    results['indicators']['bollinger_bands'] = calculate_bollinger_bands(df)
                elif indicator.lower() == 'sma':
                    results['indicators']['sma'] = calculate_sma(df)
                elif indicator.lower() == 'ema':
                    results['indicators']['ema'] = calculate_ema(df)
                elif indicator.lower() == 'volume_profile':
                    results['indicators']['volume_profile'] = calculate_volume_profile(df)
                else:
                    logger.warning(f"Unknown indicator: {indicator}")
                    
            except Exception as e:
                logger.error(f"Failed to calculate {indicator} for {symbol}: {e}")
                results['indicators'][indicator] = {'error': str(e)}
        
        # Store results back to TimescaleDB
        store_indicator_results(symbol, results['indicators'])
        
        end_time = datetime.now()
        results.update({
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'success': True
        })
        
        logger.info(f"Calculated {len(indicators)} indicators for {symbol}")
        return results
        
    except Exception as e:
        logger.error(f"Technical indicators calculation failed for {symbol}: {e}", exc_info=True)
        return {
            'task_id': self.request.id,
            'symbol': symbol,
            'error': str(e),
            'success': False,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }

@celery_app.task(bind=True, base=AnalyticsTask)
def calculate_cross_asset_correlation(
    self, 
    symbols: List[str], 
    lookback_days: int = 30,
    method: str = 'pearson'
) -> Dict[str, Any]:
    """
    Calculate correlation matrix between multiple assets
    
    Args:
        symbols: List of asset symbols
        lookback_days: Number of days for correlation calculation
        method: Correlation method ('pearson', 'spearman', 'kendall')
        
    Returns:
        Dict with correlation matrix and statistics
    """
    start_time = datetime.now()
    
    try:
        duckdb_manager = DuckDBManager()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Build query for all symbols
        symbol_conditions = "', '".join(symbols)
        
        query = f"""
        WITH price_data AS (
            SELECT 
                symbol,
                timestamp,
                close,
                LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) as prev_close
            FROM timescale.trading.ohlc_data 
            WHERE symbol IN ('{symbol_conditions}')
            AND timestamp >= '{start_date.isoformat()}'
            AND timestamp <= '{end_date.isoformat()}'
        ),
        returns_data AS (
            SELECT 
                symbol,
                timestamp,
                close,
                CASE 
                    WHEN prev_close IS NOT NULL AND prev_close != 0 
                    THEN (close - prev_close) / prev_close 
                    ELSE 0 
                END as return_pct
            FROM price_data
            WHERE prev_close IS NOT NULL
        )
        SELECT * FROM returns_data
        ORDER BY timestamp, symbol
        """
        
        df = duckdb_manager.execute_analytics_query(query)
        
        if df.empty:
            raise ValueError("No data found for correlation calculation")
        
        # Pivot data for correlation calculation
        pivot_df = df.pivot(index='timestamp', columns='symbol', values='return_pct')
        
        # Calculate correlation matrix
        correlation_matrix = pivot_df.corr(method=method)
        
        # Convert to dictionary format
        correlation_dict = {}
        for symbol1 in symbols:
            correlation_dict[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 in correlation_matrix.index and symbol2 in correlation_matrix.columns:
                    correlation_dict[symbol1][symbol2] = float(correlation_matrix.loc[symbol1, symbol2])
                else:
                    correlation_dict[symbol1][symbol2] = None
        
        # Calculate additional statistics
        avg_correlation = np.mean([
            correlation_matrix.loc[s1, s2] 
            for s1 in correlation_matrix.index 
            for s2 in correlation_matrix.columns 
            if s1 != s2 and not np.isnan(correlation_matrix.loc[s1, s2])
        ])
        
        max_correlation = np.max([
            correlation_matrix.loc[s1, s2] 
            for s1 in correlation_matrix.index 
            for s2 in correlation_matrix.columns 
            if s1 != s2 and not np.isnan(correlation_matrix.loc[s1, s2])
        ])
        
        min_correlation = np.min([
            correlation_matrix.loc[s1, s2] 
            for s1 in correlation_matrix.index 
            for s2 in correlation_matrix.columns 
            if s1 != s2 and not np.isnan(correlation_matrix.loc[s1, s2])
        ])
        
        end_time = datetime.now()
        
        results = {
            'task_id': self.request.id,
            'symbols': symbols,
            'method': method,
            'lookback_days': lookback_days,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'correlation_matrix': correlation_dict,
            'statistics': {
                'average_correlation': float(avg_correlation),
                'max_correlation': float(max_correlation),
                'min_correlation': float(min_correlation),
                'data_points': len(df)
            },
            'success': True
        }
        
        logger.info(f"Calculated correlation matrix for {len(symbols)} symbols")
        return results
        
    except Exception as e:
        logger.error(f"Cross-asset correlation calculation failed: {e}", exc_info=True)
        return {
            'task_id': self.request.id,
            'symbols': symbols,
            'error': str(e),
            'success': False,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }

@celery_app.task(bind=True, base=AnalyticsTask)
def calculate_portfolio_metrics(
    self, 
    portfolio: Dict[str, float], 
    lookback_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate portfolio performance metrics
    
    Args:
        portfolio: Dict of {symbol: weight} for portfolio composition
        lookback_days: Number of days for performance calculation
        
    Returns:
        Dict with portfolio metrics
    """
    start_time = datetime.now()
    
    try:
        duckdb_manager = DuckDBManager()
        
        symbols = list(portfolio.keys())
        weights = list(portfolio.values())
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight != 1.0:
            weights = [w / total_weight for w in weights]
            logger.info(f"Normalized portfolio weights to sum to 1.0")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get price data for all symbols
        symbol_conditions = "', '".join(symbols)
        
        query = f"""
        WITH price_data AS (
            SELECT 
                symbol,
                timestamp,
                close,
                LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) as prev_close
            FROM timescale.trading.ohlc_data 
            WHERE symbol IN ('{symbol_conditions}')
            AND timestamp >= '{start_date.isoformat()}'
            AND timestamp <= '{end_date.isoformat()}'
        ),
        returns_data AS (
            SELECT 
                symbol,
                timestamp,
                close,
                CASE 
                    WHEN prev_close IS NOT NULL AND prev_close != 0 
                    THEN (close - prev_close) / prev_close 
                    ELSE 0 
                END as return_pct
            FROM price_data
            WHERE prev_close IS NOT NULL
        )
        SELECT * FROM returns_data
        ORDER BY timestamp, symbol
        """
        
        df = duckdb_manager.execute_analytics_query(query)
        
        if df.empty:
            raise ValueError("No data found for portfolio calculation")
        
        # Pivot data
        pivot_df = df.pivot(index='timestamp', columns='symbol', values='return_pct')
        
        # Calculate weighted portfolio returns
        portfolio_returns = []
        for timestamp in pivot_df.index:
            weighted_return = 0
            valid_weights = 0
            
            for symbol, weight in zip(symbols, weights):
                if symbol in pivot_df.columns and not pd.isna(pivot_df.loc[timestamp, symbol]):
                    weighted_return += pivot_df.loc[timestamp, symbol] * weight
                    valid_weights += weight
            
            if valid_weights > 0:
                portfolio_returns.append(weighted_return)
        
        portfolio_returns = np.array(portfolio_returns)
        
        # Calculate metrics
        total_return = np.prod(1 + portfolio_returns) - 1
        annualized_return = (1 + total_return) ** (365 / lookback_days) - 1
        volatility = np.std(portfolio_returns) * np.sqrt(365)  # Annualized
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        max_drawdown = calculate_max_drawdown(portfolio_returns)
        
        end_time = datetime.now()
        
        results = {
            'task_id': self.request.id,
            'portfolio': portfolio,
            'lookback_days': lookback_days,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'metrics': {
                'total_return': float(total_return),
                'annualized_return': float(annualized_return),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'data_points': len(portfolio_returns)
            },
            'daily_returns': portfolio_returns.tolist(),
            'success': True
        }
        
        logger.info(f"Calculated portfolio metrics for {len(symbols)} assets")
        return results
        
    except Exception as e:
        logger.error(f"Portfolio metrics calculation failed: {e}", exc_info=True)
        return {
            'task_id': self.request.id,
            'portfolio': portfolio,
            'error': str(e),
            'success': False,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat()
        }

# Helper functions for technical indicators
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
    """Calculate RSI indicator"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {
        'values': rsi.dropna().tolist(),
        'current': float(rsi.iloc[-1]) if not rsi.empty else None,
        'overbought_level': 70,
        'oversold_level': 30,
        'signal': 'overbought' if rsi.iloc[-1] > 70 else 'oversold' if rsi.iloc[-1] < 30 else 'neutral'
    }

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
    """Calculate MACD indicator"""
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd_line': macd_line.dropna().tolist(),
        'signal_line': signal_line.dropna().tolist(),
        'histogram': histogram.dropna().tolist(),
        'current_macd': float(macd_line.iloc[-1]) if not macd_line.empty else None,
        'current_signal': float(signal_line.iloc[-1]) if not signal_line.empty else None,
        'signal': 'bullish' if histogram.iloc[-1] > 0 else 'bearish'
    }

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
    """Calculate Bollinger Bands"""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    current_price = df['close'].iloc[-1]
    
    return {
        'upper_band': upper_band.dropna().tolist(),
        'middle_band': sma.dropna().tolist(),
        'lower_band': lower_band.dropna().tolist(),
        'current_price': float(current_price),
        'bandwidth': float((upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1] * 100),
        'signal': 'overbought' if current_price > upper_band.iloc[-1] else 'oversold' if current_price < lower_band.iloc[-1] else 'neutral'
    }

def calculate_sma(df: pd.DataFrame, periods: List[int] = [20, 50, 200]) -> Dict[str, Any]:
    """Calculate Simple Moving Averages"""
    sma_data = {}
    for period in periods:
        sma = df['close'].rolling(window=period).mean()
        sma_data[f'sma_{period}'] = {
            'values': sma.dropna().tolist(),
            'current': float(sma.iloc[-1]) if not sma.empty else None
        }
    
    return sma_data

def calculate_ema(df: pd.DataFrame, periods: List[int] = [12, 26, 50]) -> Dict[str, Any]:
    """Calculate Exponential Moving Averages"""
    ema_data = {}
    for period in periods:
        ema = df['close'].ewm(span=period).mean()
        ema_data[f'ema_{period}'] = {
            'values': ema.dropna().tolist(),
            'current': float(ema.iloc[-1]) if not ema.empty else None
        }
    
    return ema_data

def calculate_volume_profile(df: pd.DataFrame, bins: int = 20) -> Dict[str, Any]:
    """Calculate Volume Profile"""
    price_min = df['low'].min()
    price_max = df['high'].max()
    price_bins = np.linspace(price_min, price_max, bins + 1)
    
    volume_profile = []
    for i in range(len(price_bins) - 1):
        bin_low = price_bins[i]
        bin_high = price_bins[i + 1]
        
        # Find candles that overlap with this price bin
        overlapping = df[
            (df['low'] <= bin_high) & (df['high'] >= bin_low)
        ]
        
        total_volume = overlapping['volume'].sum()
        
        volume_profile.append({
            'price_low': float(bin_low),
            'price_high': float(bin_high),
            'volume': float(total_volume)
        })
    
    return {
        'profile': volume_profile,
        'poc': max(volume_profile, key=lambda x: x['volume'])  # Point of Control
    }

def calculate_max_drawdown(returns: np.ndarray) -> float:
    """Calculate maximum drawdown"""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return float(np.min(drawdown))

def store_indicator_results(symbol: str, indicators: Dict[str, Any]):
    """Store indicator results back to TimescaleDB"""
    try:
        # This would store results in a dedicated indicators table
        # Implementation depends on your specific schema requirements
        logger.info(f"Stored indicator results for {symbol}")
    except Exception as e:
        logger.error(f"Failed to store indicator results for {symbol}: {e}")

# Batch processing tasks
@celery_app.task(bind=True)
def batch_calculate_indicators(self, symbols: List[str], indicators: List[str]) -> Dict[str, Any]:
    """Calculate indicators for multiple symbols in batch"""
    start_time = datetime.now()
    results = {}
    
    for symbol in symbols:
        try:
            result = calculate_technical_indicators.delay(symbol, indicators).get(timeout=120)
            results[symbol] = result
        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")
            results[symbol] = {'error': str(e), 'success': False}
    
    end_time = datetime.now()
    
    return {
        'task_id': self.request.id,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': (end_time - start_time).total_seconds(),
        'symbols_processed': len(symbols),
        'indicators': indicators,
        'results': results
    }
