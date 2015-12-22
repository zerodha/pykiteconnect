import exceptions as ex
from kiteclient import Kite

class KiteAdmin(Kite):
	_routes = {
		"user.login": "/user/login",
		"user.2fa": "/user/2fa",
		"user.profile": "/user/profile",
		"user.password": "/user/password",
		"user.transpassword": "/user/transpassword",
		"user.register_access_token": "/register_access_token"
	}

	def __init__(self, user_id, access_token=None, root=None, debug=False, timeout=7, micro_cache=True):
		super(KiteAdmin, self).__init__(user_id, access_token, root, debug, timeout, micro_cache)
		# update the routes
		self._routes.update(super(KiteAdmin, self).__self__._routes)

	def login(self, password, ip):
		"""
		Authenticate the user's credentials.
		If the system has 2FA enabled, the questions are returned

		Args:
			password: user's password
			ip: IP address of the user

		Raises:
			UserException: if the login fails
		"""
		return self._post("user.login", {"password": password, "ip": ip})

	def do2fa(self, qa, ans):
		"""
		Do 2FA authentication and login

		Args:
			qa: list of question ids
			ans: list of corresponding answers

		Raises:
			TwoFAException: if the user has entered the wrong answers
			UserException: if 2FA failures exceed and the account is blocked
		"""
		params = {"question[]": qa, "answer[]": ans}

		return self._post("user.2fa", params)

	def update_2fa(self, qa):
		"""
		Set the user's choice of 2FA questions and answers

		Args:
			qa: dict of question_id received from the login() call
				and corresponding answer received from the user

		Raises:
			UserException: if the updation failed
		"""
		params = {"question[]": [], "answer[]": []}

		for question in qa:
			params["question[]"].append(question)
			params["answer[]"].append(qa[question])

		return self._put("user.2fa", params)

	def reset_2fa(self, email, identification):
		"""
		Reset the user's 2FA questions and answers so they're
		prompted for a fresh set during the next login

		Args:
			email: account email
			identification: the required form of identification (eg: PAN)

		Raises:
			TwoFAException: if the update fails for some reason
		"""
		params = {"email": email, "identification": identification}

		return self._delete("user.2fa", params)

	# user
	def profile(self):
		"""
		Fetch the user's profile

		Returns:
			{
				dp_ids: [002178],
				user_id: DM0002,
				name: DM0002,
				bank_accounts: [{	account: 083311600,
									name: HDFC BANK LTD,
									branch: JAKKASANDRA}],
				phone: 98362716273,
				email: test@zerodha.com,
				pan: BPALQ5996K,
			}

		Raises:
			UserException: if the profile fetching failed
		"""
		return self._get("profile")

	def password_update(self, old_password, new_password):
		"""Change the login password"""
		return self._put("user.password", {
					"old_password": old_password,
					"new_password": new_password
				})

	def transpassword_update(self, old_password, new_password):
		"""Change the transaction password"""
		return self._put("user.transpassword", {
					"old_password": old_password,
					"new_password": new_password
				})

	def transpassword_check(self, password):
		"""Check the transaction password"""
		return self._post("user.transpassword", {
					"password": password
				})

	def reset_password(self, email, identification):
		"""
		Reset the user's primary password

		Args:
			email: account email
			identification: the required form of identification (eg: PAN)

		Raises:
			TwoFAException: if the update fails for some reason
		"""
		params = {"email": email, "identification": identification}

		return self._delete("user.password", params)

	def register_access_token(self, api_key, request_token):
		"""
		Register access token for a given request token and api key
		"""
		params = {"api_key": api_key, "request_token": request_token}

		return self._post("user.register_access_token", params)
