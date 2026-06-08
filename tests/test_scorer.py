"""
Unit tests for entry scorer module
"""

import pytest
from src.your_strategy.config import StrategyConfig
from src.your_strategy.entry_scorer import EntryScorer
from src.your_strategy.filters import TokenData


class TestEntryScorer:
    """Test F1-F6 scoring system"""
    
    @pytest.fixture
    def config(self):
        return StrategyConfig()
    
    @pytest.fixture
    def scorer(self, config):
        return EntryScorer(config)
    
    @pytest.fixture
    def valid_token(self):
        return TokenData(
            mint="test",
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
    
    def test_f1_scoring(self, scorer):
        """Test F1 (vs_pre_max) scoring"""
        assert scorer._score_f1(0.3) == -10
        assert scorer._score_f1(0.7) == 15
        assert scorer._score_f1(0.95) == 10
        assert scorer._score_f1(1.02) == 5
        assert scorer._score_f1(1.1) == -5
    
    def test_f2_scoring(self, scorer):
        """Test F2 (holder_growth) scoring"""
        assert scorer._score_f2(1.5) == 15
        assert scorer._score_f2(0.7) == 10
        assert scorer._score_f2(0.4) == 5
        assert scorer._score_f2(0.2) == -5
        assert scorer._score_f2(0) == 0  # No penalty on first sight
    
    def test_f3_scoring(self, scorer):
        """Test F3 (BSR) scoring"""
        assert scorer._score_f3(1.7) == 5
        assert scorer._score_f3(2.5) == 10
        assert scorer._score_f3(3.5) == 8
        assert scorer._score_f3(1.2) == 3
        assert scorer._score_f3(0.8) == -10
    
    def test_f4_scoring(self, scorer):
        """Test F4 (holder/UT ratio) scoring"""
        assert scorer._score_f4(1.5) == 10
        assert scorer._score_f4(3.0) == 5
        assert scorer._score_f4(7.0) == 0
        assert scorer._score_f4(15.0) == -8
    
    def test_f5_scoring(self, scorer):
        """Test F5 (speed factor) scoring"""
        assert scorer._score_f5(2.0, 0.3) == 5  # volume_ratio OK
        assert scorer._score_f5(1.0, 0.6) == 5  # ut_growth OK
        assert scorer._score_f5(2.0, 0.6) == 10  # Both OK
        assert scorer._score_f5(1.0, 0.3) == 0  # Neither
    
    def test_age_multiplier(self, scorer):
        """Test age multiplier calculation"""
        # Young token
        mult_young = scorer._get_age_multiplier(2)
        assert 0.5 <= mult_young < 1.0
        
        # Optimal age
        mult_opt = scorer._get_age_multiplier(10)
        assert mult_opt == 1.0
        
        # Old token
        mult_old = scorer._get_age_multiplier(30)
        assert mult_old < 1.0
    
    def test_evaluate_strong_signal(self, scorer, valid_token):
        """Test evaluation with strong signal"""
        decision = scorer.evaluate(
            valid_token,
            vs_pre_max=0.7,  # Good pullback
            holder_growth=0.8,  # Good growth
            volume_ratio=2.0,  # Good volume
            ut_growth=0.6,  # Good UT growth
        )
        
        assert decision.should_buy
        assert decision.score >= scorer.config.ENTRY_SCORE_THRESHOLD
        assert 'f1' in decision.factors
        assert 'f2' in decision.factors
    
    def test_evaluate_weak_signal(self, scorer, valid_token):
        """Test evaluation with weak signal"""
        decision = scorer.evaluate(
            valid_token,
            vs_pre_max=0.3,  # Bad pullback
            holder_growth=0.1,  # Weak growth
            volume_ratio=1.0,  # No volume
            ut_growth=0.0,  # No UT growth
        )
        
        assert not decision.should_buy
        assert decision.score < scorer.config.ENTRY_SCORE_THRESHOLD
