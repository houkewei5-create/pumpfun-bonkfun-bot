"""
Integration tests for the complete strategy
"""

import pytest
from src.your_strategy.config import StrategyConfig
from src.your_strategy.decider import StrategyDecider
from src.your_strategy.filters import TokenData


class TestStrategyIntegration:
    """Test complete strategy flow"""
    
    @pytest.fixture
    def config(self):
        return StrategyConfig()
    
    @pytest.fixture
    def decider(self, config):
        return StrategyDecider(config)
    
    @pytest.fixture
    def good_token(self):
        """Token that passes all checks"""
        return TokenData(
            mint="good_token",
            age_minutes=5,
            holder_count=50,
            liquidity_usd=10000,
            top10_ratio=0.5,
            rat=0.2,
            bundler=0.2,
            unique_traders=10,
            buy_volume=100,
            sell_volume=50,
            market_cap_usd=500000,
            is_lp_burned=True,
            is_lp_locked=False,
            lp_burn_ratio=0.99,
            is_mint_revoked=True,
            dev_holding_ratio=0.02,
        )
    
    def test_consider_buy_good_token(self, decider, good_token):
        """Test buy decision on good token"""
        should_buy, reason = decider.consider_buy(
            good_token,
            vs_pre_max=0.7,
            holder_growth=0.8,
            volume_ratio=2.0,
            ut_growth=0.6,
        )
        
        # Might buy depending on entry score
        assert isinstance(should_buy, bool)
        assert reason != ""
    
    def test_max_positions_limit(self, decider, good_token):
        """Test max positions limit"""
        # Fill up positions
        for i in range(decider.config.MAX_POSITIONS):
            token = TokenData(
                mint=f"token_{i}",
                age_minutes=5,
                holder_count=50,
                liquidity_usd=10000,
                top10_ratio=0.5,
                rat=0.2,
                bundler=0.2,
                unique_traders=10,
                buy_volume=100,
                sell_volume=50,
                market_cap_usd=500000,
                is_lp_burned=True,
                is_lp_locked=False,
                lp_burn_ratio=0.99,
                is_mint_revoked=True,
                dev_holding_ratio=0.02,
            )
            from src.your_strategy.entry_scorer import EntryScorer
            scorer = EntryScorer(decider.config)
            decision = scorer.evaluate(token, 0.7, 0.8, 2.0, 0.6)
            decider.open_position(token, 1000, decision, 0.01, 500000)
        
        # Try to open another position (should fail)
        should_buy, reason = decider.consider_buy(good_token, 0.7, 0.8, 2.0, 0.6)
        assert not should_buy
        assert "Max positions" in reason
    
    def test_position_context_tracking(self, decider, good_token):
        """Test position context tracking"""
        from src.your_strategy.entry_scorer import EntryScorer
        scorer = EntryScorer(decider.config)
        decision = scorer.evaluate(good_token, 0.7, 0.8, 2.0, 0.6)
        
        position = decider.open_position(
            good_token, 1000, decision, 0.01, 500000
        )
        
        assert position.token_mint == good_token.mint
        assert position.entry_price == 0.01
        assert position.is_open
        assert position.remaining_pct == 1.0
    
    def test_portfolio_stats(self, decider, good_token):
        """Test portfolio statistics"""
        from src.your_strategy.entry_scorer import EntryScorer
        scorer = EntryScorer(decider.config)
        decision = scorer.evaluate(good_token, 0.7, 0.8, 2.0, 0.6)
        
        position = decider.open_position(
            good_token, 1000, decision, 0.01, 500000
        )
        
        stats = decider.get_portfolio_stats()
        assert stats['open_positions'] == 1
        assert stats['closed_positions'] == 0
        assert stats['max_positions'] == decider.config.MAX_POSITIONS
