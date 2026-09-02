# coding: utf-8
"""Ticker tests"""
import six
import json
from mock import Mock
from mock import patch
from base64 import b64encode
from hashlib import sha1

from autobahn.websocket.protocol import WebSocketProtocol
from kiteconnect import KiteTicker


class TestTicker:

    @patch("kiteconnect.ticker.reactor")
    @patch("kiteconnect.ticker.connectWS")
    @patch("kiteconnect.ticker.ssl.optionsForClientTLS")
    def test_secure_connection_uses_hostname_aware_tls_context(
            self, mock_options_for_client_tls, mock_connect_ws, mock_reactor):
        context = Mock()
        mock_options_for_client_tls.return_value = context
        mock_reactor.running = True
        ticker = KiteTicker(
            "api-key", "access-token",
            root="wss://stream.example.test/socket", reconnect=False)

        ticker.connect()

        mock_options_for_client_tls.assert_called_once_with(
            "stream.example.test")
        mock_connect_ws.assert_called_once_with(
            ticker.factory,
            contextFactory=context,
            timeout=ticker.connect_timeout)

    @patch("kiteconnect.ticker.reactor")
    @patch("kiteconnect.ticker.connectWS")
    @patch("kiteconnect.ticker.ssl.optionsForClientTLS")
    def test_secure_connection_can_explicitly_disable_tls_verification(
            self, mock_options_for_client_tls, mock_connect_ws, mock_reactor):
        mock_reactor.running = True
        ticker = KiteTicker(
            "api-key", "access-token",
            root="wss://stream.example.test/socket", reconnect=False)

        ticker.connect(disable_ssl_verification=True)

        mock_options_for_client_tls.assert_not_called()
        mock_connect_ws.assert_called_once_with(
            ticker.factory,
            contextFactory=None,
            timeout=ticker.connect_timeout)

    @patch("kiteconnect.ticker.reactor")
    @patch("kiteconnect.ticker.connectWS")
    @patch("kiteconnect.ticker.ssl.optionsForClientTLS")
    def test_plain_websocket_does_not_build_tls_context(
            self, mock_options_for_client_tls, mock_connect_ws, mock_reactor):
        mock_reactor.running = True
        ticker = KiteTicker(
            "api-key", "access-token",
            root="ws://stream.example.test/socket", reconnect=False)

        ticker.connect()

        mock_options_for_client_tls.assert_not_called()
        mock_connect_ws.assert_called_once_with(
            ticker.factory,
            contextFactory=None,
            timeout=ticker.connect_timeout)

    def test_autoping(self, protocol):
        protocol.autoPingInterval = 1
        protocol.websocket_protocols = [Mock()]
        protocol.websocket_extensions = []
        protocol._onOpen = lambda: None
        protocol._wskey = '0' * 24
        protocol.peer = Mock()

        # usually provided by the Twisted or asyncio specific
        # subclass, but we're testing the parent here...
        protocol._onConnect = Mock()
        protocol._closeConnection = Mock()

        # set up a connection
        protocol.startHandshake()

        key = protocol.websocket_key + WebSocketProtocol._WS_MAGIC
        protocol.data = (
            b"HTTP/1.1 101 Switching Protocols\x0d\x0a"
            b"Upgrade: websocket\x0d\x0a"
            b"Connection: upgrade\x0d\x0a"
            b"Sec-Websocket-Accept: " + b64encode(sha1(key).digest()) + b"\x0d\x0a\x0d\x0a"
        )
        protocol.processHandshake()

    def test_sendclose(self, protocol):
        protocol.sendClose()

        assert protocol.transport._written is not None
        assert protocol.state == protocol.STATE_CLOSING

    def test_sendMessage(self, protocol):
        assert protocol.state == protocol.STATE_OPEN

        protocol.sendMessage(six.b(json.dumps({"message": "blah"})))
