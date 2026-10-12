# -*- coding: utf-8 -*-
"""
Momentum Trading Strategy
RSI + SMA crossover based momentum strategy
"""

import numpy as np
from strategy.base_strategy import BaseStrategy
from strategy.signal_generator import SignalGenerator
from utils.logger import TradingLogger


class MomentumStrategy(BaseStrategy):
    """
    Momentum-based trading strategy using RSI and Moving Averages.
    
    Entry Rules:
    - BUY: RSI oversold + SMA crossover (fast > slow) + price above lower BB
    - SELL: RSI overbought + SMA crossover (fast < slow) + price below upper BB
    
    Exit Rules:
    - Target: Risk-reward ratio met
    - Stop Loss: ATR-based or fixed points
    """

    def __init__(self, config):
        """
        Initialize Momentum Strategy.
        
        Args:
            config: dict - Strategy configuration
        """
        super().__init__("Momentum Strategy", config)
        self.signal_gen = SignalGenerator()
        self.logger = TradingLogger.get_logger()

    def generate_signal(self, symbol, price_data, historical_data):
        """
        Generate trading signal based on momentum indicators.
        
        Args:
            symbol: str - Trading symbol
            price_data: dict - Current price data {ltp, bid, ask, volume, timestamp}
            historical_data: list - Historical OHLC data [{open, high, low, close}, ...]
            
        Returns:
            dict - Signal with direction, strength, and indicators
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
            # Extract OHLC data
            if not historical_data or len(historical_data) < 50:
                signal["reason"] = "Insufficient historical data"
                return signal

            closes = np.array([d["close"] for d in historical_data], dtype=float)
            highs = np.array([d["high"] for d in historical_data], dtype=float)
            lows = np.array([d["low"] for d in historical_data], dtype=float)
            current_price = price_data.get("ltp", closes[-1])

            # Calculate indicators
            rsi = self.signal_gen.calculate_rsi(list(closes), period=self.config["rsi_period"])
            sma_short = self.signal_gen.calculate_sma(list(closes), self.config["sma_short_period"])
            sma_long = self.signal_gen.calculate_sma(list(closes), self.config["sma_long_period"])
            atr = self.signal_gen.calculate_atr(list(highs), list(lows), list(closes), period=self.config["atr_period"])
            macd = self.signal_gen.calculate_macd(list(closes))

            # Get current values
            current_rsi = self.signal_gen.get_last_value(rsi)
            current_sma_short = self.signal_gen.get_last_value(sma_short)
            current_sma_long = self.signal_gen.get_last_value(sma_long)
            current_atr = self.signal_gen.get_last_value(atr)
            current_macd = self.signal_gen.get_last_value(macd["macd"]) if macd else None
            current_macd_signal = self.signal_gen.get_last_value(macd["signal"]) if macd else None

            # Store indicator values
            signal["indicators"] = {
                "rsi": current_rsi,
                "sma_short": current_sma_short,
                "sma_long": current_sma_long,
                "atr": current_atr,
                "macd": current_macd,
                "macd_signal": current_macd_signal,
                "current_price": current_price,
            }

            # Generate signal based on RSI and SMA
            strength = 0
            reasons = []

            # RSI signals
            if current_rsi is not None:
                if current_rsi < self.config["rsi_oversold"]:
                    strength += 25
                    reasons.append(f"RSI oversold ({current_rsi:.2f})")
                elif current_rsi > self.config["rsi_overbought"]:
                    strength -= 25
                    reasons.append(f"RSI overbought ({current_rsi:.2f})")

            # SMA crossover signals
            if current_sma_short is not None and current_sma_long is not None:
                if current_sma_short > current_sma_long:
                    strength += 30
                    reasons.append(f"SMA crossover bullish (short > long)")
                elif current_sma_short < current_sma_long:
                    strength -= 30
                    reasons.append(f"SMA crossover bearish (short < long)")

            # MACD signals
            if current_macd is not None and current_macd_signal is not None:
                if current_macd > current_macd_signal:
                    strength += 20
                    reasons.append("MACD bullish crossover")
                elif current_macd < current_macd_signal:
                    strength -= 20
                    reasons.append("MACD bearish crossover")

            # Price position signals
            if current_sma_short and current_sma_long:
                avg_ma = (current_sma_short + current_sma_long) / 2
                if current_price > avg_ma:
                    strength += 10
                    reasons.append("Price above moving averages")
                else:
                    strength -= 10
                    reasons.append("Price below moving averages")

            # Determine direction based on net strength
            confidence = min(100, abs(strength))
            
            if strength > 30:
                signal["direction"] = "BUY"
                signal["strength"] = strength
                signal["confidence"] = confidence
            elif strength < -30:
                signal["direction"] = "SELL"
                signal["strength"] = abs(strength)
                signal["confidence"] = confidence
            else:
                signal["direction"] = "HOLD"
                signal["strength"] = abs(strength)
                signal["confidence"] = confidence

            signal["reason"] = " | ".join(reasons) if reasons else "No clear signal"
            
            # Calculate stop loss and target
            if current_atr:
                signal["stop_loss_distance"] = current_atr * self.config.get("atr_multiplier", 1.5)
            else:
                signal["stop_loss_distance"] = current_price * 0.02  # 2% default

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
        # Valid entry if direction is BUY or SELL and confidence > 50%
        is_valid = (
            signal.get("direction") in ["BUY", "SELL"] and
            signal.get("confidence", 0) >= 50
        )
        
        if is_valid:
            self.logger.info(
                f"{signal['symbol']}: {signal['direction']} signal (Confidence: {signal['confidence']:.0f}%) - "
                f"{signal['reason']}"
            )
        
        return is_valid

    def get_entry_price(self, symbol, direction, current_price):
        """
        Get entry price for a signal.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            current_price: float - Current market price
            
        Returns:
            float - Entry price
        """
        # For momentum strategy, enter at market
        return current_price

    def get_stop_loss(self, symbol, direction, entry_price, atr=None):
        """
        Calculate stop loss for a position.
        
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
                return entry_price - (atr * self.config.get("atr_multiplier", 1.5))
            else:  # SELL
                return entry_price + (atr * self.config.get("atr_multiplier", 1.5))
        else:
            # Fixed percentage stop loss
            stop_loss_pct = self.config.get("stop_loss_percent", 2.0)
            if direction == "BUY":
                return entry_price * (1 - stop_loss_pct / 100)
            else:  # SELL
                return entry_price * (1 + stop_loss_pct / 100)

    def get_target(self, symbol, direction, entry_price, stop_loss):
        """
        Calculate profit target for a position.
        
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
