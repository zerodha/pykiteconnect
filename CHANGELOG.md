
# Kite v3 (2018-01-18)

## New features

- method: `profile`
- method: `ohlc`
- method: `ltp`
- method: `renew_access_token`
- method: `invalidate_refresh_token`
- constants for products, order type, transaction type, variety, validity, exchanges and margin segments
- Param `disable_ssl` to `KiteConnect` initializer
- `quote` call supports multiple instruments call
- `exit_order` alias for `cancel_order`
- All datetime string fields has been converted to `datetime` object.
	- `orders`, `order_history`, `trades`, `order_trades`, `mf_orders` responses fields `order_timestamp`, `exchange_timestamp`, `fill_timestamp`
	- `mf_sips` fields `created`, `last_instalment`
	- `generate_session` field `login_time`
	- `quote` fields `timestamp`, `last_trade_time`
	- `instruments` field `expiry`
	- `mf_instruments` field `last_price_date`
- Requests thread pooling is enabled by default with defaults requests library settings [Read more](http://docs.python-requests.org/en/master/api/#requests.adapters.HTTPAdapter)

## API method name changes

| v2  					| v3 						|
| ----------------- 	| -------------------------	|
| request_access_token	| generate_session			|
| invalidate_token		| invalidate_access_token	|
| historical			| historical_data			|
| order_place 			| place_order				|
| order_modify 			| modify_order				|
| order_cancel 			| cancel_order				|
| product_modify 		| convert_position			|
| mf_order_place 		| place_mf_order			|
| mf_order_cancel 		| cancel_mf_order			|
| mf_sip_place 			| place_mf_sip				|
| mf_sip_modify 		| modify_mf_sip				|
| mf_sip_cancel 		| cancel_mf_sip			  	|
| set_session_hook  	| set_session_expiry_hook 	|
| orders(order_id)		| order_history(order_id) 	|
| trades(order_id)		| order_trades(order_id)  	|

## Param and other changes

- `historical_data` - Historical data accepts datetime object for `from_date` and `to_date` instead of string since historical api precision is upto minutes.
- `historical_data` - `date` field in output response is a datetime object instead of string.
- `modify_order`, `cancel_order` and `exit_order` takes variety as first param instead of `order_id`
- [Changes in `generate_session` response structure](https://kite.trade/docs/connect/v3/user/#response-attributes)
- [Changes in `positions` response structure](https://kite.trade/docs/connect/v3/portfolio/#response-attributes_1)
- [Changes in `quote` response structure](https://kite.trade/docs/connect/v3/market-quotes/#retrieving-full-market-quotes)
- [Changes in `place_order` params](https://kite.trade/docs/connect/v3/orders/#bracket-order-bo-parameters)

## Deprecated from v2

- `exceptions.UserException`
- `exceptions.ClientNetworkException`
- `exceptions.TwoFAException`
- Param `micro_cache` from `KiteConnect` initializer
- Param `order_id` from `orders` call (Renamed to `order_history`)
- Param `order_id` from `trades` call (Renamed to `order_trades`)

## KiteTicker changes

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

## KiteTicker callback changes

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


## KiteTicker deprecated methods

- `enable_reconnect`
- `disable_reconnect`
- `reconnect` - `reconnect` can be set while initializing `KiteTicker`

## KiteTicker response changes

- Full mode has following new fields
    - `last_trade_time` - Last trade time (Python datetime object or None)
    - `oi` - Open interest
    - `oi_high` - Day's open interest high
    - `oi_low` - Day's open interest low
    - `timestamp` - Tick timestamp (Python datetime object or None)


# Old changelogs

- 2015-07-15	Fixed: Different response type recevied for large number of subscriptions
- 2016-05-31	Added `WebSocket` class for streaming data.
- 2016-04-29	`instruments()` call now returns parsed CSV records.
- 2016-05-04	Added `historical()` call.
- 2016-05-09	Added `parent_order_id` param for multi-legged orders.
- 2016-07-25    Option to disable SSL cert verification (Ubuntu 12.04 openssl bug)
- 2016-08-26    Full compatability for Python 3
- 2016-10-21	Released **version 3.3** with following fixes and features
				* Added `tag` support to order APIs
				* Added proxy support for api and websocket streaming
				* Fixed market depth `orders` integer overflow issue.
- 2016-11-11	Added connection pooling (v3.4)
- 2017-01-21	Bug fixes (v3.4.1)
- 2017-04-25	Added auto reconnect feature and other bug fixes (v3.5)
- 2017-08-01	Fix BO and CO order modify issue (v3.5.1)
- 2017-08-15	Add mutual fund API calls (v3.6.0)
- 2017-09-14	Addd flag to fetch continous chart and other bug fixes (v3.6.1)
