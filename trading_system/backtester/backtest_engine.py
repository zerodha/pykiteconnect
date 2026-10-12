# -*- coding: utf-8 -*-
"""
Backtesting Engine
Historical performance analysis and strategy validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import TradingLogger
from collections import defaultdict


class BacktestEngine:
    """
    Backtest trading strategies on historical data.
    """

    def __init__(self, strategy, initial_capital=100000):
        """
        Initialize backtester.
        
        Args:
            strategy: Strategy instance
            initial_capital: float - Starting capital
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.logger = TradingLogger.get_logger()
        
        # Results tracking
        self.trades = []
        self.equity_curve = []
        self.daily_pnl = defaultdict(float)
        self.positions = {}

    def run(self, historical_data, symbols):
        """
        Run backtest on historical data.
        
        Args:
            historical_data: dict - {symbol: [OHLC data]}
            symbols: list - Symbols to backtest
            
        Returns:
            dict - Backtest results and metrics
        """
        self.logger.info(f"Starting backtest for {len(symbols)} symbols")
        
        # Initialize equity tracking
        capital = self.initial_capital
        equity_history = [capital]
        
        # Get all timestamps
        all_timestamps = self._get_all_timestamps(historical_data, symbols)
        
        # Backtest each candle
        for i, timestamp in enumerate(all_timestamps):
            # Generate signals for each symbol
            for symbol in symbols:
                if symbol not in historical_data:
                    continue
                
                symbol_data = historical_data[symbol]
                if i >= len(symbol_data):
                    continue
                
                # Get current and historical data
                current_candle = symbol_data[i]
                hist_data = symbol_data[:i+1]
                
                # Generate signal
                price_data = {"ltp": current_candle["close"]}
                signal = self.strategy.generate_signal(symbol, price_data, hist_data)
                
                # Check for entry signal
                if symbol not in self.positions and self.strategy.validate_signal(signal):
                    entry_price = current_candle["close"]
                    atr = current_candle.get("atr", entry_price * 0.02)
                    
                    stop_loss = self.strategy.get_stop_loss(symbol, signal["direction"], entry_price, atr)
                    target = self.strategy.get_target(symbol, signal["direction"], entry_price, stop_loss)
                    
                    # Position size (simplified)
                    quantity = int(capital * 0.1 / entry_price)  # Risk 10% of capital
                    
                    self.positions[symbol] = {
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "side": signal["direction"],
                        "stop_loss": stop_loss,
                        "target": target,
                        "entry_time": timestamp,
                    }
                
                # Check for exit signals
                if symbol in self.positions:
                    position = self.positions[symbol]
                    exit_price = current_candle["close"]
                    exit_reason = None
                    
                    # Check stop loss
                    if position["side"] == "BUY" and exit_price <= position["stop_loss"]:
                        exit_reason = "STOPLOSS"
                    elif position["side"] == "SELL" and exit_price >= position["stop_loss"]:
                        exit_reason = "STOPLOSS"
                    
                    # Check target
                    if position["side"] == "BUY" and exit_price >= position["target"]:
                        exit_reason = "TARGET"
                    elif position["side"] == "SELL" and exit_price <= position["target"]:
                        exit_reason = "TARGET"
                    
                    if exit_reason:
                        # Close position and record trade
                        pnl = self._close_position(symbol, exit_price, exit_reason)
                        capital += pnl
                        date = timestamp.date() if hasattr(timestamp, 'date') else timestamp
                        self.daily_pnl[date] += pnl
            
            # Update equity
            equity_history.append(capital)
        
        self.equity_curve = equity_history
        
        # Generate report
        return self._generate_report()

    def _close_position(self, symbol, exit_price, exit_reason):
        """
        Close a position and calculate P&L.
        
        Args:
            symbol: str - Trading symbol
            exit_price: float - Exit price
            exit_reason: str - Reason for exit
            
        Returns:
            float - P&L amount
        """
        position = self.positions[symbol]
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        side = position["side"]
        
        if side == "BUY":
            pnl = (exit_price - entry_price) * quantity
        else:  # SELL
            pnl = (entry_price - exit_price) * quantity
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100
        
        # Record trade
        self.trades.append({
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "reason": exit_reason,
            "entry_time": position["entry_time"],
        })
        
        del self.positions[symbol]
        return pnl

    def _get_all_timestamps(self, historical_data, symbols):
        """
        Get all timestamps from historical data.
        
        Returns:
            list - Sorted list of timestamps
        """
        timestamps = set()
        for symbol in symbols:
            if symbol in historical_data:
                for candle in historical_data[symbol]:
                    if "timestamp" in candle:
                        timestamps.add(candle["timestamp"])
        return sorted(list(timestamps))

    def _generate_report(self):
        """
        Generate backtest report with statistics.
        
        Returns:
            dict - Backtest metrics and statistics
        """
        if not self.trades:
            return {"status": "No trades executed", "trades": 0}
        
        trades_df = pd.DataFrame(self.trades)
        
        winning_trades = trades_df[trades_df["pnl"] > 0]
        losing_trades = trades_df[trades_df["pnl"] <= 0]
        
        total_trades = len(trades_df)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = trades_df["pnl"].sum()
        avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades["pnl"].sum() / losing_trades["pnl"].sum()) if len(losing_trades) > 0 and losing_trades["pnl"].sum() != 0 else 0
        
        # Calculate Sharpe ratio
        daily_returns = [self.daily_pnl[date] / self.initial_capital for date in sorted(self.daily_pnl.keys())]
        sharpe = self._calculate_sharpe(daily_returns) if daily_returns else 0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            "status": "Success",
            "initial_capital": self.initial_capital,
            "final_capital": self.equity_curve[-1] if self.equity_curve else self.initial_capital,
            "total_return": (self.equity_curve[-1] - self.initial_capital) if self.equity_curve else 0,
            "return_percent": ((self.equity_curve[-1] / self.initial_capital - 1) * 100) if self.equity_curve else 0,
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_profit": total_profit,
            "trades": self.trades,
        }

    def _calculate_sharpe(self, returns, risk_free_rate=0.05):
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: list - Daily returns
            risk_free_rate: float - Annual risk-free rate
            
        Returns:
            float - Sharpe ratio
        """
        if len(returns) < 2:
            return 0
        
        returns = np.array(returns)
        excess_returns = returns - (risk_free_rate / 252)
        
        if np.std(excess_returns) == 0:
            return 0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe

    def _calculate_max_drawdown(self):
        """
        Calculate maximum drawdown.
        
        Returns:
            float - Max drawdown as percentage
        """
        if not self.equity_curve or len(self.equity_curve) < 2:
            return 0
        
        cummax = np.maximum.accumulate(self.equity_curve)
        drawdown = (np.array(self.equity_curve) - cummax) / cummax
        return np.min(drawdown) * 100 if len(drawdown) > 0 else 0

    def plot_equity_curve(self):
        """
        Plot equity curve (requires matplotlib).
        """
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            plt.plot(self.equity_curve, linewidth=2)
            plt.title("Backtest Equity Curve")
            plt.xlabel("Candles")
            plt.ylabel("Equity (₹)")
            plt.grid(True, alpha=0.3)
            plt.show()
        except ImportError:
            self.logger.warning("matplotlib not installed for plotting")

    def print_report(self):
        """
        Print formatted backtest report.
        """
        result = self._generate_report()
        
        print("\n" + "="*60)
        print("BACKTEST REPORT")
        print("="*60)
        
        if result["status"] != "Success":
            print(f"Status: {result['status']}")
            return
        
        print(f"Initial Capital: ₹{result['initial_capital']:,.2f}")
        print(f"Final Capital:   ₹{result['final_capital']:,.2f}")
        print(f"Total Return:    ₹{result['total_return']:,.2f} ({result['return_percent']:.2f}%)")
        print()
        print(f"Total Trades:    {result['total_trades']}")
        print(f"Winning Trades:  {result['winning_trades']}")
        print(f"Losing Trades:   {result['losing_trades']}")
        print(f"Win Rate:        {result['win_rate']:.2f}%")
        print()
        print(f"Avg Win:         ₹{result['avg_win']:,.2f}")
        print(f"Avg Loss:        ₹{result['avg_loss']:,.2f}")
        print(f"Profit Factor:   {result['profit_factor']:.2f}x")
        print()
        print(f"Sharpe Ratio:    {result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:    {result['max_drawdown']:.2f}%")
        print()
        print("="*60)
