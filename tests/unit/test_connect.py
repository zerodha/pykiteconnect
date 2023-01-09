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
def test_auction_instruments(kiteconnect):
    """Test get_auction_instruments."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.holdings.auction"]),
        body=utils.get_response("portfolio.holdings.auction"),
        content_type="application/json"
    )
    auction_inst = kiteconnect.get_auction_instruments()
    assert type(auction_inst) == list


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


@responses.activate
def test_get_gtts(kiteconnect):
    """Test all gtts fetch."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["gtt"]),
        body=utils.get_response("gtt"),
        content_type="application/json"
    )
    gtts = kiteconnect.get_gtts()
    assert type(gtts) == list


@responses.activate
def test_get_gtt(kiteconnect):
    """Test single gtt fetch."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["gtt.info"].format(trigger_id=123)),
        body=utils.get_response("gtt.info"),
        content_type="application/json"
    )
    gtts = kiteconnect.get_gtt(123)
    print(gtts)
    assert gtts["id"] == 123


@responses.activate
def test_place_gtt(kiteconnect):
    """Test place gtt order."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["gtt.place"]),
        body=utils.get_response("gtt.place"),
        content_type="application/json"
    )
    gtts = kiteconnect.place_gtt(
        trigger_type=kiteconnect.GTT_TYPE_SINGLE,
        tradingsymbol="INFY",
        exchange="NSE",
        trigger_values=[1],
        last_price=800,
        orders=[{
            "transaction_type": kiteconnect.TRANSACTION_TYPE_BUY,
            "quantity": 1,
            "order_type": kiteconnect.ORDER_TYPE_LIMIT,
            "product": kiteconnect.PRODUCT_CNC,
            "price": 1,
        }]
    )
    assert gtts["trigger_id"] == 123


@responses.activate
def test_modify_gtt(kiteconnect):
    """Test modify gtt order."""
    responses.add(
        responses.PUT,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["gtt.modify"].format(trigger_id=123)),
        body=utils.get_response("gtt.modify"),
        content_type="application/json"
    )
    gtts = kiteconnect.modify_gtt(
        trigger_id=123,
        trigger_type=kiteconnect.GTT_TYPE_SINGLE,
        tradingsymbol="INFY",
        exchange="NSE",
        trigger_values=[1],
        last_price=800,
        orders=[{
            "transaction_type": kiteconnect.TRANSACTION_TYPE_BUY,
            "quantity": 1,
            "order_type": kiteconnect.ORDER_TYPE_LIMIT,
            "product": kiteconnect.PRODUCT_CNC,
            "price": 1,
        }]
    )
    assert gtts["trigger_id"] == 123


@responses.activate
def test_delete_gtt(kiteconnect):
    """Test delete gtt order."""
    responses.add(
        responses.DELETE,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["gtt.delete"].format(trigger_id=123)),
        body=utils.get_response("gtt.delete"),
        content_type="application/json"
    )
    gtts = kiteconnect.delete_gtt(123)
    assert gtts["trigger_id"] == 123


@responses.activate
def test_order_margins(kiteconnect):
    """ Test order margins and charges """
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.margins"]),
        body=utils.get_response("order.margins"),
        content_type="application/json"
    )
    order_param_single = [{
        "exchange": "NSE",
        "tradingsymbol": "INFY",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 2
    }]

    margin_detail = kiteconnect.order_margins(order_param_single)
    # Order margins
    assert margin_detail[0]['type'] == "equity"
    assert margin_detail[0]['total'] != 0
    # Order charges
    assert margin_detail[0]['charges']['transaction_tax'] != 0
    assert margin_detail[0]['charges']['gst']['total'] != 0


@responses.activate
def test_basket_order_margins(kiteconnect):
    """ Test basket order margins and charges """
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.margins.basket"]),
        body=utils.get_response("order.margins.basket"),
        content_type="application/json"
    )
    order_param_multi = [{
        "exchange": "NFO",
        "tradingsymbol": "NIFTY23JANFUT",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 75
    },
        {
        "exchange": "NFO",
        "tradingsymbol": "NIFTY23JANFUT",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 75
    }]

    margin_detail = kiteconnect.basket_order_margins(order_param_multi)
    # Order margins
    assert margin_detail['orders'][0]['exposure'] != 0
    assert margin_detail['orders'][0]['type'] == "equity"
    # Order charges
    assert margin_detail['orders'][0]['total'] != 0
