# -*- coding: utf-8 -*-
"""
Risk Management Module
Stop loss, position sizing, daily limits, drawdown management
"""

from utils.logger import TradingLogger
from config.trading_config import TradingConfig
from datetime import datetime


class RiskManager:
    """
    Manages risk across trades and positions.
    Enforces position sizing, stop loss limits, and daily drawdown limits.
    """

    def __init__(self):
        """
        Initialize risk manager.
        """
        self.logger = TradingLogger.get_logger()
        self.risk_config = TradingConfig.RISK_CONFIG
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.active_positions = 0

    def calculate_position_size(self, capital, entry_price, stop_loss, risk_percent=None):
        """
        Calculate position size based on risk parameters.
        
        Args:
            capital: float - Available trading capital
            entry_price: float - Entry price
            stop_loss: float - Stop loss price
            risk_percent: float - Risk percentage per trade (overrides config)
            
        Returns:
            int - Position quantity
        """
        try:
            if capital is None or capital <= 0:
                self.logger.error("Invalid capital for position sizing")
                return 0
            if entry_price is None or entry_price <= 0:
                self.logger.error("Invalid entry price for position sizing")
                return 0
            if stop_loss is None or stop_loss <= 0:
                self.logger.error("Invalid stop loss for position sizing")
                return 0

            risk_method = self.risk_config["position_sizing_method"]
            
            if risk_method == "risk_based":
                # Risk-based sizing
                risk_pct = risk_percent or self.risk_config["risk_per_trade"]
                if risk_pct <= 0:
                    self.logger.error("Invalid risk percentage for position sizing")
                    return 0
                max_loss_amount = (capital * risk_pct) / 100
                
                # Calculate quantity
                price_diff = abs(entry_price - stop_loss)
                if price_diff == 0:
                    self.logger.error("Invalid stop loss distance: zero")
                    return 0
                else:
                    quantity = int(max_loss_amount / price_diff)
            else:
                # Fixed sizing
                max_position = self.risk_config["max_position_size"]
                if max_position <= 0:
                    self.logger.error("Invalid max position size in risk config")
                    return 0
                if entry_price > 0:
                    quantity = int(max_position / entry_price)
                else:
                    return 0
            
            # Ensure minimum quantity
            quantity = max(1, quantity)
            
            self.logger.info(
                f"Position size calculated: {quantity} units | "
                f"Entry: {entry_price} | SL: {stop_loss}"
            )
            
            return quantity
        
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 1

    def can_enter_position(self, symbol):
        """
        Check if new position can be entered.
        
        Args:
            symbol: str - Trading symbol
            
        Returns:
            tuple - (bool, str) - Can enter and reason
        """
        # Check daily loss limit
        max_daily_loss = self.risk_config["max_daily_loss"]
        if max_daily_loss <= 0:
            return False, "Invalid max daily loss configuration"
        effective_daily_loss = max(0.0, self.daily_loss)
        if effective_daily_loss >= max_daily_loss:
            return False, f"Daily loss limit reached (₹{effective_daily_loss:.2f})"
        
        # Check max open positions
        if self.active_positions >= self.risk_config["max_open_positions"]:
            return False, f"Max open positions reached ({self.active_positions})"
        
        return True, "OK"

    def validate_order(self, symbol, entry_price, quantity, direction, stop_loss, target):
        """
        Validate order parameters against risk rules.
        
        Args:
            symbol: str - Trading symbol
            entry_price: float - Entry price
            quantity: int - Position quantity
            direction: str - BUY or SELL
            stop_loss: float - Stop loss price
            target: float - Target price
            
        Returns:
            tuple - (bool, str) - Valid and reason
        """
        try:
            if direction not in ["BUY", "SELL"]:
                return False, "Direction must be BUY or SELL"
            if entry_price is None or entry_price <= 0:
                return False, "Entry price must be greater than zero"
            if stop_loss is None or stop_loss <= 0:
                return False, "Stop loss must be greater than zero"
            if target is None or target <= 0:
                return False, "Target must be greater than zero"
            if quantity is None or quantity <= 0:
                return False, "Quantity must be greater than zero"

            # Check stop loss distance
            max_loss = self.risk_config["max_loss_per_trade"]
            if max_loss <= 0:
                return False, "Invalid max loss per trade configuration"
            loss_amount = abs(entry_price - stop_loss) * quantity
            
            if loss_amount > max_loss:
                return False, f"Loss per trade (₹{loss_amount:.2f}) exceeds max (₹{max_loss})"
            
            # Check stop loss is placed correctly
            if direction == "BUY":
                if stop_loss >= entry_price:
                    return False, "Stop loss must be below entry for BUY"
            else:  # SELL
                if stop_loss <= entry_price:
                    return False, "Stop loss must be above entry for SELL"
            
            # Check target is set
            # Check risk-reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target - entry_price)
            if risk <= 0:
                return False, "Stop loss distance must be greater than zero"
            if reward < risk:
                self.logger.warning(
                    f"Risk-reward ratio unfavorable: Risk ₹{risk:.2f}, Reward ₹{reward:.2f}"
                )
            
            return True, "Validated"
        
        except Exception as e:
            self.logger.error(f"Order validation error: {str(e)}")
            return False, str(e)

    def record_trade_loss(self, loss_amount):
        """
        Record a trade loss.
        
        Args:
            loss_amount: float - Loss amount
        """
        if loss_amount is None or loss_amount < 0:
            self.logger.warning(f"Ignoring invalid loss amount: {loss_amount}")
            return
        self.daily_loss += loss_amount
        self.daily_trades += 1
        self.logger.info(
            f"Loss recorded: ₹{loss_amount:.2f} | Daily total: ₹{self.daily_loss:.2f}"
        )

    def record_trade_profit(self, profit_amount):
        """
        Record a trade profit.
        
        Args:
            profit_amount: float - Profit amount
        """
        if profit_amount is None or profit_amount < 0:
            self.logger.warning(f"Ignoring invalid profit amount: {profit_amount}")
            return
        self.daily_loss -= profit_amount  # Reduce cumulative loss
        self.daily_trades += 1
        self.logger.info(
            f"Profit recorded: ₹{profit_amount:.2f} | Daily total: ₹{self.daily_loss:.2f}"
        )

    def increment_active_positions(self):
        """
        Increment active position counter.
        """
        self.active_positions += 1

    def decrement_active_positions(self):
        """
        Decrement active position counter.
        """
        self.active_positions = max(0, self.active_positions - 1)

    def reset_daily_limits(self):
        """
        Reset daily loss and trade counters.
        Called at the start of each trading day.
        """
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.logger.info("Daily limits reset")

    def get_risk_summary(self):
        """
        Get current risk summary.
        
        Returns:
            dict - Risk metrics
        """
        max_daily_loss = self.risk_config["max_daily_loss"]
        effective_daily_loss = max(0.0, self.daily_loss)
        remaining_loss = max(0.0, max_daily_loss - effective_daily_loss)
        
        return {
            "daily_loss": effective_daily_loss,
            "max_daily_loss": max_daily_loss,
            "remaining_loss": remaining_loss,
            "daily_trades": self.daily_trades,
            "active_positions": self.active_positions,
            "max_positions": self.risk_config["max_open_positions"],
        }
