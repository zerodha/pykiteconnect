"""
Kite Connect API client for Python -- [https://kite.trade](kite.trade)

Rainmatter (c) 2016

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
import StringIO
import csv
import json
import hashlib
import requests

import kiteconnect.exceptions as ex


class KiteConnect(object):
	"""
	The API client class. In production, you may initialise
	a single instance of this class per `api_key`.
	"""

	# Default root API endpoint. It's possible to
	# override this by passing the `root` parameter during initialisation.
	_root = "https://api.kite.trade"
	_login = "https://kite.trade/connect/login"

	# URIs to various calls
	_routes = {
		"parameters": "/parameters",
		"api.validate": "/session/token",
		"api.invalidate": "/session/token",
		"user.margins": "/user/margins/{segment}",

		"orders": "/orders",
		"trades": "/trades",
		"orders.info": "/orders/{order_id}",

		"orders.place": "/orders/{variety}",
		"orders.modify": "/orders/{variety}/{order_id}",
		"orders.cancel": "/orders/{variety}/{order_id}",
		"orders.trades": "/orders/{order_id}/trades",

		"portfolio.positions": "/portfolio/positions",
		"portfolio.holdings": "/portfolio/holdings",
		"portfolio.positions.modify": "/portfolio/positions",

		"market.instruments.all": "/instruments",
		"market.instruments": "/instruments/{exchange}",
		"market.quote": "/instruments/{exchange}/{tradingsymbol}",
		"market.historical": "/instruments/historical/{instrument_token}/{interval}",
		"market.trigger_range": "/instruments/{exchange}/{tradingsymbol}/trigger_range"
	}

	_timeout = 7

	def __init__(self, api_key, access_token=None, root=None, debug=False, timeout=7, micro_cache=True):
		"""
		Initialise a new Kite Connect client instance.

		- `api_key` is the key issued to you
		- `access_token` is the token obtained after the login flow in
			exchange for the `request_token` . Pre-login, this will default to None,
		but once you have obtained it, you should
		persist it in a database or session to pass
		to the Kite Connect class initialisation for subsequent requests.
		- `root` is the API end point root. Unless you explicitly
		want to send API requests to a non-default endpoint, this
		can be ignored.
		- `debug`, if set to True, will serialise and print requests
		and responses to stdout.
		- `timeout` is the time (seconds) for which the API client will wait for
		a request to complete before it fails.
		- `micro_cache`, when set to True, will fetch the last cached
		version of an API response if available. This saves time on
		a roundtrip to the backend. Micro caches only live for several
		seconds to prevent data from turning stale.
		"""
		self.api_key = api_key
		self.access_token = access_token
		self.debug = debug
		self.micro_cache = micro_cache
		self.session_hook = None
		self._timeout = timeout

		if root:
			self._root = root

	def set_session_hook(self, method):
		"""
		Set a callback hook for session (`TokenError` -- timeout, expiry etc.) errors.
		An `access_token` (login session) can become invalid for a number of
		reasons, but it doesn't make sense for the client to
		try and catch it during every API call.

		A callback method that handles session errors
		can be set here and when the client encounters
		a token error at any point, it'll be called.

		This callback, for instance, can log the user out of the UI,
		clear session cookies, or initiate a fresh login.
		"""
		self.session_hook = method

	def set_access_token(self, access_token):
		"""Set the `access_token` received after a successful authentication."""
		self.access_token = access_token

	def login_url(self):
		"""
		Get the remote login url to which a user should be redirected
		to initiate the login flow.
		"""
		return "%s?api_key=%s" % (self._login, self.api_key)

	def request_access_token(self, request_token, secret):
		"""Do the token exchange with the `request_token` obtained after the login flow,
		and retrieve the `access_token` required for all subsequent requests. The
		response contains not just the `access_token`, but metadata for
		the user who has authenticated.

		- `request_token` is the token obtained from the GET paramers after a successful login redirect.
		- `secret` is the API secret issued with the API key.
		"""
		h = hashlib.sha256(self.api_key.encode("utf-8") + request_token.encode("utf-8") + secret.encode("utf-8"))
		checksum = h.hexdigest()

		resp = self._post("api.validate", {
			"request_token": request_token,
			"checksum": checksum
		})

		if "access_token" in resp:
			self.set_access_token(resp["access_token"])

		return resp

	def invalidate_token(self, access_token=None):
		"""Kill the session by invalidating the access token.

		- `access_token` to invalidate. Default is the active `access_token`.
		"""
		params = None
		if access_token:
			params = {"access_token": access_token}

		return self._delete("api.invalidate", params)

	def margins(self, segment):
		"""Get account balance and cash margin details for a particular segment.

		- `segment` is the trading segment (eg: equity or commodity)
		"""
		return self._get("user.margins", {"segment": segment})

	# orders
	def order_place(self,
					exchange,
					tradingsymbol,
					transaction_type,
					quantity,
					price=None,
					product=None,
					order_type=None,
					validity=None,
					disclosed_quantity=None,
					trigger_price=None,
					squareoff_value=None,
					stoploss_value=None,
					trailing_stoploss=None,
					variety="regular"):
		"""Place an order."""
		params = locals()
		del(params["self"])

		for k in params:
			if k is None:
				del(params[k])

		return self._post("orders.place", params)["order_id"]

	def order_modify(self,
					order_id,
					parent_order_id=None,
					exchange=None,
					tradingsymbol=None,
					transaction_type=None,
					quantity=None,
					price=None,
					order_type=None,
					product=None,
					trigger_price=0,
					validity="DAY",
					disclosed_quantity=0,
					variety="regular"):
		"""Modify an open order."""
		params = locals()
		del(params["self"])

		for k in params:
			if k is None:
				del(params[k])

		if variety == "BO":
			return self._put("order_modify", {
				"order_id": order_id,
				"quantity": quantity,
				"price": price,
				"trigger_price": trigger_price,
				"disclosed_quantity": disclosed_quantity,
				"variety": variety,
				"parent_order_id": parent_order_id
			})["order_id"]
		elif variety == "CO":
			return self._put("order_modify", {
				"order_id": order_id,
				"trigger_price": trigger_price,
				"variety": variety,
				"parent_order_id": parent_order_id
			})["order_id"]
		else:
			return self._put("orders.modify", params)["order_id"]

	def order_cancel(self, order_id, variety="regular", parent_order_id=None):
		"""Cancel an order"""
		return self._delete("orders.cancel", {
			"order_id": order_id,
			"variety": variety,
			"parent_order_id": parent_order_id
		})["order_id"]

	# orderbook and tradebook
	def orders(self, order_id=None):
		"""Get the collection of orders from the orderbook."""
		if order_id:
			return self._get("orders.info", {"order_id": order_id})
		else:
			return self._get("orders")

	def trades(self, order_id=None):
		"""
		Retreive the list of trades executed (all or ones under a particular order).

		An order can be executed in tranches based on market conditions.
		These trades are individually recorded under an order.

		- `order_id` is the ID of the order (optional) whose trades are to be retrieved.
		If no `order_id` is specified, all trades for the day are returned.
		"""
		if order_id:
			return self._get("orders.trades", {"order_id": order_id})
		else:
			return self._get("trades")

	def positions(self):
		"""Retrieve the list of positions."""
		return self._get("portfolio.positions")

	def holdings(self):
		"""Retrieve the list of equity holdings."""
		return self._get("portfolio.holdings")

	def product_modify(self,
						exchange,
						tradingsymbol,
						transaction_type,
						position_type,
						quantity,
						old_product,
						new_product):
		"""Modify an open position's product type."""
		return self._put("portfolio.positions.modify", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"position_type": position_type,
			"quantity": quantity,
			"old_product": old_product,
			"new_product": new_product
		})

	def instruments(self, exchange=None):
		"""
		Retrieve the list of market instruments available to trade.

		Note that the results could be large, several hundred KBs in size,
		with tens of thousands of entries in the list.
		"""
		if exchange:
			params = {"exchange": exchange}

			return self._parse_csv(self._get("market.instruments", params))
		else:
			return self._parse_csv(self._get("market.instruments.all"))

	def quote(self, exchange, tradingsymbol):
		"""Retrieve quote and market depth for an instrument."""
		return self._get("market.quote", {"exchange": exchange, "tradingsymbol": tradingsymbol})

	def historical(self, instrument_token, from_date, to_date, interval):
		"""
		Retrieve historical data (candles) for an instrument.

		Although the actual response JSON from the API does not have field
		names such has 'open', 'high' etc., this functin call structures
		the data into an array of objects with field names. For example:

		- `instrument_token` is the instrument identifier (retrieved from the instruments()) call.
		- `date_from` is the From date (yyyy-mm-dd)
		- `date_to` is the To date (yyyy-mm-dd)
		- `interval` is the candle interval (minute, day, 5 minute etc.)
		"""
		data = self._get("market.historical", {
			"instrument_token": instrument_token,
			"from": from_date,
			"to": to_date,
			"interval": interval})

		records = []
		for d in data["candles"]:
			records.append({
				"date": d[0],
				"open": d[1],
				"high": d[2],
				"low": d[3],
				"close": d[4],
				"volume": d[5]
			})

		return records

	def trigger_range(self, exchange, tradingsymbol, transaction_type):
		"""Retrieve the buy/sell trigger range for Cover Orders."""
		return self._get("market.trigger_range", {"exchange": exchange, "tradingsymbol": tradingsymbol, "transaction_type": transaction_type})

	def _parse_csv(self, data):
		reader = csv.reader(StringIO.StringIO(data.strip()))

		records = []
		header = next(reader)
		for row in reader:
			record = dict(zip(header, row))

			record["last_price"] = float(record["last_price"])
			record["strike"] = float(record["strike"])
			record["tick_size"] = float(record["tick_size"])
			record["lot_size"] = int(record["lot_size"])

			records.append(record)

		return records

	def _get(self, route, params=None):
		"""Alias for sending a GET request."""
		return self._request(route, "GET", params)

	def _post(self, route, params=None):
		"""Alias for sending a POST request."""
		return self._request(route, "POST", params)

	def _put(self, route, params=None):
		"""Alias for sending a PUT request."""
		return self._request(route, "PUT", params)

	def _delete(self, route, params=None):
		"""Alias for sending a DELETE request."""
		return self._request(route, "DELETE", params)

	def _request(self, route, method, parameters=None):
		"""Make an HTTP request."""
		params = {}
		if parameters:
			params = parameters.copy()

		# Micro cache?
		if self.micro_cache is False:
			params["no_micro_cache"] = 1

		# Is there a token?.
		if self.access_token:
			params["access_token"] = self.access_token

		# override instance's API key if one is supplied in the params
		if "api_key" not in params or not params.get("api_key"):
			params["api_key"] = self.api_key

		uri = self._routes[route]

		# 'RESTful' URLs.
		if "{" in uri:
			for k in params:
				uri = uri.replace("{" + k + "}", str(params[k]))

		url = self._root + uri

		if self.debug:
			print("Request: ", url)
			print(params, "\n")

		try:
			r = requests.request(method,
					url,
					data=params if method == "POST" else None,
					params=params if method != "POST" else None,
					verify=False,
					allow_redirects=True,
					timeout=self._timeout)
		except requests.ConnectionError:
			raise ex.ClientNetworkException("Gateway connection error", code=503)
		except requests.Timeout:
			raise ex.ClientNetworkException("Gateway timed out", code=504)
		except requests.HTTPError:
			raise ex.ClientNetworkException("Invalid response from gateway", code=502)
		except Exception as e:
			raise ex.ClientNetworkException(e.message, code=500)

		if self.debug:
			print("Response :", r.status_code, r.content, "\n")

		# Validate the content type.
		if "json" in r.headers["content-type"]:
			try:
				data = json.loads(r.content)
			except:
				raise ex.DataException("Couldn't parse JSON response")

			# api error
			if data["status"] == "error":
				if r.status_code == 403:
					if self.session_hook:
						self.session_hook()
						return

				# native Kite errors
				exp = getattr(ex, data["error_type"])
				if data["error_type"] == "TwoFAException":
					raise(ex.TwoFAException(data["message"],
											questions=data["questions"] if "questions" in data else [],
											code=r.status_code))
				elif exp:
					raise(exp(data["message"], code=r.status_code))
				else:
					raise(ex.GeneralException(data["message"], code=r.status_code))

			return data["data"]
		elif "csv" in r.headers["content-type"]:
			return r.content
		else:
			raise ex.DataException("Unknown Content-Type in response")
