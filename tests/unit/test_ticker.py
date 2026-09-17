# coding: utf-8
"""Ticker tests"""
import six
import json
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

    def test_loop_ping_sends_ping(self, protocol):
        protocol.sendPing = Mock()
        protocol._loop_ping()

        assert protocol.sendPing.called
        assert protocol._last_ping_time is not None

    def test_loop_pong_check_drops_on_timeout(self, protocol):
        import time
        protocol.dropConnection = Mock()
        # Simulate last pong received 10 seconds ago (exceeding 2 * PING_INTERVAL = 5.0s)
        protocol._last_pong_time = time.time() - 10
        protocol._loop_pong_check()

        assert protocol.dropConnection.called

    def test_loop_pong_check_healthy(self, protocol):
        import time
        protocol.dropConnection = Mock()
        # Simulate recent pong (healthy)
        protocol._last_pong_time = time.time() - 1
        protocol._loop_pong_check()

        assert not protocol.dropConnection.called

    def test_onOpen_initializes_ping_and_pong(self, protocol):
        protocol.sendPing = Mock()
        protocol.onOpen()

        assert protocol._last_pong_time is not None
        assert protocol.sendPing.called
