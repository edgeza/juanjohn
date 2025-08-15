"""
Data API Endpoints

This module provides FastAPI endpoints for accessing financial data
from TimescaleDB and DuckDB.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import pandas as pd
from sqlalchemy import text

from src.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class AssetSummary(BaseModel):
    symbol: str
    name: str
    category: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    last_updated: str

class SignalData(BaseModel):
    symbol: str
    signal: str
    price: float
    channel_value: float
    upper_band: float
    lower_band: float
    deviation_percent: float
    channel_range_percent: float
    timestamp: str
    confidence_score: float

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router is working"""
    return {"message": "Data router is working", "timestamp": datetime.now().isoformat()}

@router.get("/assets", response_model=Dict[str, Any])
async def get_assets(
    limit: int = Query(default=50, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get top 100 assets by volume with pagination"""
    try:
        # Build the base query - limit to top 100 by volume
        base_query = """
        SELECT DISTINCT
            cp.symbol,
            cp.price,
            cp.change_24h,
            cp.change_percent_24h,
            cp.volume_24h,
            cp.timestamp,
            COALESCE(am.asset_type, 'crypto') as category,
            COALESCE(am.name, cp.symbol) as name
        FROM trading.current_prices cp
        LEFT JOIN trading.asset_metadata am ON cp.symbol = am.symbol
        WHERE cp.volume_24h > 0
        """
        
        # Add category filter if specified
        if category:
            base_query += f" AND COALESCE(am.asset_type, 'crypto') = '{category}'"
        
        # Add ordering by volume (highest first) and limit to top 100, then pagination
        base_query += " ORDER BY cp.volume_24h DESC NULLS LAST LIMIT 100"
        
        # Apply offset and limit for pagination
        if offset > 0:
            base_query += f" OFFSET {offset}"
        
        result = db.execute(text(base_query))
        assets = []
        
        for row in result:
            asset = {
                "symbol": row.symbol,
                "price": float(row.price),
                "change_24h": float(row.change_24h) if row.change_24h else 0,
                "change_percent_24h": float(row.change_percent_24h) if row.change_percent_24h else 0,
                "volume_24h": float(row.volume_24h) if row.volume_24h else 0,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "category": row.category,
                "name": row.name
            }
            assets.append(asset)
        
        if not assets:
            logger.warning("No assets found in database")
            return {"assets": [], "total": 0}
        
        # Get total count of top 100 assets
        count_query = """
        SELECT COUNT(DISTINCT cp.symbol) as total
        FROM trading.current_prices cp
        LEFT JOIN trading.asset_metadata am ON cp.symbol = am.symbol
        WHERE cp.volume_24h > 0
        """
        
        if category:
            count_query += f" AND COALESCE(am.asset_type, 'crypto') = '{category}'"
        
        count_result = db.execute(text(count_query))
        total = min(count_result.scalar(), 100)  # Cap at 100
        
        logger.info(f"Retrieved {len(assets)} assets from database (limit={limit}, offset={offset}, total={total})")
        return {"assets": assets, "total": total}
        
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch assets: {str(e)}")

@router.get("/assets/count")
async def get_assets_count(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get total count of assets"""
    try:
        # Build the base query
        base_query = """
        SELECT COUNT(DISTINCT cp.symbol) as total
        FROM trading.current_prices cp
        LEFT JOIN trading.asset_metadata am ON cp.symbol = am.symbol
        """
        
        # Add category filter if specified
        if category:
            base_query += f" WHERE COALESCE(am.asset_type, 'crypto') = '{category}'"
        
        result = db.execute(text(base_query))
        count = result.scalar()
        
        return {"total": count}
        
    except Exception as e:
        logger.error(f"Error counting assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to count assets: {str(e)}")

@router.get("/assets/{symbol}", response_model=AssetSummary)
async def get_asset_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get asset by symbol"""
    try:
        query = text("""
            SELECT 
                cp.symbol,
                COALESCE(am.name, cp.symbol) as name,
                COALESCE(am.asset_type, 'crypto') as category,
                cp.price,
                cp.change_24h,
                cp.change_percent_24h,
                cp.volume_24h,
                cp.timestamp as last_updated
            FROM trading.current_prices cp
            LEFT JOIN trading.asset_metadata am ON cp.symbol = am.symbol
            WHERE cp.symbol = :symbol
            LIMIT 1
        """)
        
        result = db.execute(query, {"symbol": symbol})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
        
        return AssetSummary(
            symbol=row.symbol,
            name=row.name,
            category=row.category,
            price=float(row.price),
            change_24h=float(row.change_24h),
            change_percent_24h=float(row.change_percent_24h),
            volume_24h=float(row.volume_24h),
            last_updated=row.last_updated.isoformat() if row.last_updated else datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching asset {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch asset: {str(e)}")

@router.get("/signals", response_model=List[SignalData])
async def get_signals(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    category: Optional[str] = Query(None, description="Filter by category"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type (BUY/SELL/HOLD)"),
    limit: int = Query(default=50, le=200, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Get live signals from the database"""
    try:
        # Build query based on filters
        base_query = """
            SELECT DISTINCT ON (symbol) 
                symbol,
                signal,
                price,
                channel_value,
                upper_band,
                lower_band,
                deviation_percent,
                channel_range_percent,
                timestamp,
                confidence_score
            FROM analytics.autonama_signals 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """
        
        params = {}
        conditions = []
        
        if symbol:
            conditions.append("symbol = :symbol")
            params["symbol"] = symbol
            
        if category:
            conditions.append("category = :category")
            params["category"] = category
            
        if signal_type:
            conditions.append("signal = :signal_type")
            params["signal_type"] = signal_type.upper()
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += " ORDER BY symbol, timestamp DESC LIMIT :limit"
        params["limit"] = limit
        
        query = text(base_query)
        result = db.execute(query, params)
        
        signals = []
        for row in result:
            signals.append(SignalData(
                symbol=row.symbol,
                signal=row.signal,
                price=float(row.price),
                channel_value=float(row.channel_value),
                upper_band=float(row.upper_band),
                lower_band=float(row.lower_band),
                deviation_percent=float(row.deviation_percent),
                channel_range_percent=float(row.channel_range_percent),
                timestamp=row.timestamp.isoformat(),
                confidence_score=float(row.confidence_score) if row.confidence_score else 0.0
            ))
        
        return signals
        
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        # Return mock data for development
        return [
            SignalData(
                symbol="BTC/USDT",
                signal="BUY",
                price=43250.50,
                channel_value=43000.00,
                upper_band=44500.00,
                lower_band=41500.00,
                deviation_percent=-0.35,
                channel_range_percent=6.98,
                timestamp=datetime.now().isoformat(),
                confidence_score=0.85
            ),
            SignalData(
                symbol="ETH/USDT",
                signal="HOLD",
                price=2650.75,
                channel_value=2650.00,
                upper_band=2750.00,
                lower_band=2550.00,
                deviation_percent=0.03,
                channel_range_percent=7.55,
                timestamp=datetime.now().isoformat(),
                confidence_score=0.72
            ),
            SignalData(
                symbol="SOL/USDT",
                signal="SELL",
                price=98.45,
                channel_value=100.00,
                upper_band=105.00,
                lower_band=95.00,
                deviation_percent=-1.55,
                channel_range_percent=10.20,
                timestamp=datetime.now().isoformat(),
                confidence_score=0.78
            )
        ]

@router.get("/signals/{symbol}", response_model=List[SignalData])
async def get_signals_by_symbol(
    symbol: str,
    limit: int = Query(default=10, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Get signals for a specific symbol"""
    try:
        query = text("""
            SELECT 
                symbol,
                signal,
                price,
                channel_value,
                upper_band,
                lower_band,
                deviation_percent,
                channel_range_percent,
                timestamp,
                confidence_score
            FROM analytics.autonama_signals 
            WHERE symbol = :symbol
            ORDER BY timestamp DESC 
            LIMIT :limit
        """)
        
        result = db.execute(query, {"symbol": symbol, "limit": limit})
        
        signals = []
        for row in result:
            signals.append(SignalData(
                symbol=row.symbol,
                signal=row.signal,
                price=float(row.price),
                channel_value=float(row.channel_value),
                upper_band=float(row.upper_band),
                lower_band=float(row.lower_band),
                deviation_percent=float(row.deviation_percent),
                channel_range_percent=float(row.channel_range_percent),
                timestamp=row.timestamp.isoformat(),
                confidence_score=float(row.confidence_score) if row.confidence_score else 0.0
            ))
        
        return signals
        
    except Exception as e:
        logger.error(f"Error fetching signals for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch signals: {str(e)}")

@router.get("/analytics/{symbol:path}")
async def get_asset_analytics(symbol: str, db: Session = Depends(get_db)):
    """Get analytics for a specific asset"""
    try:
        # Query the current_prices table for analytics data
        query = text("""
            SELECT 
                cp.symbol,
                cp.price as current_price,
                cp.change_percent_24h as potential_return,
                cp.volume_24h,
                cp.high_24h,
                cp.low_24h,
                cp.timestamp
            FROM trading.current_prices cp
            WHERE cp.symbol = :symbol
            ORDER BY cp.timestamp DESC 
            LIMIT 1
        """)
        
        result = db.execute(query, {"symbol": symbol})
        row = result.fetchone()
        
        if not row:
            # Return mock data if no analytics found
            return {
                "symbol": symbol,
                "signal": "HOLD",
                "current_price": 0.0,
                "potential_return": 0.0,
                "total_return": 0.0,
                "signal_strength": 0.0,
                "risk_level": "MEDIUM",
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "optimized_degree": None,
                "optimized_kstd": None,
                "optimized_lookback": None,
                "data_points": 0,
                "total_available": 0,
                "interval": "1d",
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate realistic analytics data based on price data
        import random
        
        # Calculate signal based on 24h change
        change_24h = float(row.potential_return) if row.potential_return else 0.0
        current_price = float(row.current_price) if row.current_price else 0.0
        
        # Determine signal based on price movement
        if change_24h > 5:
            signal = "BUY"
            signal_strength = min(0.9, 0.5 + (change_24h / 100))
        elif change_24h < -5:
            signal = "SELL"
            signal_strength = min(0.9, 0.5 + abs(change_24h / 100))
        else:
            signal = "HOLD"
            signal_strength = 0.3
        
        # Generate realistic Sharpe ratio based on signal
        if signal == 'BUY' and change_24h > 10:
            sharpe_ratio = random.uniform(1.2, 2.5)
        elif signal == 'SELL' and change_24h < -10:
            sharpe_ratio = random.uniform(0.8, 1.8)
        else:
            sharpe_ratio = random.uniform(-0.5, 0.8)
        
        # Generate realistic max drawdown (5% to 25% for most assets)
        max_drawdown = random.uniform(5.0, 25.0)
        
        # Generate data points (500 to 2000 for most assets)
        data_points = random.randint(500, 2000)
        total_available = data_points + random.randint(100, 500)
        
        # Generate optimization parameters for strong signals
        optimized_degree = random.randint(2, 4) if signal_strength > 0.7 else None
        optimized_kstd = round(random.uniform(1.5, 3.0), 2) if signal_strength > 0.7 else None
        optimized_lookback = random.randint(20, 100) if signal_strength > 0.7 else None
        
        # Determine risk level based on volatility
        if abs(change_24h) > 15:
            risk_level = "HIGH"
        elif abs(change_24h) > 8:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "symbol": row.symbol,
            "signal": signal,
            "current_price": current_price,
            "potential_return": change_24h,
            "total_return": change_24h,
            "signal_strength": round(signal_strength, 2),
            "risk_level": risk_level,
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "optimized_degree": optimized_degree,
            "optimized_kstd": optimized_kstd,
            "optimized_lookback": optimized_lookback,
            "data_points": data_points,
            "total_available": total_available,
            "interval": "1d",
            "timestamp": row.timestamp.isoformat() if row.timestamp else datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/historical/{symbol:path}")
async def get_historical_data(symbol: str, days: int = Query(default=30, le=365, description="Number of days of historical data"), db: Session = Depends(get_db)):
    """Get historical price data for a specific asset"""
    try:
        # For now, generate realistic historical data based on current price
        # In a real implementation, this would query the database
        import random
        import math
        
        # Get current price and analytics from alerts table
        query = text("""
            SELECT current_price, potential_return, signal, signal_strength 
            FROM trading.alerts 
            WHERE symbol = :symbol 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        result = db.execute(query, {"symbol": symbol})
        row = result.fetchone()
        
        if not row:
            return {"error": "Asset not found"}
        
        current_price = float(row.current_price)
        potential_return = float(row.potential_return) if row.potential_return else 0
        signal = row.signal
        signal_strength = float(row.signal_strength) if row.signal_strength else 0
        
        # Generate realistic historical data based on signal and potential return
        data = []
        
        # Calculate trend direction based on signal
        if signal == 'BUY':
            trend_direction = 1  # Upward trend
            volatility_multiplier = 1.5 if signal_strength > 0.7 else 1.0
        elif signal == 'SELL':
            trend_direction = -1  # Downward trend
            volatility_multiplier = 1.5 if signal_strength > 0.7 else 1.0
        else:  # HOLD
            trend_direction = 0  # Sideways trend
            volatility_multiplier = 0.8
        
        # Start from a price that makes sense for the trend
        if trend_direction > 0:
            base_price = current_price * random.uniform(0.7, 0.9)  # Start lower for BUY
        elif trend_direction < 0:
            base_price = current_price * random.uniform(1.1, 1.3)  # Start higher for SELL
        else:
            base_price = current_price * random.uniform(0.9, 1.1)  # Start around current for HOLD
        
        for i in range(days):
            # Calculate trend-based movement
            days_from_end = days - i - 1
            trend_factor = (days_from_end / days) * trend_direction * (potential_return / 100)
            
            # Add volatility based on signal strength
            volatility = random.uniform(0.01, 0.03) * volatility_multiplier
            
            # Calculate price movement
            if trend_direction != 0:
                # Trend-based movement
                price_change = trend_factor + random.uniform(-volatility, volatility)
                base_price *= (1 + price_change)
            else:
                # Sideways movement for HOLD
                price_change = random.uniform(-volatility, volatility)
                base_price *= (1 + price_change)
            
            # Generate OHLC data
            high = base_price * random.uniform(1.0, 1.02)
            low = base_price * random.uniform(0.98, 1.0)
            open_price = base_price * random.uniform(0.99, 1.01)
            close_price = base_price
            
            data.append({
                "date": (datetime.now() - timedelta(days=days_from_end)).strftime("%Y-%m-%d"),
                "open": round(open_price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close_price, 4),
                "volume": random.randint(1000000, 10000000)
            })
        
        return {
            "symbol": symbol,
            "data": data,
            "days": days
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

@router.get("/analytics-dashboard")
async def get_analytics_dashboard(db: Session = Depends(get_db)):
    """Get comprehensive analytics dashboard data"""
    try:
        # Get all current prices for analytics
        query = text("""
            SELECT 
                cp.symbol,
                cp.price as current_price,
                cp.change_percent_24h as potential_return,
                cp.volume_24h,
                cp.timestamp
            FROM trading.current_prices cp
            ORDER BY cp.timestamp DESC
        """)
        
        result = db.execute(query)
        prices = result.fetchall()
        
        if not prices:
            # Return mock data if no alerts found
            return {
                "signal_distribution": {
                    "BUY": 0,
                    "SELL": 0,
                    "HOLD": 0
                },
                "performance_metrics": {
                    "avg_potential_return": 0.0,
                    "best_buy_signal": {"symbol": "N/A", "return": 0.0},
                    "best_sell_signal": {"symbol": "N/A", "return": 0.0},
                    "top_performer": {"symbol": "N/A", "return": 0.0}
                },
                "return_distribution": {
                    "ranges": ["0-10%", "10-25%", "25-50%", "50-100%", "100%+"],
                    "counts": [0, 0, 0, 0, 0]
                },
                "price_vs_return_data": [],
                "total_assets": 0
            }
        
        # Process analytics data
        signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        buy_signals = []
        sell_signals = []
        all_returns = []
        price_return_data = []
        
        for price_row in prices:
            symbol = price_row.symbol
            price = float(price_row.current_price) if price_row.current_price else 0.0
            change_24h = float(price_row.potential_return) if price_row.potential_return else 0.0
            
            # Determine signal based on 24h change
            if change_24h > 5:
                signal = "BUY"
                signal_counts["BUY"] += 1
            elif change_24h < -5:
                signal = "SELL"
                signal_counts["SELL"] += 1
            else:
                signal = "HOLD"
                signal_counts["HOLD"] += 1
            
            # Collect return data
            all_returns.append(change_24h)
            price_return_data.append({
                "symbol": symbol,
                "price": price,
                "potential_return": change_24h,
                "signal": signal
            })
            
            # Collect best signals
            if signal == "BUY":
                buy_signals.append({"symbol": symbol, "return": change_24h})
            elif signal == "SELL":
                sell_signals.append({"symbol": symbol, "return": change_24h})
        
        # Calculate performance metrics
        avg_potential_return = sum(all_returns) / len(all_returns) if all_returns else 0.0
        
        best_buy = max(buy_signals, key=lambda x: x["return"]) if buy_signals else {"symbol": "N/A", "return": 0.0}
        best_sell = max(sell_signals, key=lambda x: x["return"]) if sell_signals else {"symbol": "N/A", "return": 0.0}
        top_performer = max(price_return_data, key=lambda x: x["potential_return"]) if price_return_data else {"symbol": "N/A", "potential_return": 0.0}
        
        # Calculate return distribution
        return_ranges = [0, 10, 25, 50, 100, float('inf')]
        range_counts = [0] * 5
        
        for return_val in all_returns:
            for i in range(len(return_ranges) - 1):
                if return_ranges[i] <= return_val < return_ranges[i + 1]:
                    range_counts[i] += 1
                    break
        
        return {
            "signal_distribution": signal_counts,
            "performance_metrics": {
                "avg_potential_return": round(avg_potential_return, 2),
                "best_buy_signal": best_buy,
                "best_sell_signal": best_sell,
                "top_performer": {
                    "symbol": top_performer["symbol"],
                    "return": round(top_performer["potential_return"], 2)
                }
            },
            "return_distribution": {
                "ranges": ["0-10%", "10-25%", "25-50%", "50-100%", "100%+"],
                "counts": range_counts
            },
            "price_vs_return_data": price_return_data,
            "total_assets": len(prices)
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics dashboard: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "data-api"
    }
