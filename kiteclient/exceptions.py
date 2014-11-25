"""
	Basic exception classes for Kite trade server
"""

class KiteException(Exception):
	def __init__(self, message, code = 500):
		super(KiteException, self).__init__(message)
		self.code = code

class GeneralException(KiteException):
	pass

class UserException(KiteException):
	pass

class TwoFAException(KiteException):
	def __init__(self, message, questions = None, code = 401):
		super(TwoFAException, self).__init__(message, code)
		self.questions = questions

class OrderException(KiteException):
	pass

class DataException(KiteException):
	pass

class NetworkException(KiteException):
	pass
