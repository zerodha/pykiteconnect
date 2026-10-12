# Changelog

## [1.0.0] - 2024-07-18

### Initial Release

#### Added
- Core Trading Engine with real-time market data streaming
- Momentum Strategy (RSI + SMA crossover)
- 10+ Technical Indicators (RSI, SMA, EMA, MACD, ATR, Bollinger Bands, Stochastic)
- Comprehensive Risk Management (position sizing, stop-loss, daily loss limits)
- Real-time Web Dashboard (Flask-based UI)
- Multi-market Support (NSE and MCX with market-hour awareness)
- Position Tracking with live P&L calculations
- Order Management (placement, modification, cancellation)
- Session Persistence and auto token refresh
- Structured Logging (system logs and trade logs)
- API Endpoints for external integration

#### Components
- `core/` — Authentication, market data, order management, position tracking
- `strategy/` — Base strategy, signal generation, momentum strategy
- `risk_management/` — Risk manager with position sizing and validation
- `engine/` — Main trading orchestration engine
- `dashboard/` — Flask web UI for monitoring
- `utils/` — Logger, market hours, helpers
- `config/` — Centralized configuration management

#### Features
- Momentum-based entry/exit signals
- ATR-based stop-loss calculation
- Risk-reward ratio enforcement
- Daily loss limit enforcement
- Max position size limits
- Auto square-off at market close
- Real-time P&L updates
- Trade execution logging
- WebSocket reconnection handling

#### Documentation
- Comprehensive README with architecture overview
- Quick Start guide with examples
- Configuration examples for different markets
- Troubleshooting guide
- API endpoint documentation

#### Known Limitations
- Historical data is currently dummy (needs real API integration)
- Backtesting engine not included (to be added)
- Only supports market orders (limit orders planned)
- Single strategy implementation (extensible for more)

### Next Steps (v1.1.0)
- [ ] Integrate real historical data from Kite API
- [ ] Add backtesting engine
- [ ] Support for limit orders and advanced order types
- [ ] Machine learning-based signal generation
- [ ] Multi-strategy support
- [ ] Database for persistent trade storage
- [ ] Trade analytics and performance reports
- [ ] Alerts and notifications (email, SMS)
