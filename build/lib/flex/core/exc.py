from flex.http import exc as http
from marshmallow import ValidationError as BaseValidationError
__all__ = [
	'ImproperlyConfigured', 'UnSafeUrlError', 'ValidationError'
]

class ImproperlyConfigured(Exception):
	"""Flex is somehow improperly configured"""
	pass


class UnSafeUrlError(ValueError):
	pass


class ValidationError(BaseValidationError):

	def as_dict(self, default_key='_error'):
		return self.normalized_messages(default_key)


