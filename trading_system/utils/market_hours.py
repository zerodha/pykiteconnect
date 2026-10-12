# -*- coding: utf-8 -*-
"""
Market Hours Utilities
Checks if market is open and trading is allowed
"""

from datetime import datetime
from config.trading_config import TradingConfig, Market
import pytz


class MarketHours:
    """Utility class for market hour management"""

    @staticmethod
    def is_market_open():
        """
        Check if the current market is open for trading.
        Returns: bool
        """
        market_config = TradingConfig.get_market_hours()
        tz = market_config["timezone"]
        
        now = datetime.now(tz)
        current_time = now.time()
        current_day = now.weekday()
        
        market_open = market_config["open"]
        market_close = market_config["close"]
        trading_days = market_config["trading_days"]
        
        # Check if today is a trading day
        if current_day not in trading_days:
            return False
        
        # Check if current time is within market hours
        return market_open <= current_time <= market_close

    @staticmethod
    def get_time_to_market_close():
        """
        Get remaining time until market closes.
        Returns: timedelta object
        """
        market_config = TradingConfig.get_market_hours()
        tz = market_config["timezone"]
        
        now = datetime.now(tz)
        market_close_time = market_config["close"]
        
        # Create a datetime object for market close today
        market_close_dt = now.replace(
            hour=market_close_time.hour,
            minute=market_close_time.minute,
            second=0,
            microsecond=0
        )
        
        if now > market_close_dt:
            return None  # Market already closed
        
        return market_close_dt - now

    @staticmethod
    def get_market_status():
        """
        Get detailed market status information.
        Returns: dict with status details
        """
        market_config = TradingConfig.get_market_hours()
        tz = market_config["timezone"]
        
        now = datetime.now(tz)
        is_open = MarketHours.is_market_open()
        time_to_close = MarketHours.get_time_to_market_close()
        
        return {
            "market": TradingConfig.MARKET.value.upper(),
            "is_open": is_open,
            "current_time": now,
            "market_open": market_config["open"],
            "market_close": market_config["close"],
            "time_to_close": time_to_close,
            "timezone": str(tz),
        }
