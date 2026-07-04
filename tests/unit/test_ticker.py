# coding: utf-8
"""Ticker tests"""
import six
import json
import struct
from datetime import datetime
from mock import Mock
from base64 import b64encode
from hashlib import sha1

from autobahn.websocket.protocol import WebSocketProtocol


# Instrument tokens whose least-significant byte selects the exchange segment
# (segment = token & 0xff). 1 -> a tradable segment with a 100 divisor,
# 3 -> currency (cds, 1e7 divisor), 9 -> indices (not tradable).
NSE_TOKEN = (408065 << 8) | 1
CDS_TOKEN = (100 << 8) | 3
INDEX_TOKEN = (256 << 8) | 9


def _frame(*packets):
    """Wrap raw tick packets in the binary envelope used on the wire.

    Layout: ``<number of packets: H>`` then, per packet,
    ``<packet length: H><packet bytes>``.
    """
    out = struct.pack(">H", len(packets))
    for packet in packets:
        out += struct.pack(">H", len(packet)) + packet
    return out


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


class TestParseBinary:
    """Tests for the binary market-data parsing helpers of KiteTicker."""

    def test_unpack_int_default_and_short(self, kiteticker):
        assert kiteticker._unpack_int(struct.pack(">I", 258), 0, 4) == 258
        assert kiteticker._unpack_int(struct.pack(">H", 7), 0, 2, byte_format="H") == 7

    def test_split_packets_ignores_heartbeat(self, kiteticker):
        # A payload shorter than two bytes is a heartbeat and yields no packets.
        assert kiteticker._split_packets(b"\x00") == []

    def test_split_packets_returns_each_packet(self, kiteticker):
        a = struct.pack(">II", NSE_TOKEN, 15000)
        b = struct.pack(">7I", INDEX_TOKEN, 15000, 160, 140, 150, 145, 0)
        packets = kiteticker._split_packets(_frame(a, b))
        assert [len(p) for p in packets] == [8, 28]

    def test_parse_empty_payload(self, kiteticker):
        assert kiteticker._parse_binary(b"\x00") == []

    def test_parse_ltp(self, kiteticker):
        packet = struct.pack(">II", NSE_TOKEN, 15000)
        assert kiteticker._parse_binary(_frame(packet)) == [
            {
                "tradable": True,
                "mode": "ltp",
                "instrument_token": NSE_TOKEN,
                "last_price": 150.0,
            }
        ]

    def test_parse_ltp_applies_currency_divisor(self, kiteticker):
        # Currency (cds) segment uses a 1e7 divisor.
        packet = struct.pack(">II", CDS_TOKEN, 15000)
        (tick,) = kiteticker._parse_binary(_frame(packet))
        assert tick["last_price"] == 0.0015

    def test_parse_index_quote_is_not_tradable(self, kiteticker):
        packet = struct.pack(">7I", INDEX_TOKEN, 15000, 160, 140, 150, 145, 0)
        (tick,) = kiteticker._parse_binary(_frame(packet))
        assert tick["tradable"] is False
        assert tick["mode"] == "quote"
        assert tick["last_price"] == 150.0
        assert tick["ohlc"] == {"high": 1.6, "low": 1.4, "open": 1.5, "close": 1.45}

    def test_parse_index_full_has_exchange_timestamp(self, kiteticker):
        packet = struct.pack(">8I", INDEX_TOKEN, 15000, 160, 140, 150, 145, 0, 1609459200)
        (tick,) = kiteticker._parse_binary(_frame(packet))
        assert tick["mode"] == "full"
        assert isinstance(tick["exchange_timestamp"], datetime)

    def test_parse_quote(self, kiteticker):
        packet = struct.pack(
            ">11I", NSE_TOKEN, 15000, 10, 14900, 5000, 100, 200, 150, 160, 140, 145
        )
        (tick,) = kiteticker._parse_binary(_frame(packet))
        assert tick["mode"] == "quote"
        assert tick["last_traded_quantity"] == 10
        assert tick["average_traded_price"] == 149.0
        assert tick["volume_traded"] == 5000
        assert tick["total_buy_quantity"] == 100
        assert tick["total_sell_quantity"] == 200
        assert "depth" not in tick

    def test_parse_full_with_market_depth(self, kiteticker):
        head = struct.pack(
            ">11I", NSE_TOKEN, 15000, 10, 14900, 5000, 100, 200, 150, 160, 140, 145
        )
        extra = struct.pack(">5I", 1609459200, 12345, 500, 100, 1609459200)
        depth = b""
        for i in range(10):
            depth += struct.pack(">IIH", (i + 1) * 10, 15000 + i, i + 1) + b"\x00\x00"

        (tick,) = kiteticker._parse_binary(_frame(head + extra + depth))
        assert tick["mode"] == "full"
        assert tick["oi"] == 12345
        assert tick["oi_day_high"] == 500
        assert tick["oi_day_low"] == 100
        assert isinstance(tick["exchange_timestamp"], datetime)
        assert len(tick["depth"]["buy"]) == 5
        assert len(tick["depth"]["sell"]) == 5
        assert tick["depth"]["buy"][0] == {"quantity": 10, "price": 150.0, "orders": 1}
        assert tick["depth"]["sell"][0] == {"quantity": 60, "price": 150.05, "orders": 6}

    def test_parse_multiple_packets_in_one_payload(self, kiteticker):
        ltp = struct.pack(">II", NSE_TOKEN, 15000)
        index = struct.pack(">7I", INDEX_TOKEN, 15000, 160, 140, 150, 145, 0)
        ticks = kiteticker._parse_binary(_frame(ltp, index))
        assert [t["mode"] for t in ticks] == ["ltp", "quote"]
