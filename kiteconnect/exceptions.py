"""
Exceptions raised by the Kite Connect client
"""


class KiteException(Exception):
	"""Base exception class representing a Kite client exception.
	Every specific Kite client exception is a subclass of this
	and  exposes two instance variables	`.code` (HTTP error code)
	and `.message` (error text)."""
	def __init__(self, message, code=500):
		super(KiteException, self).__init__(message)
		self.code = code


class GeneralException(KiteException):
	"""An unclassified, general error. Default code is 500"""
	def __init__(self, message, code=500):
		super(GeneralException, self).__init__(message, code)


class TokenException(KiteException):
	"""Represents all token and authentication related errors.
	Default code is 403"""
	def __init__(self, message, code=403):
		super(TokenException, self).__init__(message, code)


class PermissionException(KiteException):
	"""Represents permission denied exceptions for certain calls.
	Default code is 403"""
	def __init__(self, message, code=403):
		super(PermissionException, self).__init__(message, code)


class UserException(KiteException):
	"""Exceptions pertaining to calls dealing with the
	logged in user's data.Default code is 500."""
	def __init__(self, message, code=500):
		super(UserException, self).__init__(message, code)


class OrderException(KiteException):
	"""Represents all order placement and manipulation errors.
	Default code is 500."""
	def __init__(self, message, code=500):
		super(OrderException, self).__init__(message, code)


class InputException(KiteException):
	"""Represents user input errors such as missing and invalid
	parameters. Default code is 400."""
	def __init__(self, message, code=400):
		super(InputException, self).__init__(message, code)


class DataException(KiteException):
	"""Represents a bad response from the backend
	Order Management System (OMS). Default code is 502."""
	def __init__(self, message, code=502):
		super(DataException, self).__init__(message, code)


class NetworkException(KiteException):
	"""Represents a network issue between Kite and the backend
	Order Management System (OMS). Default code is 503."""
	def __init__(self, message, code=503):
		super(NetworkException, self).__init__(message, code)


class ClientNetworkException(KiteException):
	"""Raised when Kite Client is unable to connect to the
	Kite Connect servers. Default code is 504."""
	def __init__(self, message, code=504):
		super(ClientNetworkException, self).__init__(message, code)


class TwoFAException(KiteException):
	"""Raised when there is a two FA related error.
	Default code is 403."""
	def __init__(self, message, questions=None, code=403):
		super(TwoFAException, self).__init__(message, code)
		self.questions = questions
