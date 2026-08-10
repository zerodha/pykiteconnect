# -*- coding: utf-8 -*-
"""
Position Tracking and P&L Management
Tracks open positions and calculates live P&L
"""

from utils.logger import TradingLogger
from datetime import datetime
from enum import Enum


class PositionStatus(Enum):
    """Position status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING_EXIT = "PENDING_EXIT"


class PositionTracker:
    """
    Tracks open positions and calculates real-time P&L.
    """

    def __init__(self, kite_instance):
        """
        Initialize position tracker.
        
        Args:
            kite_instance: KiteConnect instance
        """
        self.kite = kite_instance
        self.logger = TradingLogger.get_logger()
        self.trade_logger = TradingLogger.get_trade_logger()
        
        # Track positions
        self.positions = {}  # {symbol: position_data}
        self.closed_positions = []  # History of closed positions
        self.daily_pnl = 0.0

    def open_position(
        self,
        symbol,
        entry_price,
        quantity,
        side,  # "BUY" or "SELL"
        stop_loss,
        target,
        order_id,
    ):
        """
        Register an open position.
        
        Args:
            symbol: str - Trading symbol
            entry_price: float - Entry price
            quantity: int - Position quantity
            side: str - BUY or SELL
            stop_loss: float - Stop loss price
            target: float - Target price
            order_id: str - Entry order ID
        """
        position = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target": target,
            "status": PositionStatus.OPEN.value,
            "entry_order_id": order_id,
            "entry_time": datetime.now(),
            "exit_price": None,
            "exit_time": None,
            "pnl": 0.0,
            "pnl_percent": 0.0,
        }
        
        self.positions[symbol] = position
        
        self.trade_logger.info(
            f"POSITION_OPEN | {symbol} {side} {quantity} @ {entry_price} | "
            f"SL: {stop_loss} | Target: {target}"
        )
        
        self.logger.info(
            f"Position opened: {symbol} {side} x{quantity} @ {entry_price}"
        )

    def update_position(self, symbol, current_price):
        """
        Update P&L for a position based on current price.
        
        Args:
            symbol: str - Trading symbol
            current_price: float - Current market price
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        if position["status"] != PositionStatus.OPEN.value:
            return position
        
        # Calculate P&L
        quantity = position["quantity"]
        entry_price = position["entry_price"]
        
        if position["side"] == "BUY":
            pnl = (current_price - entry_price) * quantity
        else:  # SELL
            pnl = (entry_price - current_price) * quantity
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100 if entry_price != 0 else 0
        
        position["pnl"] = pnl
        position["pnl_percent"] = pnl_percent
        
        return position

    def close_position(self, symbol, exit_price, exit_order_id=None):
        """
        Close an open position.
        
        Args:
            symbol: str - Trading symbol
            exit_price: float - Exit price
            exit_order_id: str - Exit order ID
        """
        if symbol not in self.positions:
            self.logger.warning(f"No open position for {symbol}")
            return None
        
        position = self.positions[symbol]
        
        # Calculate final P&L
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        
        if position["side"] == "BUY":
            pnl = (exit_price - entry_price) * quantity
        else:  # SELL
            pnl = (entry_price - exit_price) * quantity
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100 if entry_price != 0 else 0
        
        # Update position
        position["status"] = PositionStatus.CLOSED.value
        position["exit_price"] = exit_price
        position["exit_time"] = datetime.now()
        position["pnl"] = pnl
        position["pnl_percent"] = pnl_percent
        
        # Move to closed positions
        self.closed_positions.append(position.copy())
        
        # Update daily P&L
        self.daily_pnl += pnl
        
        # Remove from active positions
        del self.positions[symbol]
        
        exit_reason = "TARGET" if exit_price >= position["target"] else (
            "STOPLOSS" if exit_price <= position["stop_loss"] else "MANUAL"
        )
        
        self.trade_logger.info(
            f"POSITION_CLOSED | {symbol} {position['side']} {quantity} "
            f"@ Entry: {entry_price} | Exit: {exit_price} | "
            f"P&L: {pnl:.2f} ({pnl_percent:.2f}%) | Reason: {exit_reason}"
        )
        
        self.logger.info(
            f"Position closed: {symbol} | P&L: {pnl:.2f} ({pnl_percent:.2f}%) | {exit_reason}"
        )
        
        return position

    def get_position(self, symbol):
        """
        Get details of a specific position.
        
        Args:
            symbol: str - Trading symbol
            
        Returns:
            dict - Position details or None
        """
        return self.positions.get(symbol)

    def get_all_positions(self):
        """
        Get all open positions.
        
        Returns:
            dict - All open positions
        """
        return self.positions.copy()

    def get_daily_pnl(self):
        """
        Get total P&L for the day.
        
        Returns:
            float - Daily P&L
        """
        return self.daily_pnl

    def get_position_summary(self):
        """
        Get summary of all positions.
        
        Returns:
            dict - Summary data
        """
        total_positions = len(self.positions)
        total_pnl = sum(p["pnl"] for p in self.positions.values())
        total_unrealized = total_pnl
        total_realized = self.daily_pnl - total_unrealized
        
        return {
            "open_positions": total_positions,
            "total_unrealized_pnl": total_unrealized,
            "total_realized_pnl": total_realized,
            "total_daily_pnl": self.daily_pnl,
            "closed_today": len(self.closed_positions),
        }
