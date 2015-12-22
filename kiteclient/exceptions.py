"""
	Basic exception classes for Kite Connect client
"""


class KiteException(Exception):
	def __init__(self, message, code=500):
		super(KiteException, self).__init__(message)
		self.code = code


class GeneralException(KiteException):
	def __init__(self, message, code=500):
		super(GeneralException, self).__init__(message, code)


class TokenException(KiteException):
	def __init__(self, message, code=403):
		super(TokenException, self).__init__(message, code)


class UserException(KiteException):
	def __init__(self, message, code=500):
		super(UserException, self).__init__(message, code)


class OrderException(KiteException):
	def __init__(self, message, code=500):
		super(OrderException, self).__init__(message, code)


class InputException(KiteException):
	def __init__(self, message, code=400):
		super(InputException, self).__init__(message, code)


class DataException(KiteException):
	def __init__(self, message, code=502):
		super(DataException, self).__init__(message, code)


class NetworkException(KiteException):
	def __init__(self, message, code=503):
		super(NetworkException, self).__init__(message, code)


class ClientNetworkException(KiteException):
	def __init__(self, message, code=504):
		super(ClientNetworkException, self).__init__(message, code)
