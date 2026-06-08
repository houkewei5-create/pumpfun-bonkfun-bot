"""
Take Profit Detector - Ladder take profit based on market cap multiples
"""

from typing import Optional
from ..config import StrategyConfig
from ..position_context import PositionContext
from ..signal_bus import Signal, SignalType, Severity


class TakeProfitDetector:
    """Detects take profit conditions based on market cap multiples"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.tp_triggered = {}  # token_mint -> set of triggered TPs
    
    def check(self, position: PositionContext) -> Optional[Signal]:
        """Check for take profit conditions"""
        
        if position.token_mint not in self.tp_triggered:
            self.tp_triggered[position.token_mint] = set()
        
        triggered = self.tp_triggered[position.token_mint]
        mcap_mult = position.get_mcap_multiplier()
        
        # TP_200: 2.00x -> sell 20%
        if mcap_mult >= self.config.TP_200_PEAK and 'TP_200' not in triggered:
            triggered.add('TP_200')
            return Signal(
                signal_type=SignalType.TP_200,
                severity=Severity.LOW,
                token_mint=position.token_mint,
                value=mcap_mult,
                reason=f"TP_200: mcap {mcap_mult:.2f}x",
                sell_percentage=self.config.TP_200_PCT,
            )
        
        # TP_80: 1.80x -> sell 30%
        if mcap_mult >= self.config.TP_80_PEAK and 'TP_80' not in triggered:
            triggered.add('TP_80')
            return Signal(
                signal_type=SignalType.TP_80,
                severity=Severity.LOW,
                token_mint=position.token_mint,
                value=mcap_mult,
                reason=f"TP_80: mcap {mcap_mult:.2f}x",
                sell_percentage=self.config.TP_30_PCT,
            )
        
        # TP_30: 1.30x -> sell 30%
        if mcap_mult >= self.config.TP_30_PEAK and 'TP_30' not in triggered:
            triggered.add('TP_30')
            return Signal(
                signal_type=SignalType.TP_30,
                severity=Severity.LOW,
                token_mint=position.token_mint,
                value=mcap_mult,
                reason=f"TP_30: mcap {mcap_mult:.2f}x",
                sell_percentage=self.config.TP_30_PCT,
            )
        
        # TP_20: 1.20x -> sell 20%
        if mcap_mult >= self.config.TP_20_PEAK and 'TP_20' not in triggered:
            triggered.add('TP_20')
            return Signal(
                signal_type=SignalType.TP_20,
                severity=Severity.LOW,
                token_mint=position.token_mint,
                value=mcap_mult,
                reason=f"TP_20: mcap {mcap_mult:.2f}x",
                sell_percentage=self.config.TP_20_PCT,
            )
        
        return None
    
    def reset_position(self, token_mint: str) -> None:
        """Reset TP tracking when position closes"""
        if token_mint in self.tp_triggered:
            self.tp_triggered[token_mint].clear()
