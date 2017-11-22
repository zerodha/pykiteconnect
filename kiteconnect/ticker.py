import sys
import time
import json
import struct
import logging
import threading
from twisted.internet import reactor, ssl
from twisted.python import log as twisted_log
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS

from .__version__ import __version__, __title__

log = logging.getLogger(__name__)


class KiteTickerClientProtocol(WebSocketClientProtocol):
    """Kite ticker autobahn WebSocket protocol."""

    PING_INTERVAL = 2.5
    KEEPALIVE_INTERVAL = 5

    _ping_message = ""
    _next_ping = None
    _next_pong_check = None
    _last_pong_time = None
    _last_ping_time = None

    def __init__(self, *args, **kwargs):
        """Initialize protocol."""
        super(KiteTickerClientProtocol, self).__init__(*args, **kwargs)

    # Overide method
    def onConnect(self, response):  # noqa
        """On WebSocket connect."""
        self.factory.ws = self

        if self.factory.on_connect:
            self.factory.on_connect(self, response)

        # Reset reconnect on successful reconnect
        self.factory.resetDelay()

    # Overide method
    def onOpen(self):  # noqa
        """On WebSocket connection open."""
        # send ping
        self._loop_ping()
        # init last pong check after X seconds
        self._loop_pong_check()

        if self.factory.on_open:
            self.factory.on_open(self)

    # Overide method
    def onMessage(self, payload, is_binary):  # noqa
        """On text or binary message is received."""
        if self.factory.on_message:
            self.factory.on_message(self, payload, is_binary)

    # Overide method
    def onClose(self, was_clean, code, reason):  # noqa
        """On connection close received."""
        if not was_clean:
            if self.factory.on_error:
                self.factory.on_error(self, code, reason)

        if self.factory.on_close:
            self.factory.on_close(self, code, reason)

        # Cancel next ping and timer
        self._last_ping_time = None
        self._last_pong_time = None

        if self._next_ping:
            self._next_ping.cancel()

        if self._next_pong_check:
            self._next_pong_check.cancel()

    def onPong(self, response):  # noqa
        """On pong message."""
        if self._last_pong_time:
            log.debug("last pong was {} seconds back.".format(time.time() - self._last_pong_time))

        self._last_pong_time = time.time()
        log.debug("pong => {}".format(response))

    """
    Custom helper and exposed methods.
    """

    def _loop_ping(self): # noqa
        """Start a ping loop where it sends ping message every X seconds."""
        log.debug("ping => {}".format(self._ping_message))
        if self._last_ping_time:
            log.debug("last ping was {} seconds back.".format(time.time() - self._last_ping_time))

        self._last_ping_time = time.time()
        self.sendPing(self._ping_message)

        # Call self after X seconds
        self._next_ping = self.factory.reactor.callLater(self.PING_INTERVAL, self._loop_ping)

    def _loop_pong_check(self):
        if self._last_pong_time:
            # No pong message since long time, so init reconnect
            last_pong_diff = time.time() - self._last_pong_time
            if last_pong_diff > (2 * self.PING_INTERVAL):
                log.debug("Last pong was {} seconds ago. So dropping connection to reconnect.".format(last_pong_diff))
                # drop connection
                self.dropConnection(abort=True)

        self._next_pong_check = self.factory.reactor.callLater(self.PING_INTERVAL, self._loop_pong_check)


class KiteTickerClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
    """Autobahn WebSocket client factory to implement reconnection and callbacks."""

    protocol = KiteTickerClientProtocol
    maxDelay = 5
    maxRetries = 10

    _last_connection_time = None

    def __init__(self, *args, **kwargs):
        """Initialize with default callback method values."""
        self.ws = None
        self.on_open = None
        self.on_error = None
        self.on_close = None
        self.on_message = None
        self.on_connect = None
        self.on_reconnect = None
        self.on_noreconnect = None

        super(KiteTickerClientFactory, self).__init__(*args, **kwargs)

    def startedConnecting(self, connector):  # noqa
        """On connecting start or reconnection."""
        if not self._last_connection_time:
            log.debug("Start WebSocket connection.")

        self._last_connection_time = time.time()

    def clientConnectionFailed(self, connector, reason):  # noqa
        """On connection failure."""
        log.error("WebSocket connection failed: {}.".format(reason))
        log.error("Try reconnecting. Retry attempt count: {}".format(self.retries))

        # on reconnect callback
        if self.on_reconnect:
            self.on_reconnect()

        self.retry(connector)
        self.send_noreconnect()

    def clientConnectionLost(self, connector, reason):  # noqa
        """On connection lost."""
        log.error("WebSocket connection lost: {}.".format(reason))
        log.error("Try reconnecting. Retry attempt count: {}".format(self.retries))

        # on reconnect callback
        if self.on_reconnect:
            self.on_reconnect()

        self.retry(connector)
        self.send_noreconnect()

    def send_noreconnect(self):
        """Callback `no_reconnect` if max retries are exhausted."""
        if self.maxRetries is not None and (self.retries > self.maxRetries):
            log.debug("Maximum retries ({}) exhausted.".format(self.maxRetries))
            if self.on_noreconnect:
                self.on_noreconnect()


