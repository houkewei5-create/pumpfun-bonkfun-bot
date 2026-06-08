"""
Unit tests for filters module
"""

import pytest
from src.your_strategy.config import StrategyConfig
from src.your_strategy.filters import TokenData, SecurityFilter, Phase1Filter, Phase2Filter


class TestSecurityFilter:
    """Test zero-tolerance security filters"""
    
    @pytest.fixture
    def config(self):
        return StrategyConfig()
    
    @pytest.fixture
    def security_filter(self, config):
        return SecurityFilter(config)
    
    def test_lp_not_burned(self, security_filter):
        """Test LP burn check"""
        token = TokenData(
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
            is_lp_burned=False,
            is_lp_locked=False,
            lp_burn_ratio=0.95,  # < 99%
            is_mint_revoked=True,
            dev_holding_ratio=0.02,
        )
        passed, reason = security_filter.check(token)
        assert not passed
        assert "LP" in reason
    
    def test_mint_not_revoked(self, security_filter):
        """Test mint revoke check"""
        token = TokenData(
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
            is_mint_revoked=False,  # Not revoked
            dev_holding_ratio=0.02,
        )
        passed, reason = security_filter.check(token)
        assert not passed
        assert "Mint" in reason
    
    def test_dev_holding_too_high(self, security_filter):
        """Test dev holding check"""
        token = TokenData(
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
            dev_holding_ratio=0.10,  # > 5%
        )
        passed, reason = security_filter.check(token)
        assert not passed
        assert "Dev" in reason
    
    def test_security_pass(self, security_filter):
        """Test passing security checks"""
        token = TokenData(
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
        passed, reason = security_filter.check(token)
        assert passed


class TestPhase1Filter:
    """Test Phase1 basic filters"""
    
    @pytest.fixture
    def config(self):
        return StrategyConfig()
    
    @pytest.fixture
    def phase1_filter(self, config):
        return Phase1Filter(config)
    
    @pytest.fixture
    def valid_token(self):
        """Create a token that passes all checks"""
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
    
    def test_age_too_young(self, phase1_filter, valid_token):
        valid_token.age_minutes = 0.5  # < 1 min
        passed, reason = phase1_filter.check(valid_token)
        assert not passed
        assert "Age" in reason
    
    def test_age_too_old(self, phase1_filter, valid_token):
        valid_token.age_minutes = 2000  # > 1440 min
        passed, reason = phase1_filter.check(valid_token)
        assert not passed
        assert "Age" in reason
    
    def test_holder_too_few(self, phase1_filter, valid_token):
        valid_token.holder_count = 20  # < 30
        passed, reason = phase1_filter.check(valid_token)
        assert not passed
        assert "Holder" in reason
    
    def test_liquidity_too_low(self, phase1_filter, valid_token):
        valid_token.liquidity_usd = 1000  # < 5000
        passed, reason = phase1_filter.check(valid_token)
        assert not passed
        assert "Liquidity" in reason
    
    def test_valid_token_passes(self, phase1_filter, valid_token):
        passed, reason = phase1_filter.check(valid_token)
        assert passed
        assert "passed" in reason.lower()


class TestPhase2Filter:
    """Test Phase2 safety verification"""
    
    @pytest.fixture
    def config(self):
        return StrategyConfig()
    
    @pytest.fixture
    def phase2_filter(self, config):
        return Phase2Filter(config)
    
    @pytest.fixture
    def valid_token(self):
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
    
    def test_safety_score_calculation(self, phase2_filter, valid_token):
        score = phase2_filter.calculate_safety_score(valid_token)
        assert 0 <= score <= 1
        # With all good checks, should get high score
        assert score >= 0.5
    
    def test_rat_manipulation_detection(self, phase2_filter, valid_token):
        valid_token.rat = 0.35  # > 0.3
        passed, reason, score = phase2_filter.check(valid_token)
        assert not passed
        assert "Rat" in reason
