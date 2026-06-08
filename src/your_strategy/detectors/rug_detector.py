"""
Rug Detector - Detects rug pull conditions
"""

from typing import Optional
from ..config import StrategyConfig
from ..position_context import PositionContext
from ..signal_bus import Signal, SignalType, Severity


class RugDetector:
    """Detects rug pull conditions"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.prev_lp = {}  # token_mint -> previous LP amount
        self.prev_supply = {}  # token_mint -> previous supply
    
    def check(self, position: PositionContext, lp_usd: float, 
              total_supply: float, burned_supply: float) -> Optional[Signal]:
        """Check for rug pull conditions"""
        
        token_mint = position.token_mint
        
        # CRITICAL: LP went to zero
        if lp_usd == 0:
            return Signal(
                signal_type=SignalType.LP_ZERO,
                severity=Severity.CRITICAL,
                token_mint=token_mint,
                reason="LP went to zero - RUG PULL",
            )
        
        # CRITICAL: Detect supply burn (burn_ratio sudden jump)
        if token_mint in self.prev_supply:
            prev_burned = self.prev_supply[token_mint]
            current_burned_ratio = burned_supply / total_supply if total_supply > 0 else 0
            prev_burned_ratio = prev_burned / total_supply if total_supply > 0 else 0
            
            # If burn ratio jumped by > 10%
            if current_burned_ratio - prev_burned_ratio > 0.1:
                return Signal(
                    signal_type=SignalType.RUG_DETECTED,
                    severity=Severity.CRITICAL,
                    token_mint=token_mint,
                    reason=f"Supply burn detected: {current_burned_ratio:.2%}",
                )
        
        # Track current values
        self.prev_lp[token_mint] = lp_usd
        self.prev_supply[token_mint] = burned_supply
        
        return None
    
    def reset_position(self, token_mint: str) -> None:
        """Reset tracking when position closes"""
        if token_mint in self.prev_lp:
            del self.prev_lp[token_mint]
        if token_mint in self.prev_supply:
            del self.prev_supply[token_mint]
