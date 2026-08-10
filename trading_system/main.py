# -*- coding: utf-8 -*-
"""
Main entry point for the intraday trading system
"""

import sys
import os
from engine.trading_engine import TradingEngine
from dashboard.app import app, engine as dashboard_engine
from config.trading_config import TradingConfig, Market
from utils.logger import TradingLogger
from utils.market_hours import MarketHours
import threading


def main():
    """
    Main entry point. Initialize and start the trading system.
    """
    logger = TradingLogger.get_logger()
    
    # Get API credentials from environment or input
    api_key = os.getenv("KITE_API_KEY") or input("Enter Kite API Key: ")
    api_secret = os.getenv("KITE_API_SECRET") or input("Enter Kite API Secret: ")
    
    # Initialize engine
    logger.info(f"Initializing trading engine for {TradingConfig.MARKET.value.upper()}...")
    engine = TradingEngine(api_key, api_secret)
    
    # Authenticate
    logger.info("Authenticating with Kite Connect...")
    if not engine.authenticate():
        logger.error("Authentication failed!")
        return
    
    # Configure symbols
    instruments = TradingConfig.get_instruments()
    symbols = [inst["symbol"] for inst in instruments]
    engine.set_instruments(symbols)
    
    logger.info(f"Configured symbols: {', '.join(symbols)}")
    
    # Setup callbacks
    def on_signal(signal):
        if signal["confidence"] > 50:
            logger.info(f"Signal: {signal['symbol']} {signal['direction']} (Confidence: {signal['confidence']:.0f}%)")
    
    def on_position(action, position):
        logger.info(f"Position {action}: {position['symbol']}")
    
    engine.on_signal = on_signal
    engine.on_position = on_position
    
    # Set dashboard engine reference
    sys.modules['dashboard.app'].engine = engine
    
    # Start dashboard in separate thread
    logger.info("Starting web dashboard on http://localhost:5000")
    dashboard_thread = threading.Thread(
        target=lambda: app.run(debug=False, port=5000, use_reloader=False),
        daemon=True
    )
    dashboard_thread.start()
    
    # Start trading engine
    logger.info("Starting trading engine...")
    logger.info(f"Market hours: {MarketHours.get_market_status()}")
    engine.start(threaded=True)
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        engine.stop()
        logger.info("Trading engine stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
