"""
	Kite Connect API client
	https://kite.trade

	Rainmatter (c) 2015

	MIT License
"""

import json
import hashlib
import requests

import exceptions as ex


class Kite(object):
	# default API url (root)
	_root = "https://api.kite.trade/v1"

	# URIs to various calls
	_routes = {
		"parameters": "/parameters",
		"api.validate": "/session/token",
		"api.invalidate": "/session/token",
		"user.margins": "/user/margins/{segment}",
		"user.session_hash": "/user/session_hash",
		"user.session_hash.validate": "/user/session_hash/{session_hash}",

		"orders": "/orders",
		"trades": "/trades",
		"orders.info": "/orders/{order_id}",

		"orders.place": "/orders/{variety}",
		"orders.modify": "/orders/{variety}/{order_id}",
		"orders.cancel": "/orders/{variety}/{order_id}",

		"portfolio.positions": "/portfolio/positions",
		"portfolio.holdings": "/portfolio/holdings",
		"portfolio.positions.modify": "/portfolio/positions",

		"market.instruments.all": "/instruments",
		"market.instruments": "/instruments/{exchange}",
		"market.quote": "/instruments/{exchange}/{tradingsymbol}",
		"market.trigger_range": "/instruments/{exchange}/{tradingsymbol}/trigger_range"
	}

	timeout = 7

	def __init__(self, api_key, access_token=None, root=None, debug=False, timeout=7, micro_cache=True):
		self.api_key = api_key
		self.access_token = access_token
		self.debug = debug
		self.timeout = timeout
		self.micro_cache = micro_cache
		self.session_hook = None

		if root:
			self._root = root

	def set_session_hook(self, method):
		"""
		A callback hook for session timeout errors.
		An access_token (login session) can become invalid for a number of
		reasons, but it doesn't make sense for the client to
		try and catch it during every API call.

		A callback that handles saccess_tokenession timeout errors
		can be provided here and when the client encounters
		a token error, it'll be called.

		This callback, for instance, can log the user out of the UI,
		clear session cookies, or show a timeout error message
		"""
		self.session_hook = method

	def set_access_token(self, access_token):
		"""
		Set the access token received after successful login.
		After the first login, this token should be saved in the
		session somewhere and passed to the client for further
		API calls.
		"""
		self.access_token = access_token

	def set_user(self, user_id):
		"""Set the instance's user id"""
		self.user_id = user_id

	def login_url(self):
		"""Returns the remote login url to which a user is to be redirected"""
		return "%s%s?api_key=%s" % (self._root, self._routes["login"], self.api_key)

	def request_access_token(self, request_token, secret):
		"""Register access token for a given request token and api key"""
		h = hashlib.sha256(self.api_key + request_token + secret)
		checksum = h.hexdigest()

		resp = self._post("api.validate",
			{
				"request_token": request_token,
				"checksum": checksum
			})

		if "access_token" in resp:
			self.set_access_token(resp["access_token"])

		return resp

	def invalidate_token(self, access_token=None):
		"""Kill the session by invalidating the access token"""
		params = None
		if access_token:
			params = {"access_token": access_token}

		return self._delete("api.invalidate", params)

	def session_hash(self):
		"""Retrieves the session hash that was generated during login"""
		return self._get("user.session_hash")

	def session_hash_validate(self, session_hash):
		"""Validates a given hash against the login session hash"""
		return self._get("user.session_hash_validate", {"session_hash": session_hash})

	def margins(self, segment):
		"""Get account balance and cash margin details"""
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
		"""Place an order and return the NEST order number if successful"""
		params = locals()
		del(params["self"])

		for k in params:
			if k is None:
				del(params[k])

		return self._post("orders.place", params)["order_id"]

	def order_modify(self,
					order_id,
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
		"""Modify an order and return the NEST order number if successful"""
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
				"variety": variety
			})["order_id"]
		elif variety == "CO":
			return self._put("order_modify", {
				"order_id": order_id,
				"trigger_price": trigger_price,
				"variety": variety
			})["order_id"]
		else:
			return self._put("orders.modify", params)["order_id"]

	def order_cancel(self, order_id, variety="regular"):
		"""Cancel an order"""
		return self._delete("orders.cancel", {"order_id": order_id, "variety": variety})["order_id"]

	# orderbook and tradebook
	def orders(self, order_id=None):
		"""Get the collection of orders from the orderbook"""
		if order_id:
			return self._get("orders.info", {"order_id": order_id})
		else:
			return self._get("orders")

	def trades(self):
		"""Get the collection of executed trades (tradebook)"""
		return self._get("trades")

	# positions and holdings
	def positions(self):
		"""Get the list of positions"""
		return self._get("portfolio.positions")

	def holdings(self):
		"""Get the list of demat holdings"""
		return self._get("portfolio.holdings")

	def product_modify(self,
						exchange,
						tradingsymbol,
						transaction_type,
						position_type,
						quantity,
						old_product,
						new_product):
		"""Modify a position's product type"""
		return self._put("portfolio.positions.modify", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"position_type": position_type,
			"quantity": quantity,
			"old_product": old_product,
			"new_product": new_product
		})

	# instruments
	def instruments(self, exchange=None, search=None):
		"""Get list of instruments by exchange with optional substring search"""
		if exchange:
			params = {"exchange": exchange}

			if search:
				params["search"] = search

			return self._get("market.instruments", params)
		else:
			return self._get("market.all_instruments")

	def quote(self, exchange, tradingsymbol):
		"""Get quote and market depth for an instrument"""
		return self._get("market.quote", {"exchange": exchange, "tradingsymbol": tradingsymbol})

	def trigger_range(self, exchange, tradingsymbol, transaction_type):
		"""Get the buy/sell trigger range (for CO)"""
		return self._get("market.trigger_range", {"exchange": exchange, "tradingsymbol": tradingsymbol, "transaction_type": transaction_type})

	# Private http handlers and helpers
	def _get(self, route, params=None):
		"""Alias for sending a GET request"""
		return self._request(route,
							"GET",
							params)

	def _post(self, route, params=None):
		"""Alias for sending a POST request"""
		return self._request(route,
							"POST",
							params)

	def _put(self, route, params=None):
		"""Alias for sending a PUT request"""
		return self._request(route,
							"PUT",
							params)

	def _delete(self, route, params=None):
		"""Alias for sending a DELETE request"""
		return self._request(route,
							"DELETE",
							params)

	def _request(self, route, method, parameters=None):
		"""Make an HTTP request"""

		params = {}
		if parameters:
			params = parameters.copy()

		# micro cache?
		if self.micro_cache is False:
			params["no_micro_cache"] = 1

		# is there  atoken?
		if self.access_token:
			params["access_token"] = self.access_token

		if not "api_key" in params or not params.get("api_key"):
			params["api_key"] = self.api_key

		uri = self._routes[route]

		# 'RESTful' URLs
		if "{" in uri:
			for k in params:
				uri = uri.replace("{" + k + "}", str(params[k]))

		url = self._root + uri

		if self.debug:
			print "Request: ", url
			print params, "\n"

		try:
			r = requests.request(method,
					url,
					data=params if method == "POST" else None,
					params=params if method != "POST" else None,
					verify=False,
					allow_redirects=True,
					timeout=self.timeout)
		except requests.ConnectionError:
			raise ex.ClientNetworkException("Gateway connection error", code=503)
		except requests.Timeout:
			raise ex.ClientNetworkException("Gateway timed out", code=504)
		except requests.HTTPError:
			raise ex.ClientNetworkException("Invalid response from gateway", code=502)
		except Exception as e:
			raise ex.ClientNetworkException(e.message, code=500)

		if self.debug:
			print "Response :", r.status_code, r.content, "\n"

		# content types
		if r.headers["content-type"] == "application/json":
			try:
				data = json.loads(r.content)
			except:
				raise ex.DataException("Unparsable response")

			# api error
			if data["status"] == "error":
				if r.status_code == 403:
					if self.session_hook:
						self.session_hook()
						return

				# native Kite errors
				if data["error_type"] == "GeneralException":
					raise(ex.GeneralException(data["message"], code=r.status_code))

				elif data["error_type"] == "UserException":
					raise(ex.UserException(data["message"], code=r.status_code))

				elif data["error_type"] == "OrderException":
					raise(ex.OrderException(data["message"], code=r.status_code))

				elif data["error_type"] == "GeneralException":
					raise(ex.GeneralException(data["message"], code=r.status_code))

				elif data["error_type"] == "InputException":
					raise(ex.InputException(data["message"], code=r.status_code))

				elif data["error_type"] == "DataException":
					raise(ex.DataException(data["message"], code=r.status_code))

				elif data["error_type"] == "NetworkException":
					raise(ex.NetworkException(data["message"], code=r.status_code))

				else:
					raise(ex.GeneralException(data["message"], code=r.status_code))

			return data["data"]
		else:
			raise ex.DataException("Invalid response format")
