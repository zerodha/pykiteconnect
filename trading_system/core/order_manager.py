# -*- coding: utf-8 -*-
"""
Order Management
Handles order placement, modification, and cancellation
"""

from utils.logger import TradingLogger
from enum import Enum
from datetime import datetime


class OrderStatus(Enum):
    """Order status constants"""
    PENDING = "PENDING"
    PLACED = "PLACED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class OrderManager:
    """
    Manages order placement and tracking.
    Integrates with Kite Connect for order execution.
    """

    def __init__(self, kite_instance):
        """
        Initialize order manager.
        
        Args:
            kite_instance: KiteConnect instance
        """
        self.kite = kite_instance
        self.logger = TradingLogger.get_logger()
        self.trade_logger = TradingLogger.get_trade_logger()
        
        # Track orders locally
        self.orders = {}  # {order_id: order_data}
        self.position_orders = {}  # {symbol: {entry: order, stop_loss: order, ...}}

    def place_order(
        self,
        exchange,
        tradingsymbol,
        transaction_type,
        quantity,
        variety=None,
        product="MIS",
        order_type="MARKET",
        price=None,
        trigger_price=None,
        validity="DAY",
        disclosed_quantity=None,
        tag=None,
    ):
        """
        Place an order on the exchange.
        
        Args:
            exchange: str - NSE, BSE, NFO, MCX, etc.
            tradingsymbol: str - Trading symbol
            transaction_type: str - BUY or SELL
            quantity: int - Order quantity
            variety: str - regular, amo, co, iceberg, auction
            product: str - MIS, CNC, NRML
            order_type: str - MARKET, LIMIT, SL, SL-M
            price: float - Order price (for LIMIT)
            trigger_price: float - Trigger price (for SL orders)
            validity: str - DAY, IOC, TTL
            disclosed_quantity: int - Disclosed quantity for iceberg
            tag: str - Order tag for tracking
            
        Returns:
            dict - Order response from API
        """
        try:
            variety = variety or "regular"
            
            self.logger.info(
                f"Placing {transaction_type} order: {tradingsymbol} x {quantity} "
                f"({order_type} @ {price or 'market'})"
            )
            
            order_id = self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                disclosed_quantity=disclosed_quantity,
                tag=tag,
            )
            
            # Store order locally
            order_data = {
                "order_id": order_id,
                "symbol": tradingsymbol,
                "exchange": exchange,
                "type": transaction_type,
                "quantity": quantity,
                "product": product,
                "order_type": order_type,
                "price": price,
                "trigger_price": trigger_price,
                "status": OrderStatus.PLACED.value,
                "placed_at": datetime.now(),
                "tag": tag,
            }
            
            self.orders[order_id] = order_data
            
            self.trade_logger.info(
                f"ORDER_PLACED | ID: {order_id} | {tradingsymbol} {transaction_type} "
                f"{quantity} @ {price or 'MKT'}"
            )
            
            return order_data
        
        except Exception as e:
            self.logger.error(f"Order placement failed: {str(e)}")
            self.trade_logger.error(f"ORDER_FAILED | {tradingsymbol}: {str(e)}")
            raise

    def modify_order(
        self,
        order_id,
        variety="regular",
        quantity=None,
        price=None,
        trigger_price=None,
        order_type=None,
    ):
        """
        Modify an existing order.
        
        Args:
            order_id: str - Order ID to modify
            variety: str - Order variety
            quantity: int - New quantity
            price: float - New price
            trigger_price: float - New trigger price
            order_type: str - New order type
            
        Returns:
            dict - Modified order response
        """
        try:
            self.logger.info(f"Modifying order {order_id}")
            
            modified_id = self.kite.modify_order(
                variety=variety,
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                order_type=order_type,
            )
            
            self.logger.info(f"Order modified: {modified_id}")
            return modified_id
        
        except Exception as e:
            self.logger.error(f"Order modification failed: {str(e)}")
            raise

    def cancel_order(self, order_id, variety="regular"):
        """
        Cancel an existing order.
        
        Args:
            order_id: str - Order ID to cancel
            variety: str - Order variety
            
        Returns:
            dict - Cancellation response
        """
        try:
            self.logger.info(f"Cancelling order {order_id}")
            
            cancelled_id = self.kite.cancel_order(
                variety=variety,
                order_id=order_id,
            )
            
            if order_id in self.orders:
                self.orders[order_id]["status"] = OrderStatus.CANCELLED.value
            
            self.trade_logger.info(f"ORDER_CANCELLED | ID: {order_id}")
            self.logger.info(f"Order cancelled: {cancelled_id}")
            
            return cancelled_id
        
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {str(e)}")
            raise

    def get_order_status(self, order_id):
        """
        Get status of an order.
        
        Args:
            order_id: str - Order ID
            
        Returns:
            dict - Order details
        """
        if order_id in self.orders:
            return self.orders[order_id]
        return None

    def get_all_orders(self):
        """
        Get all orders from the exchange.
        
        Returns:
            list - All orders
        """
        try:
            orders = self.kite.orders()
            return orders
        except Exception as e:
            self.logger.error(f"Failed to fetch orders: {str(e)}")
            return []
