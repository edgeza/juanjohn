"""
Asset Models

Data models for the multi-asset trading system.
Defines asset types, configurations, and data structures.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class AssetType(Enum):
    """Asset type enumeration"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    COMMODITY = "commodity"

class Exchange(Enum):
    """Exchange enumeration"""
    BINANCE = "binance"
    NASDAQ = "nasdaq"
    NYSE = "nyse"
    FOREX = "forex"
    COMMODITY = "commodity"
    CCXT = "ccxt"

@dataclass
class AssetConfig:
    """Configuration for an asset"""
    symbol: str
    asset_type: AssetType
    exchange: Exchange
    priority: int = 1
    enabled: bool = True
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if isinstance(self.asset_type, str):
            self.asset_type = AssetType(self.asset_type)
        if isinstance(self.exchange, str):
            self.exchange = Exchange(self.exchange)

class OHLCModel(BaseModel):
    """OHLC data model"""
    symbol: str
    timestamp: datetime
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AssetMetadata(BaseModel):
    """Asset metadata model"""
    symbol: str
    name: Optional[str] = None
    asset_type: AssetType
    exchange: Exchange
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    precision: Optional[int] = None
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AssetPrice(BaseModel):
    """Asset price model - matches trading.current_prices schema"""
    symbol: str
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    spread: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    change_24h: Optional[Decimal] = None
    change_percent_24h: Optional[Decimal] = None
    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "unknown"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class ProcessorResult(BaseModel):
    """Result from a data processor"""
    success: bool
    symbol: str
    processor: str
    data_points: int = 0
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProcessorStats(BaseModel):
    """Statistics from a data processor"""
    processor_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    rate_limit_hits: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

class DataIngestionResult(BaseModel):
    """Result from data ingestion process"""
    task_id: str
    asset_configs: List[AssetConfig]
    results: Dict[str, ProcessorResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_assets: int = 0
    successful_assets: int = 0
    failed_assets: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_assets == 0:
            return 0.0
        return self.successful_assets / self.total_assets
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds"""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

# Default asset configurations
DEFAULT_CRYPTO_ASSETS = [
    AssetConfig("BTC/USDT", AssetType.CRYPTO, Exchange.BINANCE, priority=1),
    AssetConfig("ETH/USDT", AssetType.CRYPTO, Exchange.BINANCE, priority=1),
    AssetConfig("ADA/USDT", AssetType.CRYPTO, Exchange.BINANCE, priority=2),
    AssetConfig("BNB/USDT", AssetType.CRYPTO, Exchange.BINANCE, priority=2),
    AssetConfig("SOL/USDT", AssetType.CRYPTO, Exchange.BINANCE, priority=2),
]

DEFAULT_STOCK_ASSETS = [
    AssetConfig("AAPL", AssetType.STOCK, Exchange.NASDAQ, priority=1),
    AssetConfig("GOOGL", AssetType.STOCK, Exchange.NASDAQ, priority=1),
    AssetConfig("MSFT", AssetType.STOCK, Exchange.NASDAQ, priority=1),
    AssetConfig("TSLA", AssetType.STOCK, Exchange.NASDAQ, priority=2),
    AssetConfig("AMZN", AssetType.STOCK, Exchange.NASDAQ, priority=2),
]

DEFAULT_FOREX_ASSETS = [
    AssetConfig("EUR/USD", AssetType.FOREX, Exchange.FOREX, priority=1),
    AssetConfig("GBP/USD", AssetType.FOREX, Exchange.FOREX, priority=1),
    AssetConfig("USD/JPY", AssetType.FOREX, Exchange.FOREX, priority=2),
    AssetConfig("AUD/USD", AssetType.FOREX, Exchange.FOREX, priority=2),
    AssetConfig("USD/CAD", AssetType.FOREX, Exchange.FOREX, priority=2),
]

DEFAULT_COMMODITY_ASSETS = [
    AssetConfig("GOLD", AssetType.COMMODITY, Exchange.COMMODITY, priority=1),
    AssetConfig("OIL", AssetType.COMMODITY, Exchange.COMMODITY, priority=1),
    AssetConfig("SILVER", AssetType.COMMODITY, Exchange.COMMODITY, priority=2),
    AssetConfig("COPPER", AssetType.COMMODITY, Exchange.COMMODITY, priority=2),
    AssetConfig("PLATINUM", AssetType.COMMODITY, Exchange.COMMODITY, priority=3),
]

def get_default_assets(asset_type: AssetType) -> List[AssetConfig]:
    """Get default assets for a given type"""
    defaults = {
        AssetType.CRYPTO: DEFAULT_CRYPTO_ASSETS,
        AssetType.STOCK: DEFAULT_STOCK_ASSETS,
        AssetType.FOREX: DEFAULT_FOREX_ASSETS,
        AssetType.COMMODITY: DEFAULT_COMMODITY_ASSETS,
    }
    return defaults.get(asset_type, [])

def get_all_default_assets() -> List[AssetConfig]:
    """Get all default assets"""
    all_assets = []
    for asset_type in AssetType:
        all_assets.extend(get_default_assets(asset_type))
    return all_assets

# Utility functions for creating models from dictionary data
def create_asset_from_dict(data: Dict[str, Any]) -> AssetMetadata:
    """Create AssetMetadata from dictionary data"""
    # Convert string enums to proper enum types
    if isinstance(data.get('asset_type'), str):
        data['asset_type'] = AssetType(data['asset_type'])
    if isinstance(data.get('exchange'), str):
        data['exchange'] = Exchange(data['exchange'])
    
    return AssetMetadata(**data)

def create_price_from_dict(data: Dict[str, Any]) -> AssetPrice:
    """Create AssetPrice from dictionary data"""
    # Convert numeric strings to Decimal
    decimal_fields = ['price', 'bid', 'ask', 'spread', 'volume_24h', 
                     'change_24h', 'change_percent_24h', 'high_24h', 'low_24h']
    
    for field in decimal_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], Decimal):
                data[field] = Decimal(str(data[field]))
    
    # Convert timestamp if it's a string
    if isinstance(data.get('timestamp'), str):
        data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    
    return AssetPrice(**data)
