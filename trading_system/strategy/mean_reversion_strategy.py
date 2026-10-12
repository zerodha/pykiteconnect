# -*- coding: utf-8 -*-
"""
Mean Reversion Strategy
Identifies oversold/overbought conditions and reverses to mean
"""

import numpy as np
from strategy.base_strategy import BaseStrategy
from strategy.signal_generator import SignalGenerator
from utils.logger import TradingLogger


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy using Bollinger Bands and RSI.
    
    Entry Rules:
    - BUY: Price touches lower Bollinger Band + RSI oversold
    - SELL: Price touches upper Bollinger Band + RSI overbought
    
    Exit Rules:
    - Exit when price returns to middle band (SMA)
    """

    def __init__(self, config):
        """
        Initialize Mean Reversion Strategy.
        
        Args:
            config: dict - Strategy configuration
        """
        super().__init__("Mean Reversion Strategy", config)
        self.signal_gen = SignalGenerator()
        self.logger = TradingLogger.get_logger()

    def generate_signal(self, symbol, price_data, historical_data):
        """
        Generate trading signal based on mean reversion.
        
        Args:
            symbol: str - Trading symbol
            price_data: dict - Current price data
            historical_data: list - Historical OHLC data
            
        Returns:
            dict - Signal with direction and strength
        """
        signal = {
            "symbol": symbol,
            "direction": "HOLD",
            "strength": 0,
            "confidence": 0,
            "indicators": {},
            "entry_price": price_data.get("ltp"),
            "reason": "",
        }

        try:
            if not historical_data or len(historical_data) < 50:
                signal["reason"] = "Insufficient historical data"
                return signal

            closes = np.array([d["close"] for d in historical_data], dtype=float)
            highs = np.array([d["high"] for d in historical_data], dtype=float)
            lows = np.array([d["low"] for d in historical_data], dtype=float)
            current_price = price_data.get("ltp", closes[-1])

            # Calculate indicators
            bb = self.signal_gen.calculate_bollinger_bands(
                list(closes), period=self.config.get("bb_period", 20)
            )
            rsi = self.signal_gen.calculate_rsi(list(closes), period=self.config.get("rsi_period", 14))

            current_bb_upper = self.signal_gen.get_last_value(bb["upper"])
            current_bb_lower = self.signal_gen.get_last_value(bb["lower"])
            current_bb_middle = self.signal_gen.get_last_value(bb["middle"])
            current_rsi = self.signal_gen.get_last_value(rsi)

            signal["indicators"] = {
                "rsi": current_rsi,
                "bb_upper": current_bb_upper,
                "bb_middle": current_bb_middle,
                "bb_lower": current_bb_lower,
                "current_price": current_price,
            }

            strength = 0
            reasons = []

            # Check lower band (oversold - BUY signal)
            if current_bb_lower and current_price <= current_bb_lower:
                strength += 40
                reasons.append(f"Price at lower BB ({current_price:.2f} <= {current_bb_lower:.2f})")
                
                if current_rsi and current_rsi < self.config.get("rsi_oversold", 30):
                    strength += 30
                    reasons.append(f"RSI oversold ({current_rsi:.2f})")
            
            # Check upper band (overbought - SELL signal)
            if current_bb_upper and current_price >= current_bb_upper:
                strength -= 40
                reasons.append(f"Price at upper BB ({current_price:.2f} >= {current_bb_upper:.2f})")
                
                if current_rsi and current_rsi > self.config.get("rsi_overbought", 70):
                    strength -= 30
                    reasons.append(f"RSI overbought ({current_rsi:.2f})")
            
            # Mean reversion tendency check
            if current_bb_middle:
                mid_band_distance = abs(current_price - current_bb_middle)
                bb_width = (current_bb_upper - current_bb_lower) / 2 if current_bb_upper else 1
                
                if mid_band_distance > bb_width:
                    strength = abs(strength) * 0.7  # Reduce strength if far from mean

            confidence = min(100, abs(strength))
            
            if strength > 40:
                signal["direction"] = "BUY"
                signal["strength"] = strength
                signal["confidence"] = confidence
            elif strength < -40:
                signal["direction"] = "SELL"
                signal["strength"] = abs(strength)
                signal["confidence"] = confidence
            else:
                signal["direction"] = "HOLD"
                signal["strength"] = abs(strength)
                signal["confidence"] = confidence

            signal["reason"] = " | ".join(reasons) if reasons else "No clear signal"

            # Calculate stop loss and target
            if current_bb_upper and current_bb_lower:
                bb_range = current_bb_upper - current_bb_lower
                signal["stop_loss_distance"] = bb_range * 0.5

            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {str(e)}")
            signal["reason"] = f"Error: {str(e)}"
            return signal

    def validate_signal(self, signal):
        """
        Validate if signal meets entry criteria.
        
        Args:
            signal: dict - Generated signal
            
        Returns:
            bool - True if signal is valid for entry
        """
        is_valid = (
            signal.get("direction") in ["BUY", "SELL"] and
            signal.get("confidence", 0) >= 60  # Higher confidence for mean reversion
        )
        
        if is_valid:
            self.logger.info(
                f"{signal['symbol']}: {signal['direction']} signal (Confidence: {signal['confidence']:.0f}%) - "
                f"{signal['reason']}"
            )
        
        return is_valid

    def get_stop_loss(self, symbol, direction, entry_price, atr=None):
        """
        Calculate stop loss for mean reversion.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            entry_price: float - Entry price
            atr: float - Average True Range (optional)
            
        Returns:
            float - Stop loss price
        """
        if atr:
            if direction == "BUY":
                return entry_price - (atr * 2)  # Larger SL for mean reversion
            else:  # SELL
                return entry_price + (atr * 2)
        else:
            stop_loss_pct = self.config.get("stop_loss_percent", 3.0)  # 3% default
            if direction == "BUY":
                return entry_price * (1 - stop_loss_pct / 100)
            else:  # SELL
                return entry_price * (1 + stop_loss_pct / 100)

    def get_target(self, symbol, direction, entry_price, stop_loss):
        """
        Calculate profit target for mean reversion.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            entry_price: float - Entry price
            stop_loss: float - Stop loss price
            
        Returns:
            float - Target price
        """
        risk = abs(entry_price - stop_loss)
        risk_reward_ratio = self.config.get("risk_reward_ratio", 1.5)  # Lower ratio for mean reversion
        
        if direction == "BUY":
            return entry_price + (risk * risk_reward_ratio)
        else:  # SELL
            return entry_price - (risk * risk_reward_ratio)
