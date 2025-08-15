from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self):
        self.parameters = {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def configure(self, parameters: Dict[str, Any]):
        """Configure strategy parameters"""
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from market data"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)


class BacktestEngine:
    """Backtesting engine for strategy evaluation"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
    
    def reset(self):
        """Reset backtest state"""
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        self.max_drawdown = 0
        self.peak_equity = self.initial_capital
    
    def run_backtest(self, strategy: BaseStrategy, data: pd.DataFrame) -> Dict[str, float]:
        """Run backtest and return performance metrics"""
        try:
            self.reset()
            
            if not strategy.validate_data(data):
                raise ValueError("Invalid data format")
            
            # Generate signals
            signals = strategy.generate_signals(data)
            
            if signals.empty:
                return self._get_zero_metrics()
            
            # Execute trades
            for i, (timestamp, row) in enumerate(signals.iterrows()):
                price = row['close']
                signal = row.get('signal', 0)
                
                # Execute trade
                if signal != 0 and signal != self.position:
                    self._execute_trade(timestamp, price, signal)
                
                # Update equity curve
                current_equity = self._calculate_equity(price)
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'equity': current_equity,
                    'position': self.position
                })
                
                # Update max drawdown
                if current_equity > self.peak_equity:
                    self.peak_equity = current_equity
                else:
                    drawdown = (self.peak_equity - current_equity) / self.peak_equity
                    self.max_drawdown = max(self.max_drawdown, drawdown)
            
            return self._calculate_metrics()
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return self._get_zero_metrics()
    
    def _execute_trade(self, timestamp, price: float, new_position: int):
        """Execute a trade"""
        if self.position != 0:
            # Close existing position
            pnl = (price - self.entry_price) * self.position * (self.capital / self.entry_price)
            commission_cost = abs(pnl) * self.commission
            self.capital += pnl - commission_cost
            
            self.trades.append({
                'timestamp': timestamp,
                'type': 'close',
                'position': self.position,
                'price': price,
                'pnl': pnl - commission_cost
            })
        
        if new_position != 0:
            # Open new position
            self.position = new_position
            self.entry_price = price
            commission_cost = self.capital * self.commission
            self.capital -= commission_cost
            
            self.trades.append({
                'timestamp': timestamp,
                'type': 'open',
                'position': new_position,
                'price': price,
                'pnl': -commission_cost
            })
        else:
            self.position = 0
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity"""
        if self.position == 0:
            return self.capital
        else:
            unrealized_pnl = (current_price - self.entry_price) * self.position * (self.capital / self.entry_price)
            return self.capital + unrealized_pnl
    
    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if not self.equity_curve:
            return self._get_zero_metrics()
        
        equity_series = pd.Series([point['equity'] for point in self.equity_curve])
        returns = equity_series.pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_series.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Risk metrics
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0
        
        # Trade metrics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': -self.max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
    
    def _get_zero_metrics(self) -> Dict[str, float]:
        """Return zero metrics for failed backtests"""
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'total_trades': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0
        }
