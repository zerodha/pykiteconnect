# -*- coding: utf-8 -*-
"""
Kite Connect API client for Python -- [https://kite.trade](kite.trade).

Zerodha technologies (c) 2017

License
-------
KiteConnect Python library is licensed under the MIT License

The library
-----------
Kite Connect is a set of REST-like APIs that expose
many capabilities required to build a complete
investment and trading platform. Execute orders in
real time, manage user portfolio, stream live market
data (WebSockets), and more, with the simple HTTP API collection

This module provides an easy to use abstraction over the HTTP APIs.
The HTTP calls have been converted to methods and their JSON responses
are returned as native Python structures, for example, dicts, lists, bools etc.
See the **[Kite Connect API documentation](https://kite.trade/docs/connect/v1/)**
for the complete list of APIs, supported parameters and values, and response formats.

Getting started
---------------
    #!python
    from kiteconnect import KiteConnect

    # Initialise.
    kite = KiteConnect(api_key="your_api_key")

    # Assuming you have obtained the `request_token`
    # after the auth flow redirect by redirecting the
    # user to kite.login_url()
    try:
        user = kite.request_access_token(request_token="obtained_request_token",
                                        secret="your_api_secret")

        kite.set_access_token(user["access_token"])
    except Exception as e:
        print("Authentication failed", str(e))
        raise

    print(user["user_id"], "has logged in")

    # Get the list of positions.
    print(kite.positions())

    # Place an order.
    order_id = kite.order_place(
        tradingsymbol="INFY",
        exchange="NSE",
        quantity=1,
        transaction_type="BUY",
        order_type="MARKET"
    )

    # Fetch all orders
    kite.orders()

    # Get instruments
    kite.instruments()

    # Place an mutual fund order
    kite.mf_order_place(
        tradingsymbol="INF090I01239",
        transaction_type="BUY",
        amount=5000,
        tag="mytag"

    # Cancel a mutual fund order
    kite.mf_order_cancel(order_id="order_id")

    # Get mutual fund instruments
    kite.mf_instruments()

A typical web application
-------------------------
In a typical web application where a new instance of
views, controllers etc. are created per incoming HTTP
request, you will need to initialise a new instance of
Kite client per request as well. This is because each
individual instance represents a single user that's
authenticated, unlike an **admin** API where you may
use one instance to manage many users.

Hence, in your web application, typically:

- You will initialise an instance of the Kite client
- Redirect the user to the `login_url()`
- At the redirect url endpoint, obtain the
`request_token` from the query parameters
- Initialise a new instance of Kite client,
use `request_access_token()` to obtain the `access_token`
along with authenticated user data
- Store this response in a session and use the
stored `access_token` and initialise instances
of Kite client for subsequent API calls.

Exceptions
----------
Kite Connect client saves you the hassle of detecting API errors
by looking at HTTP codes or JSON error responses. Instead,
it raises aptly named **[exceptions](exceptions.m.html)** that you can catch.
"""

from __future__ import unicode_literals, absolute_import

from .connect import KiteConnect
from .ticker import KiteTicker

__all__ = ["KiteConnect", "KiteTicker"]
