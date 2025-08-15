"""
Asset and User Models for Autonama API
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from enum import Enum
from src.core.database import Base

class User(Base):
    """User model for authentication and alerts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Should be hashed in production
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Access and billing
    is_admin = Column(Boolean, default=False, nullable=False)
    has_access = Column(Boolean, default=False, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_status = Column(String(50), nullable=True)
    stripe_current_period_end = Column(DateTime, nullable=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user")

class Alert(Base):
    """Price alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    condition = Column(String(20), nullable=False)  # above, below, crosses_above, crosses_below
    price = Column(Float, nullable=False)
    timeframe = Column(String(10), default="1h")
    enabled = Column(Boolean, default=True)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alerts")

class AssetConfig(Base):
    """Asset configuration model"""
    __tablename__ = "asset_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # crypto, forex, stock, commodity
    enabled = Column(Boolean, default=True)
    data_source = Column(String(50), default="binance")  # binance, twelvedata, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssetType(Enum):
    """Asset type enumeration"""
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"
    COMMODITY = "commodity"

# Pydantic models for API responses
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AssetSummary(BaseModel):
    symbol: str
    name: str
    category: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    last_updated: datetime

class Symbol(BaseModel):
    symbol: str
    name: str
    category: str

class OHLCData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class AssetDetails(BaseModel):
    symbol: str
    name: str
    category: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    ohlc_data: list[OHLCData]
    last_updated: datetime
