"""
Kite REST API client
"""

import json
import requests

import exceptions as ex


class Kite:
		# root API url
	_root = "http://localhost:8000"

	# URIs to various calls
	_routes = {
		"login": "/user/login",
		"2fa": "/user/2fa",
		"logout": "/user/logout",
		"profile": "/user/profile",
		"password": "/user/password",
		"transpassword": "/user/transpassword",
		"margins": "/user/margins/{segment}",
		"session_hash": "/user/session_hash",
		"session_hash_validate": "/user/session_hash/{session_hash}",
		"otp": "/user/otp",

		"orders": "/orders",
		"trades": "/trades",
		"order_info": "/orders/{order_id}",

		"order_place": "/orders/{variety}",
		"order_modify": "/orders/{variety}/{order_id}",
		"order_cancel": "/orders/{variety}/{order_id}",

		"positions": "/positions",
		"product_modify": "/positions",
		"holdings": "/holdings",
		"holdings_t1": "/holdings/t1",

		"scrips": "/scrips/{exchange}",
		"quote": "/instruments/{exchange}/{tradingsymbol}/quote",
		"trigger_range": "/instruments/{exchange}/{tradingsymbol}/trigger_range",

		"messages_admin": "/messages/admin",
		"messages_exchange": "/messages/exchange"
	}

	timeout = 7

	def __init__(self, user_id, token=None, root=None, debug=False, timeout=7, micro_cache=True, api_key=None, access_token=None):
		self.user_id = user_id
		self.token = token
		self.debug = debug
		self.timeout = timeout
		self.micro_cache = micro_cache
		self.session_hook = None

		self.api_key = api_key
		self.access_token = access_token

		if root:
			self._root = root

	def set_session_hook(self, method):
		"""
		A callback hook for session timeout errors.
		A token (login session) can become invalid for a number of
		reasons, but it doesn't make sense for the client to
		try and catch it during every API call.

		A callback that handles session timeout errors
		can be provided here and when the client encounters
		a token error, it'll be called.

		This callback, for instance, can log the user out of the UI,
		clear session cookies, or show a timeout error message
		"""
		self.session_hook = method

	def set_token(self, token):
		"""
		Set the access token received after successful login.
		After the first login, this token should be saved in the
		session somewhere and passed to the client for further
		API calls.
		"""
		self.token = token

	def login(self, password, ip):
		"""Authenticate the user's credentials. If the system has 2FA enabled, the questions are returned"""
		return self._post("login", {"password": password, "ip": ip})

	def do2fa(self, qa, ans):
		"""Do 2FA authentication and login"""
		params = {"question[]": qa, "answer[]": ans}

		return self._post("2fa", params)

	def update_2fa(self, qa):
		"""Set the user's choice of 2FA questions and answers"""
		params = {"question[]": [], "answer[]": []}

		for question in qa:
			params["question[]"].append(question)
			params["answer[]"].append(qa[question])

		return self._put("2fa", params)

	def reset_2fa(self, email, identification):
		"""Reset the user's 2FA questions and answers so they're prompted for a fresh set during the next login"""
		params = {"email": email, "identification": identification}

		return self._delete("2fa", params)

	def session_hash(self):
		"""Retrieves the session hash that was generated during login"""
		return self._get("session_hash")

	def session_hash_validate(self, session_hash):
		"""Validates a given hash against the login session hash"""
		return self._get("session_hash_validate", {"session_hash": session_hash})

	def otp(self):
		"""Generates a one time hash for non-login routines such as payment gateway authentication
		"""
		return self._get("otp")

	def logout(self):
		"""Log the user out by invalidating the token"""
		return self._post("logout")

	# user
	def profile(self):
		"""Fetch the user's profile"""
		return self._get("profile")

	def password_update(self, old_password, new_password):
		"""Change the login password"""
		return self._put("password", {"old_password": old_password, "new_password": new_password})

	def transpassword_update(self, old_password, new_password):
		"""Change the transaction password"""
		return self._put("transpassword", {"old_password": old_password, "new_password": new_password})

	def transpassword_check(self, password):
		"""Check the transaction password"""
		return self._post("transpassword", {"password": password})

	def reset_password(self, email, identification):
		"""Reset the user's primary password"""
		params = {"email": email, "identification": identification}

		return self._delete("password", params)

	def margins(self, segment):
		"""Get account balance and cash margin details"""
		return self._get("margins", {"segment": segment})

	# orders
	def order_place(self,
					exchange,
					tradingsymbol,
					transaction_type,
					quantity,
					price=None,
					product=None,
					order_type=None,
					validity="DAY",
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

		return self._post("order_place", params)["order_id"]

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
			return self._put("order_modify", params)["order_id"]

	def order_cancel(self, order_id, variety="regular"):
		"""Cancel an order"""
		return self._delete("order_cancel", {"order_id": order_id, "variety": variety})["order_id"]

	# orderbook and tradebook
	def orders(self, order_id=None):
		"""Get the collection of orders from the orderbook"""
		if order_id:
			return self._get("order_info", {"order_id": order_id})
		else:
			return self._get("orders")

	def trades(self):
		"""Get the collection of executed trades (tradebook)"""
		return self._get("trades")

	# positions and holdings
	def positions(self):
		"""Get the list of positions"""
		return self._get("positions")

	def holdings(self):
		"""Get the list of demat holdings"""
		return self._get("holdings")

	def holdings_t1(self):
		"""Get the list of demat holdings"""
		return self._get("holdings_t1")

	def product_modify(self,
						exchange,
						tradingsymbol,
						transaction_type,
						position_type,
						quantity,
						old_product,
						new_product):
		"""Modify a position's product type"""
		return self._put("product_modify", {
			"exchange": exchange,
			"tradingsymbol": tradingsymbol,
			"transaction_type": transaction_type,
			"position_type": position_type,
			"quantity": quantity,
			"old_product": old_product,
			"new_product": new_product
		})

	# scrips
	def scrips(self, exchange, search=None):
		"""Get list of scrips by exchange with optional substring search"""
		params = {"exchange": exchange}

		if search:
			params["search"] = search

		return self._get("scrips", params)

	def quote(self, exchange, tradingsymbol):
		"""Get quote and market depth for an instrument"""
		return self._get("quote", {"exchange": exchange, "tradingsymbol": tradingsymbol})

	def trigger_range(self, exchange, tradingsymbol, transaction_type):
		"""Get the buy/sell trigger range (for CO)"""
		return self._get("trigger_range", {"exchange": exchange, "tradingsymbol": tradingsymbol, "transaction_type": transaction_type})

	# messages
	def messages_admin(self):
		"""Get messages posted by the admin"""
		return self._get("messages_admin")

	def messages_exchange(self):
		"""Get messages posted by the admin"""
		return self._get("messages_exchange")

	# __ private methods
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

		# user id has to go with every request
		params["user_id"] = self.user_id

		# micro cache?
		if self.micro_cache is False:
			params["no_micro_cache"] = 1

		# is there  atoken?
		if self.token:
			params["token"] = self.token

		params["api_key"] = self.api_key
		params["access_token"] = self.access_token

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

				elif data["error_type"] == "TwoFAException":
					raise(ex.TwoFAException(data["message"], questions=data["questions"], code=r.status_code))

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
		# non json content (images for 2FA)
		elif r.headers["content-type"] in ("image/jpeg", "image/jpg"):
			return r.content
		else:
			raise ex.DataException("Invalid response format")
