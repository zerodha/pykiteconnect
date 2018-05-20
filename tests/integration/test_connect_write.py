# coding: utf-8

# import pytest
import utils
import time
import warnings
# import kiteconnect.exceptions as ex

params = {
    "exchange": "NSE",
    "tradingsymbol": "RELIANCE",
    "transaction_type": "BUY",
    "quantity": 1
}


def is_pending_order(status):
    """Check if the status is pending order status."""
    status = status.upper()
    if ("COMPLETE" in status or "REJECT" in status or "CANCEL" in status):
        return False
    return True


def setup_order_place(kiteconnect,
                      variety,
                      product,
                      order_type,
                      diff_constant=0.01,
                      price_diff=1,
                      bo_price_diff=1,
                      price=None,
                      validity=None,
                      disclosed_quantity=None,
                      trigger_price=None,
                      squareoff=None,
                      stoploss=None,
                      trailing_stoploss=None,
                      tag="itest"):
    """Place an order with custom fields enabled. Prices are calculated from live ltp and offset based
    on `price_diff` and `diff_constant`. All BO specific fields prices are diffed by `bo_price_diff`"""
    updated_params = utils.merge_dicts(params, {
        "product": product,
        "variety": variety,
        "order_type": order_type
    })

    # NOT WORKING CURRENTLY
    # Raises exception since no price set
    # with pytest.raises(ex.InputException):
    #     kiteconnect.place_order(**updated_params)

    if price or trigger_price:
        symbol = params["exchange"] + ":" + params["tradingsymbol"]
        ltp = kiteconnect.ltp(symbol)

        # Subtract last price with diff_constant %
        diff = ltp[symbol]["last_price"] * diff_constant
        round_off_decimal = diff % price_diff if price_diff > 0 else 0
        base_price = ltp[symbol]["last_price"] - (diff - round_off_decimal)

        if price and trigger_price:
            updated_params["price"] = base_price
            updated_params["trigger_price"] = base_price - price_diff
        elif price:
            updated_params["price"] = base_price
        elif trigger_price:
            updated_params["trigger_price"] = base_price

    if stoploss:
        updated_params["stoploss"] = bo_price_diff

    if squareoff:
        updated_params["squareoff"] = bo_price_diff

    if trailing_stoploss:
        updated_params["trailing_stoploss"] = bo_price_diff

    order_id = kiteconnect.place_order(**updated_params)

    # delay order fetch so order is not in received state
    time.sleep(0.5)
    order = kiteconnect.order_history(order_id)

    return (updated_params, order_id, order)


def cleanup_orders(kiteconnect, order_id=None):
    """Cleanup all pending orders and exit position for test symbol."""
    order = kiteconnect.order_history(order_id)
    status = order[-1]["status"].upper()
    variety = order[-1]["variety"]
    exchange = order[-1]["exchange"]
    product = order[-1]["product"]
    tradingsymbol = order[-1]["tradingsymbol"]
    parent_order_id = order[-1]["parent_order_id"]

    # Cancel order if order is open
    if is_pending_order(status):
        kiteconnect.cancel_order(variety=variety, order_id=order_id, parent_order_id=parent_order_id)
    # If complete then fetch positions and exit
    elif "COMPLETE" in status:
        positions = kiteconnect.positions()
        for p in positions["net"]:
            if (p["tradingsymbol"] == tradingsymbol and
                p["exchange"] == exchange and
                p["product"] == product and
                p["quantity"] != 0 and
                    p["product"] not in [kiteconnect.PRODUCT_BO, kiteconnect.PRODUCT_CO]):

                updated_params = {
                    "tradingsymbol": p["tradingsymbol"],
                    "exchange": p["exchange"],
                    "transaction_type": "BUY" if p["quantity"] < 0 else "SELL",
                    "quantity": abs(p["quantity"]),
                    "product": p["product"],
                    "variety": kiteconnect.VARIETY_REGULAR,
                    "order_type": kiteconnect.ORDER_TYPE_MARKET
                }

                kiteconnect.place_order(**updated_params)

    # If order is complete and CO/BO order then exit the orde
    if "COMPLETE" in status and variety in [kiteconnect.VARIETY_BO, kiteconnect.VARIETY_CO]:
        orders = kiteconnect.orders()
        leg_order_id = None
        for o in orders:
            if o["parent_order_id"] == order_id:
                leg_order_id = o["order_id"]
                break

        if leg_order_id:
            kiteconnect.exit_order(variety=variety, order_id=leg_order_id, parent_order_id=order_id)


# Order place tests
#####################

