import pprint
import hashlib
from kiteclient.admin import KiteAdmin
pp = pprint.PrettyPrinter(indent=4)

# initialize kite for the first time
# if the user has already logged in, 'token' has to be passed
api_key = "xxx"
secret = "yyy"
request_token = "rrr"

h = hashlib.sha256(api_key + request_token + secret)
checksum = h.hexdigest()

token = None
kite = KiteAdmin(api_key=api_key, user_id="DK3411", root="http://127.0.0.1:8000", debug=True)

if not token:
	# login and get the 2fa questions
	questions = kite.login(password="zerozero@123", ip="127.0.0.1")

	# there will be two 2fa questions
	questions = questions["questions"]

	# set 2fa
	# print kite.update_2fa({
	# questions[0]["id"]: "a", questions[1]["id"]: "a"
	# })

	# for testing, both answers are set to 'a'
	user = kite.do2fa([questions[0]["id"], questions[1]["id"]], ["a", "a"])
	print user

	# logged in, register api request
	kite.register_token_request(user_id=user["user_id"],
		request_token=request_token,
		api_key=api_key,
		permissions='a,b,c,d,e',
		checksum=checksum)

	print kite.request_access_token(request_token=request_token, secret=secret)
	print kite.invalidate_token()
print "done"
quit()

pprint.pprint(kite.orders("151216000090430"))
quit()

# send an order
# try:
# 	print kite.order_cancel(
# 		order_id="151215000042722",
# 		variety="regular"
# 	)
# except Exception as e:
# 	print e.code


# quit()

# print kite.order_modify(
# 	variety="co",
# 	order_id="151211000145544",
# 	trigger_price=2421)

# quit()

try:
	print kite.order_place(
		exchange="NSE",
		tradingsymbol="INFY",
		transaction_type="BUY",
		quantity=1,
		price=1051,
		product="MIS",
		order_type="LIMIT",
		variety="regular"
	)
except Exception as e:
	print e

# normal order = 141119000062604, amo = 141119000077821
"""
pp.pprint(kite.product_modify(
	tradingsymbol="asdad",
	exchange="adsds",
	transaction_type="BUY",
	quantity=25,
	old_product="MIS",
	new_product="NRML"
))
"""
