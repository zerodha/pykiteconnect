# Intraday Trading System

A comprehensive, production-ready intraday trading system built on the Kite Connect API. Features momentum-based strategy, real-time WebSocket streaming, intelligent risk management, and a web-based dashboard for live monitoring.

## 🎯 Key Features

✅ **Momentum-Based Strategy** — RSI + SMA crossover with dynamic signal strength  
✅ **Real-Time Market Data** — WebSocket streaming via Kite Ticker  
✅ **Intelligent Risk Management** — Position sizing, stop-loss, daily drawdown limits  
✅ **Automatic Order Execution** — Market orders with trailing stops  
✅ **Live Dashboard** — Flask-based web UI for real-time monitoring  
✅ **Position Tracking** — Live P&L, entry/exit logs, trade analytics  
✅ **Multi-Market Support** — NSE (stocks, F&O) and MCX (commodities) with market-hour awareness  
✅ **Comprehensive Logging** — Structured logs for trades, orders, and system events  
✅ **Session Persistence** — Automatic token refresh and session recovery  

## 🏗️ Architecture

```
trading_system/
├── config/                 # Configuration management
│   └── trading_config.py  # NSE/MCX settings, risk params, strategy config
│
├── core/                   # Core trading components
│   ├── authentication.py   # Kite Connect session management
│   ├── market_data.py      # WebSocket price streaming
│   ├── order_manager.py    # Order placement & tracking
│   └── position_tracker.py # P&L & position management
│
├── strategy/              # Strategy implementation
│   ├── base_strategy.py   # Abstract base class
│   ├── signal_generator.py # Technical indicators (RSI, SMA, MACD, ATR, etc.)
│   └── momentum_strategy.py # Momentum-based entry/exit logic
│
├── risk_management/       # Risk controls
│   └── risk_manager.py    # Position sizing, loss limits, validations
│
├── engine/                # Trading orchestration
│   └── trading_engine.py  # Main engine coordinating all components
│
├── dashboard/             # Web UI
│   ├── app.py            # Flask API server
│   └── templates/
│       └── index.html    # Real-time monitoring dashboard
│
├── utils/                # Utilities
│   ├── logger.py         # Structured logging
│   └── market_hours.py   # Market hour management
│
└── main.py              # Entry point
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Kite Connect API credentials (get from [Zerodha](https://kite.zerodha.com/api))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sanjay624/pykiteconnect.git
   cd pykiteconnect
   git checkout intraday-trading-system
   cd trading_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API credentials**
   ```bash
   export KITE_API_KEY="your_api_key"
   export KITE_API_SECRET="your_api_secret"
   # Optional: enable live order placement (double opt-in required)
   export LIVE_TRADING="true"
   export ALLOW_LIVE_ORDERS="true"
   ```

4. **Run the system**
   ```bash
   python main.py
   ```

5. **Open dashboard**
   - Navigate to `http://localhost:5000` in your browser
   - Click "Start Trading" to begin

## ⚙️ Configuration

All settings are in `config/trading_config.py`:

### Market Selection
```python
from config.trading_config import Market

# Switch between NSE and MCX
TradingConfig.MARKET = Market.NSE    # Or Market.MCX
```

### Risk Management
```python
RISK_CONFIG = {
    "max_loss_per_trade": 500,        # Max loss per trade (₹)
    "max_daily_loss": 2000,           # Max daily loss (₹)
    "max_position_size": 10000,       # Max capital per position (₹)
    "max_open_positions": 3,          # Max concurrent positions
    "risk_per_trade": 1.0,            # Risk per trade as % of capital
}
```

### Strategy Parameters
```python
STRATEGY_CONFIG = {
    "momentum": {
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "sma_short_period": 9,
        "sma_long_period": 21,
        "atr_period": 14,
        "lookback_candles": 50,
    }
}
```

### Position Management
```python
POSITION_CONFIG = {
    "auto_square_off": True,           # Auto close at market close
    "square_off_time": time(15, 25),   # 5 mins before market close
    "stop_loss_type": "atr",           # ATR-based stop loss
    "stop_loss_atr_multiplier": 1.5,
    "use_trailing_stop": False,
}
```

## 📊 Strategy Explanation

### Momentum Strategy

**Entry Rules:**
- **BUY Signal:** RSI < 30 (oversold) + SMA short > SMA long + Positive MACD crossover
- **SELL Signal:** RSI > 70 (overbought) + SMA short < SMA long + Negative MACD crossover
- **Confidence Threshold:** Signal must have ≥50% confidence

**Exit Rules:**
- **Target Hit:** Price reaches profit target (risk × 2)
- **Stop Loss Hit:** Price touches stop loss (ATR × 1.5)
- **Market Close:** Auto square-off 5 minutes before market close

**Risk Management:**
- Position size scales with stop-loss distance
- Max 3 concurrent positions
- Daily loss limit: ₹2000
- Each trade max loss: ₹500

## 📈 Technical Indicators

The system includes comprehensive technical analysis:

- **RSI (Relative Strength Index)** — Momentum, overbought/oversold detection
- **SMA (Simple Moving Average)** — Trend identification
- **EMA (Exponential Moving Average)** — Weighted recent price action
- **MACD** — Trend following momentum
- **ATR (Average True Range)** — Volatility-based stop loss
- **Bollinger Bands** — Price volatility and support/resistance
- **Stochastic Oscillator** — Momentum confirmation

## 🎛️ Dashboard Features

