import pprint 
from kiteclient import Kite

# initialize kite for the first time
# if the user has already logged in, 'token' has to be passed
token = None

kite = Kite("DM1594", token=token)

if not token:
	# login and get the 2fa questions
	questions = kite.login(password="abc123", ip="127.0.0.1")

	# there will be two 2fa questions
	questions = questions["questions"]

	# set 2fa
	#print kite.update_2fa({
	#	questions[0]["id"]: "a", questions[1]["id"]: "a"
	#})

	# for testing, both answers are set to 'a'
	user = kite.do2fa({questions[0]["id"]: "a", questions[1]["id"]: "a"})

	print user

	# logged in, we have the token now
	kite.set_token(user["token"])

# send an order
"""
print kite.order_place(
	exchange="NSE",
	tradingsymbol="RELIANCE-EQ",
	transaction_type="BUY",
	quantity=1,
	price=950,
	order_type="LIMIT",
	product="MIS",
)
"""
# normal order = 141119000062604, amo = 141119000077821

print kite.holdings_t1()
