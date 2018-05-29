# coding: utf-8

import pytest
from mock import Mock
import utils
import time
import datetime
import warnings
import kiteconnect.exceptions as ex


def test_request_pool():
    from kiteconnect import KiteConnect
    pool = {
        "pool_connections": 10,
        "pool_maxsize": 10,
        "max_retries": 0,
        "pool_block": False
    }

    kiteconnect = KiteConnect(api_key="random", access_token="random", pool=pool)

    with pytest.raises(ex.TokenException):
        kiteconnect.orders()


def test_set_access_token(kiteconnect):
    """Check for token exception when invalid token is set."""
    kiteconnect.set_access_token("invalid_token")
    with pytest.raises(ex.TokenException):
        kiteconnect.positions()


def test_set_session_expiry_hook(kiteconnect):
    """Test token exception callback"""
    # check with invalid callback
    with pytest.raises(TypeError):
        kiteconnect.set_session_expiry_hook(123)

    callback = Mock()
    kiteconnect.set_session_expiry_hook(callback)
    kiteconnect.set_access_token("some_invalid_token")
    with pytest.raises(ex.TokenException):
        kiteconnect.orders()
    callback.assert_called_with()


def test_positions(kiteconnect):
    """Test positions."""
    positions = kiteconnect.positions()
    mock_resp = utils.get_json_response("portfolio.positions")["data"]
    utils.assert_responses(positions, mock_resp)


def test_holdings(kiteconnect):
    """Test holdings."""
    holdings = kiteconnect.holdings()
    mock_resp = utils.get_json_response("portfolio.holdings")["data"]
    utils.assert_responses(holdings, mock_resp)


def test_margins(kiteconnect):
    """Test margins."""
    margins = kiteconnect.margins()
    mock_resp = utils.get_json_response("user.margins")["data"]
    utils.assert_responses(margins, mock_resp)


def test_margins_segmentwise(kiteconnect):
    """Test margins for individual segments."""
    commodity = kiteconnect.margins(segment=kiteconnect.MARGIN_COMMODITY)
    assert type(commodity) == dict


def test_orders(kiteconnect):
    """Test orders get."""
    orders = kiteconnect.orders()
    assert type(orders) == list


def test_order_history(kiteconnect):
    """Test individual order get."""
    orders = kiteconnect.orders()

    if len(orders) == 0:
        warnings.warn(UserWarning("Order info: Couldn't perform individual order test since orderbook is empty."))
        return

    order = kiteconnect.order_history(order_id=orders[0]["order_id"])

    mock_resp = utils.get_json_response("order.info")["data"]
    utils.assert_responses(order, mock_resp)

    # check order info statuses order. if its not REJECTED order
    for o in order:
        if "REJECTED" not in o["status"]:
            assert "RECEIVED" in o["status"].upper()
            break

    assert order[-1]["status"] in ["OPEN", "COMPLETE", "REJECTED"]


def test_trades(kiteconnect):
    """Test trades."""
    trades = kiteconnect.trades()
    mock_resp = utils.get_json_response("trades")["data"]
    utils.assert_responses(trades, mock_resp)


def test_order_trades(kiteconnect):
    """Test individual order get."""
    trades = kiteconnect.trades()

    if len(trades) == 0:
        warnings.warn(UserWarning("Trades: Couldn't perform individual order test since trades is empty."))
        return

    order_trades = kiteconnect.order_trades(order_id=trades[0]["order_id"])

    mock_resp = utils.get_json_response("order.trades")["data"]
    utils.assert_responses(order_trades, mock_resp)


def test_all_instruments(kiteconnect):
    """Test mf instruments fetch."""
    instruments = kiteconnect.instruments()
    mock_resp = kiteconnect._parse_instruments(utils.get_response("market.instruments"))
    utils.assert_responses(instruments, mock_resp)


def test_exchange_instruments(kiteconnect):
    """Test mf instruments fetch."""
    instruments = kiteconnect.instruments(exchange=kiteconnect.EXCHANGE_NSE)
    mock_resp = kiteconnect._parse_instruments(utils.get_response("market.instruments"))
    utils.assert_responses(instruments, mock_resp)


def test_mf_orders(kiteconnect):
    """Test mf orders get."""
    mf_orders = kiteconnect.mf_orders()
    mock_resp = utils.get_json_response("mf.orders")["data"]
    utils.assert_responses(mf_orders, mock_resp)


def test_mf_order_info(kiteconnect):
    """Test mf orders get."""
    orders = kiteconnect.mf_orders()

    if len(orders) == 0:
        warnings.warn(UserWarning("MF order info: Couldn't perform individual order test since orderbook is empty."))
        return

    order = kiteconnect.mf_orders(order_id=orders[0]["order_id"])

    mock_resp = utils.get_json_response("mf.order.info")["data"]
    utils.assert_responses(order, mock_resp)


def test_mf_sips(kiteconnect):
    """Test mf sips get."""
    mf_sips = kiteconnect.mf_sips()
    mock_resp = utils.get_json_response("mf.sips")["data"]
    utils.assert_responses(mf_sips, mock_resp)


