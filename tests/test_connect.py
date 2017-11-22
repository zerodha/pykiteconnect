# coding: utf-8

import pytest
import kiteconnect.exceptions as ex


def test_set_access_token(kiteconnect):
    """Check for token exception when invalid token is set."""
    kiteconnect.set_access_token("invalid_token")
    with pytest.raises(ex.TokenException):
        kiteconnect.positions()


def test_positions(kiteconnect):
    """Test positions."""
    positions = kiteconnect.positions()
    assert type(positions) == dict
    assert "day" in positions
    assert "net" in positions


def test_holdings(kiteconnect):
    """Test holdiogs."""
    holdings = kiteconnect.holdings()
    assert type(holdings) == list


def test_margins(kiteconnect):
    """Test holdiogs."""
    margins = kiteconnect.margins()
    assert type(margins) == dict
    assert kiteconnect.MARGIN_EQUITY in margins
    assert kiteconnect.MARGIN_COMMODITY in margins


def test_margins_segmentwise(kiteconnect):
    """Test margins for individual segments."""
    commodity = kiteconnect.margins(segment=kiteconnect.MARGIN_COMMODITY)
    assert type(commodity) == dict


def test_orders(kiteconnect):
    """Test holdiogs."""
    orders = kiteconnect.orders()
    assert type(orders) == list


def test_order_get(kiteconnect):
    """Test holdiogs."""
    orders = kiteconnect.orders()
    assert type(orders) == list


def test_trades(kiteconnect):
    """Test holdiogs."""
    trades = kiteconnect.trades()
    assert type(trades) == list
