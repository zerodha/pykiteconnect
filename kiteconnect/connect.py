# -*- coding: utf-8 -*-
"""
    connect.py

    API wrapper for Kite Connect REST APIs.

    :copyright: (c) 2018 by Zerodha Technology.
    :license: see LICENSE for details.
"""
from six import StringIO, PY2
from six.moves.urllib.parse import urljoin
import csv
import json
import dateutil.parser
import hashlib
import logging
import datetime
import requests

from .__version__ import __version__, __title__
import kiteconnect.exceptions as ex

log = logging.getLogger(__name__)


class KiteConnect(object):
    """
    The Kite Connect API wrapper class.

    In production, you may initialise a single instance of this class per `api_key`.
    """

    # Default root API endpoint. It's possible to
    # override this by passing the `root` parameter during initialisation.
    _default_root_uri = "https://api.kite.trade"
    _default_login_uri = "https://kite.trade/connect/login"
    _default_timeout = 7  # In seconds

    # Constants
    # Products
    PRODUCT_MIS = "MIS"
    PRODUCT_CNC = "CNC"
    PRODUCT_NRML = "NRML"
    PRODUCT_CO = "CO"
    PRODUCT_BO = "BO"

    # Order types
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_SLM = "SL-M"
    ORDER_TYPE_SL = "SL"

    # Varities
    VARIETY_REGULAR = "regular"
    VARIETY_BO = "bo"
    VARIETY_CO = "co"
    VARIETY_AMO = "amo"

    # Transaction type
    TRANSACTION_TYPE_BUY = "BUY"
    TRANSACTION_TYPE_SELL = "SELL"

    # Validity
    VALIDITY_DAY = "DAY"
    VALIDITY_IOC = "IOC"

    # Exchanges
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_MCX = "MCX"

    # Margins segments
    MARGIN_EQUITY = "equity"
    MARGIN_COMMODITY = "commodity"

    # Status constants
    STATUS_COMPLETE = "COMPLETE"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELLED = "CANCELLED"

    # URIs to various calls
    _routes = {
        "api.token": "/session/token",
        "api.token.invalidate": "/session/token",
        "api.token.renew": "/session/refresh_token",
        "user.profile": "/user/profile",
        "user.margins": "/user/margins",
        "user.margins.segment": "/user/margins/{segment}",

        "orders": "/orders",
        "trades": "/trades",

        "order.info": "/orders/{order_id}",
        "order.place": "/orders/{variety}",
        "order.modify": "/orders/{variety}/{order_id}",
        "order.cancel": "/orders/{variety}/{order_id}",
        "order.trades": "/orders/{order_id}/trades",

        "portfolio.positions": "/portfolio/positions",
        "portfolio.holdings": "/portfolio/holdings",
        "portfolio.positions.convert": "/portfolio/positions",

        # MF api endpoints
        "mf.orders": "/mf/orders",
        "mf.order.info": "/mf/orders/{order_id}",
        "mf.order.place": "/mf/orders",
        "mf.order.cancel": "/mf/orders/{order_id}",

        "mf.sips": "/mf/sips",
        "mf.sip.info": "/mf/sips/{sip_id}",
        "mf.sip.place": "/mf/sips",
        "mf.sip.modify": "/mf/sips/{sip_id}",
        "mf.sip.cancel": "/mf/sips/{sip_id}",

        "mf.holdings": "/mf/holdings",
        "mf.instruments": "/mf/instruments",

        "market.instruments.all": "/instruments",
        "market.instruments": "/instruments/{exchange}",
        "market.margins": "/margins/{segment}",
        "market.historical": "/instruments/historical/{instrument_token}/{interval}",
        "market.trigger_range": "/instruments/trigger_range/{transaction_type}",

        "market.quote": "/quote",
        "market.quote.ohlc": "/quote/ohlc",
        "market.quote.ltp": "/quote/ltp",
    }

    def __init__(self,
                 api_key,
                 access_token=None,
                 root=None,
                 debug=False,
                 timeout=None,
                 proxies=None,
                 pool=None,
                 disable_ssl=False):
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
        a request to complete before it fails. Defaults to 7 seconds
        - `proxies` to set requests proxy.
        Check [python requests documentation](http://docs.python-requests.org/en/master/user/advanced/#proxies) for usage and examples.
        - `pool` is manages request pools. It takes a dict of params accepted by HTTPAdapter as described here in [python requests documentation](http://docs.python-requests.org/en/master/api/#requests.adapters.HTTPAdapter)
        - `disable_ssl` disables the SSL verification while making a request.
        If set requests won't throw SSLError if its set to custom `root` url without SSL.
        """
        self.debug = debug
        self.api_key = api_key
        self.session_expiry_hook = None
        self.disable_ssl = disable_ssl
        self.access_token = access_token
        self.proxies = proxies if proxies else {}

        self.root = root or self._default_root_uri
        self.timeout = timeout or self._default_timeout

        # Create requests session only if pool exists. Reuse session
        # for every request. Otherwise create session for each request
        if pool:
            self.reqsession = requests.Session()
            reqadapter = requests.adapters.HTTPAdapter(**pool)
            self.reqsession.mount("https://", reqadapter)
        else:
            self.reqsession = requests

        # disable requests SSL warning
        requests.packages.urllib3.disable_warnings()

    def set_session_expiry_hook(self, method):
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
        if not callable(method):
            raise TypeError("Invalid input type. Only functions are accepted.")

        self.session_expiry_hook = method

    def set_access_token(self, access_token):
        """Set the `access_token` received after a successful authentication."""
        self.access_token = access_token

    def login_url(self):
        """Get the remote login url to which a user should be redirected to initiate the login flow."""
        return "%s?api_key=%s&v=3" % (self._default_login_uri, self.api_key)

    def generate_session(self, request_token, api_secret):
        """
        Generate user session details like `access_token` etc by exchanging `request_token`.
        Access token is automatically set if the session is retrieved successfully.

        Do the token exchange with the `request_token` obtained after the login flow,
        and retrieve the `access_token` required for all subsequent requests. The
        response contains not just the `access_token`, but metadata for
        the user who has authenticated.

        - `request_token` is the token obtained from the GET paramers after a successful login redirect.
        - `api_secret` is the API api_secret issued with the API key.
        """
        h = hashlib.sha256(self.api_key.encode("utf-8") + request_token.encode("utf-8") + api_secret.encode("utf-8"))
        checksum = h.hexdigest()

        resp = self._post("api.token", {
            "api_key": self.api_key,
            "request_token": request_token,
            "checksum": checksum
        })

        if "access_token" in resp:
            self.set_access_token(resp["access_token"])

        if resp["login_time"] and len(resp["login_time"]) == 19:
            resp["login_time"] = dateutil.parser.parse(resp["login_time"])

        return resp

    def invalidate_access_token(self, access_token=None):
        """
        Kill the session by invalidating the access token.

        - `access_token` to invalidate. Default is the active `access_token`.
        """
        access_token = access_token or self.access_token
        return self._delete("api.token.invalidate", {
            "api_key": self.api_key,
            "access_token": access_token
        })

    def renew_access_token(self, refresh_token, api_secret):
        """
        Renew expired `refresh_token` using valid `refresh_token`.

        - `refresh_token` is the token obtained from previous successful login flow.
        - `api_secret` is the API api_secret issued with the API key.
        """
        h = hashlib.sha256(self.api_key.encode("utf-8") + refresh_token.encode("utf-8") + api_secret.encode("utf-8"))
        checksum = h.hexdigest()

        resp = self._post("api.token.renew", {
            "api_key": self.api_key,
            "refresh_token": refresh_token,
            "checksum": checksum
        })

        if "access_token" in resp:
            self.set_access_token(resp["access_token"])

        return resp

    def invalidate_refresh_token(self, refresh_token):
        """
        Invalidate refresh token.

        - `refresh_token` is the token which is used to renew access token.
        """
        return self._delete("api.token.invalidate", {
            "api_key": self.api_key,
            "refresh_token": refresh_token
        })

    def margins(self, segment=None):
        """Get account balance and cash margin details for a particular segment.

        - `segment` is the trading segment (eg: equity or commodity)
        """
        if segment:
            return self._get("user.margins.segment", {"segment": segment})
        else:
            return self._get("user.margins")

    def profile(self):
        """Get user profile details."""
        return self._get("user.profile")

    # orders
    def place_order(self,
                    variety,
                    exchange,
                    tradingsymbol,
                    transaction_type,
                    quantity,
                    product,
                    order_type,
                    price=None,
                    validity=None,
                    disclosed_quantity=None,
                    trigger_price=None,
                    squareoff=None,
                    stoploss=None,
                    trailing_stoploss=None,
                    tag=None):
        """Place an order."""
        params = locals()
        del(params["self"])

        for k in list(params.keys()):
            if params[k] is None:
                del(params[k])

        return self._post("order.place", params)["order_id"]

    def modify_order(self,
                     variety,
                     order_id,
                     parent_order_id=None,
                     quantity=None,
                     price=None,
                     order_type=None,
                     trigger_price=None,
                     validity=None,
                     disclosed_quantity=None):
        """Modify an open order."""
        params = locals()
        del(params["self"])

        for k in list(params.keys()):
            if params[k] is None:
                del(params[k])

        return self._put("order.modify", params)["order_id"]

    def cancel_order(self, variety, order_id, parent_order_id=None):
        """Cancel an order."""
        return self._delete("order.cancel", {
            "order_id": order_id,
            "variety": variety,
            "parent_order_id": parent_order_id
        })["order_id"]

    def exit_order(self, variety, order_id, parent_order_id=None):
        """Exit a BO/CO order."""
        self.cancel_order(variety, order_id, parent_order_id=parent_order_id)

    def _format_response(self, data):
        """Parse and format responses."""

        if type(data) == list:
            _list = data
        elif type(data) == dict:
            _list = [data]

        for item in _list:
            # Convert date time string to datetime object
            for field in ["order_timestamp", "exchange_timestamp", "created", "last_instalment", "fill_timestamp", "timestamp", "last_trade_time"]:
                if item.get(field) and len(item[field]) == 19:
                    item[field] = dateutil.parser.parse(item[field])

        return _list[0] if type(data) == dict else _list

    # orderbook and tradebook
    def orders(self):
        """Get list of orders."""
        return self._format_response(self._get("orders"))

    def order_history(self, order_id):
        """
        Get history of individual order.

        - `order_id` is the ID of the order to retrieve order history.
        """
        return self._format_response(self._get("order.info", {"order_id": order_id}))

    def trades(self):
        """
        Retrieve the list of trades executed (all or ones under a particular order).

        An order can be executed in tranches based on market conditions.
        These trades are individually recorded under an order.

        - `order_id` is the ID of the order (optional) whose trades are to be retrieved.
        If no `order_id` is specified, all trades for the day are returned.
        """
        return self._format_response(self._get("trades"))

    def order_trades(self, order_id):
        """
        Retrieve the list of trades executed for a particular order.

        - `order_id` is the ID of the order (optional) whose trades are to be retrieved.
            If no `order_id` is specified, all trades for the day are returned.
        """
        return self._format_response(self._get("order.trades", {"order_id": order_id}))

    def positions(self):
        """Retrieve the list of positions."""
        return self._get("portfolio.positions")

    def holdings(self):
        """Retrieve the list of equity holdings."""
        return self._get("portfolio.holdings")

    def convert_position(self,
                         exchange,
                         tradingsymbol,
                         transaction_type,
                         position_type,
                         quantity,
                         old_product,
                         new_product):
        """Modify an open position's product type."""
        return self._put("portfolio.positions.convert", {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "position_type": position_type,
            "quantity": quantity,
            "old_product": old_product,
            "new_product": new_product
        })

    def mf_orders(self, order_id=None):
        """Get all mutual fund orders or individual order info."""
        if order_id:
            return self._format_response(self._get("mf.order.info", {"order_id": order_id}))
        else:
            return self._format_response(self._get("mf.orders"))

    def place_mf_order(self,
                       tradingsymbol,
                       transaction_type,
                       quantity=None,
                       amount=None,
                       tag=None):
        """Place a mutual fund order."""
        return self._post("mf.order.place", {
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "amount": amount,
            "tag": tag
        })

    def cancel_mf_order(self, order_id):
        """Cancel a mutual fund order."""
        return self._delete("mf.order.cancel", {"order_id": order_id})

    def mf_sips(self, sip_id=None):
        """Get list of all mutual fund SIP's or individual SIP info."""
        if sip_id:
            return self._format_response(self._get("mf.sip.info", {"sip_id": sip_id}))
        else:
            return self._format_response(self._get("mf.sips"))

    def place_mf_sip(self,
                     tradingsymbol,
                     amount,
                     instalments,
                     frequency,
                     initial_amount=None,
                     instalment_day=None,
                     tag=None):
        """Place a mutual fund SIP."""
        return self._post("mf.sip.place", {
            "tradingsymbol": tradingsymbol,
            "amount": amount,
            "initial_amount": initial_amount,
            "instalments": instalments,
            "frequency": frequency,
            "instalment_day": instalment_day,
            "tag": tag
        })

    def modify_mf_sip(self,
                      sip_id,
                      amount=None,
                      status=None,
                      instalments=None,
                      frequency=None,
                      instalment_day=None):
        """Modify a mutual fund SIP."""
        return self._put("mf.sip.modify", {
            "sip_id": sip_id,
            "amount": amount,
            "status": status,
            "instalments": instalments,
            "frequency": frequency,
            "instalment_day": instalment_day
        })

    def cancel_mf_sip(self, sip_id):
        """Cancel a mutual fund SIP."""
        return self._delete("mf.sip.cancel", {"sip_id": sip_id})

    def mf_holdings(self):
        """Get list of mutual fund holdings."""
        return self._get("mf.holdings")

    def mf_instruments(self):
        """Get list of mutual fund instruments."""
        return self._parse_mf_instruments(self._get("mf.instruments"))

    def instruments(self, exchange=None):
        """
        Retrieve the list of market instruments available to trade.

        Note that the results could be large, several hundred KBs in size,
        with tens of thousands of entries in the list.

        - `exchange` is specific exchange to fetch (Optional)
        """
        if exchange:
            params = {"exchange": exchange}

            return self._parse_instruments(self._get("market.instruments", params))
        else:
            return self._parse_instruments(self._get("market.instruments.all"))

    def quote(self, *instruments):
        """
        Retrieve quote for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `tradingsymbol:exchange`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        data = self._get("market.quote", {"i": ins})
        return {key: self._format_response(data[key]) for key in data}

    def ohlc(self, *instruments):
        """
        Retrieve OHLC and market depth for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `tradingsymbol:exchange`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return self._get("market.quote.ohlc", {"i": ins})

    def ltp(self, *instruments):
        """
        Retrieve last price for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `tradingsymbol:exchange`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return self._get("market.quote.ltp", {"i": ins})

    # def instruments_margins(self, segment):
    #     """
    #     Retrive margins provided for individual segments.

    #     `segment` is segment name to retrive.
    #     """
    #     return self._get("market.margins", {"segment": segment})

    def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False):
        """
        Retrieve historical data (candles) for an instrument.

        Although the actual response JSON from the API does not have field
        names such has 'open', 'high' etc., this function call structures
        the data into an array of objects with field names. For example:

        - `instrument_token` is the instrument identifier (retrieved from the instruments()) call.
        - `from_date` is the From date (datetime object or string in format of yyyy-mm-dd HH:MM:SS.
        - `to_date` is the To date (datetime object or string in format of yyyy-mm-dd HH:MM:SS).
        - `interval` is the candle interval (minute, day, 5 minute etc.).
        - `continuous` is a boolean flag to get continuous data for futures and options instruments.
        """
        date_string_format = "%Y-%m-%d %H:%M:%S"
        from_date_string = from_date.strftime(date_string_format) if type(from_date) == datetime.datetime else from_date
        to_date_string = to_date.strftime(date_string_format) if type(to_date) == datetime.datetime else to_date

        data = self._get("market.historical", {
            "instrument_token": instrument_token,
            "from": from_date_string,
            "to": to_date_string,
            "interval": interval,
            "continuous": 1 if continuous else 0
        })

        return self._format_historical(data)

    def _format_historical(self, data):
        records = []
        for d in data["candles"]:
            records.append({
                "date": dateutil.parser.parse(d[0]),
                "open": d[1],
                "high": d[2],
                "low": d[3],
                "close": d[4],
                "volume": d[5]
            })

        return records

    def trigger_range(self, transaction_type, *instruments):
        """Retrieve the buy/sell trigger range for Cover Orders."""
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return self._get("market.trigger_range", {
            "i": ins,
            "transaction_type": transaction_type.lower()
        })

    def _parse_instruments(self, data):
        # decode to string for Python 3
        d = data
        # Decode unicode data
        if not PY2 and type(d) == bytes:
            d = data.decode("utf-8").strip()

        records = []
        reader = csv.DictReader(StringIO(d))

        for row in reader:
            row["instrument_token"] = int(row["instrument_token"])
            row["last_price"] = float(row["last_price"])
            row["strike"] = float(row["strike"])
            row["tick_size"] = float(row["tick_size"])
            row["lot_size"] = int(row["lot_size"])

            # Parse date
            if len(row["expiry"]) == 10:
                row["expiry"] = dateutil.parser.parse(row["expiry"]).date()

            records.append(row)

        return records

    def _parse_mf_instruments(self, data):
        # decode to string for Python 3
        d = data
        if not PY2 and type(d) == bytes:
            d = data.decode("utf-8").strip()

        records = []
        reader = csv.DictReader(StringIO(d))

        for row in reader:
            row["minimum_purchase_amount"] = float(row["minimum_purchase_amount"])
            row["purchase_amount_multiplier"] = float(row["purchase_amount_multiplier"])
            row["minimum_additional_purchase_amount"] = float(row["minimum_additional_purchase_amount"])
            row["minimum_redemption_quantity"] = float(row["minimum_redemption_quantity"])
            row["redemption_quantity_multiplier"] = float(row["redemption_quantity_multiplier"])
            row["purchase_allowed"] = bool(int(row["purchase_allowed"]))
            row["redemption_allowed"] = bool(int(row["redemption_allowed"]))
            row["last_price"] = float(row["last_price"])

            # Parse date
            if len(row["last_price_date"]) == 10:
                row["last_price_date"] = dateutil.parser.parse(row["last_price_date"]).date()

            records.append(row)

        return records

    def _user_agent(self):
        return (__title__ + "-python/").capitalize() + __version__

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
        params = parameters.copy() if parameters else {}

        # Form a restful URL
        uri = self._routes[route].format(**params)
        url = urljoin(self.root, uri)

        # Custom headers
        headers = {
            "X-Kite-Version": "3",  # For version 3
            "User-Agent": self._user_agent()
        }

        if self.api_key and self.access_token:
            # set authorization header
            auth_header = self.api_key + ":" + self.access_token
            headers["Authorization"] = "token {}".format(auth_header)

        if self.debug:
            log.debug("Request: {method} {url} {params} {headers}".format(method=method, url=url, params=params, headers=headers))

        try:
            r = self.reqsession.request(method,
                                        url,
                                        data=params if method in ["POST", "PUT"] else None,
                                        params=params if method in ["GET", "DELETE"] else None,
                                        headers=headers,
                                        verify=not self.disable_ssl,
                                        allow_redirects=True,
                                        timeout=self.timeout,
                                        proxies=self.proxies)
        # Any requests lib related exceptions are raised here - http://docs.python-requests.org/en/master/_modules/requests/exceptions/
        except Exception as e:
            raise e

        if self.debug:
            log.debug("Response: {code} {content}".format(code=r.status_code, content=r.content))

        # Validate the content type.
        if "json" in r.headers["content-type"]:
            try:
                data = json.loads(r.content.decode("utf8"))
            except ValueError:
                raise ex.DataException("Couldn't parse the JSON response received from the server: {content}".format(
                    content=r.content))

            # api error
            if data.get("error_type"):
                # Call session hook if its registered and TokenException is raised
                if self.session_expiry_hook and r.status_code == 403 and data["error_type"] == "TokenException":
                    self.session_expiry_hook()

                # native Kite errors
                exp = getattr(ex, data["error_type"], ex.GeneralException)
                raise exp(data["message"], code=r.status_code)

            return data["data"]
        elif "csv" in r.headers["content-type"]:
            return r.content
        else:
            raise ex.DataException("Unknown Content-Type ({content_type}) with response: ({content})".format(
                content_type=r.headers["content-type"],
                content=r.content))
