# coding: utf-8
import pytest
import responses
import kiteconnect.exceptions as ex

import utils


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
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
        body=utils.get_response("portfolio.positions"),
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
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.holdings"]),
        body=utils.get_response("portfolio.holdings"),
        content_type="application/json"
    )
    holdings = kiteconnect.holdings()
    assert type(holdings) == list


@responses.activate
def test_margins(kiteconnect):
    """Test margins."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["user.margins"]),
        body=utils.get_response("user.margins"),
        content_type="application/json"
    )
    margins = kiteconnect.margins()
    assert type(margins) == dict
    assert kiteconnect.MARGIN_EQUITY in margins
    assert kiteconnect.MARGIN_COMMODITY in margins


@responses.activate
def test_profile(kiteconnect):
    """Test profile."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["user.profile"]),
        body=utils.get_response("user.profile"),
        content_type="application/json"
    )
    profile = kiteconnect.profile()
    assert type(profile) == dict


@responses.activate
def test_margins_segmentwise(kiteconnect):
    """Test margins for individual segments."""
    responses.add(
        responses.GET,
        "{0}{1}".format(
            kiteconnect.root,
            kiteconnect._routes["user.margins.segment"].format(
                segment=kiteconnect.MARGIN_COMMODITY
            )
        ),
        body=utils.get_response("user.margins.segment"),
        content_type="application/json"
    )
    commodity = kiteconnect.margins(segment=kiteconnect.MARGIN_COMMODITY)
    assert type(commodity) == dict


@responses.activate
def test_orders(kiteconnect):
    """Test orders."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["orders"]),
        body=utils.get_response("orders"),
        content_type="application/json"
    )
    orders = kiteconnect.orders()
    assert type(orders) == list


@responses.activate
def test_order_history(kiteconnect):
    """Test mf orders get."""
    url = kiteconnect._routes["order.info"].format(order_id="abc123")
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("order.info"),
        content_type="application/json"
    )
    trades = kiteconnect.order_history(order_id="abc123")
    assert type(trades) == list


@responses.activate
def test_trades(kiteconnect):
    """Test trades."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["trades"]),
        body=utils.get_response("trades"),
        content_type="application/json"
    )
    trades = kiteconnect.trades()
    assert type(trades) == list


@responses.activate
def test_order_trades(kiteconnect):
    """Test order trades."""
    url = kiteconnect._routes["order.trades"].format(order_id="abc123")
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("trades"),
        content_type="application/json"
    )
    trades = kiteconnect.order_trades(order_id="abc123")
    assert type(trades) == list


@responses.activate
def test_instruments(kiteconnect):
    """Test mf instruments fetch."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["market.instruments.all"]),
        body=utils.get_response("market.instruments.all"),
        content_type="text/csv"
    )
    trades = kiteconnect.instruments()
    assert type(trades) == list


@responses.activate
def test_instruments_exchangewise(kiteconnect):
    """Test mf instruments fetch."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root,
                        kiteconnect._routes["market.instruments"].format(exchange=kiteconnect.EXCHANGE_NSE)),
        body=utils.get_response("market.instruments"),
        content_type="text/csv"
    )
    trades = kiteconnect.instruments(exchange=kiteconnect.EXCHANGE_NSE)
    assert type(trades) == list


@responses.activate
def test_mf_orders(kiteconnect):
    """Test mf orders get."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.orders"]),
        body=utils.get_response("mf.orders"),
        content_type="application/json"
    )
    trades = kiteconnect.mf_orders()
    assert type(trades) == list


@responses.activate
def test_mf_individual_order(kiteconnect):
    """Test mf orders get."""
    url = kiteconnect._routes["mf.order.info"].format(order_id="abc123")
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("mf.order.info"),
        content_type="application/json"
    )
    trades = kiteconnect.mf_orders(order_id="abc123")
    assert type(trades) == dict


@responses.activate
def test_mf_sips(kiteconnect):
    """Test mf sips get."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.sips"]),
        body=utils.get_response("mf.sips"),
        content_type="application/json"
    )
    trades = kiteconnect.mf_sips()
    assert type(trades) == list


@responses.activate
def test_mf_individual_sip(kiteconnect):
    """Test mf sips get."""
    url = kiteconnect._routes["mf.sip.info"].format(sip_id="abc123")
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("mf.sip.info"),
        content_type="application/json"
    )
    trades = kiteconnect.mf_sips(sip_id="abc123")
    assert type(trades) == dict


@responses.activate
def test_mf_holdings(kiteconnect):
    """Test mf holdings."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.holdings"]),
        body=utils.get_response("mf.holdings"),
        content_type="application/json"
    )
    trades = kiteconnect.mf_holdings()
    assert type(trades) == list


@responses.activate
def test_mf_instruments(kiteconnect):
    """Test mf instruments fetch."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.instruments"]),
        body=utils.get_response("mf.instruments"),
        content_type="text/csv"
    )
    trades = kiteconnect.mf_instruments()
    assert type(trades) == list
