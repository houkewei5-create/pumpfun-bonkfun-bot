"""
Your Custom Auto-Trading Strategy Module for Pump.fun

This module implements a complete automated trading strategy with:
- Phase 1 & 2 filtering (hard filters)
- Entry scoring system (F1-F6 factors)
- Position management
- Exit detection (stop loss, take profit, rug detection)
- Risk management
"""

from .config import StrategyConfig
from .filters import SecurityFilter, Phase1Filter, Phase2Filter
from .entry_scorer import EntryScorer, EntryDecision
from .decider import StrategyDecider
from .position_context import PositionContext
from .data_source import DataSource
from .signal_bus import Signal, SignalBus, Severity
from .detectors import (
    StopLossDetector,
    TakeProfitDetector,
    RugDetector,
    DumpDetector,
)

__all__ = [
    "StrategyConfig",
    "SecurityFilter",
    "Phase1Filter",
    "Phase2Filter",
    "EntryScorer",
    "EntryDecision",
    "StrategyDecider",
    "PositionContext",
    "DataSource",
    "Signal",
    "SignalBus",
    "Severity",
    "StopLossDetector",
    "TakeProfitDetector",
    "RugDetector",
    "DumpDetector",
]
