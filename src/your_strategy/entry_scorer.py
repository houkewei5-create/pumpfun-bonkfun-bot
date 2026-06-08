"""
Entry Scorer - F1-F6 scoring system for entry decisions
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from .config import StrategyConfig
from .filters import TokenData, Phase2Filter


@dataclass
class EntryDecision:
    """Entry decision result"""
    should_buy: bool
    score: int
    is_strong_golddog: bool
    fast_path: bool
    factors: dict  # F1-F6 scores
    reason: str


class EntryScorer:
    """Entry scoring system (F1-F6 factors)"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.phase2_filter = Phase2Filter(config)
        self.holder_snapshots = {}  # Track holder growth
    
    def _score_f1(self, vs_pre_max: float) -> int:
        """F1: vs_pre_max回调评分"""
        if vs_pre_max < 0.5:
            return -10
        elif 0.5 <= vs_pre_max < 0.9:
            return 15
        elif 0.9 <= vs_pre_max < 1.0:
            return 10
        elif 1.0 <= vs_pre_max < 1.05:
            return 5
        else:  # >= 1.05
            return -5
    
    def _score_f2(self, holder_growth: float) -> int:
        """F2: holder_growth"""
        if holder_growth >= 1.0:
            return 15
        elif holder_growth >= 0.5:
            return 10
        elif holder_growth >= 0.3:
            return 5
        elif holder_growth > 0:
            return -5
        else:  # First time seeing, no penalty
            return 0
    
    def _score_f3(self, bsr: float) -> int:
        """F3: Buy/Sell Ratio"""
        if 1.5 <= bsr < 2.0:
            return 5
        elif 2.0 <= bsr < 3.0:
            return 10
        elif bsr >= 3.0:
            return 8
        elif 1.0 <= bsr < 1.5:
            return 3
        else:  # < 1.0
            return -10
    
    def _score_f4(self, holder_ut_ratio: float) -> int:
        """F4: holder/UT ratio"""
        if holder_ut_ratio <= 2:
            return 10
        elif 2 < holder_ut_ratio <= 4.2:
            return 5
        elif 4.2 < holder_ut_ratio <= 10:
            return 0
        else:  # > 10
            return -8
    
    def _score_f5(self, volume_ratio: float, ut_growth: float) -> int:
        """F5: Speed factor (volume_ratio and ut_growth)"""
        score = 0
        if volume_ratio >= self.config.F5_VOLUME_RATIO_MIN:
            score += 5
        if ut_growth >= self.config.F5_UT_GROWTH_MIN:
            score += 5
        return score
    
    def _score_f6(self, safety_score: float) -> int:
        """F6: Safety score"""
        if safety_score >= self.config.F6_SAFE_HIGH:
            return 10
        elif safety_score >= self.config.F6_SAFE_MID:
            return 5
        else:
            return 0
    
    def _get_age_multiplier(self, age_minutes: float) -> float:
        """Calculate age multiplier"""
        return self.config.get_age_multiplier(age_minutes)
    
    def evaluate(self, token: TokenData, vs_pre_max: float = 0.8, 
                 holder_growth: float = 0.5, volume_ratio: float = 1.0,
                 ut_growth: float = 0.0) -> EntryDecision:
        """
        Evaluate token for entry with F1-F6 scoring
        
        Args:
            token: Token data
            vs_pre_max: Price vs previous high (0-1)
            holder_growth: Holder growth rate (0-inf)
            volume_ratio: Volume ratio
            ut_growth: Unique traders growth
        
        Returns:
            EntryDecision
        """
        factors = {}
        
        # Calculate individual factors
        f1 = self._score_f1(vs_pre_max)
        f2 = self._score_f2(holder_growth)
        f3 = self._score_f3(token.get_bsr())
        f4 = self._score_f4(token.holder_count / max(token.unique_traders, 1))
        f5 = self._score_f5(volume_ratio, ut_growth)
        
        # Get safety score
        _, _, safety_score = self.phase2_filter.check(token)
        f6 = self._score_f6(safety_score)
        
        # Apply age multiplier
        age_mult = self._get_age_multiplier(token.age_minutes)
        
        # Calculate total score
        base_score = f1 + f2 + f3 + f4 + f5 + f6
        total_score = int(base_score * age_mult)
        
        factors = {
            'f1': f1,
            'f2': f2,
            'f3': f3,
            'f4': f4,
            'f5': f5,
            'f6': f6,
            'age_multiplier': age_mult,
            'safety_score': safety_score,
        }
        
        # Check fast path (holder >= 50 and bundler <= 0.30)
        fast_path = (token.holder_count >= self.config.FAST_PATH_HOLDER_MIN and 
                     token.bundler <= self.config.FAST_PATH_BUNDLER_MAX)
        
        if fast_path:
            total_score += self.config.FAST_PATH_BONUS
            factors['fast_path_bonus'] = self.config.FAST_PATH_BONUS
        
        # Determine if strong golddog
        is_strong_golddog = (total_score >= self.config.STRONG_GOLDDOG_THRESHOLD and
                            holder_growth >= self.config.STRONG_GOLDDOG_GROWTH_MIN)
        
        # Determine if should buy
        should_buy = total_score >= self.config.ENTRY_SCORE_THRESHOLD
        
        reason = f"Score: {total_score} (Base: {base_score}, Age mult: {age_mult:.2f})"
        if not should_buy:
            reason += f" - Below threshold {self.config.ENTRY_SCORE_THRESHOLD}"
        if is_strong_golddog:
            reason += " - STRONG GOLDDOG"
        if fast_path:
            reason += " - FAST PATH"
        
        return EntryDecision(
            should_buy=should_buy,
            score=total_score,
            is_strong_golddog=is_strong_golddog,
            fast_path=fast_path,
            factors=factors,
            reason=reason,
        )
