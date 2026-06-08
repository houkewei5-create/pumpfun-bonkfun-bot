"""
Position Context - Tracks individual position state and metrics
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class PositionContext:
    """Tracks a single position's state and metrics"""
    
    # Position basics
    token_mint: str
    entry_price: float
    entry_time: datetime = field(default_factory=datetime.now)
    entry_mcap: float = 0.0
    
    # Position sizing
    position_size_percent: float = 0.05  # 5% or 8%
    amount_usd: float = 0.0  # Amount invested
    amount_tokens: float = 0.0  # Token amount
    
    # Tracking
    current_price: float = 0.0
    current_mcap: float = 0.0
    price_high: float = 0.0  # Peak price since entry
    price_low: float = 0.0  # Lowest price since entry
    remaining_pct: float = 1.0  # % still held (1.0 = 100%)
    
    # Entry evaluation
    entry_score: int = 0
    is_strong_golddog: bool = False
    entry_factors: dict = field(default_factory=dict)  # F1-F6 scores
    
    # Trade history
    sell_history: List[dict] = field(default_factory=list)  # Partial exits
    
    # Status
    is_open: bool = True
    close_time: Optional[datetime] = None
    close_reason: str = ""  # Reason for closing
    
    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price
    
    def get_unrealized_pnl_usd(self) -> float:
        """Calculate unrealized P&L in USD"""
        if self.entry_price == 0:
            return 0.0
        return self.amount_usd * self.get_unrealized_pnl() * self.remaining_pct
    
    def get_current_value_usd(self) -> float:
        """Get current value of position in USD"""
        return self.amount_usd * (1 + self.get_unrealized_pnl()) * self.remaining_pct
    
    def get_mcap_multiplier(self) -> float:
        """Get market cap multiplier (current / entry)"""
        if self.entry_mcap == 0:
            return 1.0
        return self.current_mcap / self.entry_mcap
    
    def get_price_multiplier(self) -> float:
        """Get price multiplier (current / entry)"""
        if self.entry_price == 0:
            return 1.0
        return self.current_price / self.entry_price
    
    def get_drawdown(self) -> float:
        """Get drawdown from peak"""
        if self.price_high == 0:
            return 0.0
        return (self.current_price - self.price_high) / self.price_high
    
    def get_holding_time_seconds(self) -> float:
        """Get time held in seconds"""
        return (datetime.now() - self.entry_time).total_seconds()
    
    def record_partial_exit(self, price: float, amount_usd: float, reason: str) -> None:
        """Record a partial exit"""
        self.sell_history.append({
            'timestamp': datetime.now(),
            'price': price,
            'amount_usd': amount_usd,
            'reason': reason,
        })
        # Update remaining
        self.remaining_pct = max(0, self.remaining_pct - (amount_usd / self.amount_usd))
    
    def close_position(self, reason: str) -> None:
        """Close the position"""
        self.is_open = False
        self.close_time = datetime.now()
        self.close_reason = reason
        self.remaining_pct = 0.0
