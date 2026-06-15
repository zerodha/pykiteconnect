import logging

from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")
kite.set_access_token("your_access_token")

# Place an order with automatic slicing for quantities that exceed the exchange
# freeze limit. place_autoslice_order() splits the order into multiple child
# orders internally. The response contains the parent `order_id` and a `children`
# list, where each child is either a placed order (`order_id`) or an `error`
# payload.
#
# `market_protection` (also accepted by place_order() and modify_order()) caps how
# far a MARKET / SL-M order can deviate from the last traded price before it is
# converted to a LIMIT order. Pass -1 (kite.MARKET_PROTECTION_AUTO) for the system
# default, or a value from 1 to 100 for a custom percentage.
try:
    response = kite.place_autoslice_order(
        variety=kite.VARIETY_REGULAR,
        exchange=kite.EXCHANGE_NFO,
        tradingsymbol="NIFTY25APRFUT",
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=100000,
        product=kite.PRODUCT_MIS,
        order_type=kite.ORDER_TYPE_MARKET,
        market_protection=kite.MARKET_PROTECTION_AUTO,
    )

    parent_order_id = response["order_id"]
    logging.info("Auto-slice parent order ID: {}".format(parent_order_id))

    for child in response.get("children", []):
        if "order_id" in child:
            logging.info("Child order placed: {}".format(child["order_id"]))
        else:
            logging.info("Child order failed: {}".format(child.get("error")))
except Exception as e:
    logging.info("Auto-slice order placement failed: {}".format(e))
