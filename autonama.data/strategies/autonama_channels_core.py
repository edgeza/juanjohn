"""
Autonama Channels Core Algorithm - v2 Migration

This module contains the core Autonama Channels algorithm migrated from the Simple version
with TimescaleDB integration and enhanced for the v2 architecture.
"""

import logging
import numpy as np
import pandas as pd
import warnings
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)


class AutonamaChannelsCore:
    """
    Core Autonama Channels algorithm with polynomial regression-based channel calculation.
    
    This is the migrated version of the proven algorithm from the Simple version,
    enhanced for TimescaleDB integration and v2 architecture.
    """
    
    def __init__(self, degree: int = 2, kstd: float = 2.0):
        """
        Initialize Autonama Channels calculator.
        
        Args:
            degree: Polynomial degree for regression curve (default: 2)
            kstd: Standard deviation multiplier for channel width (default: 2.0)
        """
        self.degree = degree
        self.kstd = kstd
        self.logger = logger
    
    def calculate_autonama_channels(self, data: pd.Series) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Calculate Autonama channels for the given price data using polynomial regression.
        
        Args:
            data: Series of price data
            
        Returns:
            Tuple of (center_channel, upper_channel, lower_channel) arrays or (None, None, None) on failure
        """
        try:
            # Skip calculation if we don't have enough data points for the requested degree
            if len(data) <= self.degree + 2:
                self.logger.warning(f"Insufficient data points: {len(data)} <= {self.degree + 2}")
                return None, None, None
                
            X = np.arange(len(data))
            y = data.values
            
            # Safeguard against too high polynomial degrees relative to the data size
            degree = self.degree
            if degree > min(10, len(data) // 20):
                degree = min(10, len(data) // 20)  # Adjust to safer value
                self.logger.info(f"Adjusted polynomial degree from {self.degree} to {degree} for data size {len(data)}")
                
            with warnings.catch_warnings():
                warnings.simplefilter('error', np.RankWarning)
                try:
                    coefficients = np.polyfit(X, y, degree)
                except np.RankWarning:
                    self.logger.warning("Polynomial fit rank warning - returning None")
                    return None, None, None
                except Exception as e:
                    self.logger.error(f"Polynomial fit error: {e}")
                    return None, None, None
            
            poly = np.poly1d(coefficients)
            autonama_channel = poly(X)
            
            # Check for unrealistic values in the regression line
            if np.any(np.isnan(autonama_channel)) or np.any(np.isinf(autonama_channel)):
                self.logger.warning("NaN or Inf values in regression line")
                return None, None, None
                
            # Check for extreme values in the regression line
            mean_price = np.mean(y)
            if mean_price > 0 and np.any(np.abs(autonama_channel/mean_price) > 10):
                self.logger.warning("Extreme values detected in regression line")
                return None, None, None
            
            std_dev = np.std(y - autonama_channel)
            autonama_upper = autonama_channel + self.kstd * std_dev
            autonama_lower = autonama_channel - self.kstd * std_dev
            
            self.logger.debug(f"Successfully calculated channels: center={autonama_channel[-1]:.4f}, upper={autonama_upper[-1]:.4f}, lower={autonama_lower[-1]:.4f}")
            
            return autonama_channel, autonama_upper, autonama_lower
            
        except Exception as e:
            self.logger.error(f"Error calculating Autonama channels: {e}")
            return None, None, None
    
    def generate_trading_signals(self, close_data: pd.Series, lookback: int = 1) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
        """
        Generate trading signals based on Autonama channels.
        
        Args:
            close_data: Series of price data
            lookback: Lookback window for price smoothing (default: 1, no smoothing)
            
        Returns:
            Tuple of (entries, exits, indicators) or (None, None, None) on failure
        """
        try:
            # Ensure we have a proper DatetimeIndex
            if not isinstance(close_data.index, pd.DatetimeIndex):
                try:
                    close_data.index = pd.to_datetime(close_data.index, utc=True)
                except Exception:
                    # If conversion fails, create a fallback DatetimeIndex
                    close_data.index = pd.date_range(start='2020-01-01', periods=len(close_data), freq='D')
            
            # Handle timezone-aware DatetimeIndex
            if close_data.index.tz is not None:
                close_data.index = close_data.index.tz_localize(None)
            
            # Check for NaN values in close_data and fill them
            if close_data.isna().any():
                close_data = close_data.fillna(method='ffill').fillna(method='bfill')
                if close_data.isna().any():
                    self.logger.error("Unable to fill NaN values in price data")
                    return None, None, None
            
            # Apply lookback window smoothing if specified
            calc_data = close_data
            if lookback > 1:
                calc_data = close_data.rolling(window=lookback).mean()
                calc_data = calc_data.fillna(method='bfill')
            
            # Calculate channels using the smoothed data
            autonama_channel, autonama_upper, autonama_lower = self.calculate_autonama_channels(calc_data)
            
            # Check if channel calculation failed
            if autonama_channel is None or autonama_upper is None or autonama_lower is None:
                self.logger.error("Failed to calculate Autonama channels")
                return None, None, None
            
            # Convert to Series with proper index
            autonama_channel = pd.Series(autonama_channel, index=close_data.index)
            autonama_upper = pd.Series(autonama_upper, index=close_data.index)
            autonama_lower = pd.Series(autonama_lower, index=close_data.index)
            
            # Check for NaN values in calculated channels
            if autonama_channel.isna().any() or autonama_upper.isna().any() or autonama_lower.isna().any():
                autonama_channel = autonama_channel.fillna(method='ffill').fillna(method='bfill')
                autonama_upper = autonama_upper.fillna(method='ffill').fillna(method='bfill')
                autonama_lower = autonama_lower.fillna(method='ffill').fillna(method='bfill')
                
                if autonama_channel.isna().any() or autonama_upper.isna().any() or autonama_lower.isna().any():
                    self.logger.error("Unable to fill NaN values in calculated channels")
                    return None, None, None
            
            # Create indicators dataframe
            indicators = pd.DataFrame({
                "Close": close_data,
                "Autonama_Channel": autonama_channel,
                "Autonama_Upper": autonama_upper,
                "Autonama_Lower": autonama_lower,
            }, index=close_data.index)
            
            # Generate trading signals
            # Simplified signals for reliability
            entries = close_data < autonama_lower
            exits = close_data > autonama_upper
            
            # Add momentum-based refinements
            try:
                momentum = close_data.diff()
                
                # Enhanced entry conditions
                enhanced_entries = (
                    (close_data < autonama_lower * 1.01) |
                    ((close_data < autonama_channel * 0.985) & (momentum < 0))
                )
                
                # Enhanced exit conditions
                enhanced_exits = (
                    (close_data > autonama_upper * 0.99) |
                    ((close_data > autonama_channel * 1.015) & (momentum > 0))
                )
                
                entries = enhanced_entries
                exits = enhanced_exits
                
            except Exception as e:
                self.logger.warning(f"Using simplified signals due to momentum calculation error: {e}")
            
            # Add signal statistics to indicators
            indicators['Entry_Signal'] = entries.astype(int)
            indicators['Exit_Signal'] = exits.astype(int)
            indicators['Channel_Position'] = (close_data - autonama_lower) / (autonama_upper - autonama_lower)
            
            self.logger.info(f"Generated signals: {entries.sum()} entries, {exits.sum()} exits")
            
            return entries, exits, indicators
            
        except Exception as e:
            self.logger.error(f"Error generating trading signals: {e}")
            return None, None, None
    
    def compute_signal_and_insights(self, symbol: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Compute trading signal and insights for a symbol.
        
        Args:
            symbol: Symbol to analyze
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal information and insights or None on failure
        """
        try:
            # Ensure we have enough data points
            if len(data) < 30:
                self.logger.warning(f"Insufficient data points for {symbol}: {len(data)} < 30")
                return None
            
            # Get close data
            if "close" not in data.columns and "Close" not in data.columns:
                self.logger.error(f"No 'close' or 'Close' column in data for {symbol}")
                return None
            
            close_col = "close" if "close" in data.columns else "Close"
            close_data = data[close_col]
            
            # Calculate Autonama channels
            self.logger.info(f"Calculating Autonama channels for {symbol} with degree={self.degree}, kstd={self.kstd}")
            autonama_channel, autonama_upper, autonama_lower = self.calculate_autonama_channels(close_data)
            
            # Check if channel calculation succeeded
            if autonama_channel is None or autonama_upper is None or autonama_lower is None:
                self.logger.error(f"Failed to calculate Autonama channels for {symbol}")
                return None
            
            # Convert to Series if ndarray
            if isinstance(autonama_channel, np.ndarray):
                autonama_channel = pd.Series(autonama_channel, index=close_data.index)
                autonama_upper = pd.Series(autonama_upper, index=close_data.index)
                autonama_lower = pd.Series(autonama_lower, index=close_data.index)
            
            # Get latest values
            latest_price = float(close_data.iloc[-1])
            latest_channel = float(autonama_channel.iloc[-1])
            latest_upper = float(autonama_upper.iloc[-1])
            latest_lower = float(autonama_lower.iloc[-1])
            
            # Calculate price deviation from channel
            price_deviation = latest_price - latest_channel
            price_deviation_pct = (price_deviation / latest_channel) * 100 if latest_channel != 0 else 0
            
            # Determine spread based on asset type
            spread_pct = self._estimate_spread(symbol)
            
            # Adjust potential earnings by accounting for spread
            adjusted_potential_earnings = price_deviation_pct - (spread_pct * 2)  # Deduct spread twice (entry and exit)
            
            # Determine signal
            if latest_price < latest_lower:
                signal = "BUY"
            elif latest_price > latest_upper:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Calculate potential earnings (channel range)
            channel_range_abs = latest_upper - latest_lower
            channel_range_pct = (channel_range_abs / latest_price) * 100 if latest_price != 0 else 0
            
            # Calculate additional metrics
            additional_insights = self._compute_additional_insights(data)
            
            result = {
                "Symbol": symbol,
                "Last_Price": latest_price,
                "Autonama_Lower": latest_lower,
                "Autonama_Channel": latest_channel,
                "Autonama_Upper": latest_upper,
                "Signal": signal,
                "Deviation_Pct": round(price_deviation_pct, 2),
                "Potential_Earnings_Pct": round(max(0, adjusted_potential_earnings), 2),
                "Channel_Range_Pct": round(channel_range_pct, 2),
                "Spread_Pct": round(spread_pct, 2),
                "Timestamp": datetime.utcnow(),
                **additional_insights
            }
            
            self.logger.info(f"Signal for {symbol}: {signal} (deviation: {price_deviation_pct:.2f}%)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in compute_signal_and_insights for {symbol}: {str(e)}")
            return None
    
    def _estimate_spread(self, symbol: str) -> float:
        """
        Estimate trading spread based on symbol characteristics.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Estimated spread percentage
        """
        symbol_upper = symbol.upper()
        
        # Crypto assets
        if any(crypto in symbol_upper for crypto in ["BTC", "ETH", "ADA", "DOT", "LINK", "SOL", "AVAX", "MATIC", "UNI", "BNB"]):
            return 0.1  # 0.1% for major cryptos
        
        # Forex pairs
        if "/" in symbol and any(curr in symbol_upper for curr in ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]):
            return 0.02  # 0.02% for major forex pairs
        
        # Commodities
        if any(comm in symbol_upper for comm in ["XAU", "XAG", "CL=F", "GC=F", "SI=F"]):
            return 0.05  # 0.05% for commodities
        
        # Stocks (default)
        return 0.05  # 0.05% for stocks
    
    def _compute_additional_insights(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute additional market insights from the data.
        
        Args:
            data: DataFrame of price data
            
        Returns:
            Dictionary with additional insights
        """
        try:
            if data is None or len(data) < 30:
                return {}
            
            close_col = "close" if "close" in data.columns else "Close"
            close_data = data[close_col]
            
            # Calculate basic metrics
            returns = close_data.pct_change().dropna()
            
            # Detect trend
            short_ma = close_data.rolling(20).mean()
            long_ma = close_data.rolling(50).mean()
            
            if len(short_ma.dropna()) == 0 or len(long_ma.dropna()) == 0:
                return {}
            
            recent_short = short_ma.iloc[-1]
            recent_long = long_ma.iloc[-1]
            
            if recent_short > recent_long:
                trend = "Uptrend"
                trend_strength = (recent_short / recent_long - 1) * 100
            else:
                trend = "Downtrend"
                trend_strength = (recent_long / recent_short - 1) * 100
            
            # Calculate volatility
            if len(returns) > 0:
                volatility = returns.std() * 100 * (252 ** 0.5)  # Annualized volatility
                
                if volatility < 15:
                    volatility_desc = "Low"
                elif volatility < 35:
                    volatility_desc = "Medium"
                else:
                    volatility_desc = "High"
            else:
                volatility = 0
                volatility_desc = "Unknown"
            
            # Determine market regime
            if trend == "Uptrend" and volatility_desc in ["Low", "Medium"]:
                market_regime = "Bullish"
            elif trend == "Uptrend" and volatility_desc == "High":
                market_regime = "Volatile Bull"
            elif trend == "Downtrend" and volatility_desc in ["Low", "Medium"]:
                market_regime = "Bearish"
            else:
                market_regime = "Volatile Bear"
            
            return {
                "Trend": trend,
                "Trend_Strength": round(trend_strength, 2),
                "Volatility": volatility_desc,
                "Volatility_Value": round(volatility, 2),
                "Market_Regime": market_regime
            }
            
        except Exception as e:
            self.logger.warning(f"Error computing additional insights: {e}")
            return {}


def create_autonama_channels_calculator(degree: int = 2, kstd: float = 2.0) -> AutonamaChannelsCore:
    """
    Factory function to create an Autonama Channels calculator.
    
    Args:
        degree: Polynomial degree for regression curve
        kstd: Standard deviation multiplier for channel width
        
    Returns:
        AutonamaChannelsCore instance
    """
    return AutonamaChannelsCore(degree=degree, kstd=kstd)


# Helper functions for backward compatibility
def calculate_autonama_channels(data: pd.Series, degree: int = 2, kstd: float = 2.0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Calculate Autonama channels for the given price data.
    
    Args:
        data: Series of price data
        degree: Polynomial degree for the regression curve
        kstd: Standard deviation multiplier for channel width
        
    Returns:
        Tuple of (center_channel, upper_channel, lower_channel) arrays or (None, None, None) on failure
    """
    calculator = AutonamaChannelsCore(degree=degree, kstd=kstd)
    return calculator.calculate_autonama_channels(data)


def compute_signal_and_insights(symbol: str, data: pd.DataFrame, degree: int = 2, kstd: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Compute trading signal and insights for a symbol.
    
    Args:
        symbol: Symbol to analyze
        data: DataFrame with OHLCV data
        degree: Polynomial degree
        kstd: Standard deviation multiplier
        
    Returns:
        Dictionary with signal information and insights or None on failure
    """
    calculator = AutonamaChannelsCore(degree=degree, kstd=kstd)
    return calculator.compute_signal_and_insights(symbol, data)