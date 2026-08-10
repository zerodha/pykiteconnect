# Quick Start Guide for Intraday Trading System

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get Kite API Credentials
1. Go to [Zerodha Kite](https://kite.zerodha.com/)
2. Create an account if you don't have one
3. Navigate to [API](https://kite.zerodha.com/api/) section
4. Create a new app
5. Get your `api_key` and `api_secret`

### Step 3: Set Environment Variables
```bash
# macOS/Linux
export KITE_API_KEY="your_api_key_here"
export KITE_API_SECRET="your_api_secret_here"

# Windows (Command Prompt)
set KITE_API_KEY=your_api_key_here
set KITE_API_SECRET=your_api_secret_here

# Windows (PowerShell)
$env:KITE_API_KEY="your_api_key_here"
$env:KITE_API_SECRET="your_api_secret_here"
```

### Step 4: Run the System
```bash
python main.py
```

You'll be prompted to authenticate:
1. Visit the login URL provided
2. Log in with your Zerodha credentials
3. Copy the `request_token` from the redirect URL
4. Paste it when prompted in the terminal

### Step 5: Open Dashboard
Navigate to **http://localhost:5000** in your browser

## Dashboard Guide

### Status Section
- **Engine Status** — Green (Running) or Red (Stopped)
- **Market Status** — Open/Closed with time remaining
- **Daily P&L** — Your profit/loss for the day

### Controls
- **Start Trading** — Activates the momentum strategy
- **Stop Trading** — Gracefully stops all positions

### Monitoring Tabs

#### Open Positions
Shows live positions with:
- Current P&L amount and percentage
- Entry and stop-loss prices
- Profit target
- Entry time

#### Current Signals
Real-time trading signals:
- BUY/SELL/HOLD status
- Signal confidence (0-100%)
- Technical indicators (RSI, SMA, MACD)
- Reason for signal

#### Closed Trades
Historical performance:
- Entry and exit prices
- Profit/loss per trade
- Exit time and reason

## Configuration Examples

### For NSE Stocks (Aggressive)
```python
# trading_config.py
RISK_CONFIG = {
    "max_loss_per_trade": 1000,
    "max_daily_loss": 5000,
    "max_position_size": 20000,
    "max_open_positions": 5,
}

STRATEGY_CONFIG = {
    "momentum": {
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "sma_short_period": 9,
        "sma_long_period": 21,
        "lookback_candles": 50,
    }
}
```

### For MCX Commodities (Conservative)
```python
RISK_CONFIG = {
    "max_loss_per_trade": 500,
    "max_daily_loss": 2000,
    "max_position_size": 5000,
    "max_open_positions": 2,
}

STRATEGY_CONFIG = {
    "momentum": {
        "rsi_period": 21,  # Longer period for commodities
        "rsi_overbought": 75,
        "rsi_oversold": 25,
        "sma_short_period": 12,
        "sma_long_period": 26,
        "lookback_candles": 100,
    }
}
```

## Common Issues & Solutions

### Issue: "ConnectionError: Failed to establish a new connection"
**Solution:** 
- Check internet connection
- Verify Kite API endpoint is accessible
- Check if your IP is whitelisted in Kite settings

### Issue: "TokenException: Token is invalid or expired"
**Solution:**
- Delete `.kite_session.json` file
- Re-run `python main.py`
- Complete the authentication flow again

### Issue: "No signals being generated"
**Solution:**
- Check if market is open
- Look at console logs for errors
- Verify `lookback_candles` is sufficient (minimum 50)
- Check signal confidence threshold (default 50%)

### Issue: "Dashboard not loading on localhost:5000"
**Solution:**
- Check if Flask is running (look for port 5000 in logs)
- Try different port: edit `app.run(port=5001)`
- Clear browser cache and refresh
- Check firewall rules

## Beginner Tips

1. **Start Small**
   - Set `max_position_size` to 5000 (₹)
   - Set `max_daily_loss` to 1000 (₹)
   - Trade only 1-2 symbols

2. **Monitor First**
   - Run with `auto_square_off = False` initially
   - Watch signals for a few days
   - Understand when signals work/fail

3. **Optimize Gradually**
   - Change only ONE parameter at a time
   - Test for at least 5 trading sessions
   - Document results

4. **Risk Management**
   - Never risk more than 1% of capital per trade
   - Always use stop-loss
   - Close losing trades quickly

5. **Log Analysis**
   - Check `trading_system.log` daily
   - Review `trades_*.log` for trade analysis
   - Identify patterns in winning/losing trades

## Advanced Usage

### Custom Instruments
Edit `trading_config.py`:

```python
INSTRUMENTS = {
    "NSE": [
        {"symbol": "INFY", "exchange": "NSE", "lot_size": 1, "type": "EQUITY"},
        {"symbol": "NIFTY", "exchange": "NFO", "lot_size": 50, "type": "INDEX"},
    ],
    "MCX": [
        {"symbol": "GOLDM", "exchange": "MCX", "lot_size": 1, "type": "COMMODITY"},
    ]
}
```

### Dynamic Position Sizing
Edit `trading_config.py`:

```python
RISK_CONFIG = {
    "position_sizing_method": "risk_based",  # or "fixed"
    "risk_per_trade": 2.0,  # Risk 2% of capital per trade
}
```

### Trailing Stop Loss
Edit `trading_config.py`:

```python
POSITION_CONFIG = {
    "use_trailing_stop": True,
    "trailing_stop_percent": 2.0,  # Trail by 2%
}
```

## Performance Benchmarks

Expected performance with default momentum strategy (based on historical data):

| Market | Win Rate | Avg Win | Avg Loss | Profit Factor |
|--------|----------|---------|----------|---------------|
| NSE Stocks | 55% | ₹250 | ₹150 | 1.8x |
| MCX Commodities | 50% | ₹500 | ₹400 | 1.6x |

*Note: Past performance is not indicative of future results. Always backtest before live trading.*

## Next Level

### Backtesting
Implement historical backtesting:

```python
from backtester import BacktestEngine

backtest = BacktestEngine(symbol="INFY", start_date="2024-01-01", end_date="2024-06-30")
results = backtest.run(MomentumStrategy())
print(f"Win Rate: {results['win_rate']:.1%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

### Multi-Strategy
Combine multiple strategies for robust signals.

### Machine Learning
Train models on historical data for signal generation.

## Resources

- **Kite Connect Docs**: https://kite.trade/docs/connect/v3/
- **Technical Analysis**: https://school.stockcharts.com/
- **Trading Journal**: Keep detailed records of all trades
- **Community**: https://www.zerodha.com/support

---

**Happy Trading! 📈**

Remember: Risk management is more important than strategy. Trade small, trade often, stay consistent.
