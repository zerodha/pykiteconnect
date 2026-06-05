# coding: utf-8
"""Ticker tests"""
import six
import json
import time
from mock import Mock
from base64 import b64encode
from hashlib import sha1

from autobahn.websocket.protocol import WebSocketProtocol


class TestTicker:

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

    def test_kite_protocol_sends_ping(self, protocol, monkeypatch):
        # Ensure we don't schedule real Twisted delayed calls during unit tests.
        protocol.factory.reactor = Mock()
        protocol.factory.reactor.callLater = Mock(return_value=Mock())

        send_ping = Mock()
        monkeypatch.setattr(protocol, "sendPing", send_ping)

        protocol._loop_ping()

        assert send_ping.call_count == 1
        protocol.factory.reactor.callLater.assert_called_once()

    def test_kite_protocol_drops_on_pong_timeout(self, protocol):
        protocol.factory.reactor = Mock()
        protocol.factory.reactor.callLater = Mock(return_value=Mock())

        protocol._last_pong_time = time.time() - (protocol.PONG_TIMEOUT + 1)
        protocol.dropConnection = Mock()
        protocol.sendClose = Mock()

        protocol._loop_pong_check()

        protocol.sendClose.assert_called_once()
        protocol.dropConnection.assert_called_once()
