# coding: utf-8
import os
import json

# Mock responses path
responses_path = {
    "base": "../mock_responses/",
    "user.profile": "profile.json",
    "user.margins": "margins.json",
    "user.margins.segment": "margins.json",

    "orders": "orders.json",
    "trades": "trades.json",
    "order.info": "order_info.json",
    "order.trades": "order_trades.json",

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
    "market.historical": "historical_minute.json",
    "market.trigger_range": "trigger_range.json",

    "market.quote": "quote.json",
    "market.quote.ohlc": "ohlc.json",
    "market.quote.ltp": "ltp.json"
}


def full_path(rel_path):
    """return the full path of given rel_path."""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            rel_path
        )
    )


def get_response(key):
    """Get mock response based on route."""
    path = full_path(responses_path["base"] + responses_path[key])
    return open(path, "r").read()


def get_json_response(key):
    """Get json mock response based on route."""
    return json.loads(get_response(key))


def assert_responses(inp, sample):
    """Check if all keys given as a list is there in input."""
    # Type check only if its a list or dict
    # Issue with checking all types are a float value can be inferred as int and
    # in some responses it will None instrad of empty string
    if type(sample) in [list, dict]:
        assert type(inp) == type(sample)

    # If its a list then just check the first element if its available
    if type(inp) == list and len(inp) > 0:
        assert_responses(inp[0], sample[0])

    # If its a dict then iterate individual keys to test
    if type(sample) == dict:
        for key in sample.keys():
            assert_responses(inp[key], sample[key])


def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z
