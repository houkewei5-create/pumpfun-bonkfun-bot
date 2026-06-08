"""
Stop Loss Detector - Time-layered stop loss detection
"""

from datetime import datetime
from typing import Optional, Tuple
from ..config import StrategyConfig
from ..position_context import PositionContext
from ..signal_bus import Signal, SignalType, Severity


class StopLossDetector:
    """Detects stop loss conditions"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.price_history = {}  # token_mint -> [(timestamp, price)]
    
    def record_price(self, token_mint: str, price: float) -> None:
        """Record price for rate calculation"""
        if token_mint not in self.price_history:
            self.price_history[token_mint] = []
        self.price_history[token_mint].append((datetime.now(), price))
        # Keep only last 70 seconds
        cutoff = datetime.now().timestamp() - 70
        self.price_history[token_mint] = [
            (ts, p) for ts, p in self.price_history[token_mint]
            if ts.timestamp() > cutoff
        ]
    
    def _get_price_change_rate(self, token_mint: str, seconds: int) -> Optional[float]:
        """Get price change rate over N seconds"""
        if token_mint not in self.price_history or len(self.price_history[token_mint]) < 2:
            return None
        
        history = self.price_history[token_mint]
        now = datetime.now().timestamp()
        cutoff = now - seconds
        
        old_price = None
        for ts, price in history:
            if ts.timestamp() <= cutoff:
                old_price = price
        
        if old_price is None:
            return None
        
        latest_price = history[-1][1]
        return (latest_price - old_price) / old_price
    
    def check(self, position: PositionContext) -> Optional[Signal]:
        """Check for stop loss conditions"""
        
        # Get holding time
        holding_time = position.get_holding_time_seconds()
        in_protect_period = holding_time < self.config.PROTECT_PERIOD_SEC
        
        pnl = position.get_unrealized_pnl()
        
        # CRITICAL: Absolute fallback (-25%)
        if pnl <= self.config.STOP_ABS_FALLBACK:
            return Signal(
                signal_type=SignalType.ABS_FALLBACK,
                severity=Severity.CRITICAL,
                token_mint=position.token_mint,
                value=pnl,
                reason=f"Absolute fallback: {pnl:.2%}",
            )
        
        # CRITICAL: Absolute floor after protect period (-3%)
        if not in_protect_period and pnl <= self.config.STOP_ABS_FLOOR:
            return Signal(
                signal_type=SignalType.ABS_FLOOR,
                severity=Severity.CRITICAL,
                token_mint=position.token_mint,
                value=pnl,
                reason=f"Absolute floor: {pnl:.2%}",
            )
        
        # HIGH: Rate-based stop loss (only check if not in protect period)
        if not in_protect_period:
            # 10s drop >= 12%
            rate_10s = self._get_price_change_rate(position.token_mint, 10)
            if rate_10s and rate_10s <= self.config.STOP_RATE_10S:
                return Signal(
                    signal_type=SignalType.RATE_STOP_10S,
                    severity=Severity.HIGH,
                    token_mint=position.token_mint,
                    value=rate_10s,
                    reason=f"10s drop: {rate_10s:.2%}",
                )
            
            # 30s drop >= 20%
            rate_30s = self._get_price_change_rate(position.token_mint, 30)
            if rate_30s and rate_30s <= self.config.STOP_RATE_30S:
                return Signal(
                    signal_type=SignalType.RATE_STOP_30S,
                    severity=Severity.HIGH,
                    token_mint=position.token_mint,
                    value=rate_30s,
                    reason=f"30s drop: {rate_30s:.2%}",
                )
            
            # 1m drop >= 30%
            rate_1m = self._get_price_change_rate(position.token_mint, 60)
            if rate_1m and rate_1m <= self.config.STOP_RATE_1M:
                return Signal(
                    signal_type=SignalType.RATE_STOP_1M,
                    severity=Severity.HIGH,
                    token_mint=position.token_mint,
                    value=rate_1m,
                    reason=f"1m drop: {rate_1m:.2%}",
                )
        
        # MID: Soft stop loss at 5min
        if holding_time > 300 and pnl <= self.config.STOP_SOFT_10:
            return Signal(
                signal_type=SignalType.SOFT_STOP_5M,
                severity=Severity.MID,
                token_mint=position.token_mint,
                value=pnl,
                reason=f"Soft stop 5m: {pnl:.2%}",
            )
        
        # MID: Soft stop loss at 15min
        if holding_time > 900 and pnl <= self.config.STOP_SOFT_6:
            return Signal(
                signal_type=SignalType.SOFT_STOP_15M,
                severity=Severity.MID,
                token_mint=position.token_mint,
                value=pnl,
                reason=f"Soft stop 15m: {pnl:.2%}",
            )
        
        return None
