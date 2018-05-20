# The Kite Connect API Python client - v3
[![PyPI](https://img.shields.io/pypi/v/kiteconnect.svg)](https://pypi.python.org/pypi/kiteconnect)
[![Build Status](https://travis-ci.org/zerodhatech/pykiteconnect.svg?branch=kite3)](https://travis-ci.org/zerodhatech/pykiteconnect)
[![Windows Build Status](https://ci.appveyor.com/api/projects/status/github/zerodhatech/pykiteconnect?svg=true)](https://ci.appveyor.com/project/rainmattertech/pykiteconnect)
[![codecov.io](https://codecov.io/gh/zerodhatech/pykiteconnect/branch/kite3/graphs/badge.svg?branch=kite3)](https://codecov.io/gh/zerodhatech/pykiteconnect/branch/kite3)

The official Python client for communicating with the [Kite Connect API](https://kite.trade).

Kite Connect is a set of REST-like APIs that expose many capabilities required to build a complete investment and trading platform. Execute orders in real time, manage user portfolio, stream live market data (WebSockets), and more, with the simple HTTP API collection.

[Zerodha Technology](https://zerodha.com) (c) 2018. Licensed under the MIT License.

## Documentation
- [Python client documentation](https://kite.trade/docs/pykiteconnect/v3)
- [Kite Connect HTTP API documentation](https://kite.trade/docs/connect/v3)

## Installing the client
You can install the pre release via pip
```
pip install kiteconnect --upgrade --pre
```

Its recommended to update `setuptools` to latest if you are facing any issue while installing

```
pip install -U pip setuptools
```

Since some of the dependencies uses C extensions it has to compiled before installing the package.

### Linux, BSD and macOS
- On Linux, and BSDs, you will need a C compiler (such as GCC).

#### Debian/Ubuntu
```
apt-get install libffi-dev python-dev python3-dev
```
#### Centos/RHEL/Fedora
```
yum install libffi-devel python3-devel python-devel
```
#### macOS/OSx
```
xcode-select --install
```

### Microsoft Windows
Each Python version uses a specific compiler version (e.g. CPython 2.7 uses Visual C++ 9.0, CPython 3.3 uses Visual C++ 10.0, etc). So, you need to install the compiler version that corresponds to your Python version
- Python 2.6, 2.7, 3.0, 3.1, 3.2 - [Microsoft Visual C++ 9.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_9.0_standalone:_Visual_C.2B-.2B-_Compiler_for_Python_2.7_.28x86.2C_x64.29)
- Python 3.3, 3.4 - [Microsoft Visual C++ 10.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_10.0_standalone:_Windows_SDK_7.1_.28x86.2C_x64.2C_ia64.29)
- Python 3.5, 3.6 - [Microsoft Visual C++ 14.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_14.0_standalone:_Visual_C.2B-.2B-_Build_Tools_2015_.28x86.2C_x64.2C_ARM.29)

For more details check [official Python documentation](https://wiki.python.org/moin/WindowsCompilers).

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

data = kite.generate_session("request_token_here", api_secret="your_secret")
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

Refer to the [Python client documentation](https://kite.trade/docs/pykiteconnect/v3) for the complete list of supported methods.

## WebSocket usage
```python
import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

# Initialise
kws = KiteTicker("your_api_key", "your_access_token")

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
```

# Run unit tests

```
python setup.py test
```

or

```
pytest -s tests/unit --cov-report html:cov_html --cov=./
```

# Run integration tests

```
pytest -s tests/integration/ --cov-report html:cov_html --cov=./  --api-key api_key --access-token access_token
```

# Generate documentation

```
pip install pdoc

pdoc --html --html-dir docs kiteconnect
```

## Changelog

[Check CHANGELOG.md](CHANGELOG.md)
