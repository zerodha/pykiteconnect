New features
=============
- method: `profile`
- method: `ohlc`
- method: `ltp`
- method: `instruments_margins`
- constants for products, order type, transaction type, variety, validity, exchanges and margin segments
- Param `disable_ssl` to `KiteConnect` initializer
- `quote` call supports multiple instruments call
- `exit_order` alias for `cancel_order`

API method name changes
=======================
| v2  				| v3 						|
| ----------------- | -------------------------	|
| historical		| historical_data			|
| order_place 		| place_order				|
| order_modify 		| modify_order				|
| order_cancel 		| cancel_order				|
| product_modify 	| convert_position			|
| mf_order_place 	| place_mf_order			|
| mf_order_cancel 	| cancel_mf_order			|
| mf_sip_place 		| place_mf_sip				|
| mf_sip_modify 	| modify_mf_sip				|
| mf_sip_cancel 	| cancel_mf_sip			  	|
| set_session_hook  | set_session_expiry_hook 	|
| orders(order_id)	| order_history(order_id) 	|
| trades(order_id)	| order_trades(order_id)  	|

Param and other changes
=======================
- `historical_data` - Historical data accepts datetime object for `from_date` and `to_date` instead of string since historical api precision is upto minutes.
- `historical_data` - `date` field in output response is a datetime object instead of string.
- Changes in `request_access_token` response structure
- Changes in `positions` response structure
- Changes in `quote` response structure

Deprecated from v2
==================
- `exceptions.UserException`
- `exceptions.ClientNetworkException`
- `exceptions.TwoFAException`
- Param `micro_cache` from `KiteConnect` initializer
- Param `order_id` from `orders` call (Renamed to `order_history`)
- Param `order_id` from `trades` call (Renamed to `order_trades`)

KiteTicker changes
==================
- Rename class `WebSocket` to `KiteTicker`
- `KiteTicker` initializer param `public_token` is replaced with `access_token`
- Added `KiteTicker` param `reconnect` to enable/disable auto re-connection.
- Auto re-connection is enabled by default (`reconnect` is `True` by default)
- `reconnect_interval` is deprecated and replaced with `reconnect_max_delay`
- Rename: `reconnect_tries` to `reconnect_max_tries`
- Auto reconnect uses exponential back-off algorithm instead of fixed reconnect interval (https://en.wikipedia.org/wiki/Exponential_backoff)
- Underlying WebSocket library is replaced with Autohbahn Python client (Supports 2,7+, 3.3+) for more stability.
- Added param `connect_timeout` to `KiteTicker` initializer
- Added method `stop_retry` to stop auto reconnect while auto re-connection in progress.

KiteTicker callback changes
===========================
- `on_ticks(ws, ticks)` -  Triggered when ticks are received.
	- `ticks` - List of `tick` object. Check below for sample structure.
- `on_close(ws, code, reason)` -  Triggered when connection is closed.
	- `code` - WebSocket standard close event code (https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent)
	- `reason` - DOMString indicating the reason the server closed the connection
- `on_error(ws, code, reason)` -  Triggered when connection is closed with an error.
	- `code` - WebSocket standard close event code (https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent)
	- `reason` - DOMString indicating the reason the server closed the connection
- `on_connect` -  Triggered when connection is established successfully.
	- `response` - Response received from server on successful connection.
- `on_message(ws, payload, is_binary)` -  Triggered when message is received from the server.
	- `payload` - Raw response from the server (either text or binary).
	- `is_binary` - Bool to check if response is binary type.
- `on_reconnect(ws, attempts_count)` -  Triggered when auto re-connection is attempted.
	- `attempts_count` - Current reconnect attempt number.
- `on_noreconnect(ws)` -  Triggered when number of auto re-connection attempts exceeds `reconnect_tries`.


KiteTicker deprecated methods
=============================
- `enable_reconnect`
- `disable_reconnect`
- `reconnect` - `reconnect` can be set while initializing `KiteTicker`

KiteTicker response changes
==========================
- Full mode has following new fields
    - `last_trade_time` - Last trade time (Python datetime object or None)
    - `oi` - Open interest
    - `oi_high` - Day's open interest high
    - `oi_low` - Day's open interest low
    - `timestamp` - Tick timestamp (Python datetime object or None)
