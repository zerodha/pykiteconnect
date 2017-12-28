# coding: utf-8
import os

# Mock responses path
responses_path = {
    "base": "../mock_responses/",
    "user.margins": "margins.json",
    "user.margins.segment": "margins.json",

    "orders": "orders.json",
    "trades": "trades.json",
    "order.info": "order_info.json",
    "order.trades": "",

    "portfolio.positions": "positions.json",
    "portfolio.holdings": "holdings.json",

    # MF api endpoints
    "mf.orders": "mf_orders.json",
    "mf.order.info": "mf_orders_info.json",

    "mf.sips": "mf_sips.json",
    "mf.sip.info": "mf_sip_info.json",

    "mf.holdings": "mf_holdings.json",
    "mf.instruments": "mf_instruments.csv",

    "market.instruments": "instruments_nse.csv",
    "market.instruments.all": "instruments_all.csv",
    "market.historical": "",
    "market.trigger_range": "",

    "market.quote": "",
    "market.quote.ohlc": "",
    "market.quote.ltp": ""
}


def full_path(rel_path):
    """return the full path of given rel_path"""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            rel_path
        )
    )


def get_response(key):
    """Get mock response based on route"""
    path = full_path(responses_path["base"] + responses_path[key])
    return open(path, "r").read()


def assert_dict_keys(inp, keys):
    """Check if all keys given as a list is there in input"""
    for k in keys:
        assert k in inp
