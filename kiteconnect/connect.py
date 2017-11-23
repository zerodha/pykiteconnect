# coding: utf-8

from six import StringIO, PY2
from six.moves.urllib.parse import urljoin
import csv
import json
import hashlib
import logging
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

    # URIs to various calls
    _routes = {
        "parameters": "/parameters",
        "api.validate": "/session/token",
        "api.invalidate": "/session/token",
        "user.margins": "/user/margins",
        "user.margins.segment": "/user/margins/{segment}",

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
        "market.margins": "/margins/{segment}",
        "market.instruments": "/instruments/{exchange}",
        "market.historical": "/instruments/historical/{instrument_token}/{interval}",
        "market.trigger_range": "/instruments/{exchange}/{tradingsymbol}/trigger_range",

        "market.quote": "/instruments/{exchange}/{tradingsymbol}",
        "market.quote.ohlc": "/quote/ohlc",
        "market.quote.ltp": "/quote/ltp",
    }

    # Public constants
    BO = "BO"

    def __init__(self,
                 api_key,
                 access_token=None,
                 root=None,
                 debug=False,
                 timeout=None,
                 micro_cache=True,
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
        - `micro_cache`, when set to True, will fetch the last cached
        version of an API response if available. This saves time on
        a roundtrip to the backend. Micro caches only live for several
        seconds to prevent data from turning stale.
        - `proxies` to set requests proxy.
        Check [python requests documentation](http://docs.python-requests.org/en/master/user/advanced/#proxies) for usage and examples.
        - `pool` is manages request pools. It takes a dict of params accepted by HTTPAdapter as described here http://docs.python-requests.org/en/master/api/
        - `disable_ssl` disables the SSL verification while making a request.
        If set requests won't throw SSLError if its set to custom `root` url without SSL.
        """
        self.debug = debug
        self.api_key = api_key
        self.session_expiry_hook = None
        self.micro_cache = micro_cache
        self.disable_ssl = disable_ssl
        self.access_token = access_token
        self.proxies = proxies if proxies else {}

        self.root = root or self._default_root_uri
        self.timeout = timeout or self._default_timeout

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
        return "%s?api_key=%s" % (self._default_login_uri, self.api_key)

    def request_access_token(self, request_token, api_secret):
        """
        Get `access_token` by exchanging `request_token`.

        Do the token exchange with the `request_token` obtained after the login flow,
        and retrieve the `access_token` required for all subsequent requests. The
        response contains not just the `access_token`, but metadata for
        the user who has authenticated.

        - `request_token` is the token obtained from the GET paramers after a successful login redirect.
        - `api_secret` is the API api_secret issued with the API key.
        """
        h = hashlib.sha256(self.api_key.encode("utf-8") + request_token.encode("utf-8") + api_secret.encode("utf-8"))
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

    def margins(self, segment=None):
        """Get account balance and cash margin details for a particular segment.

        - `segment` is the trading segment (eg: equity or commodity)
        """
        if segment:
            return self._get("user.margins.segment", {"segment": segment})
        else:
            return self._get("user.margins")

    # orders
    def place_order(self,
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
                    variety=VARIETY_REGULAR,
                    tag=""):
        """Place an order."""
        params = locals()
        del(params["self"])

        for k in list(params.keys()):
            if params[k] is None:
                del(params[k])

        return self._post("orders.place", params)["order_id"]

    def modify_order(self,
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

        for k in list(params.keys()):
            if params[k] is None:
                del(params[k])

        return self._put("orders.modify", params)["order_id"]

    def cancel_order(self, order_id, variety="regular", parent_order_id=None):
        """Cancel an order."""
        return self._delete("orders.cancel", {
            "order_id": order_id,
            "variety": variety,
            "parent_order_id": parent_order_id
        })["order_id"]

    def exit_order(self, order_id, variety="regular", parent_order_id=None):
        """Exit a BO/CO order."""
        self.cancel_order(order_id, variety=variety, parent_order_id=parent_order_id)

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

    def convert_position(self,
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

    def mf_orders(self, order_id=None):
        """Get all mutual fund orders or individual order info."""
        if order_id:
            return self._get("mf.order.info", {"order_id": order_id})
        else:
            return self._get("mf.orders")

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
            return self._get("mf.sip.info", {"sip_id": sip_id})
        else:
            return self._get("mf.sips")

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
                      amount,
                      status,
                      instalments,
                      frequency,
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

            return self._parse_csv(self._get("market.instruments", params))
        else:
            return self._parse_csv(self._get("market.instruments.all"))

    def quote(self, exchange, tradingsymbol):
        """
        Retrieve quote and market depth for an instrument.

        - `exchange` is instrument exchange
        - `tradingsymbol` is instrument name
        """
        return self._get("market.quote", {"exchange": exchange, "tradingsymbol": tradingsymbol})

    def ohlc(self, instruments):
        """
        Retrieve OHLC and market depth for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `tradingsymbol:exchange`. For example NSE:INFY
        """
        return self._get("market.quote.ohlc", {"i": instruments})

    def ltp(self, instruments):
        """
        Retrieve last price for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `tradingsymbol:exchange`. For example NSE:INFY
        """
        return self._get("market.quote.ltp", {"i": instruments})

    def instruments_margins(self, segment):
        """
        Retrive margins provided for individual segments.

        `segment` is segment name to retrive.
        """
        return self._get("market.margins", {"segment": segment})

    def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False):
        """
        Retrieve historical data (candles) for an instrument.

        Although the actual response JSON from the API does not have field
        names such has 'open', 'high' etc., this functin call structures
        the data into an array of objects with field names. For example:

        - `instrument_token` is the instrument identifier (retrieved from the instruments()) call.
        - `date_from` is the From date (datetime object)
        - `date_to` is the To date (datetime object)
        - `interval` is the candle interval (minute, day, 5 minute etc.)
        - `continuous` is a boolean flag to get continous data for futures and options instruments.
        """
        date_string_format = "%Y-%m-%d+%H:%M:%S"

        data = self._get("market.historical", {
            "instrument_token": instrument_token,
            "from": from_date.strftime(date_string_format),
            "to": to_date.strftime(date_string_format),
            "interval": interval,
            "continuous": 1 if continuous else 0
        })

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
        return self._get("market.trigger_range", {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type
        })

    def _parse_csv(self, data):
        # decode to string for Python 3
        d = data
        if not PY2:
            d = data.decode("utf-8").strip()

        reader = csv.reader(StringIO(d))

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

    def _parse_mf_instruments(self, data):
        # decode to string for Python 3
        d = data
        if not PY2:
            d = data.decode("utf-8").strip()

        reader = csv.DictReader(StringIO(d))

        # Return list instead of file reader
        records = [row for row in reader]
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

        # Add access token to params if its set
        if self.access_token:
            params["access_token"] = self.access_token

        # override instance's API key if one is supplied in the params
        if "api_key" not in params or not params.get("api_key"):
            params["api_key"] = self.api_key

        # Form a restful URL
        uri = self._routes[route].format(**params)
        url = urljoin(self.root, uri)

        if self.debug:
            log.debug("Request: {method} {url} {params}".format(method=method, url=url, params=params))

        # Custom headers
        headers = {
            "X-Kite-Version": "3",  # For version 3
            "User-Agent": self._user_agent()
        }

        try:
            r = self.reqsession.request(method,
                                        url,
                                        data=params if method in ["POST", "PUT"] else None,
                                        params=params if method in ["GET", "DELETE"] else None,
                                        headers=headers,
                                        verify=False,
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
            except:
                raise ex.DataException("Couldn't parse the JSON response received from the server: {content}".format(
                    content=r.content))

            # api error
            if data.get("error_type"):
                # Call session hook if its registered and TokenException is raised
                if self.session_expiry_hook and r.status_code == 403 and data["error_type"] == "TokenException":
                        self.session_expiry_hook()
                        return

                # native Kite errors
                exp = getattr(ex, data["error_type"])
                if exp:
                    raise(exp(data["message"], code=r.status_code))
                else:
                    raise(ex.GeneralException(data["message"], code=r.status_code))

            return data["data"]
        elif "csv" in r.headers["content-type"]:
            return r.content
        else:
            raise ex.DataException("Unknown Content-Type ({content_type}) with response: ({content})".format(
                content_type=r.headers["content-type"],
                content=r.content))
