# -*- coding: utf-8 -*-
"""
Example: Fetch Real Historical Data
Fetch actual data from Kite Connect API
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.authentication import AuthenticationManager
from data.historical_data import HistoricalDataFetcher
from utils.logger import TradingLogger


def main():
    """
    Example: Fetch real historical data from Kite Connect.
    """
    logger = TradingLogger.get_logger()
    
    logger.info("Example: Fetching Real Historical Data")
    logger.info("="*50)
    
    # Get credentials
    api_key = os.getenv("KITE_API_KEY") or input("Enter Kite API Key: ")
    api_secret = os.getenv("KITE_API_SECRET") or input("Enter Kite API Secret: ")
    
    # Authenticate
    logger.info("Authenticating...")
    auth = AuthenticationManager(api_key, api_secret)
    
    # Try to restore saved session
    saved_session = auth.load_saved_session()
    if saved_session:
        kite = auth.restore_session(saved_session["access_token"])
        logger.info("Session restored from file")
    else:
        # Need new login
        login_url = auth.get_login_url()
        print(f"\nLogin here: {login_url}\n")
        request_token = input("Paste request_token from redirect URL: ")
        session_data = auth.create_session(request_token)
        kite = auth.get_kite_instance()
    
    # Fetch historical data
    logger.info("Fetching historical data...")
    fetcher = HistoricalDataFetcher(kite)
    
    # Fetch last 50 5-minute candles for INFY
    data = fetcher.get_last_n_candles(
        exchange="NSE",
        symbol="INFY",
        n=50,
        interval="5minute"
    )
    
    if data:
        logger.info(f"Fetched {len(data)} candles for INFY")
        
        # Print sample candles
        print("\nRecent candles:")
        print("-" * 60)
        for i, candle in enumerate(data[-5:], 1):
            timestamp = candle.get("date", "N/A")
            print(
                f"{i}. {timestamp} | O: {candle['open']:.2f} | H: {candle['high']:.2f} | "
                f"L: {candle['low']:.2f} | C: {candle['close']:.2f} | V: {candle['volume']}"
            )
    else:
        logger.error("Failed to fetch data")


if __name__ == "__main__":
    main()
