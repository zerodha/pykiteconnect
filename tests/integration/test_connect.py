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
    """Test orders get."""
    orders = kiteconnect.orders()
    assert type(orders) == list


def test_order_get(kiteconnect):
    """Test individual order get."""
    orders = kiteconnect.orders()
    assert type(orders) == list


def test_trades(kiteconnect):
    """Test trades."""
    trades = kiteconnect.trades()
    assert type(trades) == list


def test_mf_orders(kiteconnect):
    """Test mf orders get."""
    trades = kiteconnect.mf_orders()
    assert type(trades) == list


def test_mf_sips(kiteconnect):
    """Test mf sips get."""
    trades = kiteconnect.mf_sips()
    assert type(trades) == list


def test_mf_holdings(kiteconnect):
    """Test mf holdings."""
    trades = kiteconnect.mf_holdings()
    assert type(trades) == list


def test_mf_instruments(kiteconnect):
    """Test mf instruments fetch."""
    trades = kiteconnect.mf_instruments()
    assert type(trades) == list
