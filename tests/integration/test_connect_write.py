# coding: utf-8

import pytest
import utils
import warnings
import kiteconnect.exceptions as ex

params = {
    "tradingsymbol": "RELIANCE",
    "exchange": "NSE",
    "transaction_type": "BUY",
    "quantity": 1
}


# Order place tests
#####################

def test_place_order_market_regular(kiteconnect):
    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": kiteconnect.VARIETY_REGULAR,
        "order_type": kiteconnect.ORDER_TYPE_MARKET
    })

    order_id = kiteconnect.place_order(**updated_params)
    order = kiteconnect.orders(order_id)
    assert order[-1]["order_type"] == kiteconnect.ORDER_TYPE_MARKET
    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR


def test_place_order_limit_regular(kiteconnect):
    symbol = params["exchange"] + ":" + params["tradingsymbol"]
    ltp = kiteconnect.ltp(symbol)

    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": kiteconnect.VARIETY_REGULAR,
        "order_type": kiteconnect.ORDER_TYPE_LIMIT
    })

    # NOT WORKING CURRENTLY
    # Raises exception since no price set
    # with pytest.raises(ex.InputException):
    #     kiteconnect.place_order(**updated_params)

    diff = ltp[symbol]["last_price"] * 0.01
    updated_params["price"] = ltp[symbol]["last_price"] - (diff - (diff % 0.05))
    order_id = kiteconnect.place_order(**updated_params)
    order = kiteconnect.orders(order_id)
    assert order[-1]["order_type"] == kiteconnect.ORDER_TYPE_LIMIT
    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR


def test_place_order_sl_regular(kiteconnect):
    symbol = params["exchange"] + ":" + params["tradingsymbol"]
    ltp = kiteconnect.ltp(symbol)

    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": kiteconnect.VARIETY_REGULAR,
        "order_type": kiteconnect.ORDER_TYPE_SL
    })

    # NOT WORKING CURRENTLY
    # Raises exception since no price set
    # with pytest.raises(ex.InputException):
    #     kiteconnect.place_order(**updated_params)

    diff = ltp[symbol]["last_price"] * 0.01
    updated_params["price"] = ltp[symbol]["last_price"] - (diff - (diff % 0.05))
    updated_params["trigger_price"] = updated_params["price"] - 1
    order_id = kiteconnect.place_order(**updated_params)
    order = kiteconnect.orders(order_id)
    assert order[-1]["order_type"] == kiteconnect.ORDER_TYPE_SL
    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR


def test_place_order_slm_regular(kiteconnect):
    symbol = params["exchange"] + ":" + params["tradingsymbol"]
    ltp = kiteconnect.ltp(symbol)

    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": kiteconnect.VARIETY_REGULAR,
        "order_type": kiteconnect.ORDER_TYPE_SLM
    })

    # NOT WORKING CURRENTLY
    # Raises exception since no price set
    # with pytest.raises(ex.InputException):
    #     kiteconnect.place_order(**updated_params)

    diff = ltp[symbol]["last_price"] * 0.01
    updated_params["trigger_price"] = ltp[symbol]["last_price"] - (diff - (diff % 0.05))
    order_id = kiteconnect.place_order(**updated_params)
    order = kiteconnect.orders(order_id)
    assert order[-1]["order_type"] == kiteconnect.ORDER_TYPE_SLM
    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR


def test_place_order_tag(kiteconnect):
    """Send custom tag and get it in orders."""
    tag = "mytag"
    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": kiteconnect.VARIETY_REGULAR,
        "order_type": kiteconnect.ORDER_TYPE_MARKET,
        "tag": tag
    })

    order_id = kiteconnect.place_order(**updated_params)
    order_info = kiteconnect.orders(order_id=order_id)
    assert order_info[0]["tag"] == tag


# Order modify and cancel tests
################################

def setup_order_modify_cancel(kiteconnect, variety):
    symbol = params["exchange"] + ":" + params["tradingsymbol"]
    ltp = kiteconnect.ltp(symbol)

    updated_params = utils.merge_dicts(params, {
        "product": kiteconnect.PRODUCT_MIS,
        "variety": variety,
        "order_type": kiteconnect.ORDER_TYPE_LIMIT
    })

    diff = ltp[symbol]["last_price"] * 0.01
    updated_params["price"] = ltp[symbol]["last_price"] - (diff - (diff % 0.05))
    order_id = kiteconnect.place_order(**updated_params)

    order = kiteconnect.orders(order_id)
    status = order[-1]["status"].upper()
    if "OPEN" not in status:
        warnings.warn(UserWarning("Order is not open with status: ", status))
        return

    return (updated_params, order_id, order)


def test_order_cancel_regular(kiteconnect):
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_REGULAR)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    returned_order_id = kiteconnect.cancel_order(order_id, updated_params["variety"])
    assert returned_order_id == order_id

    order = kiteconnect.orders(order_id)
    status = order[-1]["status"].upper()
    assert "CANCELLED" in status


def test_order_cancel_amo(kiteconnect):
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_AMO)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    returned_order_id = kiteconnect.cancel_order(order_id, updated_params["variety"])
    assert returned_order_id == order_id

    order = kiteconnect.orders(order_id)
    status = order[-1]["status"].upper()
    assert "CANCELLED" in status


def test_order_modify_limit_regular(kiteconnect):
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_REGULAR)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    assert order[-1]["quantity"] == updated_params["quantity"]
    assert order[-1]["price"] == updated_params["price"]

    to_quantity = 2
    to_price = updated_params["price"] - 1
    kiteconnect.modify_order(order_id, updated_params["variety"], quantity=to_quantity, price=to_price)

    order = kiteconnect.orders(order_id)
    assert order[-1]["quantity"] == to_quantity
    assert order[-1]["price"] == to_price


def test_order_modify_limit_amo(kiteconnect):
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_AMO)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    assert order[-1]["quantity"] == updated_params["quantity"]
    assert order[-1]["price"] == updated_params["price"]

    to_quantity = 2
    to_price = updated_params["price"] - 1
    kiteconnect.modify_order(order_id, updated_params["variety"], quantity=to_quantity, price=to_price)

    order = kiteconnect.orders(order_id)
    assert order[-1]["quantity"] == to_quantity
    assert order[-1]["price"] == to_price
