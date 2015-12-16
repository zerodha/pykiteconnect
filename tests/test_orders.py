# import the local copy and not the installed package
import sys
import os
sys.path.insert(1, os.path.abspath(sys.path[0]) + '/../')

import unittest
import config
from kiteclient import Kite


class OrdersTestCase(unittest.TestCase):
	def setUp(self):
		"""Login and to 2FA"""
		self.kite = Kite(config.user_id, token=None, debug=True)
		questions = self.kite.login(password=config.password, ip="127.0.0.1")
		questions = questions["questions"]

		user = self.kite.do2fa([questions[0]["id"], questions[1]["id"]], ["a", "a"])
		self.assertIsInstance(user, dict)

		if "token" not in user:
			raise Exception("token not found in login response")

		self.kite.set_token(user["token"])

	def test_buysell(self):
		"""Buy 2. Sell 1 so that one position remains open"""
		exchange = "NSE"
		tradingsymbol = "INFY"

		# Place a market order and check
		order_id = self.kite.order_place(
			exchange=exchange,
			tradingsymbol=tradingsymbol,
			transaction_type="BUY",
			quantity=2,
			order_type="MARKET",
			product="MIS",
			variety="regular"
		)
		self.assertTrue(order_id.isdigit())

		# get the details of that order
		order = self.kite.orders(order_id=order_id)
		self.assertIsInstance(order, list)
		self.assert_order_details(order[0], tradingsymbol=tradingsymbol, product="MIS", order_type="MARKET", transaction_type="BUY")

		# sell the instrument
		order_id = self.kite.order_place(
			exchange=exchange,
			tradingsymbol=tradingsymbol,
			transaction_type="SELL",
			quantity=1,
			order_type="MARKET",
			product="MIS",
			variety="regular"
		)
		self.assertTrue(order_id.isdigit())
		order = self.kite.orders(order_id=order_id)
		self.assertIsInstance(order, list)
		self.assert_order_details(order[0], tradingsymbol=tradingsymbol, product="MIS", order_type="MARKET", transaction_type="SELL")

	def test_product_modify(self):
		exchange = "NSE"
		tradingsymbol = "INFY"

		# Place a market order and check
		resp = self.kite.product_modify(
			exchange=exchange,
			tradingsymbol=tradingsymbol,
			transaction_type="BUY",
			position_type="day",
			quantity=1,
			old_product="MIS",
			new_product="CNC",
		)
		self.assertTrue(resp)

		# see if the product has actually changed
		positions = self.kite.positions()
		self.assertIsInstance(positions, dict)

		product_changed = False
		for p in positions["net"]:
			if p["tradingsymbol"] == "INFY" and p["net_quantity"] == 1:
				self.assertEqual(p["product"], "CNC")
				product_changed = True
				break

		self.assertTrue(product_changed)

	def test_order_modify(self):
		exchange = "NSE"
		tradingsymbol = "INFY"

		# get the LTP
		quote = self.kite.quote(exchange=exchange, tradingsymbol=tradingsymbol)
		self.assertIsInstance(quote, dict)

		ltp = quote["last_price"]

		# Place a market order and check
		order_id = self.kite.order_place(
			exchange=exchange,
			tradingsymbol=tradingsymbol,
			transaction_type="BUY",
			quantity=1,
			price=ltp - 10,
			order_type="LIMIT",
			product="MIS",
			variety="regular"
		)
		self.assertTrue(order_id.isdigit())

		# get the details of that order
		order = self.kite.orders(order_id=order_id)
		self.assertIsInstance(order, list)
		self.assert_order_details(order[0],
								status="open",
								tradingsymbol=tradingsymbol,
								product="MIS",
								order_type="LIMIT",
								transaction_type="BUY")

		# modify the order
		mod_id = self.kite.order_modify(
			order_id=order_id,
			exchange=exchange,
			tradingsymbol=tradingsymbol,
			transaction_type="BUY",
			quantity=2,
			price=ltp - 11,
			product="MIS",
			order_type="LIMIT",
			variety="regular"
		)
		self.assertTrue(mod_id.isdigit())

	def assert_order_details(self,
							order,
							quantity=None,
							tradingsymbol=None,
							price=None,
							status=None,
							product=None,
							order_type=None,
							transaction_type=None):
		"""Validate order params"""
		if tradingsymbol is not None:
			self.assertEqual(order["tradingsymbol"], tradingsymbol)

		if quantity is not None:
			self.assertEqual(order["quantity"], quantity)

		if price is not None:
			self.assertEqual(order["price"], price)

		if status is not None:
			self.assertEqual(order["status"], status)

		if product is not None:
			self.assertEqual(order["product"], product)

		if order_type is not None:
			self.assertEqual(order["order_type"], order_type)

		if transaction_type is not None:
			self.assertEqual(order["transaction_type"], transaction_type)

if __name__ == "__main__":
	unittest.main(failfast=True)
