# -*- coding: utf-8 -*-
"""
Breakout Strategy
Identifies breakouts from consolidation zones
"""

import numpy as np
from strategy.base_strategy import BaseStrategy
from strategy.signal_generator import SignalGenerator
from utils.logger import TradingLogger


class BreakoutStrategy(BaseStrategy):
    """
    Breakout Strategy using Support/Resistance and Volume.
    
    Entry Rules:
    - BUY: Price breaks above resistance + volume surge
    - SELL: Price breaks below support + volume surge
    
    Exit Rules:
    - Exit when price reverses from breakout direction
    """

    def __init__(self, config):
        """
        Initialize Breakout Strategy.
        
        Args:
            config: dict - Strategy configuration
        """
        super().__init__("Breakout Strategy", config)
        self.signal_gen = SignalGenerator()
        self.logger = TradingLogger.get_logger()

    def generate_signal(self, symbol, price_data, historical_data):
        """
        Generate trading signal based on breakout.
        
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
            volumes = np.array([d.get("volume", 0) for d in historical_data], dtype=float)
            current_price = price_data.get("ltp", closes[-1])
            current_volume = price_data.get("volume", volumes[-1] if len(volumes) > 0 else 0)

            # Calculate support and resistance
            period = self.config.get("period", 20)
            resistance = np.max(highs[-period:])
            support = np.min(lows[-period:])
            avg_volume = np.mean(volumes[-period:])

            # Volume surge check
            volume_surge = current_volume > avg_volume * 1.5 if avg_volume > 0 else False

            signal["indicators"] = {
                "resistance": resistance,
                "support": support,
                "current_price": current_price,
                "volume_surge": volume_surge,
                "current_volume": current_volume,
                "avg_volume": avg_volume,
            }

            strength = 0
            reasons = []

            # Check breakout above resistance
            if current_price > resistance:
                strength += 30
                reasons.append(f"Price above resistance ({current_price:.2f} > {resistance:.2f})")
                
                if volume_surge:
                    strength += 30
                    reasons.append(f"Volume surge ({current_volume:.0f} > {avg_volume:.0f})")
            
            # Check breakout below support
            elif current_price < support:
                strength -= 30
                reasons.append(f"Price below support ({current_price:.2f} < {support:.2f})")
                
                if volume_surge:
                    strength -= 30
                    reasons.append(f"Volume surge ({current_volume:.0f} > {avg_volume:.0f})")
            
            # Check for consolidation (no breakout)
            else:
                consolidation_range = resistance - support
                mid_point = (resistance + support) / 2
                
                if abs(current_price - mid_point) < consolidation_range * 0.2:
                    reasons.append("In consolidation zone")

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

            signal["reason"] = " | ".join(reasons) if reasons else "No clear breakout"

            # Calculate stop loss and target
            breakout_range = resistance - support
            signal["stop_loss_distance"] = breakout_range * 0.5

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
            signal.get("confidence", 0) >= 50 and
            signal.get("indicators", {}).get("volume_surge", False)  # Volume confirmation required
        )
        
        if is_valid:
            self.logger.info(
                f"{signal['symbol']}: {signal['direction']} breakout (Confidence: {signal['confidence']:.0f}%) - "
                f"{signal['reason']}"
            )
        
        return is_valid

    def get_stop_loss(self, symbol, direction, entry_price, atr=None):
        """
        Calculate stop loss for breakout.
        
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
                return entry_price - atr
            else:  # SELL
                return entry_price + atr
        else:
            stop_loss_pct = self.config.get("stop_loss_percent", 2.0)
            if direction == "BUY":
                return entry_price * (1 - stop_loss_pct / 100)
            else:  # SELL
                return entry_price * (1 + stop_loss_pct / 100)

    def get_target(self, symbol, direction, entry_price, stop_loss):
        """
        Calculate profit target for breakout.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            entry_price: float - Entry price
            stop_loss: float - Stop loss price
            
        Returns:
            float - Target price
        """
        risk = abs(entry_price - stop_loss)
        risk_reward_ratio = self.config.get("risk_reward_ratio", 2.0)
        
        if direction == "BUY":
            return entry_price + (risk * risk_reward_ratio)
        else:  # SELL
            return entry_price - (risk * risk_reward_ratio)
