# -*- coding: utf-8 -*-
"""
Unit Tests for Trading System
Comprehensive test suite for all modules
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from config.trading_config import TradingConfig, Market
from strategy.signal_generator import SignalGenerator
from strategy.momentum_strategy import MomentumStrategy
from strategy.mean_reversion_strategy import MeanReversionStrategy
from strategy.breakout_strategy import BreakoutStrategy
from risk_management.risk_manager import RiskManager
from core.position_tracker import PositionTracker
from core.order_manager import OrderManager
from utils.market_hours import MarketHours
from engine.trading_engine import TradingEngine


class TestTradingConfig:
    """
    Unit tests for TradingConfig
    """

    def test_market_selection(self):
        """Test market selection"""
        original_market = TradingConfig.MARKET
        
        TradingConfig.MARKET = Market.NSE
        assert TradingConfig.MARKET == Market.NSE
        
        TradingConfig.MARKET = Market.MCX
        assert TradingConfig.MARKET == Market.MCX
        
        # Restore
        TradingConfig.MARKET = original_market

    def test_get_market_hours(self):
        """Test getting market hours"""
        TradingConfig.MARKET = Market.NSE
        hours = TradingConfig.get_market_hours()
        
        assert "open" in hours
        assert "close" in hours
        assert "timezone" in hours

    def test_get_instruments(self):
        """Test getting configured instruments"""
        instruments = TradingConfig.get_instruments()
        assert isinstance(instruments, list)
        assert len(instruments) > 0

    def test_risk_config(self):
        """Test risk configuration parameters"""
        risk_config = TradingConfig.RISK_CONFIG
        
        assert "max_loss_per_trade" in risk_config
        assert "max_daily_loss" in risk_config
        assert "max_open_positions" in risk_config
        assert risk_config["max_loss_per_trade"] > 0


class TestSignalGenerator:
    """
    Unit tests for SignalGenerator
    """

    def test_calculate_sma(self):
        """Test SMA calculation"""
        prices = [100, 101, 102, 103, 104, 105] * 5
        sma = SignalGenerator.calculate_sma(prices, period=5)
        
        assert sma is not None
        assert len(sma) == len(prices)
        # First 4 values should be NaN
        assert all(np.isnan(sma[i]) for i in range(4))
        # 5th value should be valid
        assert not np.isnan(sma[4])

    def test_calculate_ema(self):
        """Test EMA calculation"""
        prices = [100, 101, 102, 103, 104, 105] * 5
        ema = SignalGenerator.calculate_ema(prices, period=5)
        
        assert ema is not None
        assert len(ema) == len(prices)

    def test_calculate_rsi(self):
        """Test RSI calculation"""
        prices = list(range(100, 200)) + list(range(199, 100, -1))
        rsi = SignalGenerator.calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert len(rsi) == len(prices)
        # RSI should be between 0 and 100
        valid_rsi = [r for r in rsi if not np.isnan(r)]
        assert all(0 <= r <= 100 for r in valid_rsi)

    def test_calculate_atr(self):
        """Test ATR calculation"""
        high = [105, 106, 107, 108] * 10
        low = [95, 96, 97, 98] * 10
        close = [100, 101, 102, 103] * 10
        
        atr = SignalGenerator.calculate_atr(high, low, close, period=14)
        
        assert atr is not None
        assert len(atr) == len(close)

    def test_calculate_macd(self):
        """Test MACD calculation"""
        prices = list(range(100, 200))
        macd = SignalGenerator.calculate_macd(prices)
        
        assert macd is not None
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd

    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        prices = list(np.random.normal(100, 2, 100))
        bb = SignalGenerator.calculate_bollinger_bands(prices, period=20)
        
        assert bb is not None
        assert "middle" in bb
        assert "upper" in bb
        assert "lower" in bb
        
        # Upper band should be > middle > lower
        for i in range(len(prices)):
            if not np.isnan(bb["upper"][i]) and not np.isnan(bb["lower"][i]):
                assert bb["upper"][i] > bb["middle"][i] > bb["lower"][i]

    def test_get_trend_direction(self):
        """Test trend direction detection"""
        # Uptrend
        uptrend = [100, 101, 102, 103, 104]
        direction = SignalGenerator.get_trend_direction(uptrend)
        assert direction == "UP"
        
        # Downtrend
        downtrend = [104, 103, 102, 101, 100]
        direction = SignalGenerator.get_trend_direction(downtrend)
        assert direction == "DOWN"
        
        # Flat
        flat = [100, 100, 100, 100, 100]
        direction = SignalGenerator.get_trend_direction(flat)
        assert direction == "FLAT"


class TestMomentumStrategy:
    """
    Unit tests for MomentumStrategy
    """

    def setup_method(self):
        """Setup test strategy"""
        config = TradingConfig.STRATEGY_CONFIG["momentum"]
        self.strategy = MomentumStrategy(config)
        self.historical_data = self._generate_test_data()

    def _generate_test_data(self, num_candles=100):
        """Generate test historical data"""
        data = []
        price = 100
        for i in range(num_candles):
            change = np.random.normal(0.5, 1.0)
            data.append({
                "open": price,
                "high": price + abs(change) + 1,
                "low": price - abs(change) - 1,
                "close": price + change,
                "volume": 100000,
            })
            price += change
        return data

    def test_generate_signal(self):
        """Test signal generation"""
        price_data = {"ltp": 105}
        signal = self.strategy.generate_signal("INFY", price_data, self.historical_data)
        
        assert signal is not None
        assert "symbol" in signal
        assert "direction" in signal
        assert signal["direction"] in ["BUY", "SELL", "HOLD"]
        assert "confidence" in signal
        assert 0 <= signal["confidence"] <= 100

    def test_validate_signal(self):
        """Test signal validation"""
        # Valid signal
        valid_signal = {
            "symbol": "INFY",
            "direction": "BUY",
            "confidence": 75,
            "reason": "test",
        }
        assert self.strategy.validate_signal(valid_signal) == True
        
        # Low confidence signal
        low_confidence = {
            "symbol": "INFY",
            "direction": "BUY",
            "confidence": 30,
            "reason": "test",
        }
        assert self.strategy.validate_signal(low_confidence) == False
        
        # Hold signal
        hold_signal = {
            "symbol": "INFY",
            "direction": "HOLD",
            "confidence": 75,
            "reason": "test",
        }
        assert self.strategy.validate_signal(hold_signal) == False

    def test_get_stop_loss(self):
        """Test stop loss calculation"""
        entry_price = 100
        atr = 5
        
        sl_buy = self.strategy.get_stop_loss("INFY", "BUY", entry_price, atr)
        assert sl_buy < entry_price
        
        sl_sell = self.strategy.get_stop_loss("INFY", "SELL", entry_price, atr)
        assert sl_sell > entry_price

    def test_get_target(self):
        """Test profit target calculation"""
        entry_price = 100
        stop_loss = 95
        
        target_buy = self.strategy.get_target("INFY", "BUY", entry_price, stop_loss)
        assert target_buy > entry_price
        
        stop_loss_sell = 105
        target_sell = self.strategy.get_target("INFY", "SELL", entry_price, stop_loss_sell)
        assert target_sell < entry_price


class TestRiskManager:
    """
    Unit tests for RiskManager
    """

    def setup_method(self):
        """Setup test risk manager"""
        self.risk_manager = RiskManager()

    def test_calculate_position_size(self):
        """Test position sizing"""
        capital = 100000
        entry_price = 100
        stop_loss = 95
        
        quantity = self.risk_manager.calculate_position_size(capital, entry_price, stop_loss)
        assert quantity > 0
        assert isinstance(quantity, int)
        
        # Max loss should not exceed configured max
        loss = abs(entry_price - stop_loss) * quantity
        assert loss <= TradingConfig.RISK_CONFIG["max_loss_per_trade"]

    def test_can_enter_position(self):
        """Test position entry validation"""
        can_enter, reason = self.risk_manager.can_enter_position("INFY")
        assert isinstance(can_enter, bool)
        
        # After exceeding max positions
        self.risk_manager.active_positions = TradingConfig.RISK_CONFIG["max_open_positions"]
        can_enter, reason = self.risk_manager.can_enter_position("INFY")
        assert can_enter == False

    def test_validate_order(self):
        """Test order validation"""
        # Valid order
        is_valid, reason = self.risk_manager.validate_order(
            "INFY", 100, 100, "BUY", 95, 110
        )
        assert isinstance(is_valid, bool)
        
        # Invalid order (SL above entry for BUY)
        is_valid, reason = self.risk_manager.validate_order(
            "INFY", 100, 100, "BUY", 105, 110
        )
        assert is_valid == False

        # Invalid quantity
        is_valid, reason = self.risk_manager.validate_order(
            "INFY", 100, 0, "BUY", 95, 110
        )
        assert is_valid == False

    def test_daily_loss_tracking(self):
        """Test daily loss tracking"""
        initial_loss = self.risk_manager.daily_loss
        
        self.risk_manager.record_trade_loss(500)
        assert self.risk_manager.daily_loss == initial_loss + 500
        
        self.risk_manager.record_trade_profit(300)
        assert self.risk_manager.daily_loss == initial_loss + 200

    def test_reset_daily_limits(self):
        """Test daily limit reset"""
        self.risk_manager.record_trade_loss(500)
        self.risk_manager.daily_trades = 10
        
        self.risk_manager.reset_daily_limits()
        assert self.risk_manager.daily_loss == 0
        assert self.risk_manager.daily_trades == 0

    def test_calculate_position_size_invalid_inputs(self):
        """Test position sizing rejects invalid values"""
        quantity = self.risk_manager.calculate_position_size(100000, 0, 95)
        assert quantity == 0

        quantity = self.risk_manager.calculate_position_size(100000, 100, 0)
        assert quantity == 0


class TestTradingEngineSafety:
    """
    Unit tests for execution safety gates and symbol-token LTP mapping.
    """

    def test_paper_mode_simulates_orders(self, monkeypatch):
        monkeypatch.setenv("LIVE_TRADING", "false")
        monkeypatch.setenv("ALLOW_LIVE_ORDERS", "false")
        engine = TradingEngine("api_key", "api_secret")
        engine.order_manager = Mock()

        order_data = engine._place_order(
            exchange="NSE",
            tradingsymbol="INFY",
            transaction_type="BUY",
            quantity=1,
            order_type="MARKET",
        )

        assert order_data["is_simulated"] is True
        assert order_data["status"] == "SIMULATED"
        engine.order_manager.place_order.assert_not_called()

    def test_live_mode_places_real_orders(self, monkeypatch):
        monkeypatch.setenv("LIVE_TRADING", "true")
        monkeypatch.setenv("ALLOW_LIVE_ORDERS", "true")
        engine = TradingEngine("api_key", "api_secret")
        engine.order_manager = Mock()
        engine.order_manager.place_order.return_value = {"order_id": "123", "status": "PLACED"}

        order_data = engine._place_order(
            exchange="NSE",
            tradingsymbol="INFY",
            transaction_type="BUY",
            quantity=1,
            order_type="MARKET",
        )

        assert order_data["order_id"] == "123"
        engine.order_manager.place_order.assert_called_once()

    def test_single_live_flag_keeps_paper_mode(self, monkeypatch):
        monkeypatch.setenv("LIVE_TRADING", "true")
        monkeypatch.setenv("ALLOW_LIVE_ORDERS", "false")
        engine = TradingEngine("api_key", "api_secret")
        engine.order_manager = Mock()

        order_data = engine._place_order(
            exchange="NSE",
            tradingsymbol="INFY",
            transaction_type="BUY",
            quantity=1,
            order_type="MARKET",
        )

        assert order_data["is_simulated"] is True
        engine.order_manager.place_order.assert_not_called()

    def test_ltp_uses_token_stream_then_quote_fallback(self, monkeypatch):
        monkeypatch.setenv("LIVE_TRADING", "false")
        monkeypatch.setenv("ALLOW_LIVE_ORDERS", "false")
        engine = TradingEngine("api_key", "api_secret")
        engine.symbol_to_instrument_token = {"INFY": 12345}
        engine.symbol_to_exchange = {"INFY": "NSE"}
        engine.market_data = Mock()
        engine.kite = Mock()

        engine.market_data.get_ltp.return_value = 1520.5
        ltp = engine._get_ltp("INFY")
        assert ltp == 1520.5
        engine.kite.quote.assert_not_called()

        engine.market_data.get_ltp.return_value = None
        engine.kite.quote.return_value = {"NSE:INFY": {"last_price": 1519.0}}
        ltp = engine._get_ltp("INFY")
        assert ltp == 1519.0
        engine.kite.quote.assert_called_with("NSE:INFY")


class TestPositionTracker:
    """
    Unit tests for PositionTracker
    """

    def setup_method(self):
        """Setup test position tracker"""
        mock_kite = Mock()
        self.tracker = PositionTracker(mock_kite)

    def test_open_position(self):
        """Test opening a position"""
        self.tracker.open_position(
            symbol="INFY",
            entry_price=100,
            quantity=100,
            side="BUY",
            stop_loss=95,
            target=110,
            order_id="123"
        )
        
        position = self.tracker.get_position("INFY")
        assert position is not None
        assert position["entry_price"] == 100
        assert position["quantity"] == 100
        assert position["side"] == "BUY"

    def test_update_position(self):
        """Test position P&L update"""
        self.tracker.open_position(
            symbol="INFY",
            entry_price=100,
            quantity=100,
            side="BUY",
            stop_loss=95,
            target=110,
            order_id="123"
        )
        
        # Update with profit
        updated = self.tracker.update_position("INFY", 105)
        assert updated["pnl"] == 500  # (105-100) * 100
        assert updated["pnl_percent"] == 5.0

    def test_close_position(self):
        """Test closing a position"""
        self.tracker.open_position(
            symbol="INFY",
            entry_price=100,
            quantity=100,
            side="BUY",
            stop_loss=95,
            target=110,
            order_id="123"
        )
        
        closed = self.tracker.close_position("INFY", 110)
        assert closed["pnl"] == 1000  # (110-100) * 100
        
        # Position should be removed
        assert self.tracker.get_position("INFY") is None
        # Should be in closed positions
        assert len(self.tracker.closed_positions) == 1

    def test_get_position_summary(self):
        """Test position summary"""
        summary = self.tracker.get_position_summary()
        
        assert "open_positions" in summary
        assert "total_unrealized_pnl" in summary
        assert "total_realized_pnl" in summary
        assert "total_daily_pnl" in summary


class TestOrderManager:
    """
    Unit tests for OrderManager
    """

    def setup_method(self):
        """Setup test order manager"""
        mock_kite = Mock()
        mock_kite.place_order.return_value = "12345"
        self.manager = OrderManager(mock_kite)

    def test_place_order(self):
        """Test order placement"""
        result = self.manager.place_order(
            exchange="NSE",
            tradingsymbol="INFY",
            transaction_type="BUY",
            quantity=100,
        )
        
        assert result is not None
        assert "order_id" in result
        assert result["status"] == "PLACED"

    def test_get_order_status(self):
        """Test getting order status"""
        # Place order first
        self.manager.place_order(
            exchange="NSE",
            tradingsymbol="INFY",
            transaction_type="BUY",
            quantity=100,
        )
        
        status = self.manager.get_order_status("12345")
        assert status is not None


class TestMarketHours:
    """
    Unit tests for MarketHours
    """

    def test_get_market_status(self):
        """Test getting market status"""
        status = MarketHours.get_market_status()
        
        assert "market" in status
        assert "is_open" in status
        assert "current_time" in status
        assert "market_open" in status
        assert "market_close" in status

    def test_is_market_open(self):
        """Test market open check"""
        is_open = MarketHours.is_market_open()
        assert isinstance(is_open, bool)

    def test_get_time_to_market_close(self):
        """Test time to market close"""
        time_to_close = MarketHours.get_time_to_market_close()
        # Should be either None or a timedelta
        assert time_to_close is None or isinstance(time_to_close, timedelta)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
