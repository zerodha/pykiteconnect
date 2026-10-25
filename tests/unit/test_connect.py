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
def test_market_protection(kiteconnect):
    """Test place order with market protection."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.place"].format(variety="regular")),
        body=utils.get_response("order.place"),
        content_type="application/json"
    )

    order_id = kiteconnect.place_order(
        variety="regular",
        exchange="NSE",
        tradingsymbol="INFY",
        transaction_type="BUY",
        quantity=1,
        product="CNC",
        order_type="MARKET",
        market_protection=kiteconnect.MARKET_PROTECTION_AUTO,
    )
    assert order_id == "151220000000000"


@responses.activate
def test_place_order_algo_id(kiteconnect):
    """Test place order with algo_id."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.place"].format(variety="regular")),
        body=utils.get_response("order.place"),
        content_type="application/json"
    )

    order_id = kiteconnect.place_order(
        variety="regular",
        exchange="NSE",
        tradingsymbol="INFY",
        transaction_type="BUY",
        quantity=1,
        product="CNC",
        order_type="MARKET",
        algo_id="algo-123",
        tag="tag-123",
    )

    request_body = responses.calls[0].request.body
    if not isinstance(request_body, str):
        request_body = request_body.decode("utf-8")

    assert "algo_id=algo-123" in request_body
    assert "tag=tag-123" in request_body
    assert order_id == "151220000000000"


@responses.activate
def test_place_autoslice_order(kiteconnect):
    """Test place_autoslice_order returns the parent order id and children list."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.place"].format(variety="regular")),
        body=utils.get_response("order.place.autoslice"),
        content_type="application/json"
    )

    order_response = kiteconnect.place_autoslice_order(
        variety="regular",
        exchange="NSE",
        tradingsymbol="INFY",
        transaction_type="BUY",
        quantity=100000,
        product="CNC",
        order_type="MARKET",
        algo_id="algo-123",
    )

    request_body = responses.calls[0].request.body
    if not isinstance(request_body, str):
        request_body = request_body.decode("utf-8")

    assert "autoslice=true" in request_body
    assert "algo_id=algo-123" in request_body
    assert type(order_response) == dict
    assert order_response["order_id"] == "1914227164488687616"
    assert any("order_id" in c for c in order_response["children"])
    assert any(
        c.get("error", {}).get("error_type") == "MarginException"
        for c in order_response["children"]
    )


@responses.activate
def test_modify_order_market_protection(kiteconnect):
    """Test modify order with market protection."""
    responses.add(
        responses.PUT,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.modify"].format(variety="regular", order_id="151220000000000")),
        body=utils.get_response("order.modify"),
        content_type="application/json"
    )

    order_id = kiteconnect.modify_order(
        variety="regular",
        order_id="151220000000000",
        order_type="MARKET",
        market_protection=kiteconnect.MARKET_PROTECTION_AUTO,
    )
    assert order_id == "151220000000000"


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

@responses.activate
def test_virtual_contract_note(kiteconnect):
    """ Test virtual contract note charges """
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["order.contract_note"]),
        body=utils.get_response("order.contract_note"),
        content_type="application/json"
    )

    order_book_params = [{
        "order_id": "111111111",
        "exchange": "NSE",
        "tradingsymbol": "SBIN",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "CNC",
        "order_type": "MARKET",
        "quantity": 1,
        "average_price": 560
    },
	{
        "order_id": "2222222222",
        "exchange": "MCX",
        "tradingsymbol": "GOLDPETAL23JULFUT",
        "transaction_type": "SELL",
        "variety": "regular",
        "product": "NRML",
        "order_type": "LIMIT",
        "quantity": 1,
        "average_price": 5862
    },
	{
        "order_id": "3333333333",
        "exchange": "NFO",
        "tradingsymbol": "NIFTY2371317900PE",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "NRML",
        "order_type": "LIMIT",
        "quantity": 100,
        "average_price": 1.5
    }]

    order_book_charges = kiteconnect.get_virtual_contract_note(order_book_params)
    # Order charges
    assert order_book_charges[0]['charges']['transaction_tax_type'] == "stt"
    assert order_book_charges[0]['charges']['total'] != 0
    # CTT tax type
    assert order_book_charges[1]['charges']['transaction_tax_type'] == "ctt"


@responses.activate
def test_quote(kiteconnect):
    """Test market quote for instruments."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["market.quote"]),
        body=utils.get_response("market.quote"),
        content_type="application/json"
    )
    quote = kiteconnect.quote("NSE:INFY")
    assert type(quote) == dict
    assert "NSE:INFY" in quote
    assert "last_price" in quote["NSE:INFY"]
    assert quote["NSE:INFY"]["last_price"] == 1412.95


