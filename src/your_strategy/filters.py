"""
Token Filters - Phase1 & Phase2 filtering logic
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from .config import StrategyConfig


@dataclass
class TokenData:
    """Token data for filtering"""
    mint: str
    age_minutes: float
    holder_count: int
    liquidity_usd: float
    top10_ratio: float  # 0-1
    rat: float  # 0-1
    bundler: float  # 0-1
    unique_traders: int
    buy_volume: float
    sell_volume: float
    market_cap_usd: float
    
    # Security fields
    is_lp_burned: bool
    is_lp_locked: bool
    lp_burn_ratio: float  # 0-1
    is_mint_revoked: bool
    dev_holding_ratio: float  # 0-1
    
    def get_bsr(self) -> float:
        """Calculate Buy/Sell Ratio"""
        if self.sell_volume == 0:
            return float('inf')
        return self.buy_volume / self.sell_volume


class SecurityFilter:
    """Zero-tolerance security filters"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def check(self, token: TokenData) -> Tuple[bool, str]:
        """
        Check zero-tolerance security filters
        
        Returns:
            (passed: bool, reason: str)
        """
        # 1. LP 销毁比例 ≥ 99% 或 is_locked = True
        if not (token.lp_burn_ratio >= self.config.LP_BURN_MIN_RATIO or token.is_lp_locked):
            return False, f"LP not burned/locked enough: {token.lp_burn_ratio:.2%}"
        
        # 2. 铸币权已撤销
        if self.config.MINT_MUST_BE_REVOKED and not token.is_mint_revoked:
            return False, "Mint not revoked"
        
        # 3. 团队代币销毁 ≥ 80%（即 dev ≤ 20%）
        if token.dev_holding_ratio > (1 - self.config.DEV_HOLDING_MAX):
            return False, f"Dev holding too high: {token.dev_holding_ratio:.2%}"
        
        return True, "Security check passed"


class Phase1Filter:
    """Phase 1 - Basic filtering (10 rules)"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.security_filter = SecurityFilter(config)
    
    def check(self, token: TokenData) -> Tuple[bool, str]:
        """
        Check all Phase1 filters
        
        Returns:
            (passed: bool, reason: str)
        """
        # First check security
        passed, reason = self.security_filter.check(token)
        if not passed:
            return False, f"Security: {reason}"
        
        # Rule 1: Age
        if not (self.config.MIN_AGE_MINUTES <= token.age_minutes <= self.config.MAX_AGE_MINUTES):
            return False, f"Age {token.age_minutes:.1f}min not in range [{self.config.MIN_AGE_MINUTES}, {self.config.MAX_AGE_MINUTES}]"
        
        # Rule 2: Holder count
        if token.holder_count < self.config.HOLDER_MIN:
            return False, f"Holder count {token.holder_count} < {self.config.HOLDER_MIN}"
        
        # Rule 3: Liquidity
        if token.liquidity_usd < self.config.LIQUIDITY_MIN_USD:
            return False, f"Liquidity ${token.liquidity_usd:.0f} < ${self.config.LIQUIDITY_MIN_USD:.0f}"
        
        # Rule 4: Top10 ratio
        if token.top10_ratio > self.config.TOP10_MAX_RATIO:
            return False, f"Top10 ratio {token.top10_ratio:.2%} > {self.config.TOP10_MAX_RATIO:.2%}"
        
        # Rule 5: Rat
        if token.rat > self.config.RAT_MAX:
            return False, f"Rat {token.rat:.2%} > {self.config.RAT_MAX:.2%}"
        
        # Rule 6: Bundler
        if token.bundler > self.config.BUNDLER_MAX:
            return False, f"Bundler {token.bundler:.2%} > {self.config.BUNDLER_MAX:.2%}"
        
        # Rule 7: Unique traders
        if token.unique_traders < self.config.UT_MIN:
            return False, f"UT {token.unique_traders} < {self.config.UT_MIN}"
        
        # Rule 8: Buy/Sell Ratio
        bsr = token.get_bsr()
        if bsr <= self.config.BSR_MIN:
            return False, f"BSR {bsr:.2f} <= {self.config.BSR_MIN}"
        
        # Rule 9: Holder/UT ratio
        if token.unique_traders > 0:
            holder_ut_ratio = token.holder_count / token.unique_traders
            if holder_ut_ratio > self.config.HOLDER_UT_RATIO_MAX:
                return False, f"Holder/UT ratio {holder_ut_ratio:.1f} > {self.config.HOLDER_UT_RATIO_MAX}"
        
        # Rule 10: Market cap
        if not (self.config.MCAP_MIN_USD <= token.market_cap_usd <= self.config.MCAP_MAX_USD):
            return False, f"Mcap ${token.market_cap_usd:.0f} not in range [${self.config.MCAP_MIN_USD:.0f}, ${self.config.MCAP_MAX_USD:.0f}]"
        
        return True, "All Phase1 checks passed"


class Phase2Filter:
    """Phase 2 - Safety verification"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def calculate_safety_score(self, token: TokenData) -> float:
        """
        Calculate safety score (0-1)
        
        Returns:
            safety_score: float (0-1)
        """
        score = 0.0
        
        # LP lock or burn ≥ 50%
        if token.is_lp_locked or token.lp_burn_ratio >= 0.5:
            score += self.config.LP_LOCK_OR_BURN_SCORE
        
        # Mint revoked
        if token.is_mint_revoked:
            score += self.config.MINT_REVOKED_SCORE
        
        # Dev burn ≥ 80%
        if token.dev_holding_ratio <= (1 - 0.8):  # dev ≤ 20%
            score += self.config.DEV_BURN_SCORE
        
        # Top10 < 50%
        if token.top10_ratio < 0.5:
            score += self.config.TOP10_SAFE_SCORE
        
        return min(score, 1.0)
    
    def check(self, token: TokenData) -> Tuple[bool, str, float]:
        """
        Check Phase2 safety verification
        
        Returns:
            (passed: bool, reason: str, safety_score: float)
        """
        safety_score = self.calculate_safety_score(token)
        
        # Check safety score threshold
        if safety_score < self.config.SAFETY_SCORE_THRESHOLD:
            return False, f"Safety score {safety_score:.2f} < {self.config.SAFETY_SCORE_THRESHOLD}", safety_score
        
        # Manipulation detection
        if token.rat > self.config.RAT_SAFETY_MAX:
            return False, f"Rat manipulation detected: {token.rat:.2%} > {self.config.RAT_SAFETY_MAX:.2%}", safety_score
        
        if token.bundler > self.config.BUNDLER_SAFETY_MAX:
            return False, f"Bundler manipulation detected: {token.bundler:.2%} > {self.config.BUNDLER_SAFETY_MAX:.2%}", safety_score
        
        return True, f"Safety check passed (score: {safety_score:.2f})", safety_score
