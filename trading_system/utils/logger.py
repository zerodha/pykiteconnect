# -*- coding: utf-8 -*-
"""
Logging Configuration
Structured logging for trading system
"""

import logging
import logging.handlers
from datetime import datetime
from config.trading_config import TradingConfig


class TradingLogger:
    """Centralized logging for the trading system"""

    _logger = None
    _trade_logger = None

    @classmethod
    def get_logger(cls, name="trading_system"):
        """
        Get or create logger instance.
        Returns: logger object
        """
        if cls._logger is None:
            cls._setup_logging()
        return logging.getLogger(name)

    @classmethod
    def get_trade_logger(cls):
        """
        Get dedicated trade logger for order/position tracking.
        Returns: logger object
        """
        if cls._trade_logger is None:
            cls._setup_trade_logging()
        return cls._trade_logger

    @classmethod
    def _setup_logging(cls):
        """
        Setup main logging configuration.
        """
        log_config = TradingConfig.LOGGING_CONFIG
        log_level = getattr(logging, log_config["log_level"])
        log_file = log_config["log_file"]
        max_bytes = log_config["max_log_size_mb"] * 1024 * 1024
        backup_count = log_config["backup_count"]

        # Create logger
        cls._logger = logging.getLogger("trading_system")
        cls._logger.setLevel(log_level)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        cls._logger.addHandler(file_handler)
        cls._logger.addHandler(console_handler)

    @classmethod
    def _setup_trade_logging(cls):
        """
        Setup dedicated trade logging to a separate file.
        """
        trade_log_file = f"trades_{datetime.now().strftime('%Y%m%d')}.log"
        
        cls._trade_logger = logging.getLogger("trades")
        cls._trade_logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(trade_log_file)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        cls._trade_logger.addHandler(file_handler)

    @classmethod
    def log_trade(cls, action, details):
        """
        Log trade-related events.
        
        Args:
            action: str - Type of action (ENTRY, EXIT, SL_HIT, etc.)
            details: dict - Trade details
        """
        trade_logger = cls.get_trade_logger()
        message = f"{action} | {details}"
        trade_logger.info(message)
