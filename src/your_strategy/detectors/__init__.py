"""
Detectors - Various signal detectors for position management
"""

from .stop_loss import StopLossDetector
from .take_profit import TakeProfitDetector
from .rug_detector import RugDetector
from .dump_detector import DumpDetector

__all__ = [
    'StopLossDetector',
    'TakeProfitDetector',
    'RugDetector',
    'DumpDetector',
]
