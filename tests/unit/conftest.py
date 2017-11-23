# coding: utf-8

"""Pytest config."""
import os
import pytest
import responses
from kiteconnect import KiteConnect


def fp(rel_path):
    "return the full path of given rel_path"
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            rel_path
        )
    )


@pytest.fixture()
def kiteconnect():
    """Init Kite connect object."""
    kiteconnect = KiteConnect(api_key='<API-KEY>', access_token='<ACCESS-TOKEN>')
    kiteconnect.root = 'http://kite_trade_test'
    return kiteconnect
