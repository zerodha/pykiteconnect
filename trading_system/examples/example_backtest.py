# -*- coding: utf-8 -*-
"""
Example: Simple Momentum Trading
Basic example of using the trading system
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.trading_config import TradingConfig, Market
from strategy.momentum_strategy import MomentumStrategy
from data.historical_data import HistoricalDataFetcher
from backtester.backtest_engine import BacktestEngine
from utils.logger import TradingLogger


def main():
    """
    Example: Run momentum strategy on historical data.
    """
    logger = TradingLogger.get_logger()
    
    logger.info("Example: Momentum Trading System")
    logger.info("="*50)
    
    # Configure strategy
    strategy_config = TradingConfig.STRATEGY_CONFIG["momentum"]
    strategy = MomentumStrategy(strategy_config)
    
    # Create dummy historical data for example
    logger.info("Generating example data...")
    historical_data = generate_example_data()
    
    # Backtest the strategy
    logger.info("Running backtest...")
    backtester = BacktestEngine(strategy, initial_capital=100000)
    
    # Run backtest
    result = backtester.run({"INFY": historical_data}, ["INFY"])
    
    # Print results
    backtester.print_report()
    
    logger.info("\nTop 5 Trades:")
    for i, trade in enumerate(result["trades"][:5], 1):
        print(
            f"{i}. {trade['symbol']} {trade['side']} | "
            f"Entry: ₹{trade['entry_price']:.2f} | Exit: ₹{trade['exit_price']:.2f} | "
            f"P&L: ₹{trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)"
        )


def generate_example_data(num_candles=200):
    """
    Generate synthetic OHLC data for testing.
    
    Returns:
        list - OHLC candles
    """
    import random
    import numpy as np
    
    data = []
    price = 1850  # Starting price
    
    # Trend phases
    trends = [0.5, 1.2, -0.8, 0.3, 1.0, -0.5]  # Different trend strengths
    trend_idx = 0
    candles_per_trend = num_candles // len(trends)
    
    for i in range(num_candles):
        # Determine current trend
        if (i // candles_per_trend) < len(trends):
            trend = trends[i // candles_per_trend]
        else:
            trend = trends[-1]
        
        # Generate price movement
        change = random.gauss(trend, 1.5)  # Mean trend, std dev 1.5
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0.5, 2.0)
        low_price = min(open_price, close_price) - random.uniform(0.5, 2.0)
        volume = random.randint(50000, 500000)
        
        data.append({
            "timestamp": datetime.now() - timedelta(minutes=5*(num_candles-i)),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        })
        
        price = close_price
    
    return sorted(data, key=lambda x: x["timestamp"])


if __name__ == "__main__":
    main()
