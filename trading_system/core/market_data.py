# -*- coding: utf-8 -*-
"""
Real-time Market Data Handler
WebSocket-based price streaming from Kite Ticker
"""

from kiteconnect import KiteTicker
from utils.logger import TradingLogger
from collections import deque
from datetime import datetime
import threading
import time


class MarketDataHandler:
    """
    Manages real-time market data streaming via WebSocket.
    Maintains price history and provides callbacks for updates.
    """

    def __init__(self, kite_instance, api_key, access_token):
        """
        Initialize market data handler.
        
        Args:
            kite_instance: KiteConnect instance
            api_key: str - Kite API key
            access_token: str - Access token
        """
        self.kite = kite_instance
        self.api_key = api_key
        self.access_token = access_token
        self.ticker = KiteTicker(api_key, access_token, debug=False)
        self.logger = TradingLogger.get_logger()
        
        # Store market data
        self.price_data = {}  # {token: {"ltp": price, "last_update": time, ...}}
        self.candle_data = {}  # {token: deque of OHLC candles}
        self.callbacks = []  # Callback functions on price update
        
        self._is_connected = False
        self._setup_callbacks()

    def _setup_callbacks(self):
        """
        Setup WebSocket callbacks.
        """
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_reconnect = self._on_reconnect
        self.ticker.on_noreconnect = self._on_noreconnect

    def _on_connect(self, ws, response):
        """
        Callback when WebSocket connects.
        """
        self._is_connected = True
        self.logger.info(f"Market data connected: {response}")

    def _on_close(self, ws, code, reason):
        """
        Callback when WebSocket closes.
        """
        self._is_connected = False
        self.logger.warning(f"Market data connection closed: {code} - {reason}")

    def _on_error(self, ws, code, reason):
        """
        Callback on WebSocket error.
        """
        self.logger.error(f"Market data error: {code} - {reason}")

    def _on_reconnect(self, attempts):
        """
        Callback on reconnection attempt.
        """
        self.logger.info(f"Market data reconnection attempt: {attempts}")

    def _on_noreconnect(self):
        """
        Callback when reconnection fails.
        """
        self.logger.error("Market data connection failed after max retries")

    def _on_ticks(self, ws, ticks):
        """
        Callback when price updates are received.
        
        Args:
            ws: WebSocket instance
            ticks: list of tick data
        """
        for tick in ticks:
            token = tick.get('instrument_token')
            if token:
                # Update price data
                self.price_data[token] = {
                    'ltp': tick.get('last_price'),
                    'bid': tick.get('bid'),
                    'ask': tick.get('ask'),
                    'volume': tick.get('volume_traded'),
                    'timestamp': datetime.now(),
                    'ohlc': tick.get('ohlc'),
                }
                
                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        callback(token, self.price_data[token])
                    except Exception as e:
                        self.logger.error(f"Callback error: {str(e)}")

    def connect(self, threaded=True):
        """
        Connect to WebSocket for market data.
        
        Args:
            threaded: bool - Run in separate thread
        """
        try:
            self.logger.info("Connecting to market data...")
            self.ticker.connect(threaded=threaded)
            time.sleep(1)  # Give connection time to establish
            self.logger.info("Market data connection initiated")
        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}")
            raise

    def subscribe(self, instrument_tokens):
        """
        Subscribe to price updates for instruments.
        
        Args:
            instrument_tokens: list - Instrument tokens to subscribe
        """
        try:
            if not isinstance(instrument_tokens, list):
                instrument_tokens = [instrument_tokens]
            
            self.ticker.subscribe(instrument_tokens)
            self.logger.info(f"Subscribed to {len(instrument_tokens)} instruments")
        except Exception as e:
            self.logger.error(f"Subscription error: {str(e)}")
            raise

    def unsubscribe(self, instrument_tokens):
        """
        Unsubscribe from price updates.
        
        Args:
            instrument_tokens: list - Instrument tokens to unsubscribe
        """
        try:
            if not isinstance(instrument_tokens, list):
                instrument_tokens = [instrument_tokens]
            
            self.ticker.unsubscribe(instrument_tokens)
            self.logger.info(f"Unsubscribed from {len(instrument_tokens)} instruments")
        except Exception as e:
            self.logger.error(f"Unsubscription error: {str(e)}")

    def set_mode(self, mode, instrument_tokens):
        """
        Set streaming mode for instruments.
        
        Args:
            mode: str - MODE_LTP, MODE_QUOTE, or MODE_FULL
            instrument_tokens: list - Instrument tokens
        """
        try:
            if not isinstance(instrument_tokens, list):
                instrument_tokens = [instrument_tokens]
            
            self.ticker.set_mode(mode, instrument_tokens)
            self.logger.info(f"Set mode {mode} for instruments")
        except Exception as e:
            self.logger.error(f"Set mode error: {str(e)}")

    def get_ltp(self, instrument_token):
        """
        Get last traded price for an instrument.
        
        Args:
            instrument_token: int - Instrument token
            
        Returns:
            float - Last traded price or None
        """
        if instrument_token in self.price_data:
            return self.price_data[instrument_token].get('ltp')
        return None

    def add_callback(self, callback):
        """
        Add callback function for price updates.
        
        Args:
            callback: function(token, price_data) - Called on price update
        """
        self.callbacks.append(callback)

    def is_connected(self):
        """
        Check if WebSocket is connected.
        
        Returns:
            bool - Connection status
        """
        return self._is_connected

    def disconnect(self):
        """
        Disconnect from WebSocket.
        """
        try:
            self.ticker.close()
            self.logger.info("Market data disconnected")
        except Exception as e:
            self.logger.error(f"Disconnect error: {str(e)}")
