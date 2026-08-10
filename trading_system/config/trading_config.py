# -*- coding: utf-8 -*-
"""
Trading Configuration
Market hours, instruments, risk parameters, and strategy settings
"""

import pytz
import os
from datetime import time
from enum import Enum


class Market(Enum):
    """Market selection"""
    NSE = "nse"
    MCX = "mcx"


class TradingConfig:
    """
    Central configuration for the intraday trading system.
    Modify these settings as needed for your strategy.
    """

    # ===== MARKET SELECTION =====
    MARKET = Market.NSE  # Change to Market.MCX for commodity trading

    # ===== MARKET HOURS =====
    MARKET_HOURS = {
        Market.NSE: {
            "open": time(9, 15),
            "close": time(15, 30),
            "timezone": pytz.timezone('Asia/Kolkata'),
            "trading_days": [0, 1, 2, 3, 4],  # Monday to Friday
        },
        Market.MCX: {
            "open": time(9, 0),
            "close": time(23, 30),
            "timezone": pytz.timezone('Asia/Kolkata'),
            "trading_days": [0, 1, 2, 3, 4],  # Monday to Friday
        },
    }

    # ===== INSTRUMENT CONFIGURATION =====
    # Define instruments to trade: symbols, exchange, lot size
    INSTRUMENTS = {
        "NSE": [
            {"symbol": "INFY", "exchange": "NSE", "lot_size": 1, "type": "EQUITY"},
            {"symbol": "TCS", "exchange": "NSE", "lot_size": 1, "type": "EQUITY"},
            {"symbol": "RELIANCE", "exchange": "NSE", "lot_size": 1, "type": "EQUITY"},
        ],
        "MCX": [
            {"symbol": "CRUDE", "exchange": "MCX", "lot_size": 100, "type": "COMMODITY"},
            {"symbol": "GOLD", "exchange": "MCX", "lot_size": 1, "type": "COMMODITY"},
        ],
    }

    # ===== RISK MANAGEMENT =====
    RISK_CONFIG = {
        "max_loss_per_trade": 500,  # Maximum loss per trade in INR
        "max_daily_loss": 2000,  # Maximum daily loss in INR
        "max_position_size": 10000,  # Maximum capital per position in INR
        "position_sizing_method": "fixed",  # "fixed" or "risk_based"
        "risk_per_trade": 1.0,  # Risk per trade as % of capital (for risk_based sizing)
        "max_open_positions": 3,  # Maximum concurrent positions
        "max_profit_target_multiplier": 2.0,  # Risk-reward ratio (profit target = SL * multiplier)
    }

    # ===== MOMENTUM STRATEGY PARAMETERS =====
    STRATEGY_CONFIG = {
        "momentum": {
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "sma_short_period": 9,
            "sma_long_period": 21,
            "atr_period": 14,  # Average True Range for volatility-based stop loss
            "entry_signal": "rsi_sma_crossover",  # Signal type: "rsi_sma_crossover", "rsi_only", etc.
            "timeframe": "5min",  # Candle timeframe: "1min", "5min", "15min", "30min"
            "lookback_candles": 50,  # Number of candles to analyze
        }
    }

    # ===== POSITION MANAGEMENT =====
    POSITION_CONFIG = {
        "auto_square_off": True,  # Automatically close positions at market close
        "square_off_time": time(15, 25),  # Square off 5 mins before market close (NSE)
        "stop_loss_type": "atr",  # "fixed_points", "fixed_percent", "atr"
        "stop_loss_atr_multiplier": 1.5,  # For ATR-based stop loss
        "stop_loss_fixed_points": 20,  # For fixed points stop loss
        "use_trailing_stop": False,  # Enable trailing stop loss
        "trailing_stop_percent": 2.0,  # Trailing stop as % of entry price
    }

    # ===== API & CONNECTIVITY =====
    API_CONFIG = {
        "timeout": 10,  # API request timeout in seconds
        "max_retries": 3,  # Max retries for API calls
        "websocket_reconnect_attempts": 10,
        "websocket_reconnect_delay": 5,  # seconds
    }

    # ===== EXECUTION SAFETY =====
    EXECUTION_CONFIG = {
        "paper_trading_default": True,
        "live_trading_env": "LIVE_TRADING",
        "allow_live_orders_env": "ALLOW_LIVE_ORDERS",
    }

    # ===== LOGGING & ALERTS =====
    LOGGING_CONFIG = {
        "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
        "log_file": "trading_system.log",
        "max_log_size_mb": 10,
        "backup_count": 5,
    }

    # ===== TRADING HOURS FOR CURRENT MARKET =====
    @classmethod
    def get_market_hours(cls):
        """Get market hours for the selected market"""
        return cls.MARKET_HOURS[cls.MARKET]

    @classmethod
    def get_instruments(cls):
        """Get instruments for the selected market"""
        exchange_key = "NSE" if cls.MARKET == Market.NSE else "MCX"
        return cls.INSTRUMENTS.get(exchange_key, [])

    @classmethod
    def switch_market(cls, market: Market):
        """Switch between NSE and MCX"""
        cls.MARKET = market
        print(f"Switched to {market.value.upper()} market")

    @classmethod
    def get_execution_config(cls):
        """Resolve execution configuration from defaults + environment flags."""
        live_flag = os.getenv(cls.EXECUTION_CONFIG["live_trading_env"], "false").strip().lower() == "true"
        allow_live_orders_flag = (
            os.getenv(cls.EXECUTION_CONFIG["allow_live_orders_env"], "false").strip().lower() == "true"
        )

        return {
            "live_trading_requested": live_flag,
            "allow_live_orders": allow_live_orders_flag,
            "live_orders_enabled": live_flag and allow_live_orders_flag,
            "paper_trading": not (live_flag and allow_live_orders_flag),
            "live_trading_env": cls.EXECUTION_CONFIG["live_trading_env"],
            "allow_live_orders_env": cls.EXECUTION_CONFIG["allow_live_orders_env"],
        }
