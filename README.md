# The Kite Connect API Python client
The official Python client for communicating with the [Kite Connect API](https://kite.trade).

Kite Connect is a set of REST-like APIs that expose many capabilities required to build a complete investment and trading platform. Execute orders in real time, manage user portfolio, stream live market data (WebSockets), and more, with the simple HTTP API collection.

[Rainmatter](http://rainmatter.com) (c) 2016. Licensed under the MIT License.

## Documentation
- [Python client documentation](https://kite.trade/docs/pykiteconnect)
- [Kite Connect HTTP API documentation](https://kite.trade/docs/connect/v1)

## Installing the client
```
pip install kiteconnect
```

## API usage
```python
import logging
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.request_access_token("request_token_here", secret="your_secret")
kite.set_access_token(data["access_token"])

# Place an order
try:
    order_id = kite.place_order(tradingsymbol="INFY",
                                exchange=kite.EXCHANGE_NSE,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=1,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_NRML)

    logging.info("Order placed. ID is: {}".format(order_id))
except Exception as e:
    logging.info("Order placement failed: {}".format(e.message))

# Fetch all orders
kite.orders()

# Get instruments
kite.instruments()

# Place an mutual fund order
kite.place_mf_order(
    tradingsymbol="INF090I01239",
    transaction_type=kite.TRANSACTION_TYPE_BUY,
    amount=5000,
    tag="mytag"
)

# Cancel a mutual fund order
kite.cancel_mf_order(order_id="order_id")

# Get mutual fund instruments
kite.mf_instruments()
```

Refer to the [Python client documentation](https://kite.trade/docs/pykiteconnect) for the complete list of supported methods.

## WebSocket usage
```python
import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

# Initialise
kws = KiteTicker("your_api_key", "your_public_token", "logged_in_user_id")

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
```

# Generate documentation

```
pip install pdoc

pdoc --html --html-dir docs kiteconnect
```

## Changelog
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
