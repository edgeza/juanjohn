import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy

class AutonamaChannelsStrategy(BaseStrategy):
    """Autonama Channels trading strategy"""
    
    def __init__(self):
        super().__init__()
        self.name = "Autonama Channels"
        self.default_parameters = {
            'lookback_period': 20,
            'channel_width': 0.02,
            'entry_threshold': 1.0,
            'exit_threshold': 0.5,
            'stop_loss': 0.05,
            'take_profit': 0.10
        }
    
    def configure(self, parameters: Dict[str, Any]):
        """Configure strategy parameters"""
        self.parameters = {**self.default_parameters, **parameters}
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on Autonama Channels"""
        if not self.validate_data(data):
            return pd.DataFrame()
        
        df = data.copy()
        
        # Calculate channels
        df = self._calculate_channels(df)
        
        # Generate entry/exit signals
        df = self._generate_entry_signals(df)
        df = self._generate_exit_signals(df)
        
        # Combine signals
        df['signal'] = self._combine_signals(df)
        
        return df[['signal']].fillna(0)
    
    def _calculate_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Autonama channel levels"""
        lookback = self.parameters['lookback_period']
        width = self.parameters['channel_width']
        
        # Rolling statistics
        df['rolling_high'] = df['high'].rolling(window=lookback).max()
        df['rolling_low'] = df['low'].rolling(window=lookback).min()
        df['rolling_close'] = df['close'].rolling(window=lookback).mean()
        
        # Channel levels
        df['upper_channel'] = df['rolling_high'] * (1 + width)
        df['lower_channel'] = df['rolling_low'] * (1 - width)
        df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
        
        # Channel position (where current price is relative to channels)
        df['channel_position'] = (df['close'] - df['lower_channel']) / (df['upper_channel'] - df['lower_channel'])
        
        return df
    
    def _generate_entry_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry signals"""
        threshold = self.parameters['entry_threshold']
        
        # Long entry: price breaks below lower channel
        df['long_entry'] = (
            (df['close'] <= df['lower_channel']) & 
            (df['close'].shift(1) > df['lower_channel'].shift(1)) &
            (df['channel_position'] < (1 - threshold) / 2)
        )
        
        # Short entry: price breaks above upper channel
        df['short_entry'] = (
            (df['close'] >= df['upper_channel']) & 
            (df['close'].shift(1) < df['upper_channel'].shift(1)) &
            (df['channel_position'] > (1 + threshold) / 2)
        )
        
        return df
    
    def _generate_exit_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate exit signals"""
        exit_threshold = self.parameters['exit_threshold']
        
        # Long exit: price reaches middle channel or upper channel
        df['long_exit'] = (
            (df['close'] >= df['middle_channel']) |
            (df['channel_position'] > (1 + exit_threshold) / 2)
        )
        
        # Short exit: price reaches middle channel or lower channel
        df['short_exit'] = (
            (df['close'] <= df['middle_channel']) |
            (df['channel_position'] < (1 - exit_threshold) / 2)
        )
        
        return df
    
    def _combine_signals(self, df: pd.DataFrame) -> pd.Series:
        """Combine entry and exit signals into position signals"""
        signals = pd.Series(0, index=df.index)
        current_position = 0
        
        for i in range(len(df)):
            if current_position == 0:  # No position
                if df['long_entry'].iloc[i]:
                    current_position = 1  # Long
                elif df['short_entry'].iloc[i]:
                    current_position = -1  # Short
            elif current_position == 1:  # Long position
                if df['long_exit'].iloc[i] or self._check_stop_loss_take_profit(df, i, current_position):
                    current_position = 0  # Close long
            elif current_position == -1:  # Short position
                if df['short_exit'].iloc[i] or self._check_stop_loss_take_profit(df, i, current_position):
                    current_position = 0  # Close short
            
            signals.iloc[i] = current_position
        
        return signals
    
    def _check_stop_loss_take_profit(self, df: pd.DataFrame, index: int, position: int) -> bool:
        """Check stop loss and take profit conditions"""
        if index == 0:
            return False
        
        current_price = df['close'].iloc[index]
        entry_price = self._find_entry_price(df, index, position)
        
        if entry_price is None:
            return False
        
        stop_loss = self.parameters['stop_loss']
        take_profit = self.parameters['take_profit']
        
        if position == 1:  # Long position
            # Stop loss: price drops below entry - stop_loss%
            if current_price <= entry_price * (1 - stop_loss):
                return True
            # Take profit: price rises above entry + take_profit%
            if current_price >= entry_price * (1 + take_profit):
                return True
        elif position == -1:  # Short position
            # Stop loss: price rises above entry + stop_loss%
            if current_price >= entry_price * (1 + stop_loss):
                return True
            # Take profit: price drops below entry - take_profit%
            if current_price <= entry_price * (1 - take_profit):
                return True
        
        return False
    
    def _find_entry_price(self, df: pd.DataFrame, current_index: int, position: int) -> float:
        """Find the entry price for the current position"""
        # Look backwards to find when position was opened
        for i in range(current_index - 1, -1, -1):
            if i == 0:
                return df['close'].iloc[0]
            
            # Check if this was an entry point
            if position == 1 and df['long_entry'].iloc[i]:
                return df['close'].iloc[i]
            elif position == -1 and df['short_entry'].iloc[i]:
                return df['close'].iloc[i]
        
        return df['close'].iloc[current_index - 1]  # Fallback
    
    def get_parameter_ranges(self) -> Dict[str, tuple]:
        """Get parameter ranges for optimization"""
        return {
            'lookback_period': (10, 100),
            'channel_width': (0.01, 0.1),
            'entry_threshold': (0.5, 2.0),
            'exit_threshold': (0.2, 1.5),
            'stop_loss': (0.01, 0.1),
            'take_profit': (0.02, 0.2)
        }
