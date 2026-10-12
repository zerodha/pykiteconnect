# -*- coding: utf-8 -*-
"""
Trading Engine
Orchestrates the entire trading system - market data, signals, orders, positions
"""

import threading
import time
from datetime import datetime, timedelta, time as dt_time
import uuid
from core.authentication import AuthenticationManager
from core.market_data import MarketDataHandler
from core.order_manager import OrderManager
from core.position_tracker import PositionTracker
from strategy.momentum_strategy import MomentumStrategy
from risk_management.risk_manager import RiskManager
from data.historical_data import HistoricalDataFetcher
from utils.logger import TradingLogger
from utils.market_hours import MarketHours
from config.trading_config import TradingConfig


class TradingEngine:
    """
    Main trading engine that orchestrates all components.
    Manages authentication, market data, signals, orders, and positions.
    """
    LOOKBACK_BUFFER_CANDLES = 5

    def __init__(self, api_key, api_secret):
        """
        Initialize trading engine.
        
        Args:
            api_key: str - Kite API key
            api_secret: str - Kite API secret
        """
        self.logger = TradingLogger.get_logger()
        self.logger.info("=" * 50)
        self.logger.info("TRADING ENGINE INITIALIZED")
        self.logger.info("=" * 50)
        
        # Core components
        self.auth = AuthenticationManager(api_key, api_secret)
        self.kite = None
        self.market_data = None
        self.order_manager = None
        self.position_tracker = None
        self.strategy = None
        self.risk_manager = RiskManager()
        self.historical_data_fetcher = None
        
        # State
        self.is_running = False
        self.is_trading = False
        self.engine_thread = None
        self.symbols_to_trade = []
        self.historical_data_cache = {}  # Cache for historical data
        self.skipped_symbols = set()
        self.symbol_to_instrument_token = {}
        self.instrument_token_to_symbol = {}
        self.symbol_to_exchange = {}
        self.execution_config = TradingConfig.get_execution_config()
        self.live_orders_enabled = self.execution_config["live_orders_enabled"]
        self.execution_mode = "LIVE" if self.live_orders_enabled else "PAPER"
        self.logger.warning(
            f"Execution mode: {self.execution_mode} | "
            f"{self.execution_config['live_trading_env']}={self.execution_config['live_trading_requested']} | "
            f"{self.execution_config['allow_live_orders_env']}={self.execution_config['allow_live_orders']}"
        )
        
        # Callbacks
        self.on_signal = None
        self.on_order = None
        self.on_position = None

    def authenticate(self, access_token=None):
        """
        Authenticate with Kite Connect.
        
        Args:
            access_token: str - Saved access token (optional)
            
        Returns:
            bool - Authentication success
        """
        try:
            if access_token:
                self.kite = self.auth.restore_session(access_token)
                self.logger.info("Session restored from saved token")
            else:
                # Try to load saved session
                saved_session = self.auth.load_saved_session()
                if saved_session:
                    self.kite = self.auth.restore_session(saved_session["access_token"])
                    self.logger.info("Session restored from saved file")
                else:
                    # Need new login
                    login_url = self.auth.get_login_url()
                    self.logger.info(f"Please login: {login_url}")
                    request_token = input("Enter request_token from redirect URL: ")
                    session_data = self.auth.create_session(request_token)
                    self.kite = self.auth.get_kite_instance()
                    self.logger.info(f"New session created for {session_data['user_name']}")
            
            # Initialize other components with authenticated Kite instance
            self.market_data = MarketDataHandler(
                self.kite,
                self.auth.api_key,
                self.kite.access_token
            )
            self.order_manager = OrderManager(self.kite)
            self.position_tracker = PositionTracker(self.kite)
            self.strategy = MomentumStrategy(TradingConfig.STRATEGY_CONFIG["momentum"])
            self.historical_data_fetcher = HistoricalDataFetcher(self.kite)
            
            # Fetch user profile to verify authentication
            profile = self.kite.profile()
            self.logger.info(f"Authenticated as: {profile['user_name']} ({profile['email']})")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False

    def set_instruments(self, symbols):
        """
        Set instruments to trade.
        
        Args:
            symbols: list - Trading symbols (e.g., ['INFY', 'TCS'])
        """
        self.symbols_to_trade = symbols
        self.logger.info(f"Instruments set: {', '.join(symbols)}")

    def start(self, threaded=True):
        """
        Start the trading engine.
        
        Args:
            threaded: bool - Run in separate thread
        """
        if not self.kite:
            self.logger.error("Not authenticated. Call authenticate() first.")
            return False
        
        if not self.symbols_to_trade:
            self.logger.error("No instruments set. Call set_instruments() first.")
            return False
        
        # Check market status
        market_status = MarketHours.get_market_status()
        if not market_status["is_open"]:
            self.logger.warning(f"Market is not open. Next close: {market_status['market_close']}")
        
        try:
            self._initialize_symbol_token_mapping()
            self.execution_config = TradingConfig.get_execution_config()
            self.live_orders_enabled = self.execution_config["live_orders_enabled"]
            self.execution_mode = "LIVE" if self.live_orders_enabled else "PAPER"
            self.logger.warning(f"Trading start mode: {self.execution_mode}")

            # Connect to market data
            self.logger.info("Connecting to market data...")
            self.market_data.connect(threaded=True)
            time.sleep(1)

            # Subscribe to instrument tokens
            instrument_tokens = list(self.symbol_to_instrument_token.values())
            if instrument_tokens:
                self.market_data.subscribe(instrument_tokens)
                self.market_data.set_mode(self.market_data.ticker.MODE_FULL, instrument_tokens)
            else:
                self.logger.error("No valid instrument tokens resolved; cannot start trading.")
                return False
            
            # Fetch initial historical data
            self.logger.info("Fetching historical data...")
            self._fetch_historical_data()
            
            self.is_running = True
            self.is_trading = True
            
            if threaded:
                self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
                self.engine_thread.start()
                self.logger.info("Trading engine started (threaded mode)")
            else:
                self._run_engine()
                self.logger.info("Trading engine started (blocking mode)")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start engine: {str(e)}")
            return False

    def _run_engine(self):
        """
        Main engine loop - monitors market and generates signals.
        """
        try:
            while self.is_running:
                # Check market hours
                market_status = MarketHours.get_market_status()
                
                if not market_status["is_open"]:
                    # Market closed
                    time_to_close = market_status["time_to_close"]
                    if time_to_close:
                        self.logger.info(f"Market closes in {time_to_close}")
                    self.is_trading = False
                    time.sleep(60)
                    continue
                
                self.is_trading = True
                
                # Process each symbol
                for symbol in self.symbols_to_trade:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {str(e)}")
                
                # Sleep before next cycle
                time.sleep(5)  # 5-second cycle
        
        except Exception as e:
            self.logger.error(f"Engine error: {str(e)}")
            self.stop()

    def _process_symbol(self, symbol):
        """
        Process a single symbol - fetch data, generate signal, manage positions.
        
        Args:
            symbol: str - Trading symbol
        """
        # Get current price
        current_price = self._get_ltp(symbol)
        
        if not current_price:
            return
        
        # Get historical data
        if symbol not in self.historical_data_cache:
            self._fetch_symbol_historical_data(symbol)
        
        historical_data = self.historical_data_cache.get(symbol, [])
        
        if not historical_data:
            return
        
        # Generate signal
        price_data = {"ltp": current_price}
        signal = self.strategy.generate_signal(symbol, price_data, historical_data)
        
        # Store signal
        self.strategy.update_signal(symbol, signal)
        
        # Trigger callback
        if self.on_signal:
            self.on_signal(signal)
        
        # Check for position
        position = self.position_tracker.get_position(symbol)
        
        if position and position["status"] == "OPEN":
            # Update position P&L
            updated_position = self.position_tracker.update_position(symbol, current_price)
            
            # Check exit conditions
            self._check_exit_conditions(symbol, current_price, position)
        
        else:
            # No open position - check for entry signal
            if self.strategy.validate_signal(signal):
                self._attempt_entry(symbol, signal, current_price)

    def _attempt_entry(self, symbol, signal, current_price):
        """
        Attempt to enter a position based on signal.
        
        Args:
            symbol: str - Trading symbol
            signal: dict - Trading signal
            current_price: float - Current price
        """
        try:
            # Check if can enter
            can_enter, reason = self.risk_manager.can_enter_position(symbol)
            if not can_enter:
                self.logger.warning(f"Cannot enter {symbol}: {reason}")
                return
            
            # Get entry parameters
            direction = signal["direction"]
            entry_price = current_price
            atr = signal["indicators"].get("atr")
            
            # Calculate stop loss and target
            stop_loss = self.strategy.get_stop_loss(symbol, direction, entry_price, atr)
            target = self.strategy.get_target(symbol, direction, entry_price, stop_loss)
            
            # Calculate position size
            capital = 100000  # TODO: Get from account
            quantity = self.risk_manager.calculate_position_size(
                capital, entry_price, stop_loss
            )
            
            # Validate order
            is_valid, reason = self.risk_manager.validate_order(
                symbol, entry_price, quantity, direction, stop_loss, target
            )
            
            if not is_valid:
                self.logger.warning(f"Order validation failed for {symbol}: {reason}")
                return
            
            # Place entry order
            exchange = self.symbol_to_exchange.get(symbol, "NSE" if TradingConfig.MARKET.value == "nse" else "MCX")
            transaction_type = "BUY" if direction == "BUY" else "SELL"
            
            order_data = self._place_order(
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                variety="regular",
                product="MIS",
                order_type="MARKET",
                tag=f"MOMENTUM_{direction}"
            )
            
            # Open position
            self.position_tracker.open_position(
                symbol=symbol,
                entry_price=entry_price,
                quantity=quantity,
                side=direction,
                stop_loss=stop_loss,
                target=target,
                order_id=order_data["order_id"]
            )
            
            # Increment active positions
            self.risk_manager.increment_active_positions()
            
            # Trigger callback
            if self.on_position:
                self.on_position("OPEN", self.position_tracker.get_position(symbol))
            
            self.logger.info(
                f"Entry: {symbol} {direction} x{quantity} @ {entry_price} | "
                f"SL: {stop_loss} | Target: {target}"
            )
        
        except Exception as e:
            self.logger.error(f"Entry error for {symbol}: {str(e)}")

    def _check_exit_conditions(self, symbol, current_price, position):
        """
        Check if position should be exited.
        
        Args:
            symbol: str - Trading symbol
            current_price: float - Current price
            position: dict - Position data
        """
        direction = position["side"]
        entry_price = position["entry_price"]
        stop_loss = position["stop_loss"]
        target = position["target"]
        
        exit_reason = None
        
        # Check stop loss
        if direction == "BUY":
            if current_price <= stop_loss:
                exit_reason = "STOPLOSS"
        else:  # SELL
            if current_price >= stop_loss:
                exit_reason = "STOPLOSS"
        
        # Check target
        if direction == "BUY":
            if current_price >= target:
                exit_reason = "TARGET"
        else:  # SELL
            if current_price <= target:
                exit_reason = "TARGET"
        
        # Check market close time
        market_status = MarketHours.get_market_status()
        if TradingConfig.POSITION_CONFIG.get("auto_square_off"):
            time_to_close = market_status.get("time_to_close")
            current_time = market_status.get("current_time")
            square_off_time = TradingConfig.POSITION_CONFIG.get("square_off_time")
            should_square_off = False

            if (
                isinstance(current_time, datetime)
                and isinstance(square_off_time, dt_time)
            ):
                should_square_off = current_time.time() >= square_off_time
            elif isinstance(time_to_close, timedelta):
                should_square_off = time_to_close.total_seconds() <= 300

            if should_square_off:
                exit_reason = "MARKET_CLOSE"
        
        if exit_reason:
            self._exit_position(symbol, current_price, exit_reason)

    def _exit_position(self, symbol, exit_price, reason):
        """
        Exit a position.
        
        Args:
            symbol: str - Trading symbol
            exit_price: float - Exit price
            reason: str - Exit reason
        """
        try:
            position = self.position_tracker.get_position(symbol)
            
            if not position:
                return
            
            # Close position
            exchange = self.symbol_to_exchange.get(symbol, "NSE" if TradingConfig.MARKET.value == "nse" else "MCX")
            transaction_type = "SELL" if position["side"] == "BUY" else "BUY"
            
            order_data = self._place_order(
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=position["quantity"],
                variety="regular",
                product="MIS",
                order_type="MARKET",
                tag=f"EXIT_{reason}"
            )
            
            # Update position
            closed_position = self.position_tracker.close_position(
                symbol, exit_price, order_data["order_id"]
            )
            
            # Decrement active positions
            self.risk_manager.decrement_active_positions()
            
            # Record P&L
            if closed_position["pnl"] < 0:
                self.risk_manager.record_trade_loss(abs(closed_position["pnl"]))
            else:
                self.risk_manager.record_trade_profit(closed_position["pnl"])
            
            # Trigger callback
            if self.on_position:
                self.on_position("CLOSED", closed_position)
            
            self.logger.info(
                f"Exit: {symbol} {position['side']} x{position['quantity']} @ {exit_price} | "
                f"P&L: {closed_position['pnl']:.2f} ({closed_position['pnl_percent']:.2f}%) | "
                f"Reason: {reason}"
            )
        
        except Exception as e:
            self.logger.error(f"Exit error for {symbol}: {str(e)}")

    def _fetch_historical_data(self):
        """
        Fetch historical data for all symbols.
        """
        required_candles = self._get_required_lookback_candles()
        interval = self._get_historical_interval()
        for symbol in self.symbols_to_trade:
            self._fetch_symbol_historical_data(
                symbol,
                required_candles=required_candles,
                interval=interval,
            )

    def _fetch_symbol_historical_data(self, symbol, required_candles=None, interval=None):
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: str - Trading symbol
        """
        try:
            if not self.historical_data_fetcher:
                self.logger.error(f"Historical data fetcher not initialized for {symbol}")
                self.skipped_symbols.add(symbol)
                return

            instrument_token = self.symbol_to_instrument_token.get(symbol)
            if not instrument_token:
                self.logger.error(f"No instrument token mapping found for {symbol}; skipping symbol")
                self.skipped_symbols.add(symbol)
                return

            required_candles = required_candles or self._get_required_lookback_candles()
            interval = interval or self._get_historical_interval()
            historical_data = self.historical_data_fetcher.get_last_n_candles_by_token(
                instrument_token=instrument_token,
                n=required_candles,
                interval=interval,
            )

            if not historical_data or len(historical_data) < required_candles:
                self.logger.error(
                    f"Insufficient historical data for {symbol} "
                    f"({0 if not historical_data else len(historical_data)}/{required_candles}); skipping symbol"
                )
                self.historical_data_cache.pop(symbol, None)
                self.skipped_symbols.add(symbol)
                return

            self.historical_data_cache[symbol] = historical_data
            self.skipped_symbols.discard(symbol)
            self.logger.info(f"Loaded historical candles for {symbol}: {len(historical_data)}")
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            self.historical_data_cache.pop(symbol, None)
            self.skipped_symbols.add(symbol)

    def stop(self):
        """
        Stop the trading engine.
        """
        try:
            self.is_running = False
            self.is_trading = False
            
            # Disconnect market data
            if self.market_data:
                self.market_data.disconnect()
            
            # Close all positions
            for symbol in list(self.position_tracker.get_all_positions().keys()):
                try:
                    current_price = self._get_ltp(symbol) or 100
                    self._exit_position(symbol, current_price, "MANUAL_STOP")
                except:
                    pass
            
            self.logger.info("Trading engine stopped")
            
            # Print summary
            summary = self.position_tracker.get_position_summary()
            risk_summary = self.risk_manager.get_risk_summary()
            self.logger.info(f"Daily Summary: {summary}")
            self.logger.info(f"Risk Summary: {risk_summary}")
        
        except Exception as e:
            self.logger.error(f"Error stopping engine: {str(e)}")

    def get_status(self):
        """
        Get current engine status.
        
        Returns:
            dict - Status information
        """
        market_status = MarketHours.get_market_status()
        position_summary = self.position_tracker.get_position_summary()
        risk_summary = self.risk_manager.get_risk_summary()
        
        return {
            "is_running": self.is_running,
            "is_trading": self.is_trading,
            "execution_mode": self.execution_mode,
            "live_orders_enabled": self.live_orders_enabled,
            "market_status": market_status,
            "positions": position_summary,
            "risk": risk_summary,
            "signals": self.strategy.signals if self.strategy else {},
        }

    def _initialize_symbol_token_mapping(self):
        """
        Build canonical symbol <-> instrument token mappings.
        """
        configured_instruments = TradingConfig.get_instruments()
        configured_by_symbol = {item["symbol"]: item for item in configured_instruments}
        symbols = list(self.symbols_to_trade)

        self.symbol_to_exchange = {}
        for symbol in symbols:
            instrument_cfg = configured_by_symbol.get(symbol, {})
            self.symbol_to_exchange[symbol] = instrument_cfg.get(
                "exchange",
                "NSE" if TradingConfig.MARKET.value == "nse" else "MCX",
            )

        self.symbol_to_instrument_token = {}
        self.instrument_token_to_symbol = {}

        exchanges = sorted(set(self.symbol_to_exchange.values()))
        for exchange in exchanges:
            try:
                instruments = self.kite.instruments(exchange=exchange)
            except Exception as e:
                self.logger.error(f"Failed loading instruments for {exchange}: {str(e)}")
                continue

            token_by_symbol = {
                instrument.get("tradingsymbol"): instrument.get("instrument_token")
                for instrument in instruments
            }

            for symbol, symbol_exchange in self.symbol_to_exchange.items():
                if symbol_exchange != exchange:
                    continue
                token = token_by_symbol.get(symbol)
                if token:
                    self.symbol_to_instrument_token[symbol] = token
                    self.instrument_token_to_symbol[token] = symbol
                else:
                    self.logger.error(f"Instrument token not found for {exchange}:{symbol}")

        missing_symbols = [s for s in symbols if s not in self.symbol_to_instrument_token]
        if missing_symbols:
            self.logger.error(
                f"Skipping symbols with missing instrument token mapping: {', '.join(missing_symbols)}"
            )
            self.symbols_to_trade = [s for s in symbols if s in self.symbol_to_instrument_token]
        self.logger.info(
            f"Resolved instrument mappings for {len(self.symbols_to_trade)} symbols"
        )

    def _get_ltp(self, symbol):
        """
        Get LTP for a symbol from stream first, then quote fallback.
        """
        instrument_token = self.symbol_to_instrument_token.get(symbol)
        exchange = self.symbol_to_exchange.get(symbol, "NSE" if TradingConfig.MARKET.value == "nse" else "MCX")

        if instrument_token and self.market_data:
            streamed_ltp = self.market_data.get_ltp(instrument_token)
            if streamed_ltp is not None:
                return streamed_ltp

        quote_key = f"{exchange}:{symbol}"
        try:
            quote = self.kite.quote(quote_key)
            if quote and quote_key in quote:
                return quote[quote_key].get("last_price")
        except Exception as e:
            self.logger.warning(f"Quote fallback failed for {quote_key}: {str(e)}")

        return None

    def _get_required_lookback_candles(self):
        """
        Determine minimum lookback candles needed for configured indicators.
        """
        strategy_config = TradingConfig.STRATEGY_CONFIG.get("momentum", {})
        configured_lookback = strategy_config.get("lookback_candles", 50)
        indicator_periods = [
            strategy_config.get("rsi_period", 14),
            strategy_config.get("sma_short_period", 9),
            strategy_config.get("sma_long_period", 21),
            strategy_config.get("atr_period", 14),
        ]
        required = max([configured_lookback] + indicator_periods) + self.LOOKBACK_BUFFER_CANDLES
        return max(50, int(required))

    def _get_historical_interval(self):
        """
        Map strategy timeframe to Kite historical interval.
        """
        timeframe = TradingConfig.STRATEGY_CONFIG.get("momentum", {}).get("timeframe", "5min")
        timeframe_map = {
            "1min": "1minute",
            "5min": "5minute",
            "15min": "15minute",
            "30min": "30minute",
            "60min": "60minute",
            "daily": "day",
        }
        return timeframe_map.get(timeframe, "5minute")

    def _place_order(self, **order_kwargs):
        """
        Place live order only when explicitly enabled, else simulate.
        """
        if self.live_orders_enabled:
            return self.order_manager.place_order(**order_kwargs)

        symbol = order_kwargs.get("tradingsymbol", "UNKNOWN")
        transaction_type = order_kwargs.get("transaction_type", "NA")
        quantity = order_kwargs.get("quantity", 0)
        simulated_order_id = f"SIM-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
        self.logger.warning(
            f"[PAPER MODE] Simulated {transaction_type} order for {symbol} x{quantity}; "
            "live order placement blocked"
        )
        return {
            "order_id": simulated_order_id,
            "symbol": symbol,
            "exchange": order_kwargs.get("exchange"),
            "type": transaction_type,
            "quantity": quantity,
            "product": order_kwargs.get("product"),
            "order_type": order_kwargs.get("order_type"),
            "price": order_kwargs.get("price"),
            "trigger_price": order_kwargs.get("trigger_price"),
            "status": "SIMULATED",
            "placed_at": datetime.now(),
            "tag": order_kwargs.get("tag"),
            "is_simulated": True,
        }
