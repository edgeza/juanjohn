"""
Optimization API Endpoints

This module provides FastAPI endpoints for strategy optimization and signal generation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import pandas as pd
import numpy as np
from sqlalchemy import text

from src.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class OptimizationRequest(BaseModel):
    symbol: str = Field(..., description="Asset symbol to optimize")
    strategy: str = Field(default="polynomial_regression", description="Strategy type")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")
    lookback_days: int = Field(default=365, description="Days to look back")
    optimization_trials: int = Field(default=10, description="Number of optimization trials")

class OptimizationResult(BaseModel):
    symbol: str
    strategy: str
    signal: str
    confidence: float
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    expected_return: Optional[float] = None
    optimization_metrics: Dict[str, Any]
    timestamp: str

class StrategySignal(BaseModel):
    symbol: str
    signal: str
    confidence: float
    price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: str
    description: str

def calculate_polynomial_regression(data: pd.Series, degree: int = 4, kstd: float = 2.0):
    """
    Calculate polynomial regression with upper and lower bands.
    
    Args:
        data: Price series
        degree: Polynomial degree
        kstd: Standard deviation multiplier
        
    Returns:
        Tuple of (regression_line, upper_band, lower_band) or (None, None, None) on error
    """
    try:
        if len(data) < degree + 1:
            return None, None, None
            
        X = np.arange(len(data))
        y = data.values
        
        # Fit polynomial
        coefficients = np.polyfit(X, y, degree)
        polynomial = np.poly1d(coefficients)
        regression_line = polynomial(X)
        
        # Calculate bands
        std_dev = np.std(y - regression_line)
        upper_band = regression_line + kstd * std_dev
        lower_band = regression_line - kstd * std_dev
        
        return regression_line, upper_band, lower_band
        
    except Exception as e:
        logger.error(f"Error in polynomial regression: {e}")
        return None, None, None

def generate_polynomial_signal(close_price: float, upper_band: float, lower_band: float) -> tuple:
    """
    Generate trading signal based on price position relative to polynomial bands.
    
    Args:
        close_price: Current closing price
        upper_band: Upper polynomial band
        lower_band: Lower polynomial band
        
    Returns:
        Tuple of (signal, confidence, target_price, stop_loss, take_profit)
    """
    try:
        signal = 'HOLD'
        confidence = 0.5
        target_price = None
        stop_loss = None
        take_profit = None
        
        if close_price < lower_band:
            signal = 'BUY'
            confidence = 0.8
            target_price = upper_band
            stop_loss = lower_band * 0.95
            take_profit = upper_band * 1.05
        elif close_price > upper_band:
            signal = 'SELL'
            confidence = 0.8
            target_price = lower_band
            stop_loss = upper_band * 1.05
            take_profit = lower_band * 0.95
        else:
            # Price is between bands
            band_range = upper_band - lower_band
            price_position = (close_price - lower_band) / band_range if band_range > 0 else 0.5
            
            if price_position < 0.3:
                signal = 'BUY'
                confidence = 0.6
                target_price = upper_band
            elif price_position > 0.7:
                signal = 'SELL'
                confidence = 0.6
                target_price = lower_band
        
        return signal, confidence, target_price, stop_loss, take_profit
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        return 'HOLD', 0.5, None, None, None

@router.post("/optimize", response_model=OptimizationResult)
async def optimize_strategy(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """Optimize strategy parameters for a specific symbol"""
    try:
        logger.info(f"Optimizing {request.strategy} for {request.symbol}")
        
        # For now, return a mock optimization result
        # In a real implementation, this would run actual optimization
        current_price = 43250.50  # Mock price
        signal, confidence, target_price, stop_loss, take_profit = generate_polynomial_signal(
            current_price, current_price * 1.05, current_price * 0.95
        )
        
        return OptimizationResult(
            symbol=request.symbol,
            strategy=request.strategy,
            signal=signal,
            confidence=confidence,
            current_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=2.0 if target_price and stop_loss else None,
            expected_return=5.0,
            optimization_metrics={
                "degree": 4,
                "kstd": 2.0,
                "lookback_period": 100,
                "r_squared": 0.85
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.get("/signals", response_model=List[StrategySignal])
async def get_strategy_signals(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    strategy: str = Query("polynomial_regression", description="Strategy type"),
    db: Session = Depends(get_db)
):
    """Get strategy signals for multiple symbols"""
    try:
        # Get symbols to analyze
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
        else:
            # Default to top symbols
            symbol_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "BNB/USDT"]
        
        signals = []
        
        for symbol in symbol_list:
            try:
                # Mock data for demonstration
                # In real implementation, fetch actual price data
                mock_prices = {
                    "BTC/USDT": 43250.50,
                    "ETH/USDT": 2650.75,
                    "SOL/USDT": 98.45,
                    "ADA/USDT": 0.485,
                    "BNB/USDT": 320.50
                }
                
                current_price = mock_prices.get(symbol, 100.0)
                
                # Calculate polynomial regression (mock)
                regression_line, upper_band, lower_band = calculate_polynomial_regression(
                    pd.Series([current_price * 0.95, current_price, current_price * 1.05]),
                    degree=4,
                    kstd=2.0
                )
                
                if regression_line is not None:
                    signal, confidence, target_price, stop_loss, take_profit = generate_polynomial_signal(
                        current_price, upper_band[-1], lower_band[-1]
                    )
                    
                    description = f"{symbol} showing {signal} signal with {confidence:.1%} confidence"
                    
                    signal_obj = StrategySignal(
                        symbol=symbol,
                        signal=signal,
                        confidence=confidence,
                        price=current_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        timestamp=datetime.now().isoformat(),
                        description=description
                    )
                    
                    signals.append(signal_obj)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        return signals
        
    except Exception as e:
        logger.error(f"Error getting strategy signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")

@router.get("/strategies")
async def get_available_strategies():
    """Get list of available trading strategies"""
    return {
        "strategies": [
            {
                "name": "polynomial_regression",
                "description": "Polynomial regression with confidence bands",
                "parameters": {
                    "degree": "Polynomial degree (2-6)",
                    "kstd": "Standard deviation multiplier for bands (1.5-3.0)",
                    "lookback_period": "Number of periods for calculation (50-500)"
                }
            }
        ]
    }

@router.get("/health")
async def optimization_health_check():
    """Health check for optimization service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "optimization-api",
        "available_strategies": ["polynomial_regression"]
    }
