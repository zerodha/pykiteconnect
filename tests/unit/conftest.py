# coding: utf-8

"""Pytest config."""
import os
import sys
import pytest
from kiteconnect import KiteConnect, KiteTicker

sys.path.append(os.path.join(os.path.dirname(__file__), '../helpers'))


@pytest.fixture()
def kiteconnect():
    """Init Kite connect object."""
    kiteconnect = KiteConnect(api_key='<API-KEY>', access_token='<ACCESS-TOKEN>')
    kiteconnect.root = 'http://kite_trade_test'
    return kiteconnect


@pytest.fixture()
def kiteconnect_with_pooling():
    """Init kite connect object with pooling."""
    kiteconnect = KiteConnect(
        api_key="<API-KEY>",
        access_token="<ACCESS-TOKEN>",
        pool={
            "pool_connections": 20,
            "pool_maxsize": 10,
            "max_retries": 2,
            "pool_block": False
        }
    )
    return kiteconnect


@pytest.fixture()
def kiteticker():
    """Init Kite ticker object."""
    kws = KiteTicker("<API-KEY>", "<PUB-TOKEN>", "<USER-ID>", debug=True, reconnect=False)
    kws.socket_url = "ws://127.0.0.1:9000?api_key=<API-KEY>?&user_id=<USER-ID>&public_token=<PUBLIC-TOKEN>"
    return kws


@pytest.fixture()
def protocol():
    from autobahn.test import FakeTransport
    from kiteconnect.ticker import KiteTickerClientProtocol,\
        KiteTickerClientFactory

    t = FakeTransport()
    f = KiteTickerClientFactory()
    p = KiteTickerClientProtocol()
    p.factory = f
    p.transport = t

    p._connectionMade()
    p.state = p.STATE_OPEN
    p.websocket_version = 18
    return p
