"""
WebSocket endpoints for real-time data streaming

This module provides WebSocket connections for:
- Real-time market data updates
- Live signal notifications
- Optimization progress updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from src.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.signal_subscribers: List[WebSocket] = []
        self.market_data_subscribers: List[WebSocket] = []
        self.optimization_subscribers: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, subscription_type: str = "general"):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if subscription_type == "signals":
            self.signal_subscribers.append(websocket)
        elif subscription_type == "market_data":
            self.market_data_subscribers.append(websocket)
        elif subscription_type == "optimization":
            self.optimization_subscribers.append(websocket)
        
        logger.info(f"WebSocket connected: {subscription_type}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.signal_subscribers:
            self.signal_subscribers.remove(websocket)
        if websocket in self.market_data_subscribers:
            self.market_data_subscribers.remove(websocket)
        if websocket in self.optimization_subscribers:
            self.optimization_subscribers.remove(websocket)
        
        logger.info("WebSocket disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast_to_subscribers(self, message: Dict[str, Any], subscribers: List[WebSocket]):
        if not subscribers:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = []
        
        for connection in subscribers:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_signals(self, signals_data: Dict[str, Any]):
        await self.broadcast_to_subscribers(
            {"type": "signals_update", "data": signals_data},
            self.signal_subscribers
        )

    async def broadcast_market_data(self, market_data: Dict[str, Any]):
        await self.broadcast_to_subscribers(
            {"type": "market_data_update", "data": market_data},
            self.market_data_subscribers
        )

    async def broadcast_optimization_update(self, optimization_data: Dict[str, Any]):
        await self.broadcast_to_subscribers(
            {"type": "optimization_update", "data": optimization_data},
            self.optimization_subscribers
        )

manager = ConnectionManager()

@router.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """WebSocket endpoint for real-time signal updates"""
    await manager.connect(websocket, "signals")
    
    try:
        # Send initial signals data or test message if database is not ready
        try:
            db = next(get_db())
            initial_signals = await get_latest_signals(db)
            await manager.send_personal_message(
                json.dumps({"type": "initial_signals", "data": initial_signals}, default=str),
                websocket
            )
        except Exception as e:
            # Send test message if database is not ready
            logger.info(f"Database not ready, sending test message: {e}")
            await manager.send_personal_message(
                json.dumps({
                    "type": "test_message", 
                    "data": {
                        "message": "WebSocket connection established successfully",
                        "timestamp": datetime.now().isoformat(),
                        "status": "connected"
                    }
                }, default=str),
                websocket
            )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (like subscription preferences)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_category":
                    category = message.get("category")
                    # Handle category-specific subscriptions
                    logger.info(f"Client subscribed to category: {category}")
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in signals WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@router.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data updates"""
    await manager.connect(websocket, "market_data")
    
    try:
        # Send initial market data
        db = next(get_db())
        initial_data = await get_market_overview_data(db)
        await manager.send_personal_message(
            json.dumps({"type": "initial_market_data", "data": initial_data}, default=str),
            websocket
        )
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_symbols":
                    symbols = message.get("symbols", [])
                    logger.info(f"Client subscribed to symbols: {symbols}")
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in market data WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@router.websocket("/ws/optimization")
async def websocket_optimization(websocket: WebSocket):
    """WebSocket endpoint for optimization progress updates"""
    await manager.connect(websocket, "optimization")
    
    try:
        # Keep connection alive for optimization updates
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_task":
                    task_id = message.get("task_id")
                    logger.info(f"Client subscribed to optimization task: {task_id}")
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in optimization WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

# Background tasks for broadcasting updates
async def get_latest_signals(db: Session) -> List[Dict[str, Any]]:
    """Get latest signals for WebSocket broadcast"""
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
            ORDER BY timestamp DESC 
            LIMIT 20
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

async def get_market_overview_data(db: Session) -> Dict[str, Any]:
    """Get market overview data for WebSocket broadcast"""
    try:
        # Get latest prices
        query = text("""
            SELECT DISTINCT ON (symbol)
                symbol,
                close as current_price,
                volume,
                timestamp
            FROM trading.ohlc_data
            ORDER BY symbol, timestamp DESC
            LIMIT 20
        """)
        
        result = db.execute(query)
        market_data = []
        
        for row in result:
            market_data.append({
                "symbol": row.symbol,
                "current_price": float(row.close),
                "volume": float(row.volume),
                "timestamp": row.timestamp
            })
        
        return {
            "market_data": market_data,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        return {"market_data": [], "timestamp": datetime.now()}

# Function to be called by background tasks to broadcast updates
async def broadcast_signal_update(signals_data: Dict[str, Any]):
    """Broadcast signal updates to all connected clients"""
    await manager.broadcast_signals(signals_data)

async def broadcast_market_update(market_data: Dict[str, Any]):
    """Broadcast market data updates to all connected clients"""
    await manager.broadcast_market_data(market_data)

async def broadcast_optimization_progress(optimization_data: Dict[str, Any]):
    """Broadcast optimization progress to all connected clients"""
    await manager.broadcast_optimization_update(optimization_data)

# Health check for WebSocket connections
@router.get("/ws/health")
async def websocket_health():
    """Health check for WebSocket connections"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "signal_subscribers": len(manager.signal_subscribers),
        "market_data_subscribers": len(manager.market_data_subscribers),
        "optimization_subscribers": len(manager.optimization_subscribers),
        "timestamp": datetime.now()
    }