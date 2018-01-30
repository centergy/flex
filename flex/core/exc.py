# from werkzeug.exceptions import (
# 	HTTPException as BaseHTTPException, BadRequest, ClientDisconnected,
# 	SecurityError, BadHost,
# 	Unauthorized, Forbidden, NotFound, MethodNotAllowed, NotAcceptable,
# 	RequestTimeout, Conflict, Gone, LengthRequired, PreconditionFailed,
# 	RequestEntityTooLarge, RequestURITooLarge, UnsupportedMediaType,
# 	RequestedRangeNotSatisfiable, ExpectationFailed, ImATeapot,
# 	UnprocessableEntity, Locked, PreconditionRequired, TooManyRequests,
# 	RequestHeaderFieldsTooLarge, UnavailableForLegalReasons, InternalServerError,
# 	NotImplemented, BadGateway, ServiceUnavailable, GatewayTimeout,
# 	HTTPVersionNotSupported, BadRequestKeyError, Aborter, abort
# )
# from werkzeug.wrappers import BaseResponse


# class HTTPException(BaseHTTPException):

# 	def __init__(self, message=None, response=None, json=False, code=None):
# 		Exception.__init__(self)
# 		self.is_json = json
# 		if code is not None:
# 			self.code = code
# 		if message is not None:
# 			self.description = message
# 		self.response = response


# _orig_init = BaseHTTPException.__init__
# _orig_get_response = BaseHTTPException.get_response

# def _monkey_patch_http_exception():
# 	BaseHTTPException.__init__ = HTTPException.__init__

# _monkey_patch_http_exception()
# del _monkey_patch_http_exception

from flex.http.exc import *

class ImproperlyConfigured(Exception):
	"""Flex is somehow improperly configured"""
	pass


class UnSafeUrlError(ValueError):
	pass

class AppContextError(RuntimeError):
	pass

class RequestContextError(RuntimeError):
	pass