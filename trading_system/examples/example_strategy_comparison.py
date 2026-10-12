# -*- coding: utf-8 -*-
"""
Example: Compare Multiple Strategies
Test momentum, mean reversion, and breakout strategies
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.trading_config import TradingConfig
from strategy.momentum_strategy import MomentumStrategy
from strategy.mean_reversion_strategy import MeanReversionStrategy
from strategy.breakout_strategy import BreakoutStrategy
from backtester.backtest_engine import BacktestEngine
from utils.logger import TradingLogger
import random


def main():
    """
    Example: Compare multiple strategies on same data.
    """
    logger = TradingLogger.get_logger()
    
    logger.info("Example: Strategy Comparison")
    logger.info("="*50)
    
    # Generate example data
    historical_data = generate_example_data(300)
    
    strategies = {
        "Momentum": MomentumStrategy(TradingConfig.STRATEGY_CONFIG["momentum"]),
        "Mean Reversion": MeanReversionStrategy({
            "bb_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
        }),
        "Breakout": BreakoutStrategy({
            "period": 20,
            "risk_reward_ratio": 2.0,
        }),
    }
    
    results = {}
    
    # Test each strategy
    for strategy_name, strategy in strategies.items():
        logger.info(f"\nBacktesting {strategy_name}...")
        backtester = BacktestEngine(strategy, initial_capital=100000)
        result = backtester.run({"INFY": historical_data}, ["INFY"])
        results[strategy_name] = result
    
    # Compare results
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    print(
        f"{'Strategy':<20} | {'Return':<12} | {'Trades':<8} | {'Win Rate':<10} | "
        f"{'Sharpe':<8} | {'Drawdown':<10}"
    )
    print("-" * 80)
    
    for strategy_name, result in results.items():
        if result["status"] != "Success":
            print(f"{strategy_name:<20} | {result['status']:<12}")
        else:
            return_pct = result["return_percent"]
            trades = result["total_trades"]
            win_rate = result["win_rate"]
            sharpe = result["sharpe_ratio"]
            drawdown = result["max_drawdown"]
            
            print(
                f"{strategy_name:<20} | {return_pct:>10.2f}% | {trades:>7} | "
                f"{win_rate:>8.2f}% | {sharpe:>7.2f} | {drawdown:>9.2f}%"
            )
    
    print("="*80)
    
    # Find best strategy
    best_strategy = max(
        results.items(),
        key=lambda x: x[1].get("return_percent", 0) if x[1]["status"] == "Success" else -999
    )
    
    logger.info(f"\nBest Strategy: {best_strategy[0]} ({best_strategy[1]['return_percent']:.2f}%)")


def generate_example_data(num_candles=300):
    """
    Generate synthetic OHLC data with different market conditions.
    
    Returns:
        list - OHLC candles
    """
    data = []
    price = 1850
    volatility = 1.5
    
    for i in range(num_candles):
        # Change volatility and trend periodically
        if i % 100 == 0:
            trend = random.choice([-0.8, -0.3, 0.5, 1.0, 1.5])
            volatility = random.uniform(0.5, 2.5)
        
        change = random.gauss(trend, volatility)
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + abs(random.gauss(0, volatility))
        low_price = min(open_price, close_price) - abs(random.gauss(0, volatility))
        volume = int(random.gauss(300000, 100000))
        
        data.append({
            "timestamp": datetime.now() - timedelta(minutes=5*(num_candles-i)),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": max(1000, volume),
        })
        
        price = close_price
    
    return sorted(data, key=lambda x: x["timestamp"])


if __name__ == "__main__":
    main()
