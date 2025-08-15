from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    symbol: str
    interval: str
    signal: str
    current_price: float
    potential_return: float
    signal_strength: float
    risk_level: str
    timestamp: Optional[str] = None
    created_at: Optional[str] = None

class AlertSummary(BaseModel):
    total_alerts: int
    buy_signals: int
    sell_signals: int
    hold_signals: int
    avg_potential_return: float
    max_potential_return: float 