# -*- coding: utf-8 -*-
"""
Database Layer for Trade Persistence
Store and retrieve trades, orders, and performance metrics
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from utils.logger import TradingLogger


class TradeDatabase:
    """
    SQLite database for persistent trade storage.
    """

    def __init__(self, db_path="trading_data.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: str - Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = TradingLogger.get_logger()
        self._initialize_database()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection - Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """
        Create database tables if they don't exist.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    pnl REAL,
                    pnl_percent REAL,
                    exit_reason TEXT,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL,
                    status TEXT NOT NULL,
                    order_type TEXT,
                    placed_at TIMESTAMP NOT NULL,
                    executed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily Performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    total_profit REAL,
                    total_loss REAL,
                    max_loss REAL,
                    max_profit REAL,
                    sharpe_ratio REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Signals table (for analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_direction TEXT NOT NULL,
                    confidence REAL,
                    rsi REAL,
                    sma_short REAL,
                    sma_long REAL,
                    macd REAL,
                    generated_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(entry_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
            
            self.logger.info("Database initialized successfully")

    def add_trade(self, trade_data):
        """
        Store a closed trade in the database.
        
        Args:
            trade_data: dict - Trade information
            
        Returns:
            int - Trade ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate duration
            if trade_data.get("exit_time") and trade_data.get("entry_time"):
                duration = (trade_data["exit_time"] - trade_data["entry_time"]).total_seconds()
            else:
                duration = None
            
            cursor.execute("""
                INSERT INTO trades (
                    symbol, side, quantity, entry_price, exit_price,
                    entry_time, exit_time, pnl, pnl_percent, exit_reason,
                    duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data["symbol"],
                trade_data["side"],
                trade_data["quantity"],
                trade_data["entry_price"],
                trade_data.get("exit_price"),
                trade_data["entry_time"],
                trade_data.get("exit_time"),
                trade_data.get("pnl"),
                trade_data.get("pnl_percent"),
                trade_data.get("exit_reason"),
                duration,
            ))
            
            self.logger.info(f"Trade stored: {trade_data['symbol']} {trade_data['side']}")
            return cursor.lastrowid

    def add_order(self, order_data):
        """
        Store an order in the database.
        
        Args:
            order_data: dict - Order information
            
        Returns:
            int - Order ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO orders (
                    order_id, symbol, side, quantity, price,
                    status, order_type, placed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_data["order_id"],
                order_data["symbol"],
                order_data["side"],
                order_data["quantity"],
                order_data.get("price"),
                order_data["status"],
                order_data.get("order_type"),
                order_data["placed_at"],
            ))
            
            return cursor.lastrowid

    def add_signal(self, signal_data):
        """
        Store a trading signal in the database.
        
        Args:
            signal_data: dict - Signal information
            
        Returns:
            int - Signal ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals (
                    symbol, signal_direction, confidence,
                    rsi, sma_short, sma_long, macd, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data["symbol"],
                signal_data["direction"],
                signal_data.get("confidence"),
                signal_data.get("indicators", {}).get("rsi"),
                signal_data.get("indicators", {}).get("sma_short"),
                signal_data.get("indicators", {}).get("sma_long"),
                signal_data.get("indicators", {}).get("macd"),
                signal_data.get("timestamp", datetime.now()),
            ))
            
            return cursor.lastrowid

    def get_trades(self, symbol=None, limit=100):
        """
        Retrieve trades from database.
        
        Args:
            symbol: str - Filter by symbol (optional)
            limit: int - Maximum number of trades to return
            
        Returns:
            list - List of trades
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute("""
                    SELECT * FROM trades
                    WHERE symbol = ?
                    ORDER BY entry_time DESC
                    LIMIT ?
                """, (symbol, limit))
            else:
                cursor.execute("""
                    SELECT * FROM trades
                    ORDER BY entry_time DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_daily_performance(self, date=None):
        """
        Get daily performance metrics.
        
        Args:
            date: datetime - Specific date (optional, defaults to today)
            
        Returns:
            dict - Daily performance data or None
        """
        if date is None:
            date = datetime.now().date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_performance
                WHERE date = ?
            """, (str(date),))
            
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_daily_performance(self, date, performance_data):
        """
        Save daily performance metrics.
        
        Args:
            date: datetime - Date for performance
            performance_data: dict - Performance metrics
        """
        if isinstance(date, datetime):
            date = date.date()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if record exists
            cursor.execute("SELECT id FROM daily_performance WHERE date = ?", (str(date),))
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE daily_performance SET
                    total_trades = ?,
                    winning_trades = ?,
                    losing_trades = ?,
                    win_rate = ?,
                    total_pnl = ?,
                    total_profit = ?,
                    total_loss = ?,
                    max_loss = ?,
                    max_profit = ?,
                    sharpe_ratio = ?
                    WHERE date = ?
                """, (
                    performance_data.get("total_trades"),
                    performance_data.get("winning_trades"),
                    performance_data.get("losing_trades"),
                    performance_data.get("win_rate"),
                    performance_data.get("total_pnl"),
                    performance_data.get("total_profit"),
                    performance_data.get("total_loss"),
                    performance_data.get("max_loss"),
                    performance_data.get("max_profit"),
                    performance_data.get("sharpe_ratio"),
                    str(date),
                ))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO daily_performance (
                        date, total_trades, winning_trades, losing_trades,
                        win_rate, total_pnl, total_profit, total_loss,
                        max_loss, max_profit, sharpe_ratio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(date),
                    performance_data.get("total_trades"),
                    performance_data.get("winning_trades"),
                    performance_data.get("losing_trades"),
                    performance_data.get("win_rate"),
                    performance_data.get("total_pnl"),
                    performance_data.get("total_profit"),
                    performance_data.get("total_loss"),
                    performance_data.get("max_loss"),
                    performance_data.get("max_profit"),
                    performance_data.get("sharpe_ratio"),
                ))

    def get_performance_summary(self, days=30):
        """
        Get performance summary for the last N days.
        
        Args:
            days: int - Number of days to summarize
            
        Returns:
            dict - Aggregated performance metrics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(total_trades) as total_trades,
                    SUM(winning_trades) as winning_trades,
                    SUM(losing_trades) as losing_trades,
                    AVG(win_rate) as avg_win_rate,
                    SUM(total_pnl) as total_pnl,
                    AVG(sharpe_ratio) as avg_sharpe,
                    COUNT(*) as trading_days
                FROM daily_performance
                WHERE date >= DATE('now', '-' || ? || ' days')
            """, (days,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_symbol_statistics(self, symbol):
        """
        Get performance statistics for a specific symbol.
        
        Args:
            symbol: str - Trading symbol
            
        Returns:
            dict - Symbol statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    AVG(pnl) as avg_pnl,
                    SUM(pnl) as total_pnl,
                    MAX(pnl) as max_profit,
                    MIN(pnl) as max_loss,
                    AVG(pnl_percent) as avg_return_percent,
                    AVG(duration_seconds) as avg_duration_seconds
                FROM trades
                WHERE symbol = ? AND exit_time IS NOT NULL
            """, (symbol,))
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data["total_trades"] > 0:
                    data["win_rate"] = (data["winning_trades"] / data["total_trades"]) * 100
                    data["profit_factor"] = abs(data["total_pnl"] / (data["max_loss"] or 1))
                return data
            return None

    def export_trades_to_csv(self, filepath, symbol=None):
        """
        Export trades to CSV file.
        
        Args:
            filepath: str - Path to save CSV file
            symbol: str - Filter by symbol (optional)
        """
        import csv
        
        trades = self.get_trades(symbol=symbol, limit=10000)
        
        if not trades:
            self.logger.warning("No trades to export")
            return
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
            
            self.logger.info(f"Exported {len(trades)} trades to {filepath}")
        except Exception as e:
            self.logger.error(f"Export error: {str(e)}")