class KiteTicker(object):
    """
    The WebSocket client for connecting to Kite Connect's streaming quotes service.

    Getting started:
    ---------------
        #!python
        from kiteconnect import WebSocket
        # Initialise.
        kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id")
        # Callback for tick reception.
        def on_tick(tick, ws):
            print(tick)
        # Callback for successful connection.
        def on_connect(ws):
            # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
            ws.subscribe([738561, 5633])
            # Set RELIANCE to tick in `full` mode.
            ws.set_mode(ws.MODE_FULL, [738561])
        # Assign the callbacks.
        kws.on_tick = on_tick
        kws.on_connect = on_connect
        # To enable auto reconnect WebSocket connection in case of network failure
        # - First param is interval between reconnection attempts in seconds.
        # Callback `on_reconnect` is triggered on every reconnection attempt. (Default interval is 5 seconds)
        # - Second param is maximum number of retries before the program exits triggering `on_noreconnect` calback. (Defaults to 50 attempts)
        # Note that you can also enable auto reconnection    while initialising websocket.
        # Example `kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id", reconnect=True, reconnect_interval=5, reconnect_tries=50)`
        kws.enable_reconnect(reconnect_interval=5, reconnect_tries=50)
        # Infinite loop on the main thread. Nothing after this will run.
        # You have to use the pre-defined callbacks to manage subscriptions.
        kws.connect()
    Callbacks
    ---------
    Param `ws` is the currently initialised WebSocket object itself.
    - `on_tick(ticks, ws)` -  Ticks (array of dicts) and the WebSocket object are passed as params.
    - `on_close(ws)` -  Triggered when connection is closed.
    - `on_error(error, ws)` -  Triggered when connection is closed with an error. Error object and WebSocket object are passed as params.
    - `on_connect` -  Triggered when connection is established successfully.
    - `on_message(data, ws)` -  Triggered when there is any message received. This is raw data received from WebSocket.
    - `on_reconnect(ws)` -  Triggered when auto reconnection is attempted.
    - `on_noreconnect` -  Triggered when number of auto reconnection attempts exceeds `reconnect_tries`.
    Tick structure (passed to the tick callback you assign):
    ---------------------------
        [{
            "mode": "quote",
            "tradeable": True,
            "instrument_token": 738561,
            "last_price": 957,
            "last_quantity": 100,
            "sell_quantity": 2286,
            "buy_quantity": 0,
            "volume": 5333469,
            "change": 0,
            "average_price": 959,
            "ohlc": {
                "high": 973,
                "close": 957,
                "open": 969,
                "low": 956
            },
            "depth": {
                "sell": [{
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }],
                "buy": [{
                    "price": 957,
                    "orders": 196608,
                    "quantity": 2286
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }, {
                    "price": 0,
                    "orders": 0,
                    "quantity": 0
                }]
            }
        }]
    """

    EXCHANGE_MAP = {
        "nse": 1,
        "nfo": 2,
        "cds": 3,
        "bse": 4,
        "bfo": 5,
        "bsecds": 6,
        "mcx": 7,
        "mcxsx": 8,
        "indices": 9
    }

    # Default connection timeout
    CONNECT_TIMEOUT = 30
    # Default Reconnect max delay.
    RECONNECT_MAX_DELAY = 60
    # Default reconnect attempts
    RECONNECT_MAX_TRIES = 50
    # Default root API endpoint. It's possible to
    # override this by passing the `root` parameter during initialisation.
    ROOT_URI = "wss://websocket.kite.trade"

    # Available streaming modes.
    MODE_FULL = "full"
    MODE_QUOTE = "quote"
    MODE_LTP = "ltp"

    # Available actions.
    _message_code = 11
    _message_subscribe = "subscribe"
    _message_unsubscribe = "unsubscribe"
    _message_setmode = "mode"

    # Minimum delay which should be set between retries. User can't set less than this
    _minimum_reconnect_max_delay = 5
    # Maximum number or retries user can set
    _maximum_reconnect_max_tries = 300

    def __init__(self, api_key, public_token, user_id, debug=False, root=None,
                 reconnect=True, reconnect_max_tries=RECONNECT_MAX_TRIES, reconnect_max_delay=RECONNECT_MAX_DELAY,
                 connect_timeout=CONNECT_TIMEOUT):
        """
        Initialise websocket client instance.

        - `api_key` is the API key issued to you
        - `public_token` is the token obtained after the login flow in
            exchange for the `request_token` . Pre-login, this will default to None,
            but once you have obtained it, you should
            persist it in a database or session to pass
            to the Kite Connect class initialisation for subsequent requests.
        - `user_id` is the Zerodha client id of the authenticated user
        - `root` is the websocket API end point root. Unless you explicitly
            want to send API requests to a non-default endpoint, this
            can be ignored.
        - `reconnect` is a boolean to enable WebSocket autreconnect in case of network failure/disconnection.
        - `reconnect_interval` - Interval (in seconds) between auto reconnection attemptes. Defaults to 5 seconds.
        - `reconnect_tries` - Maximum number reconnection attempts. Defaults to 50 attempts.
        """
        self.root = root or self.ROOT_URI

        # Set max reconnect tries
        if reconnect_max_tries > self._maximum_reconnect_max_tries:
            log.warning("`reconnect_max_tries` can not be more than {val}. Setting to highest possible value - {val}.".format(
                val=self._maximum_reconnect_max_tries))
            self.reconnect_max_tries = self._maximum_reconnect_max_tries
        else:
            self.reconnect_max_tries = reconnect_max_tries

        # Set max reconnect delay
        if reconnect_max_delay < self._minimum_reconnect_max_delay:
            log.warning("`reconnect_max_delay` can not be less than {val}. Setting to lowest possible value - {val}.".format(
                val=self._minimum_reconnect_max_delay))
            self.reconnect_max_delay = self._minimum_reconnect_max_delay
        else:
            self.reconnect_max_delay = reconnect_max_delay

        self.connect_timeout = connect_timeout

        self.socket_url = "{root}?api_key={api_key}&user_id={user_id}"\
            "&public_token={public_token}".format(
                root=self.root,
                api_key=api_key,
                public_token=public_token,
                user_id=user_id
            )

        self.debug = debug

        # Placeholders for callbacks.
        self.on_tick = None
        self.on_open = None
        self.on_close = None
        self.on_error = None
        self.on_connect = None
        self.on_message = None
        self.on_reconnect = None
        self.on_noreconnect = None

        self.subscribed_tokens = set()
        self.modes = set()

    def _create_connection(self, url, **kwargs):
        """Create a WebSocket client connection."""
        self.factory = KiteTickerClientFactory(url, **kwargs)

        # Alias for current websocket connection
        self.ws = self.factory.ws

        # Register private callbacks
        self.factory.on_open = self._on_open
        self.factory.on_error = self._on_error
        self.factory.on_close = self._on_close
        self.factory.on_message = self._on_message
        self.factory.on_connect = self._on_connect
        self.factory.on_reconnect = self._on_reconnect
        self.factory.on_noreconnect = self._on_noreconnect

        self.factory.maxDelay = self.reconnect_max_delay
        self.factory.maxRetries = self.reconnect_max_tries

    def _user_agent(self):
        return (__title__ + "-python/").capitalize() + __version__

    def connect(self, threaded=False, disable_ssl_verification=False, proxy=None):
        """Connect to websocket."""
        # Custom headers
        headers = {
            "X-Kite-Version": "3",  # For version 3
        }

        # Init WebSocket client factory
        self._create_connection(self.socket_url, useragent=self._user_agent(),
                                proxy=proxy, headers=headers)

        # Set SSL context
        context_factory = None
        if self.factory.isSecure and not disable_ssl_verification:
            context_factory = ssl.ClientContextFactory()

        # Establish WebSocket connection to a server
        connectWS(self.factory, contextFactory=context_factory, timeout=self.connect_timeout)

        if self.debug:
            twisted_log.startLogging(sys.stdout)

        # Run in seperate thread of blocking
        opts = {}
        if threaded:
            self.websocket_thread = threading.Thread(target=reactor.run, kwargs=opts)
            self.websocket_thread.daemon = True
            self.websocket_thread.start()
        else:
            reactor.run(**opts)

    def is_connected(self):
        """Check if WebSocket connection is established."""
        if self.ws:
            return True if self.ws.STATE_OPEN else False

    def close(self, code=None, reason=None):
        """Close the WebSocket connection."""
        if self.ws:
            self.ws.sendClose(code, reason)

    def stop_retry(self):
        """Stop auto retry when it is in progress."""
        if self.factory:
            self.factory.stopTrying()

    def subscribe(self, instrument_tokens):
        """
        Subscribe to a list of instrument_tokens.

        - `instrument_tokens` is list of instrument instrument_tokens to subscribe
        """
        try:
            self.ws.sendMessage(json.dumps({"a": self._message_subscribe, "v": instrument_tokens}))

            for token in instrument_tokens:
                self.subscribed_tokens.add(token)

            return True
        except Exception as e:
            self.close(reason="Error while subscribe: {}".format(str(e)))
            raise

    def unsubscribe(self, instrument_tokens):
        """
        Unsubscribe the given list of instrument_tokens.

        - `instrument_tokens` is list of instrument_tokens to unsubscribe.
        """
        try:
            self.ws.sendMessage(json.dumps({"a": self._message_unsubscribe, "v": instrument_tokens}))

            for token in instrument_tokens:
                try:
                    self.subscribed_tokens.remove(token)
                except:
                    pass

            return True
        except Exception as e:
            self.close(reason="Error while unsubscribe: {}".format(str(e)))
            raise

    def set_mode(self, mode, instrument_tokens):
        """
        Set streaming mode for the given list of tokens.

        - `mode` is the mode to set. It can be one of the following class constants:
            MODE_LTP, MODE_QUOTE, or MODE_FULL.
        - `instrument_tokens` is list of instrument tokens on which the mode should be applied
        """
        try:
            self.ws.sendMessage(json.dumps({"a": self._message_setmode, "v": [mode, instrument_tokens]}))
            return True
        except Exception as e:
            self.close(reason="Error while setting mode: {}".format(str(e)))
            raise

    def _on_connect(self, ws, response):
        self.ws = ws
        if self.on_connect:
            self.on_connect(self, response)

    def _on_close(self, ws, code, reason):
        """Call `on_close` callback when connection is closed."""
        if self.on_close:
            self.on_close(self, code, reason)

    def _on_error(self, ws, code, reason):
        """Call `on_error` callback when connection throws an error."""
        if self.on_error:
            self.on_error(self, code, reason)

    def _on_message(self, ws, payload, is_binary):
        """Call `on_message` callback when text message is received."""
        if self.on_message:
            self.on_message(self, payload, is_binary)

        if self.on_tick:
            # If the message is binary, parse it and send it to the callback.
            if is_binary and len(payload) > 4:
                self.on_tick(self, self._parse_binary(payload))

    def _on_open(self, ws):
        if self.on_open:
            return self.on_open(self)

    def _on_reconnect(self):
        if self.on_reconnect:
            return self.on_reconnect(self)

    def _on_noreconnect(self):
        if self.on_noreconnect:
            return self.on_noreconnect(self)

    def _parse_binary(self, bin):
        """Parse binary data to a (list of) ticks structure."""
        packets = self._split_packets(bin)  # split data to individual ticks packet
        data = []

        for packet in packets:
            instrument_token = self._unpack_int(packet, 0, 4)
            segment = instrument_token & 0xff  # Retrive segment constant from instrument_token

            divisor = 10000000.0 if segment == self.EXCHANGE_MAP["cds"] else 100.0

            # All indices are not tradable
            tradeable = False if segment == self.EXCHANGE_MAP["indices"] else True

            # LTP packets
            if len(packet) == 8:
                data.append({
                    "tradeable": tradeable,
                    "mode": self.MODE_LTP,
                    "instrument_token": instrument_token,
                    "last_price": self._unpack_int(packet, 4, 8) / divisor
                })
            # Indices quote call
            elif len(packet) == 28:
                d = {
                    "tradeable": tradeable,
                    "mode": self.MODE_QUOTE,
                    "instrument_token": instrument_token,
                    "last_price": self._unpack_int(packet, 4, 8) / divisor,
                    "ohlc": {
                        "high": self._unpack_int(packet, 8, 12) / divisor,
                        "low": self._unpack_int(packet, 12, 16) / divisor,
                        "open": self._unpack_int(packet, 16, 20) / divisor,
                        "close": self._unpack_int(packet, 20, 24) / divisor
                    },
                    "change": self._unpack_int(packet, 24, 28) / divisor,
                }

                # Compute the change price using close price and last price
                if(d["ohlc"]["close"] != 0):
                    d["change"] = (d["last_price"] - d["ohlc"]["close"]) * 100 / d["ohlc"]["close"]

                data.append(d)
            # Quote and full mode
            elif len(packet) == 44 or len(packet) == 164:
                mode = self.MODE_QUOTE if len(packet) == 44 else self.MODE_FULL

                d = {
                    "tradeable": True,
                    "mode": mode,
                    "instrument_token": instrument_token,
                    "last_price": self._unpack_int(packet, 4, 8) / divisor,
                    "last_quantity": self._unpack_int(packet, 8, 12),
                    "average_price": self._unpack_int(packet, 12, 16) / divisor,
                    "volume": self._unpack_int(packet, 16, 20),
                    "buy_quantity": self._unpack_int(packet, 20, 24),
                    "sell_quantity": self._unpack_int(packet, 24, 28),
                    "ohlc": {
                        "open": self._unpack_int(packet, 28, 32) / divisor,
                        "high": self._unpack_int(packet, 32, 36) / divisor,
                        "low": self._unpack_int(packet, 36, 40) / divisor,
                        "close": self._unpack_int(packet, 40, 44) / divisor
                    }
                }

                # Compute the change price using close price and last price
                d["change"] = 0
                if(d["ohlc"]["close"] != 0):
                    d["change"] = (d["last_price"] - d["ohlc"]["close"]) * 100 / d["ohlc"]["close"]

                if len(packet) == 164:
                    # Market depth entries.
                    depth = {
                        "buy": [],
                        "sell": []
                    }

                    if len(packet) > 44:
                        # Compile the market depth lists.
                        for i, p in enumerate(range(44, len(packet), 12)):
                            depth["sell" if i >= 5 else "buy"].append({
                                "quantity": self._unpack_int(packet, p, p + 4),
                                "price": self._unpack_int(packet, p + 4, p + 8) / divisor,
                                "orders": self._unpack_int(packet, p + 8, p + 12)
                            })

                    d["depth"] = depth

                data.append(d)

        return data

    def _unpack_int(self, bin, start, end):
        """Unpack binary data as unsgined interger."""
        return struct.unpack(">I", bin[start:end])[0]

    def _split_packets(self, bin):
        """Split the data to individual packets of ticks."""
        # Ignore heartbeat data.
        if len(bin) < 2:
            return []

        number_of_packets = struct.unpack(">H", bin[0:2])[0]
        packets = []

        j = 2
        for i in range(number_of_packets):
            packet_length = struct.unpack(">H", bin[j:j + 2])[0]
            packets.append(bin[j + 2: j + 2 + packet_length])
            j = j + 2 + packet_length

        return packets