def test_place_order_market_regular(kiteconnect):
    """Place regular marker order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_REGULAR,
        order_type=kiteconnect.ORDER_TYPE_MARKET
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_limit_regular(kiteconnect):
    """Place regular limit order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_REGULAR,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_sl_regular(kiteconnect):
    """Place regular SL order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_REGULAR,
        order_type=kiteconnect.ORDER_TYPE_SL,
        price=True,
        trigger_price=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR
    assert order[-1]["trigger_price"]
    assert order[-1]["price"]

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_slm_regular(kiteconnect):
    """Place regular SL-M order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_REGULAR,
        order_type=kiteconnect.ORDER_TYPE_SLM,
        trigger_price=True
    )

    assert order[-1]["trigger_price"]
    assert order[-1]["price"] == 0
    assert order[-1]["product"] == kiteconnect.PRODUCT_MIS
    assert order[-1]["variety"] == kiteconnect.VARIETY_REGULAR

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


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
    order_info = kiteconnect.order_history(order_id=order_id)
    assert order_info[0]["tag"] == tag

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_co_market(kiteconnect):
    """Place market CO order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_CO,
        order_type=kiteconnect.ORDER_TYPE_MARKET,
        trigger_price=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_CO
    assert order[-1]["variety"] == kiteconnect.VARIETY_CO

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_co_limit(kiteconnect):
    """Place LIMIT co order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_CO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        trigger_price=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_CO
    assert order[-1]["variety"] == kiteconnect.VARIETY_CO

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_bo_limit(kiteconnect):
    """Place LIMIT BO order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True,
        stoploss=True,
        squareoff=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_place_order_bo_sl(kiteconnect):
    """Place BO SL order."""
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_SL,
        price=True,
        trigger_price=True,
        stoploss=True,
        squareoff=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


# Regular order modify and cancel
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
    updated_params["price"] = ltp[symbol]["last_price"] - (diff - (diff % 1))
    order_id = kiteconnect.place_order(**updated_params)

    # delay order fetch so order is not in received state
    time.sleep(0.5)

    order = kiteconnect.order_history(order_id)
    status = order[-1]["status"].upper()
    if not is_pending_order(status):
        warnings.warn(UserWarning("Order is not open with status: ", status))
        return

    return (updated_params, order_id, order)


def test_order_cancel_regular(kiteconnect):
    """Regular order cancel."""
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_REGULAR)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    returned_order_id = kiteconnect.cancel_order(updated_params["variety"], order_id)
    assert returned_order_id == order_id
    time.sleep(0.5)

    order = kiteconnect.order_history(order_id)
    status = order[-1]["status"].upper()
    assert "CANCELLED" in status

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_order_modify_limit_regular(kiteconnect):
    """Modify limit regular."""
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_REGULAR)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    assert order[-1]["quantity"] == updated_params["quantity"]
    assert order[-1]["price"] == updated_params["price"]

    to_quantity = 2
    to_price = updated_params["price"] - 1
    kiteconnect.modify_order(updated_params["variety"], order_id, quantity=to_quantity, price=to_price)
    time.sleep(0.5)

    order = kiteconnect.order_history(order_id)
    assert order[-1]["quantity"] == to_quantity
    assert order[-1]["price"] == to_price

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_order_cancel_amo(kiteconnect):
    setup = setup_order_modify_cancel(kiteconnect, kiteconnect.VARIETY_AMO)
    if setup:
        updated_params, order_id, order = setup
    else:
        return

    returned_order_id = kiteconnect.cancel_order(updated_params["variety"], order_id)
    assert returned_order_id == order_id
    time.sleep(0.5)

    order = kiteconnect.order_history(order_id)
    status = order[-1]["status"].upper()
    assert "CANCELLED" in status

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


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
    kiteconnect.modify_order(updated_params["variety"], order_id, quantity=to_quantity, price=to_price)
    time.sleep(0.5)

    order = kiteconnect.order_history(order_id)
    assert order[-1]["quantity"] == to_quantity
    assert order[-1]["price"] == to_price

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


# BO order modify, cancel and exit
###################################

def test_modify_order_bo_limit_main(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True,
        stoploss=True,
        squareoff=True
    )

    status = order[-1]["status"]
    quantity = order[-1]["quantity"]
    price = order[-1]["price"]

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    if not is_pending_order(status):
        warnings.warn(UserWarning("Order is not open with status: ", status))
        return

    kiteconnect.modify_order(kiteconnect.VARIETY_BO, order_id, quantity=quantity + 1, price=price + 1)
    time.sleep(0.5)
    modified_order = kiteconnect.order_history(order_id=order_id)

    assert modified_order[-1]["quantity"] == quantity + 1
    assert modified_order[-1]["price"] == price + 1

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_modify_order_bo_limit_leg(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True,
        stoploss=True,
        squareoff=True,
        bo_price_diff=10,
        diff_constant=0,
        price_diff=2
    )

    status = order[-1]["status"]

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    if "COMPLETE" not in status:
        warnings.warn(UserWarning("Order is not complete with status: ", status))
        return

    orders = kiteconnect.orders()
    leg_orders = []
    for o in orders:
        if o["parent_order_id"] == order_id:
            leg_orders.append(o)

    for o in leg_orders:
        if o["price"]:
            kiteconnect.modify_order(kiteconnect.VARIETY_BO, o["order_id"], parent_order_id=order_id, price=o["price"] + 1)
        elif o["trigger_price"]:
            kiteconnect.modify_order(kiteconnect.VARIETY_BO, o["order_id"], parent_order_id=order_id, trigger_price=o["trigger_price"] + 1)

    time.sleep(0.5)
    updated_orders = kiteconnect.orders()

    for l in leg_orders:
        for o in updated_orders:
            if l["order_id"] == o["order_id"]:
                if o["price"]:
                    assert o["price"] == l["price"] + 1
                elif o["trigger_price"]:
                    assert o["trigger_price"] == l["trigger_price"] + 1
            else:
                continue

    try:
        cleanup_orders(kiteconnect, order_id)
    except Exception as e:
        warnings.warn(UserWarning("Error while cleaning up orders: {}".format(e)))


def test_cancel_order_bo_limit_main(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True,
        stoploss=True,
        squareoff=True
    )

    status = order[-1]["status"]

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    if not is_pending_order(status):
        warnings.warn(UserWarning("Order is not open with status: ", status))
        return

    kiteconnect.cancel_order(variety=kiteconnect.VARIETY_BO, order_id=order_id)
    time.sleep(0.5)
    modified_order = kiteconnect.order_history(order_id=order_id)

    assert modified_order[-1]["status"] == "CANCELLED"


def test_exit_order_bo_limit_leg(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_BO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        price=True,
        stoploss=True,
        squareoff=True,
        bo_price_diff=10,
        diff_constant=0,
        price_diff=2
    )

    status = order[-1]["status"]

    assert order[-1]["product"] == kiteconnect.PRODUCT_BO
    assert order[-1]["variety"] == kiteconnect.VARIETY_BO

    if "COMPLETE" not in status:
        warnings.warn(UserWarning("Order is not complete with status: ", status))
        return

    orders = kiteconnect.orders()
    leg_orders = []
    for o in orders:
        if o["parent_order_id"] == order_id:
            leg_orders.append(o)

    leg_order = leg_orders[0]
    kiteconnect.exit_order(variety=kiteconnect.VARIETY_BO, order_id=leg_order["order_id"], parent_order_id=order_id)

    time.sleep(0.5)
    for o in leg_orders:
        order_info = kiteconnect.order_history(order_id=o["order_id"])
        assert not is_pending_order(order_info[-1]["status"])


# CO order modify/cancel and exit
#################################

def test_exit_order_co_market_leg(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_CO,
        order_type=kiteconnect.ORDER_TYPE_MARKET,
        trigger_price=True
    )

    assert order[-1]["product"] == kiteconnect.PRODUCT_CO
    assert order[-1]["variety"] == kiteconnect.VARIETY_CO

    status = order[-1]["status"]
    if "COMPLETE" not in status:
        warnings.warn(UserWarning("Order is not complete with status: ", status))
        return

    orders = kiteconnect.orders()

    leg_order = None
    for o in orders:
        if o["parent_order_id"] == order_id:
            leg_order = o
            exit

    kiteconnect.exit_order(variety=kiteconnect.VARIETY_CO, order_id=leg_order["order_id"], parent_order_id=order_id)
    time.sleep(0.5)
    leg_order_info = kiteconnect.order_history(order_id=leg_order["order_id"])
    assert not is_pending_order(leg_order_info[-1]["status"])


def test_cancel_order_co_limit(kiteconnect):
    updated_params, order_id, order = setup_order_place(
        kiteconnect=kiteconnect,
        product=kiteconnect.PRODUCT_MIS,
        variety=kiteconnect.VARIETY_CO,
        order_type=kiteconnect.ORDER_TYPE_LIMIT,
        trigger_price=True,
        price=True
    )

    status = order[-1]["status"]
    if not is_pending_order(status):
        warnings.warn(UserWarning("Order is not pending with status: ", status))
        return

    assert order[-1]["product"] == kiteconnect.PRODUCT_CO
    assert order[-1]["variety"] == kiteconnect.VARIETY_CO

    kiteconnect.cancel_order(variety=kiteconnect.VARIETY_CO, order_id=order_id)
    time.sleep(0.5)
    updated_order = kiteconnect.order_history(order_id=order_id)
    assert not is_pending_order(updated_order[-1]["status"])
