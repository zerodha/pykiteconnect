# The Kite Connect API Python client
The official Python client for communicating with the [Kite Connect API](https://kite.trade).

Kite Connect is a set of REST-like APIs that expose many capabilities required to build a complete investment and trading platform. Execute orders in real time, manage user portfolio, stream live market data (WebSockets), and more, with the simple HTTP API collection. 

[Rainmatter](http://rainmatter.com) (c) 2016. Licensed under the MIT License.

## Documentation
- [Python client documentation](https://kite.trade/docs/pyconnect)
- [Kite Connect HTTP API documentation](https://kite.trade/docs/connect/v1)

## Installing the client
`pip install kiteconnect`

## Usage
```python
from kiteconnect import KiteConnect

kite = new KiteConnect(api_key="xxx")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

access_token = kite.request_access_token("request_token_here", secret="your_secret")
kite.set_access_token(access_token)

# Place an order
try:
	order_id = kite.order_place(tradingsymbol="INFY",
					exchange="NSE",
					transaction_type="BUY",
					quantity=1,
					order_type="MARKET"
					product="NRML")

	print("Order placed. ID is", order_id)
except Exception as e:
	print("Order placement failed", e.message)

# Fetch all orders
print(kite.orders())
```

Refer to the [Python client documentation](https://kite.trade/docs/pyconnect) for the complete list of supported methods. 