def test_mf_holdings(kiteconnect):
    """Test mf holdings."""
    mf_holdings = kiteconnect.mf_holdings()
    mock_resp = utils.get_json_response("mf.holdings")["data"]
    utils.assert_responses(mf_holdings, mock_resp)


def test_mf_instruments(kiteconnect):
    """Test mf instruments fetch."""
    mf_instruments = kiteconnect.mf_instruments()
    mock_resp = kiteconnect._parse_mf_instruments(utils.get_response("mf.instruments"))
    utils.assert_responses(mf_instruments, mock_resp)


# Historical API tests
######################

@pytest.mark.parametrize("max_interval,candle_interval", [
    (30, "minute"),
    (365, "hour"),
    (2000, "day"),
    (90, "3minute"),
    (90, "5minute"),
    (90, "10minute"),
    (180, "15minute"),
    (180, "30minute"),
    (365, "60minute")
], ids=[
    "minute",
    "hour",
    "day",
    "3minute",
    "5minute",
    "10minute",
    "15minute",
    "30minute",
    "60minute",
])
def test_historical_data_intervals(max_interval, candle_interval, kiteconnect):
    """Test historical data for each intervals"""
    # Reliance token
    instrument_token = 256265
    to_date = datetime.datetime.now()
    diff = int(max_interval / 3)

    from_date = (to_date - datetime.timedelta(days=diff))

    # minute data
    data = kiteconnect.historical_data(instrument_token, from_date, to_date, candle_interval)
    mock_resp = kiteconnect._format_historical(utils.get_json_response("market.historical")["data"])
    utils.assert_responses(data, mock_resp)

    # Max interval
    from_date = (to_date - datetime.timedelta(days=(max_interval + 1)))
    with pytest.raises(ex.InputException):
        kiteconnect.historical_data(instrument_token, from_date, to_date, candle_interval)


def test_quote(kiteconnect):
    """Test quote."""
    instruments = ["NSE:INFY"]

    # Test sending instruments as a list
    time.sleep(1.1)
    quote = kiteconnect.quote(instruments)
    mock_resp = utils.get_json_response("market.quote")["data"]
    utils.assert_responses(quote, mock_resp)

    # Test sending instruments as args
    time.sleep(1.1)
    quote = kiteconnect.quote(*instruments)
    mock_resp = utils.get_json_response("market.quote")["data"]
    utils.assert_responses(quote, mock_resp)


def test_quote_ohlc(kiteconnect):
    """Test ohlc."""
    instruments = ["NSE:INFY"]

    # Test sending instruments as a list
    time.sleep(1.1)
    ohlc = kiteconnect.ohlc(instruments)
    mock_resp = utils.get_json_response("market.quote.ohlc")["data"]
    utils.assert_responses(ohlc, mock_resp)

    # Test sending instruments as args
    time.sleep(1.1)
    ohlc = kiteconnect.ohlc(*instruments)
    mock_resp = utils.get_json_response("market.quote.ohlc")["data"]
    utils.assert_responses(ohlc, mock_resp)


def test_quote_ltp(kiteconnect):
    """Test ltp."""
    instruments = ["NSE:INFY"]

    # Test sending instruments as a list
    time.sleep(1.1)
    ltp = kiteconnect.ltp(instruments)
    mock_resp = utils.get_json_response("market.quote.ltp")["data"]
    utils.assert_responses(ltp, mock_resp)

    # Test sending instruments as args
    time.sleep(1.1)
    ltp = kiteconnect.ltp(*instruments)
    mock_resp = utils.get_json_response("market.quote.ltp")["data"]
    utils.assert_responses(ltp, mock_resp)


def test_trigger_range(kiteconnect):
    """Test ltp."""
    instruments = ["NSE:INFY", "NSE:RELIANCE"]

    # Test sending instruments as a list
    buy_resp = kiteconnect.trigger_range(kiteconnect.TRANSACTION_TYPE_BUY, *instruments)
    mock_resp = utils.get_json_response("market.trigger_range")["data"]
    utils.assert_responses(buy_resp, mock_resp)

    buy_resp = kiteconnect.trigger_range(kiteconnect.TRANSACTION_TYPE_SELL, *instruments)
    mock_resp = utils.get_json_response("market.trigger_range")["data"]
    utils.assert_responses(buy_resp, mock_resp)

    # Test sending instruments as a args
    buy_resp = kiteconnect.trigger_range(kiteconnect.TRANSACTION_TYPE_BUY, instruments)
    mock_resp = utils.get_json_response("market.trigger_range")["data"]
    utils.assert_responses(buy_resp, mock_resp)

    buy_resp = kiteconnect.trigger_range(kiteconnect.TRANSACTION_TYPE_SELL, instruments)
    mock_resp = utils.get_json_response("market.trigger_range")["data"]
    utils.assert_responses(buy_resp, mock_resp)
