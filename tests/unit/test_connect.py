# coding: utf-8
import responses
import pytest
import kiteconnect.exceptions as ex

from .conftest import fp


def test_set_access_token(kiteconnect):
    """Check for token exception when invalid token is set."""
    kiteconnect.root = "https://api.kite.trade"
    kiteconnect.set_access_token("invalid_token")
    with pytest.raises(ex.TokenException):
        kiteconnect.positions()


@responses.activate
def test_positions(kiteconnect):
    """Test positions."""
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
        body=open(fp("responses/positions.json"), "r").read(),
        content_type="application/json"
    )
    positions = kiteconnect.positions()
    assert type(positions) == dict
    assert "day" in positions
    assert "net" in positions


@responses.activate
def test_holdings(kiteconnect):
    """Test holdings."""
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["portfolio.holdings"]),
        body=open(fp("responses/holdings.json"), "r").read(),
        content_type="application/json"
    )
    holdings = kiteconnect.holdings()
    assert type(holdings) == list


@responses.activate
def test_margins(kiteconnect):
    """Test margins."""
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["user.margins"]),
        body=open(fp("responses/margins.json"), "r").read(),
        content_type="application/json"
    )
    margins = kiteconnect.margins()
    assert type(margins) == dict
    assert kiteconnect.MARGIN_EQUITY in margins
    assert kiteconnect.MARGIN_COMMODITY in margins


@responses.activate
def test_margins_segmentwise(kiteconnect):
    """Test margins for individual segments."""
    responses.add(
        responses.GET,
        "%s%s" % (
            kiteconnect.root,
            kiteconnect._routes["user.margins.segment"].format(
                segment=kiteconnect.MARGIN_COMMODITY
            )
        ),
        body=open(fp("responses/margins.json"), "r").read(),
        content_type="application/json"
    )
    commodity = kiteconnect.margins(segment=kiteconnect.MARGIN_COMMODITY)
    assert type(commodity) == dict


@responses.activate
def test_orders(kiteconnect):
    """Test orders."""
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["orders"]),
        body=open(fp("responses/orders.json"), "r").read(),
        content_type="application/json"
    )
    orders = kiteconnect.orders()
    assert type(orders) == list


@responses.activate
def test_trades(kiteconnect):
    """Test trades."""
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["trades"]),
        body=open(fp("responses/trades.json"), "r").read(),
        content_type="application/json"
    )
    trades = kiteconnect.trades()
    assert type(trades) == list
