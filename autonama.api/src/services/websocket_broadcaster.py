"""
WebSocket Broadcasting Service

This service handles periodic broadcasting of updates to WebSocket clients.
It integrates with the existing data pipeline to provide real-time updates.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.database import get_db
from src.api.v1.endpoints.websocket import manager

logger = logging.getLogger(__name__)

class WebSocketBroadcaster:
    def __init__(self):
        self.is_running = False
        self.broadcast_tasks = []

    async def start_broadcasting(self):
        """Start all broadcasting tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting WebSocket broadcasting service")
        
        # Start different broadcast tasks
        self.broadcast_tasks = [
            asyncio.create_task(self.broadcast_signals_periodically()),
            asyncio.create_task(self.broadcast_market_data_periodically()),
            asyncio.create_task(self.broadcast_optimization_updates_periodically())
        ]
        
        # Wait for all tasks
        await asyncio.gather(*self.broadcast_tasks, return_exceptions=True)

    async def stop_broadcasting(self):
        """Stop all broadcasting tasks"""
        self.is_running = False
        
        for task in self.broadcast_tasks:
            task.cancel()
        
        logger.info("Stopped WebSocket broadcasting service")

    async def broadcast_signals_periodically(self):
        """Broadcast signal updates every 15 seconds"""
        while self.is_running:
            try:
                if manager.signal_subscribers:
                    db = next(get_db())
                    signals_data = await self.get_latest_signals(db)
                    
                    if signals_data:
                        await manager.broadcast_signals({
                            "signals": signals_data,
                            "timestamp": datetime.now(),
                            "count": len(signals_data)
                        })
                        logger.debug(f"Broadcasted {len(signals_data)} signals to {len(manager.signal_subscribers)} clients")
                
                await asyncio.sleep(15)  # Broadcast every 15 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting signals: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def broadcast_market_data_periodically(self):
        """Broadcast market data updates every 30 seconds"""
        while self.is_running:
            try:
                if manager.market_data_subscribers:
                    db = next(get_db())
                    market_data = await self.get_market_overview_data(db)
                    
                    if market_data:
                        await manager.broadcast_market_data(market_data)
                        logger.debug(f"Broadcasted market data to {len(manager.market_data_subscribers)} clients")
                
                await asyncio.sleep(30)  # Broadcast every 30 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting market data: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def broadcast_optimization_updates_periodically(self):
        """Broadcast optimization updates every 10 seconds"""
        while self.is_running:
            try:
                if manager.optimization_subscribers:
                    # Check for active optimization tasks
                    optimization_data = await self.get_optimization_status()
                    
                    if optimization_data:
                        await manager.broadcast_optimization_update(optimization_data)
                        logger.debug(f"Broadcasted optimization updates to {len(manager.optimization_subscribers)} clients")
                
                await asyncio.sleep(10)  # Broadcast every 10 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting optimization updates: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    async def get_latest_signals(self, db: Session) -> List[Dict[str, Any]]:
        """Get latest signals from database"""
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
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC 
                LIMIT 50
            """)
            
            result = db.execute(query)
            signals = []
            
            for row in result:
                signals.append({
                    "symbol": row.symbol,
                    "signal": row.signal,
                    "price": float(row.price),
                    "channel_value": float(row.channel_value),
                    "upper_band": float(row.upper_band),
                    "lower_band": float(row.lower_band),
                    "deviation_percent": float(row.deviation_percent),
                    "channel_range_percent": float(row.channel_range_percent),
                    "timestamp": row.timestamp,
                    "confidence_score": float(row.confidence_score) if row.confidence_score else 0.0
                })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error fetching latest signals: {e}")
            return []

    async def get_market_overview_data(self, db: Session) -> Dict[str, Any]:
        """Get market overview data"""
        try:
            # Get latest prices
            price_query = text("""
                SELECT DISTINCT ON (symbol)
                    symbol,
                    close as current_price,
                    volume,
                    timestamp
                FROM trading.ohlc_data
                ORDER BY symbol, timestamp DESC
                LIMIT 20
            """)
            
            price_result = db.execute(price_query)
            market_data = []
            
            for row in price_result:
                market_data.append({
                    "symbol": row.symbol,
                    "current_price": float(row.close),
                    "volume": float(row.volume),
                    "timestamp": row.timestamp
                })
            
            # Get signal summary
            signal_query = text("""
                SELECT 
                    signal,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM analytics.autonama_signals 
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                GROUP BY signal
            """)
            
            signal_result = db.execute(signal_query)
            signals_summary = {}
            
            for row in signal_result:
                signals_summary[row.signal] = {
                    "count": row.count,
                    "avg_confidence": float(row.avg_confidence) if row.avg_confidence else 0.0
                }
            
            return {
                "market_data": market_data,
                "signals_summary": signals_summary,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return {
                "market_data": [],
                "signals_summary": {},
                "timestamp": datetime.now()
            }

    async def get_optimization_status(self) -> Dict[str, Any]:
        """Get optimization status updates"""
        try:
            # This would integrate with Celery to get real optimization status
            # For now, return a placeholder structure
            return {
                "active_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching optimization status: {e}")
            return {}

    async def broadcast_immediate_signal_update(self, signal_data: Dict[str, Any]):
        """Broadcast immediate signal update (called by signal generation tasks)"""
        try:
            await manager.broadcast_signals({
                "type": "new_signal",
                "signal": signal_data,
                "timestamp": datetime.now()
            })
            logger.info(f"Broadcasted immediate signal update for {signal_data.get('symbol')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting immediate signal: {e}")

    async def broadcast_immediate_optimization_update(self, optimization_data: Dict[str, Any]):
        """Broadcast immediate optimization update (called by optimization tasks)"""
        try:
            await manager.broadcast_optimization_update({
                "type": "optimization_progress",
                "data": optimization_data,
                "timestamp": datetime.now()
            })
            logger.info(f"Broadcasted optimization update for task {optimization_data.get('task_id')}")
            
        except Exception as e:
            logger.error(f"Error broadcasting optimization update: {e}")

# Global broadcaster instance
broadcaster = WebSocketBroadcaster()

# Functions to be called by other services
async def start_websocket_broadcasting():
    """Start the WebSocket broadcasting service"""
    await broadcaster.start_broadcasting()

async def stop_websocket_broadcasting():
    """Stop the WebSocket broadcasting service"""
    await broadcaster.stop_broadcasting()

async def broadcast_new_signal(signal_data: Dict[str, Any]):
    """Broadcast a new signal immediately"""
    await broadcaster.broadcast_immediate_signal_update(signal_data)

async def broadcast_optimization_progress(optimization_data: Dict[str, Any]):
    """Broadcast optimization progress immediately"""
    await broadcaster.broadcast_immediate_optimization_update(optimization_data)