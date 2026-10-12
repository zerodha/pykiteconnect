# -*- coding: utf-8 -*-
"""
Base Strategy Class
Abstract base for all trading strategies
"""

from abc import ABC, abstractmethod
from utils.logger import TradingLogger
from datetime import datetime


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    All strategies should inherit from this class.
    """

    def __init__(self, name, config):
        """
        Initialize strategy.
        
        Args:
            name: str - Strategy name
            config: dict - Strategy configuration
        """
        self.name = name
        self.config = config
        self.logger = TradingLogger.get_logger()
        self.signals = {}  # {symbol: {"signal": "BUY"/"SELL"/"HOLD", "strength": 0-100, ...}}

    @abstractmethod
    def generate_signal(self, symbol, price_data, historical_data):
        """
        Generate trading signal for a symbol.
        
        Args:
            symbol: str - Trading symbol
            price_data: dict - Current price data
            historical_data: list - Historical OHLC data
            
        Returns:
            dict - Signal with BUY/SELL/HOLD and strength (0-100)
        """
        pass

    @abstractmethod
    def validate_signal(self, signal):
        """
        Validate if signal meets entry criteria.
        
        Args:
            signal: dict - Generated signal
            
        Returns:
            bool - True if signal is valid for entry
        """
        pass

    def get_signal(self, symbol):
        """
        Get current signal for a symbol.
        
        Args:
            symbol: str - Trading symbol
            
        Returns:
            dict - Current signal or None
        """
        return self.signals.get(symbol)

    def update_signal(self, symbol, signal):
        """
        Update signal for a symbol.
        
        Args:
            symbol: str - Trading symbol
            signal: dict - Signal data
        """
        self.signals[symbol] = signal
        signal["timestamp"] = datetime.now()

    def clear_signals(self):
        """
        Clear all stored signals.
        """
        self.signals.clear()
