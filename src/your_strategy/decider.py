"""
Strategy Decider - Core decision engine for buy/sell logic
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .config import StrategyConfig
from .filters import TokenData, Phase1Filter, Phase2Filter
from .entry_scorer import EntryScorer, EntryDecision
from .position_context import PositionContext
from .signal_bus import Signal, SignalBus, SignalType, Severity
from .detectors import StopLossDetector, TakeProfitDetector, RugDetector, DumpDetector


class StrategyDecider:
    """Core trading decision engine"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.phase1_filter = Phase1Filter(config)
        self.phase2_filter = Phase2Filter(config)
        self.entry_scorer = EntryScorer(config)
        
        # Detectors
        self.stop_loss_detector = StopLossDetector(config)
        self.take_profit_detector = TakeProfitDetector(config)
        self.rug_detector = RugDetector(config)
        self.dump_detector = DumpDetector(config)
        
        # Position tracking
        self.positions: Dict[str, PositionContext] = {}  # token_mint -> position
        self.graveyard: Dict[str, datetime] = {}  # token_mint -> time added
        self.signal_bus = SignalBus()
    
    # ========== ENTRY LOGIC ==========
    def consider_buy(self, token: TokenData, vs_pre_max: float = 0.8,
                     holder_growth: float = 0.5, volume_ratio: float = 1.0,
                     ut_growth: float = 0.0) -> Tuple[bool, str]:
        """
        Decide whether to buy a token
        
        Returns:
            (should_buy: bool, reason: str)
        """
        
        # Check if already in graveyard
        if self._is_in_graveyard(token.mint):
            return False, "Token in graveyard"
        
        # Check if already holding
        if token.mint in self.positions:
            return False, "Already holding this token"
        
        # Check max positions
        open_positions = sum(1 for p in self.positions.values() if p.is_open)
        if open_positions >= self.config.MAX_POSITIONS:
            return False, f"Max positions ({self.config.MAX_POSITIONS}) reached"
        
        # Phase 1 filter
        passed_p1, reason_p1 = self.phase1_filter.check(token)
        if not passed_p1:
            return False, f"Phase1: {reason_p1}"
        
        # Phase 2 filter
        passed_p2, reason_p2, safety_score = self.phase2_filter.check(token)
        if not passed_p2:
            return False, f"Phase2: {reason_p2}"
        
        # Entry scoring
        decision: EntryDecision = self.entry_scorer.evaluate(
            token, vs_pre_max, holder_growth, volume_ratio, ut_growth
        )
        
        if not decision.should_buy:
            return False, f"Entry score {decision.score} < {self.config.ENTRY_SCORE_THRESHOLD}"
        
        return True, decision.reason
    
    def open_position(self, token: TokenData, amount_usd: float,
                     entry_decision: EntryDecision, entry_price: float,
                     entry_mcap: float) -> PositionContext:
        """
        Open a new position
        
        Returns:
            PositionContext
        """
        # Calculate position size
        if entry_decision.is_strong_golddog:
            position_size = self.config.POSITION_SIZE_STRONG
        else:
            position_size = self.config.POSITION_SIZE_NORMAL
        
        # Cap at single token limit
        actual_amount = min(amount_usd * position_size, 
                          self.config.INITIAL_CAPITAL_USD * self.config.SINGLE_TOKEN_CAP)
        
        # Create position
        position = PositionContext(
            token_mint=token.mint,
            entry_price=entry_price,
            entry_time=datetime.now(),
            entry_mcap=entry_mcap,
            position_size_percent=position_size,
            amount_usd=actual_amount,
            amount_tokens=actual_amount / entry_price if entry_price > 0 else 0,
            current_price=entry_price,
            current_mcap=entry_mcap,
            price_high=entry_price,
            price_low=entry_price,
            entry_score=entry_decision.score,
            is_strong_golddog=entry_decision.is_strong_golddog,
            entry_factors=entry_decision.factors,
        )
        
        self.positions[token.mint] = position
        return position
    
    # ========== EXIT LOGIC ==========
    def check_exits(self) -> List[Tuple[str, Signal]]:
        """
        Check all positions for exit signals
        
        Returns:
            List of (token_mint, signal) tuples
        """
        exit_signals: List[Tuple[str, Signal]] = []
        
        for token_mint, position in list(self.positions.items()):
            if not position.is_open:
                continue
            
            # Check detectors
            signal = self._check_position_signals(position)
            if signal:
                exit_signals.append((token_mint, signal))
        
        return exit_signals
    
    def _check_position_signals(self, position: PositionContext) -> Optional[Signal]:
        """
        Check all detectors for a position
        Returns first signal found (by severity)
        """
        signals = []
        
        # Stop loss
        sl_signal = self.stop_loss_detector.check(position)
        if sl_signal:
            signals.append(sl_signal)
        
        # Take profit
        tp_signal = self.take_profit_detector.check(position)
        if tp_signal:
            signals.append(tp_signal)
        
        if signals:
            # Return highest severity
            return max(signals, key=lambda s: s.severity.value)
        
        return None
    
    def on_signal(self, signal: Signal) -> Optional[List[Dict]]:
        """
        Handle a signal and return execution actions
        
        Returns:
            List of execution actions or None
        """
        position = self.positions.get(signal.token_mint)
        if not position or not position.is_open:
            return None
        
        actions = []
        holding_time = position.get_holding_time_seconds()
        in_protect_period = holding_time < self.config.PROTECT_PERIOD_SEC
        
        # CRITICAL: Execute immediately
        if signal.severity == Severity.CRITICAL:
            actions.append({
                'action': 'sell_all',
                'reason': signal.reason,
                'signal': signal.signal_type.value,
            })
            position.close_position(signal.reason)
        
        # HIGH: Check protect period
        elif signal.severity == Severity.HIGH:
            if in_protect_period:
                # Suppress during protect period
                pass
            else:
                actions.append({
                    'action': 'sell_all',
                    'reason': signal.reason,
                    'signal': signal.signal_type.value,
                })
                position.close_position(signal.reason)
        
        # MID: Direct execution (soft stops)
        elif signal.severity == Severity.MID:
            actions.append({
                'action': 'sell_all',
                'reason': signal.reason,
                'signal': signal.signal_type.value,
            })
            position.close_position(signal.reason)
        
        # LOW: Partial or full exit (take profits)
        elif signal.severity == Severity.LOW:
            if signal.sell_percentage:
                actions.append({
                    'action': 'sell_partial',
                    'percentage': signal.sell_percentage,
                    'reason': signal.reason,
                    'signal': signal.signal_type.value,
                })
                position.record_partial_exit(
                    position.current_price,
                    position.amount_usd * signal.sell_percentage,
                    signal.reason
                )
            else:
                actions.append({
                    'action': 'sell_all',
                    'reason': signal.reason,
                    'signal': signal.signal_type.value,
                })
                position.close_position(signal.reason)
        
        return actions if actions else None
    
    def close_position(self, token_mint: str, reason: str) -> None:
        """Close a position and add to graveyard"""
        if token_mint in self.positions:
            position = self.positions[token_mint]
            position.close_position(reason)
            
            # Add to graveyard if rug
            if 'rug' in reason.lower():
                self.graveyard[token_mint] = datetime.now()
            else:
                # Regular close: 10 minute cooldown
                self.graveyard[token_mint] = datetime.now()
    
    def _is_in_graveyard(self, token_mint: str) -> bool:
        """Check if token is in graveyard"""
        if token_mint not in self.graveyard:
            return False
        
        added_time = self.graveyard[token_mint]
        cooldown = timedelta(seconds=self.config.GRAVEYARD_COOLDOWN_SEC)
        
        if datetime.now() - added_time > cooldown:
            # Remove from graveyard
            del self.graveyard[token_mint]
            return False
        
        return True
    
    # ========== POSITION UPDATES ==========
    def update_position(self, token_mint: str, current_price: float, 
                       current_mcap: float) -> None:
        """Update position with latest market data"""
        if token_mint not in self.positions:
            return
        
        position = self.positions[token_mint]
        position.current_price = current_price
        position.current_mcap = current_mcap
        
        # Update high/low
        if current_price > position.price_high:
            position.price_high = current_price
        if position.price_low == 0 or current_price < position.price_low:
            position.price_low = current_price
    
    def record_price(self, token_mint: str, price: float) -> None:
        """Record price for rate calculation"""
        self.stop_loss_detector.record_price(token_mint, price)
    
    # ========== STATISTICS ==========
    def get_portfolio_stats(self) -> Dict:
        """Get portfolio statistics"""
        open_positions = [p for p in self.positions.values() if p.is_open]
        closed_positions = [p for p in self.positions.values() if not p.is_open]
        
        total_invested = sum(p.amount_usd for p in open_positions)
        total_value = sum(p.get_current_value_usd() for p in open_positions)
        total_pnl_usd = total_value - total_invested
        total_pnl_pct = (total_pnl_usd / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'total_invested': total_invested,
            'total_value': total_value,
            'total_pnl_usd': total_pnl_usd,
            'total_pnl_pct': total_pnl_pct,
            'max_positions': self.config.MAX_POSITIONS,
            'graveyard_size': len(self.graveyard),
        }
