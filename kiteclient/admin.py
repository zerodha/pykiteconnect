from kiteclient import Kite


class KiteAdmin(Kite):
	_routes = {
		"user.login": "/user/login",
		"user.2fa": "/user/2fa",
		"user.profile": "/user/profile",
		"user.password": "/user/password",
		"user.transpassword": "/user/transpassword",
		"user.logout": "/user/logout",
		"api.register": "/session"
	}

	def __init__(self, api_key=None, user_id=None, token=None, access_token=None, root=None, debug=False, timeout=7, micro_cache=True):
		super(KiteAdmin, self).__init__(api_key=api_key,
										access_token=access_token,
										root=root,
										debug=debug,
										timeout=timeout,
										micro_cache=micro_cache)
		# update the routes
		self._routes.update(super(KiteAdmin, self)._routes)
		self.user_id = user_id
		self.token = token

	def set_user(self, user_id):
		"""Set the instance's user id."""
		self.user_id = user_id

	def set_token(self, token):
		"""Set token"""
		self.token = token

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
		return self._post("user.login", {"user_id": self.user_id,
										"token": self.token,
										"password": password,
										"ip": ip})

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
		params = {"user_id": self.user_id,
				"token": self.token,
				"question[]": qa,
				"answer[]": ans}

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
		params = {"user_id": self.user_id,
				"token": self.token,
				"question[]": [],
				"answer[]": []}

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
		params = {"user_id": self.user_id,
				"token": self.token,
				"email": email,
				"identification": identification}

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
		return self._get("user.profile", {"user_id": self.user_id, "token": self.token})

	def password_update(self, old_password, new_password):
		"""Change the login password"""
		return self._put("user.password",
				{"user_id": self.user_id,
				"token": self.token,
				"old_password": old_password,
				"new_password": new_password})

	def transpassword_update(self, old_password, new_password):
		"""Change the transaction password"""
		return self._put("user.transpassword",
					{"user_id": self.user_id,
					"token": self.token,
					"old_password": old_password,
					"new_password": new_password})

	def transpassword_check(self, password):
		"""Check the transaction password"""
		return self._post("user.transpassword",
			{"user_id": self.user_id,
			"token": self.token,
			"password": password})

	def reset_password(self, email, identification):
		"""
		Reset the user's primary password

		Args:
			email: account email
			identification: the required form of identification (eg: PAN)

		Raises:
			TwoFAException: if the update fails for some reason
		"""
		params = {"user_id": self.user_id,
				"token": self.token,
				"email": email,
				"identification": identification}

		return self._delete("user.password", params)

	def register_request_token(self, request_token, api_key, api_id, checksum, permissions, user_id):
		"""Register access token for a given request token and api key"""
		return self._post("api.register",
			{
				"request_token": request_token,
				"api_key": api_key,
				"api_id": api_id,
				"checksum": checksum,
				"permissions": permissions,
				"user_id": user_id
			})

	def logout(self):
		"""Log the user out completely of all sessions
		including all api client sessions"""
		return self._post()
