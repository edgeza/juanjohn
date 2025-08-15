"""
Portfolio Data Models

This module defines Pydantic models for portfolio management including
positions, transactions, performance metrics, and risk analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class PositionStatus(str, Enum):
    """Position status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Transaction(BaseModel):
    """Transaction model for portfolio tracking."""
    id: Optional[str] = Field(None, description="Transaction ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    symbol: str = Field(..., description="Asset symbol")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    quantity: Decimal = Field(..., description="Quantity of asset")
    price: Decimal = Field(..., description="Price per unit")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    fee: Decimal = Field(Decimal('0'), description="Transaction fee")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    order_id: Optional[str] = Field(None, description="Related order ID")
    notes: Optional[str] = Field(None, description="Transaction notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('quantity', 'price', 'total_amount')
    def validate_positive_values(cls, v):
        """Validate financial values are positive."""
        if v <= 0:
            raise ValueError("Financial values must be positive")
        return v
    
    @validator('fee')
    def validate_fee(cls, v):
        """Validate fee is non-negative."""
        if v < 0:
            raise ValueError("Fee cannot be negative")
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount consistency."""
        quantity = values.get('quantity')
        price = values.get('price')
        if quantity and price:
            expected_total = quantity * price
            if abs(v - expected_total) > Decimal('0.01'):  # Allow small rounding differences
                logger.warning(f"Total amount {v} doesn't match quantity * price {expected_total}")
        return v
    
    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after fees."""
        if self.transaction_type in [TransactionType.BUY, TransactionType.WITHDRAWAL]:
            return self.total_amount + self.fee
        else:
            return self.total_amount - self.fee
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class Position(BaseModel):
    """Position model for tracking asset holdings."""
    id: Optional[str] = Field(None, description="Position ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    symbol: str = Field(..., description="Asset symbol")
    quantity: Decimal = Field(..., description="Current quantity held")
    average_cost: Decimal = Field(..., description="Average cost per unit")
    current_price: Optional[Decimal] = Field(None, description="Current market price")
    market_value: Optional[Decimal] = Field(None, description="Current market value")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Unrealized profit/loss")
    realized_pnl: Decimal = Field(Decimal('0'), description="Realized profit/loss")
    status: PositionStatus = Field(PositionStatus.OPEN, description="Position status")
    opened_at: datetime = Field(..., description="Position opened timestamp")
    closed_at: Optional[datetime] = Field(None, description="Position closed timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity is not zero for open positions."""
        if v == 0:
            raise ValueError("Position quantity cannot be zero")
        return v
    
    @validator('average_cost', 'current_price')
    def validate_prices(cls, v):
        """Validate prices are positive."""
        if v is not None and v <= 0:
            raise ValueError("Prices must be positive")
        return v
    
    @property
    def cost_basis(self) -> Decimal:
        """Calculate total cost basis."""
        return self.quantity * self.average_cost
    
    @property
    def unrealized_pnl_percent(self) -> Optional[Decimal]:
        """Calculate unrealized P&L percentage."""
        if self.current_price and self.average_cost != 0:
            return ((self.current_price - self.average_cost) / self.average_cost) * 100
        return None
    
    @property
    def is_profitable(self) -> Optional[bool]:
        """Check if position is currently profitable."""
        if self.unrealized_pnl is not None:
            return self.unrealized_pnl > 0
        return None
    
    def update_market_data(self, current_price: Decimal) -> None:
        """Update position with current market data."""
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        self.unrealized_pnl = self.market_value - self.cost_basis
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class Portfolio(BaseModel):
    """Portfolio model for managing investment portfolios."""
    id: Optional[str] = Field(None, description="Portfolio ID")
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    base_currency: str = Field("USD", description="Base currency for calculations")
    initial_balance: Decimal = Field(..., description="Initial portfolio balance")
    current_balance: Decimal = Field(..., description="Current cash balance")
    total_value: Decimal = Field(..., description="Total portfolio value")
    total_invested: Decimal = Field(Decimal('0'), description="Total amount invested")
    total_pnl: Decimal = Field(Decimal('0'), description="Total profit/loss")
    total_pnl_percent: Decimal = Field(Decimal('0'), description="Total P&L percentage")
    positions: List[Position] = Field(default_factory=list, description="Current positions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('initial_balance', 'current_balance', 'total_value')
    def validate_balances(cls, v):
        """Validate balances are non-negative."""
        if v < 0:
            raise ValueError("Balances cannot be negative")
        return v
    
    @property
    def positions_value(self) -> Decimal:
        """Calculate total value of all positions."""
        return sum(pos.market_value or Decimal('0') for pos in self.positions)
    
    @property
    def cash_percentage(self) -> Decimal:
        """Calculate cash percentage of portfolio."""
        if self.total_value == 0:
            return Decimal('100')
        return (self.current_balance / self.total_value) * 100
    
    @property
    def positions_percentage(self) -> Decimal:
        """Calculate positions percentage of portfolio."""
        if self.total_value == 0:
            return Decimal('0')
        return (self.positions_value / self.total_value) * 100
    
    @property
    def open_positions_count(self) -> int:
        """Count of open positions."""
        return len([pos for pos in self.positions if pos.status == PositionStatus.OPEN])
    
    def add_position(self, position: Position) -> None:
        """Add a position to the portfolio."""
        self.positions.append(position)
        self.updated_at = datetime.utcnow()
    
    def remove_position(self, symbol: str) -> bool:
        """Remove a position from the portfolio."""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol:
                del self.positions[i]
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def update_portfolio_value(self) -> None:
        """Update total portfolio value."""
        self.total_value = self.current_balance + self.positions_value
        self.total_pnl = self.total_value - self.initial_balance
        if self.initial_balance != 0:
            self.total_pnl_percent = (self.total_pnl / self.initial_balance) * 100
        self.updated_at = datetime.utcnow()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PortfolioPerformance(BaseModel):
    """Portfolio performance metrics model."""
    portfolio_id: str = Field(..., description="Portfolio ID")
    period_start: datetime = Field(..., description="Performance period start")
    period_end: datetime = Field(..., description="Performance period end")
    
    # Return metrics
    total_return: Decimal = Field(..., description="Total return")
    total_return_percent: Decimal = Field(..., description="Total return percentage")
    annualized_return: Decimal = Field(..., description="Annualized return percentage")
    
    # Risk metrics
    volatility: Decimal = Field(..., description="Portfolio volatility")
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown")
    max_drawdown_percent: Decimal = Field(..., description="Maximum drawdown percentage")
    
    # Performance metrics
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: Decimal = Field(..., description="Win rate percentage")
    average_win: Decimal = Field(..., description="Average winning trade")
    average_loss: Decimal = Field(..., description="Average losing trade")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    
    # Portfolio composition
    largest_position_percent: Decimal = Field(..., description="Largest position as % of portfolio")
    number_of_positions: int = Field(..., description="Number of positions")
    turnover_rate: Optional[Decimal] = Field(None, description="Portfolio turnover rate")
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_trades(self) -> int:
        """Calculate total number of trades."""
        return self.winning_trades + self.losing_trades
    
    @property
    def loss_rate(self) -> Decimal:
        """Calculate loss rate percentage."""
        return Decimal('100') - self.win_rate
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class RiskMetrics(BaseModel):
    """Risk analysis metrics model."""
    portfolio_id: str = Field(..., description="Portfolio ID")
    
    # Risk measures
    value_at_risk_95: Decimal = Field(..., description="Value at Risk (95% confidence)")
    value_at_risk_99: Decimal = Field(..., description="Value at Risk (99% confidence)")
    expected_shortfall: Decimal = Field(..., description="Expected shortfall (CVaR)")
    beta: Optional[Decimal] = Field(None, description="Portfolio beta")
    
    # Concentration risk
    concentration_risk: RiskLevel = Field(..., description="Concentration risk level")
    herfindahl_index: Decimal = Field(..., description="Herfindahl concentration index")
    
    # Correlation risk
    average_correlation: Decimal = Field(..., description="Average correlation between positions")
    max_correlation: Decimal = Field(..., description="Maximum correlation between positions")
    
    # Liquidity risk
    liquidity_score: Decimal = Field(..., description="Portfolio liquidity score (0-100)")
    illiquid_positions_percent: Decimal = Field(..., description="Percentage in illiquid positions")
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class Order(BaseModel):
    """Order model for trade execution."""
    id: Optional[str] = Field(None, description="Order ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    symbol: str = Field(..., description="Asset symbol")
    order_type: OrderType = Field(..., description="Order type")
    transaction_type: TransactionType = Field(..., description="Buy or sell")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Optional[Decimal] = Field(None, description="Order price (for limit orders)")
    stop_price: Optional[Decimal] = Field(None, description="Stop price")
    filled_quantity: Decimal = Field(Decimal('0'), description="Filled quantity")
    average_fill_price: Optional[Decimal] = Field(None, description="Average fill price")
    status: OrderStatus = Field(OrderStatus.PENDING, description="Order status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Order expiration time")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Order quantity must be positive")
        return v
    
    @validator('price', 'stop_price', 'average_fill_price')
    def validate_prices(cls, v):
        """Validate prices are positive."""
        if v is not None and v <= 0:
            raise ValueError("Prices must be positive")
        return v
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to fill."""
        return self.quantity - self.filled_quantity
    
    @property
    def fill_percentage(self) -> Decimal:
        """Calculate fill percentage."""
        if self.quantity == 0:
            return Decimal('0')
        return (self.filled_quantity / self.quantity) * 100
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.filled_quantity > 0 and self.filled_quantity < self.quantity
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class PortfolioSummary(BaseModel):
    """Portfolio summary model for dashboard display."""
    portfolio: Portfolio
    performance: Optional[PortfolioPerformance] = None
    risk_metrics: Optional[RiskMetrics] = None
    recent_transactions: List[Transaction] = Field(default_factory=list)
    pending_orders: List[Order] = Field(default_factory=list)
    
    @property
    def portfolio_id(self) -> Optional[str]:
        """Get portfolio ID."""
        return self.portfolio.id
    
    @property
    def portfolio_name(self) -> str:
        """Get portfolio name."""
        return self.portfolio.name
    
    @property
    def total_value(self) -> Decimal:
        """Get total portfolio value."""
        return self.portfolio.total_value
    
    @property
    def total_pnl(self) -> Decimal:
        """Get total P&L."""
        return self.portfolio.total_pnl
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Utility functions for portfolio models
def create_transaction_from_dict(data: Dict[str, Any]) -> Transaction:
    """Create Transaction from dictionary."""
    return Transaction(**data)


def create_position_from_dict(data: Dict[str, Any]) -> Position:
    """Create Position from dictionary."""
    return Position(**data)


def create_portfolio_from_dict(data: Dict[str, Any]) -> Portfolio:
    """Create Portfolio from dictionary."""
    return Portfolio(**data)


def calculate_portfolio_performance(portfolio: Portfolio, transactions: List[Transaction], 
                                  start_date: datetime, end_date: datetime) -> PortfolioPerformance:
    """
    Calculate portfolio performance metrics.
    
    Args:
        portfolio: Portfolio object
        transactions: List of transactions
        start_date: Performance calculation start date
        end_date: Performance calculation end date
        
    Returns:
        PortfolioPerformance object
    """
    # This is a simplified implementation
    # In practice, you would need more sophisticated calculations
    
    period_transactions = [
        t for t in transactions 
        if start_date <= t.timestamp <= end_date
    ]
    
    winning_trades = len([t for t in period_transactions if t.transaction_type == TransactionType.SELL and t.total_amount > 0])
    losing_trades = len([t for t in period_transactions if t.transaction_type == TransactionType.SELL and t.total_amount < 0])
    total_trades = winning_trades + losing_trades
    
    win_rate = (Decimal(winning_trades) / Decimal(total_trades)) * 100 if total_trades > 0 else Decimal('0')
    
    return PortfolioPerformance(
        portfolio_id=portfolio.id or "",
        period_start=start_date,
        period_end=end_date,
        total_return=portfolio.total_pnl,
        total_return_percent=portfolio.total_pnl_percent,
        annualized_return=Decimal('0'),  # Would need more complex calculation
        volatility=Decimal('0'),  # Would need price history
        max_drawdown=Decimal('0'),  # Would need historical values
        max_drawdown_percent=Decimal('0'),
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        average_win=Decimal('0'),  # Would need transaction analysis
        average_loss=Decimal('0'),  # Would need transaction analysis
        largest_position_percent=Decimal('0'),  # Would need position analysis
        number_of_positions=len(portfolio.positions)
    )