@responses.activate
def test_ohlc(kiteconnect):
    """Test OHLC snapshot for instruments."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["market.quote.ohlc"]),
        body=utils.get_response("market.quote.ohlc"),
        content_type="application/json"
    )
    ohlc = kiteconnect.ohlc("NSE:INFY")
    assert type(ohlc) == dict
    assert "NSE:INFY" in ohlc
    assert "ohlc" in ohlc["NSE:INFY"]
    assert ohlc["NSE:INFY"]["last_price"] == 1075


@responses.activate
def test_ltp(kiteconnect):
    """Test last traded price for instruments."""
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["market.quote.ltp"]),
        body=utils.get_response("market.quote.ltp"),
        content_type="application/json"
    )
    ltp = kiteconnect.ltp("NSE:INFY")
    assert type(ltp) == dict
    assert "NSE:INFY" in ltp
    assert ltp["NSE:INFY"]["last_price"] == 1074.35


@responses.activate
def test_historical_data(kiteconnect):
    """Test historical candle data retrieval."""
    url = kiteconnect._routes["market.historical"].format(
        instrument_token=408065, interval="minute"
    )
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("market.historical"),
        content_type="application/json"
    )
    candles = kiteconnect.historical_data(
        instrument_token=408065,
        from_date="2017-12-15 09:15:00",
        to_date="2017-12-15 09:20:00",
        interval="minute"
    )
    assert type(candles) == list
    assert len(candles) > 0
    assert "date" in candles[0]
    assert "open" in candles[0]
    assert "high" in candles[0]
    assert "low" in candles[0]
    assert "close" in candles[0]
    assert "volume" in candles[0]
    assert candles[0]["open"] == 1704.5


@responses.activate
def test_trigger_range(kiteconnect):
    """Test trigger range for cover orders."""
    url = kiteconnect._routes["market.trigger_range"].format(
        transaction_type="buy"
    )
    responses.add(
        responses.GET,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("market.trigger_range"),
        content_type="application/json"
    )
    trigger = kiteconnect.trigger_range(
        kiteconnect.TRANSACTION_TYPE_BUY, "NSE:INFY", "NSE:RELIANCE"
    )
    assert type(trigger) == dict
    assert "NSE:INFY" in trigger
    assert "lower" in trigger["NSE:INFY"]
    assert "upper" in trigger["NSE:INFY"]


@responses.activate
def test_convert_position(kiteconnect):
    """Test position product type conversion."""
    responses.add(
        responses.PUT,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.positions.convert"]),
        body=utils.get_response("portfolio.positions.convert"),
        content_type="application/json"
    )
    result = kiteconnect.convert_position(
        exchange=kiteconnect.EXCHANGE_NSE,
        tradingsymbol="INFY",
        transaction_type=kiteconnect.TRANSACTION_TYPE_BUY,
        position_type=kiteconnect.POSITION_TYPE_DAY,
        quantity=1,
        old_product=kiteconnect.PRODUCT_MIS,
        new_product=kiteconnect.PRODUCT_CNC
    )
    assert result is True


@responses.activate
def test_place_mf_order(kiteconnect):
    """Test placing a mutual fund order."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.order.place"]),
        body=utils.get_response("mf.order.place"),
        content_type="application/json"
    )
    order = kiteconnect.place_mf_order(
        tradingsymbol="INF090I01239",
        transaction_type=kiteconnect.TRANSACTION_TYPE_BUY,
        amount=5000
    )
    assert type(order) == dict
    assert "order_id" in order
    assert order["order_id"] == "3bb085d1-5038-450e-a807-6543fef6c9ae"


@responses.activate
def test_cancel_mf_order(kiteconnect):
    """Test cancelling a mutual fund order."""
    url = kiteconnect._routes["mf.order.cancel"].format(order_id="3bb085d1-5038-450e-a807-6543fef6c9ae")
    responses.add(
        responses.DELETE,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("mf.order.cancel"),
        content_type="application/json"
    )
    result = kiteconnect.cancel_mf_order(order_id="3bb085d1-5038-450e-a807-6543fef6c9ae")
    assert type(result) == dict
    assert result["order_id"] == "3bb085d1-5038-450e-a807-6543fef6c9ae"


@responses.activate
def test_place_mf_sip(kiteconnect):
    """Test placing a mutual fund SIP."""
    responses.add(
        responses.POST,
        "{0}{1}".format(kiteconnect.root, kiteconnect._routes["mf.sip.place"]),
        body=utils.get_response("mf.sip.place"),
        content_type="application/json"
    )
    sip = kiteconnect.place_mf_sip(
        tradingsymbol="INF090I01239",
        amount=1000,
        instalments=12,
        frequency="monthly"
    )
    assert type(sip) == dict
    assert "sip_id" in sip
    assert sip["sip_id"] == "986124545877922"


@responses.activate
def test_modify_mf_sip(kiteconnect):
    """Test modifying a mutual fund SIP."""
    url = kiteconnect._routes["mf.sip.modify"].format(sip_id="986124545877922")
    responses.add(
        responses.PUT,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("mf.sip.modify"),
        content_type="application/json"
    )
    result = kiteconnect.modify_mf_sip(
        sip_id="986124545877922",
        amount=2000,
        instalments=6
    )
    assert type(result) == dict
    assert result["sip_id"] == "986124545877922"


@responses.activate
def test_cancel_mf_sip(kiteconnect):
    """Test cancelling a mutual fund SIP."""
    url = kiteconnect._routes["mf.sip.cancel"].format(sip_id="986124545877922")
    responses.add(
        responses.DELETE,
        "{0}{1}".format(kiteconnect.root, url),
        body=utils.get_response("mf.sip.cancel"),
        content_type="application/json"
    )
    result = kiteconnect.cancel_mf_sip(sip_id="986124545877922")
    assert type(result) == dict
    assert result["sip_id"] == "986124545877922"
