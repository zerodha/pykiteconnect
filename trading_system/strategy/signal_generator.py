# -*- coding: utf-8 -*-
"""
Signal Generation using Technical Indicators
RSI, SMA, MACD, ATR, and other indicators
"""

import numpy as np
from utils.logger import TradingLogger


class SignalGenerator:
    """
    Generates trading signals using technical indicators.
    """

    def __init__(self):
        """Initialize signal generator."""
        self.logger = TradingLogger.get_logger()

    # ===== MOVING AVERAGES =====
    @staticmethod
    def calculate_sma(prices, period):
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: list - Price data
            period: int - Period for SMA
            
        Returns:
            list - SMA values
        """
        if len(prices) < period:
            return None
        
        sma = np.convolve(prices, np.ones(period) / period, mode='valid')
        # Pad the beginning with NaN to match length
        return [np.nan] * (period - 1) + list(sma)

    @staticmethod
    def calculate_ema(prices, period):
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: list - Price data
            period: int - Period for EMA
            
        Returns:
            list - EMA values
        """
        if len(prices) < period:
            return None
        
        prices = np.array(prices, dtype=float)
        ema = np.zeros_like(prices)
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # First EMA is the SMA
        ema[period - 1] = np.mean(prices[:period])
        
        # Calculate subsequent EMAs
        for i in range(period, len(prices)):
            ema[i] = prices[i] * multiplier + ema[i - 1] * (1 - multiplier)
        
        # Pad the beginning
        ema[:period - 1] = np.nan
        return list(ema)

    # ===== RSI (Relative Strength Index) =====
    @staticmethod
    def calculate_rsi(prices, period=14):
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: list - Price data
            period: int - Period for RSI (default 14)
            
        Returns:
            list - RSI values (0-100)
        """
        if len(prices) < period + 1:
            return None
        
        prices = np.array(prices, dtype=float)
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gain = np.convolve(gains, np.ones(period) / period, mode='valid')
        avg_loss = np.convolve(losses, np.ones(period) / period, mode='valid')
        
        # Calculate RS and RSI
        rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        # Pad the beginning
        rsi_padded = [np.nan] * (period) + list(rsi)
        return rsi_padded[:len(prices)]

    # ===== MACD (Moving Average Convergence Divergence) =====
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: list - Price data
            fast: int - Fast EMA period (default 12)
            slow: int - Slow EMA period (default 26)
            signal: int - Signal line EMA period (default 9)
            
        Returns:
            dict - MACD line, signal line, and histogram
        """
        if len(prices) < slow + signal:
            return None
        
        ema_fast = SignalGenerator.calculate_ema(prices, fast)
        ema_slow = SignalGenerator.calculate_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return None
        
        # MACD line
        macd_line = np.array(ema_fast) - np.array(ema_slow)
        
        # Signal line (EMA of MACD)
        signal_line = SignalGenerator.calculate_ema(list(macd_line), signal)
        
        # Histogram
        histogram = macd_line - np.array(signal_line)
        
        return {
            "macd": list(macd_line),
            "signal": signal_line,
            "histogram": list(histogram),
        }

    # ===== ATR (Average True Range) =====
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """
        Calculate Average True Range (volatility indicator).
        
        Args:
            high: list - High prices
            low: list - Low prices
            close: list - Close prices
            period: int - Period for ATR (default 14)
            
        Returns:
            list - ATR values
        """
        if len(high) < period or len(low) < period or len(close) < period:
            return None
        
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        
        # Calculate true range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.max([tr1, tr2, tr3], axis=0)
        
        # Calculate ATR
        atr = np.convolve(tr, np.ones(period) / period, mode='valid')
        
        # Pad the beginning
        atr_padded = [np.nan] * (period - 1) + list(atr)
        return atr_padded[:len(close)]

    # ===== BOLLINGER BANDS =====
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, num_std_dev=2):
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: list - Price data
            period: int - Period for SMA (default 20)
            num_std_dev: int - Number of standard deviations (default 2)
            
        Returns:
            dict - Middle band (SMA), upper band, lower band
        """
        if len(prices) < period:
            return None
        
        prices = np.array(prices, dtype=float)
        
        # Middle band (SMA)
        middle_band = np.convolve(prices, np.ones(period) / period, mode='valid')
        middle_band_padded = [np.nan] * (period - 1) + list(middle_band)
        middle_band_padded = middle_band_padded[:len(prices)]
        
        # Calculate standard deviation
        std_dev = []
        for i in range(period - 1, len(prices)):
            std = np.std(prices[i - period + 1:i + 1])
            std_dev.append(std)
        
        std_dev_padded = [np.nan] * (period - 1) + std_dev
        std_dev_padded = std_dev_padded[:len(prices)]
        
        # Bands
        upper_band = np.array(middle_band_padded) + (num_std_dev * np.array(std_dev_padded))
        lower_band = np.array(middle_band_padded) - (num_std_dev * np.array(std_dev_padded))
        
        return {
            "middle": middle_band_padded,
            "upper": list(upper_band),
            "lower": list(lower_band),
        }

    # ===== MOMENTUM =====
    @staticmethod
    def calculate_momentum(prices, period=10):
        """
        Calculate Momentum indicator.
        
        Args:
            prices: list - Price data
            period: int - Period for momentum (default 10)
            
        Returns:
            list - Momentum values
        """
        if len(prices) < period:
            return None
        
        prices = np.array(prices, dtype=float)
        momentum = np.diff(prices, n=period)
        
        # Pad the beginning
        momentum_padded = [np.nan] * period + list(momentum)
        return momentum_padded[:len(prices)]

    # ===== STOCHASTIC OSCILLATOR =====
    @staticmethod
    def calculate_stochastic(high, low, close, period=14, smooth_k=3, smooth_d=3):
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: list - High prices
            low: list - Low prices
            close: list - Close prices
            period: int - Period for stochastic (default 14)
            smooth_k: int - Period for K smoothing (default 3)
            smooth_d: int - Period for D smoothing (default 3)
            
        Returns:
            dict - %K and %D lines
        """
        if len(high) < period or len(low) < period or len(close) < period:
            return None
        
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        
        # Calculate raw stochastic
        lowest_low = np.array([np.min(low[max(0, i - period + 1):i + 1]) for i in range(len(low))])
        highest_high = np.array([np.max(high[max(0, i - period + 1):i + 1]) for i in range(len(high))])
        
        raw_k = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
        
        # Smooth K
        k = SignalGenerator.calculate_sma(list(raw_k), smooth_k)
        
        # Smooth D (D is SMA of K)
        d = SignalGenerator.calculate_sma(k, smooth_d) if k else None
        
        return {
            "k": k,
            "d": d,
        }

    # ===== UTILITY FUNCTIONS =====
    @staticmethod
    def get_last_value(indicator_values):
        """
        Get the last valid (non-NaN) value from indicator.
        
        Args:
            indicator_values: list - Indicator values
            
        Returns:
            float - Last valid value or None
        """
        if not indicator_values:
            return None
        
        for value in reversed(indicator_values):
            if value is not None and not np.isnan(value):
                return value
        return None

    @staticmethod
    def get_trend_direction(indicator_values, window=3):
        """
        Determine trend direction from indicator.
        
        Args:
            indicator_values: list - Indicator values
            window: int - Window size for trend detection
            
        Returns:
            str - "UP", "DOWN", or "FLAT"
        """
        if len(indicator_values) < window:
            return "FLAT"
        
        recent_values = [v for v in indicator_values[-window:] if v is not None and not np.isnan(v)]
        
        if len(recent_values) < 2:
            return "FLAT"
        
        # Check trend
        if all(recent_values[i] < recent_values[i + 1] for i in range(len(recent_values) - 1)):
            return "UP"
        elif all(recent_values[i] > recent_values[i + 1] for i in range(len(recent_values) - 1)):
            return "DOWN"
        else:
            return "FLAT"
