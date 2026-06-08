"""
Dump Detector - Detects selling pressure and dump conditions
"""

from typing import Optional
from ..config import StrategyConfig
from ..position_context import PositionContext
from ..signal_bus import Signal, SignalType, Severity


class DumpDetector:
    """Detects dump/dump bait conditions"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def check(self, position: PositionContext, sell_ratio_30s: float) -> Optional[Signal]:
        """
        Check for dump conditions based on sell ratio
        
        Args:
            position: Current position
            sell_ratio_30s: Sell volume ratio in last 30 seconds (0-1)
        
        Returns:
            Signal if dump detected, None otherwise
        """
        
        # Detect bait dump: High sell ratio early
        if sell_ratio_30s > 0.85:
            return Signal(
                signal_type=SignalType.BAIT_DUMP,
                severity=Severity.MID,
                token_mint=position.token_mint,
                value=sell_ratio_30s,
                reason=f"Bait dump detected: {sell_ratio_30s:.2%} sell ratio",
            )
        
        return None
