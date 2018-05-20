###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Zerodha technologies Pvt. Ltd.
#
# This example shows how to run KiteTicker in threaded mode.
# KiteTicker runs in seprate thread and main thread is blocked to juggle between
# different modes for current subscribed tokens. In real world web apps
# the main thread will be your web server and you can access WebSocket object
# in your main thread while running KiteTicker in separate thread.
###############################################################################

import time
import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

# Initialise.
kws = KiteTicker("api_key", "public_token")

# RELIANCE BSE
tokens = [738561]


# Callback for tick reception.
def on_ticks(ws, ticks):
    if len(ticks) > 0:
        logging.info("Current mode: {}".format(ticks[0]["mode"]))


# Callback for successful connection.
def on_connect(ws, response):
    logging.info("Successfully connected. Response: {}".format(response))
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)
    logging.info("Subscribe to tokens in Full mode: {}".format(tokens))


# Callback when current connection is closed.
def on_close(ws, code, reason):
    logging.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


# Callback when connection closed with error.
def on_error(ws, code, reason):
    logging.info("Connection error: {code} - {reason}".format(code=code, reason=reason))


# Callback when reconnect is on progress
def on_reconnect(ws, attempts_count):
    logging.info("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
def on_noreconnect(ws):
    logging.info("Reconnect failed.")


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error
kws.on_connect = on_connect
kws.on_reconnect = on_reconnect
kws.on_noreconnect = on_noreconnect

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect(threaded=True)

# Block main thread
logging.info("This is main thread. Will change webosocket mode every 5 seconds.")

count = 0
while True:
    count += 1
    if count % 2 == 0:
        if kws.is_connected():
            logging.info("### Set mode to LTP for all tokens")
            kws.set_mode(kws.MODE_LTP, tokens)
    else:
        if kws.is_connected():
            logging.info("### Set mode to quote for all tokens")
            kws.set_mode(kws.MODE_QUOTE, tokens)

    time.sleep(5)