### Real-Time Monitoring
- **Engine Status** — Running/Stopped state
- **Market Status** — Open/Closed with time to close
- **Daily P&L** — Realized, unrealized, and total profit/loss
- **Risk Metrics** — Daily loss, max positions, active trades

### Tables
- **Open Positions** — Live P&L, entry/exit prices, stop-loss, targets
- **Current Signals** — Symbol, direction, confidence, technical indicators
- **Closed Trades** — Historical trade performance

### Controls
- **Start Trading** — Activate the trading engine
- **Stop Trading** — Graceful shutdown with position closing
- **Auto-Refresh** — Dashboard updates every 2 seconds

## 📝 API Endpoints

The Flask dashboard exposes REST endpoints:

| Endpoint | Method | Purpose |
|----------|--------|----------|
| `/api/status` | GET | Engine & market status |
| `/api/positions` | GET | Open positions |
| `/api/signals` | GET | Current trading signals |
| `/api/risk` | GET | Risk management metrics |
| `/api/trades` | GET | Closed trades history |
| `/api/start` | POST | Start trading engine |
| `/api/stop` | POST | Stop trading engine |
| `/api/health` | GET | System health check |

## 📋 Logging

Two separate log streams:

1. **System Logs** (`trading_system.log`)
   - DEBUG: Detailed internal operations
   - INFO: Key events (orders, positions, signals)
   - WARNING: Risk limit warnings
   - ERROR: Failures and exceptions

2. **Trade Logs** (`trades_YYYYMMDD.log`)
   - Structured trade entry/exit events
   - Order placement/cancellation
   - Stop-loss and target hits

Example log:
```
2024-07-18 14:35:22 - TRADE_ENTRY | INFY BUY 10 @ 1850.50 | SL: 1820.00 | Target: 1880.00
2024-07-18 14:42:15 - POSITION_UPDATE | INFY BUY P&L: ₹250.00 (1.35%)
2024-07-18 14:55:30 - TRADE_EXIT | INFY BUY @ 1875.50 | P&L: ₹250.00 (1.35%) | TARGET
```

## 🔧 Customization

### Adding a New Strategy

1. Create a new strategy class inheriting from `BaseStrategy`:

```python
from strategy.base_strategy import BaseStrategy
from strategy.signal_generator import SignalGenerator

class YourStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__("Your Strategy", config)
        self.signal_gen = SignalGenerator()
    
    def generate_signal(self, symbol, price_data, historical_data):
        # Your signal logic here
        return signal
    
    def validate_signal(self, signal):
        # Your validation logic here
        return is_valid
```

2. Update `trading_engine.py` to use your strategy:

```python
from strategy.your_strategy import YourStrategy

self.strategy = YourStrategy(TradingConfig.STRATEGY_CONFIG["your_strategy"])
```

### Modifying Risk Parameters

Edit `config/trading_config.py`:

```python
RISK_CONFIG = {
    "max_loss_per_trade": 1000,      # Increase from 500
    "max_daily_loss": 5000,           # Increase from 2000
    "max_open_positions": 5,          # Increase from 3
}
```

## ⚠️ Important Notes

### Paper vs Live Execution Safety
- Default mode is **PAPER** (safe): orders are simulated and no live order is sent.
- Live orders are enabled only when both flags are set:
  - `LIVE_TRADING=true`
  - `ALLOW_LIVE_ORDERS=true`
- If either flag is missing/false, live order placement stays blocked.

### Market Hours
System is aware of NSE (9:15 AM - 3:30 PM) and MCX (9:00 AM - 11:30 PM) hours. Trading signals are generated only during market hours.

### Token Expiry
Access tokens expire daily. The system handles auto-refresh via refresh_token. If you encounter TokenException:
1. Re-authenticate by removing `.kite_session.json`
2. Run the system again and complete the login flow

### Historical Data
The engine fetches real historical candles from Kite before generating signals. If historical fetch fails for a symbol, that symbol is skipped (no dummy candle fallback for trading decisions).

## 🐛 Troubleshooting

### "Not authenticated" error
- Ensure API credentials are correct
- Check if your IP is whitelisted in Kite settings
- Token may have expired; delete `.kite_session.json` and re-login

### Dashboard not loading
- Check if Flask is running: `http://localhost:5000`
- Ensure port 5000 is not in use
- Check firewall settings

### No signals generated
- Check market hours (system won't trade outside market hours)
- Verify historical data is being fetched
- Check signal configuration thresholds

### Orders not being placed
- Verify account has sufficient margin
- Check position limits haven't been exceeded
- Ensure trading symbols are correct for the exchange

## 📚 Resources

- [Kite Connect API Docs](https://kite.trade/docs/connect/v3/)
- [Zerodha Support](https://support.zerodha.com)
- [Technical Analysis Guide](https://school.stockcharts.com/doku.php?id=technical_indicators)

## 📄 License

MIT License - See LICENSE file

## ⚡ Next Steps

1. **Backtest the strategy** — Run historical analysis to validate profitability
2. **Paper trading** — Test with live data before real money
3. **Optimize parameters** — Fine-tune RSI, SMA periods for your instruments
4. **Add more indicators** — Extend with volume, Fibonacci, VWAP
5. **Risk optimization** — Adjust position sizing based on historical volatility
6. **Multi-timeframe** — Combine 5-min, 15-min, hourly signals

---

**Built with ❤️ for traders. Trade responsibly!**
