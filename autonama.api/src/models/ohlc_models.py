"""
OHLC Data Models

This module defines Pydantic models for OHLC (Open, High, Low, Close) data structures
including candlestick data, volume information, and technical indicators.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class Timeframe(str, Enum):
    """Supported timeframes for OHLC data."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    DAY_3 = "3d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class CandleType(str, Enum):
    """Candlestick pattern types."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"


class DataSource(str, Enum):
    """Data source enumeration."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    TWELVEDATA = "twelvedata"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    CCXT = "ccxt"


class OHLCData(BaseModel):
    """OHLC candlestick data model."""
    symbol: str = Field(..., description="Asset symbol")
    timestamp: datetime = Field(..., description="Candlestick timestamp")
    timeframe: Timeframe = Field(..., description="Timeframe of the candlestick")
    
    # OHLC prices
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price")
    low: Decimal = Field(..., description="Lowest price")
    close: Decimal = Field(..., description="Closing price")
    
    # Volume data
    volume: Decimal = Field(..., description="Trading volume")
    volume_quote: Optional[Decimal] = Field(None, description="Quote volume")
    trades_count: Optional[int] = Field(None, description="Number of trades")
    
    # Additional data
    vwap: Optional[Decimal] = Field(None, description="Volume weighted average price")
    source: DataSource = Field(..., description="Data source")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('open', 'high', 'low', 'close')
    def validate_prices(cls, v):
        """Validate prices are positive."""
        if v <= 0:
            raise ValueError("Prices must be positive")
        return v
    
    @validator('volume')
    def validate_volume(cls, v):
        """Validate volume is non-negative."""
        if v < 0:
            raise ValueError("Volume cannot be negative")
        return v
    
    @validator('trades_count')
    def validate_trades_count(cls, v):
        """Validate trades count is positive."""
        if v is not None and v <= 0:
            raise ValueError("Trades count must be positive")
        return v
    
    @validator('high')
    def validate_high_price(cls, v, values):
        """Validate high is the highest price."""
        if 'open' in values and v < values['open']:
            raise ValueError("High price cannot be lower than open price")
        if 'low' in values and v < values['low']:
            raise ValueError("High price cannot be lower than low price")
        if 'close' in values and v < values['close']:
            raise ValueError("High price cannot be lower than close price")
        return v
    
    @validator('low')
    def validate_low_price(cls, v, values):
        """Validate low is the lowest price."""
        if 'open' in values and v > values['open']:
            raise ValueError("Low price cannot be higher than open price")
        if 'close' in values and v > values['close']:
            raise ValueError("Low price cannot be higher than close price")
        return v
    
    @property
    def price_change(self) -> Decimal:
        """Calculate price change (close - open)."""
        return self.close - self.open
    
    @property
    def price_change_percent(self) -> Decimal:
        """Calculate percentage price change."""
        if self.open == 0:
            return Decimal('0')
        return (self.price_change / self.open) * 100
    
    @property
    def is_bullish(self) -> bool:
        """Check if candlestick is bullish (close > open)."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if candlestick is bearish (close < open)."""
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        """Check if candlestick is a doji (close ≈ open)."""
        body_size = abs(self.close - self.open)
        range_size = self.high - self.low
        return range_size > 0 and (body_size / range_size) < 0.1
    
    @property
    def body_size(self) -> Decimal:
        """Calculate the size of the candlestick body."""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> Decimal:
        """Calculate upper shadow length."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> Decimal:
        """Calculate lower shadow length."""
        return min(self.open, self.close) - self.low
    
    @property
    def range_size(self) -> Decimal:
        """Calculate the total range (high - low)."""
        return self.high - self.low
    
    @property
    def candle_type(self) -> CandleType:
        """Determine the candlestick pattern type."""
        if self.is_doji:
            return CandleType.DOJI
        elif self.is_bullish:
            return CandleType.BULLISH
        else:
            return CandleType.BEARISH
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class OHLCBatch(BaseModel):
    """Batch of OHLC data for bulk operations."""
    symbol: str = Field(..., description="Asset symbol")
    timeframe: Timeframe = Field(..., description="Timeframe")
    data: List[OHLCData] = Field(..., description="List of OHLC data points")
    start_time: datetime = Field(..., description="Start time of the batch")
    end_time: datetime = Field(..., description="End time of the batch")
    source: DataSource = Field(..., description="Data source")
    
    @validator('data')
    def validate_data_not_empty(cls, v):
        """Validate data list is not empty."""
        if not v:
            raise ValueError("OHLC data list cannot be empty")
        return v
    
    @validator('data')
    def validate_data_consistency(cls, v, values):
        """Validate all data points have consistent symbol and timeframe."""
        if not v:
            return v
        
        symbol = values.get('symbol')
        timeframe = values.get('timeframe')
        
        for ohlc in v:
            if ohlc.symbol != symbol:
                raise ValueError(f"Inconsistent symbol in batch: expected {symbol}, got {ohlc.symbol}")
            if ohlc.timeframe != timeframe:
                raise ValueError(f"Inconsistent timeframe in batch: expected {timeframe}, got {ohlc.timeframe}")
        
        return v
    
    @property
    def count(self) -> int:
        """Get number of data points in batch."""
        return len(self.data)
    
    @property
    def duration(self) -> timedelta:
        """Get duration of the batch."""
        return self.end_time - self.start_time
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class OHLCQuery(BaseModel):
    """OHLC data query parameters."""
    symbol: str = Field(..., description="Asset symbol")
    timeframe: Timeframe = Field(..., description="Timeframe")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    limit: Optional[int] = Field(1000, description="Maximum number of records")
    offset: Optional[int] = Field(0, description="Number of records to skip")
    source: Optional[DataSource] = Field(None, description="Filter by data source")
    
    @validator('limit')
    def validate_limit(cls, v):
        """Validate limit is reasonable."""
        if v is not None and (v <= 0 or v > 10000):
            raise ValueError("Limit must be between 1 and 10000")
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        """Validate offset is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Offset cannot be negative")
        return v
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        """Validate end_time is after start_time."""
        start_time = values.get('start_time')
        if start_time and v and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class OHLCResponse(BaseModel):
    """OHLC data response model."""
    symbol: str = Field(..., description="Asset symbol")
    timeframe: Timeframe = Field(..., description="Timeframe")
    data: List[OHLCData] = Field(..., description="OHLC data points")
    total_count: int = Field(..., description="Total number of available records")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(..., description="Number of records per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    query_time: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def count(self) -> int:
        """Get number of data points returned."""
        return len(self.data)
    
    @property
    def start_time(self) -> Optional[datetime]:
        """Get start time of returned data."""
        return min(d.timestamp for d in self.data) if self.data else None
    
    @property
    def end_time(self) -> Optional[datetime]:
        """Get end time of returned data."""
        return max(d.timestamp for d in self.data) if self.data else None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class OHLCStats(BaseModel):
    """OHLC statistics model."""
    symbol: str = Field(..., description="Asset symbol")
    timeframe: Timeframe = Field(..., description="Timeframe")
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")
    
    # Price statistics
    highest_high: Decimal = Field(..., description="Highest high in period")
    lowest_low: Decimal = Field(..., description="Lowest low in period")
    period_open: Decimal = Field(..., description="Opening price of period")
    period_close: Decimal = Field(..., description="Closing price of period")
    price_change: Decimal = Field(..., description="Total price change")
    price_change_percent: Decimal = Field(..., description="Total percentage change")
    
    # Volume statistics
    total_volume: Decimal = Field(..., description="Total volume in period")
    average_volume: Decimal = Field(..., description="Average volume per candle")
    max_volume: Decimal = Field(..., description="Maximum volume in single candle")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    
    # Volatility statistics
    volatility: Decimal = Field(..., description="Price volatility")
    average_range: Decimal = Field(..., description="Average high-low range")
    max_range: Decimal = Field(..., description="Maximum high-low range")
    
    # Candlestick statistics
    bullish_candles: int = Field(..., description="Number of bullish candles")
    bearish_candles: int = Field(..., description="Number of bearish candles")
    doji_candles: int = Field(..., description="Number of doji candles")
    total_candles: int = Field(..., description="Total number of candles")
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def bullish_percentage(self) -> Decimal:
        """Calculate percentage of bullish candles."""
        if self.total_candles == 0:
            return Decimal('0')
        return (Decimal(self.bullish_candles) / Decimal(self.total_candles)) * 100
    
    @property
    def bearish_percentage(self) -> Decimal:
        """Calculate percentage of bearish candles."""
        if self.total_candles == 0:
            return Decimal('0')
        return (Decimal(self.bearish_candles) / Decimal(self.total_candles)) * 100
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class TechnicalIndicator(BaseModel):
    """Technical indicator data model."""
    symbol: str = Field(..., description="Asset symbol")
    timestamp: datetime = Field(..., description="Indicator timestamp")
    timeframe: Timeframe = Field(..., description="Timeframe")
    indicator_name: str = Field(..., description="Name of the indicator")
    value: Union[Decimal, Dict[str, Decimal]] = Field(..., description="Indicator value(s)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Indicator parameters")
    source: DataSource = Field(..., description="Data source")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# Utility functions for OHLC models
def create_ohlc_from_dict(data: Dict[str, Any]) -> OHLCData:
    """
    Create OHLCData from dictionary.
    
    Args:
        data: Dictionary containing OHLC data
        
    Returns:
        OHLCData object
    """
    return OHLCData(**data)


def create_ohlc_batch(symbol: str, timeframe: Timeframe, data_list: List[Dict[str, Any]], 
                     source: DataSource) -> OHLCBatch:
    """
    Create OHLCBatch from list of dictionaries.
    
    Args:
        symbol: Asset symbol
        timeframe: Data timeframe
        data_list: List of OHLC data dictionaries
        source: Data source
        
    Returns:
        OHLCBatch object
    """
    ohlc_data = [create_ohlc_from_dict(d) for d in data_list]
    
    if not ohlc_data:
        raise ValueError("Cannot create batch from empty data list")
    
    start_time = min(d.timestamp for d in ohlc_data)
    end_time = max(d.timestamp for d in ohlc_data)
    
    return OHLCBatch(
        symbol=symbol,
        timeframe=timeframe,
        data=ohlc_data,
        start_time=start_time,
        end_time=end_time,
        source=source
    )


def calculate_ohlc_stats(ohlc_data: List[OHLCData]) -> OHLCStats:
    """
    Calculate statistics from OHLC data.
    
    Args:
        ohlc_data: List of OHLCData objects
        
    Returns:
        OHLCStats object
    """
    if not ohlc_data:
        raise ValueError("Cannot calculate stats from empty data")
    
    # Sort by timestamp
    sorted_data = sorted(ohlc_data, key=lambda x: x.timestamp)
    
    # Calculate statistics
    highest_high = max(d.high for d in sorted_data)
    lowest_low = min(d.low for d in sorted_data)
    period_open = sorted_data[0].open
    period_close = sorted_data[-1].close
    price_change = period_close - period_open
    price_change_percent = (price_change / period_open) * 100 if period_open != 0 else Decimal('0')
    
    total_volume = sum(d.volume for d in sorted_data)
    average_volume = total_volume / len(sorted_data)
    max_volume = max(d.volume for d in sorted_data)
    
    # Count candle types
    bullish_candles = sum(1 for d in sorted_data if d.is_bullish)
    bearish_candles = sum(1 for d in sorted_data if d.is_bearish)
    doji_candles = sum(1 for d in sorted_data if d.is_doji)
    
    # Calculate volatility (standard deviation of price changes)
    price_changes = [d.price_change_percent for d in sorted_data]
    mean_change = sum(price_changes) / len(price_changes)
    variance = sum((pc - mean_change) ** 2 for pc in price_changes) / len(price_changes)
    volatility = variance ** Decimal('0.5')
    
    # Calculate range statistics
    ranges = [d.range_size for d in sorted_data]
    average_range = sum(ranges) / len(ranges)
    max_range = max(ranges)
    
    return OHLCStats(
        symbol=sorted_data[0].symbol,
        timeframe=sorted_data[0].timeframe,
        period_start=sorted_data[0].timestamp,
        period_end=sorted_data[-1].timestamp,
        highest_high=highest_high,
        lowest_low=lowest_low,
        period_open=period_open,
        period_close=period_close,
        price_change=price_change,
        price_change_percent=price_change_percent,
        total_volume=total_volume,
        average_volume=average_volume,
        max_volume=max_volume,
        volatility=volatility,
        average_range=average_range,
        max_range=max_range,
        bullish_candles=bullish_candles,
        bearish_candles=bearish_candles,
        doji_candles=doji_candles,
        total_candles=len(sorted_data)
    )
