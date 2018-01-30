"""
Handled exceptions raised by REST framework.

In addition Django's built in 403 and 404 exceptions are handled.
(`django.http.Http404` and `django.core.exceptions.PermissionDenied`)
"""
import re
import math
import traceback
import six
import flask as fl

from werkzeug.exceptions import Aborter as BaseAborter, HTTPException as BaseHTTPException
from flex.utils.decorators import cached_property, export
from . import status
from .payload import Payload
from collections import OrderedDict, Sequence, Mapping
from werkzeug.datastructures import OrderedMultiDict
from .response import Response
from flex.conf import config

__all__ = [ 'http_error_handler', ]

default_exceptions = {}

def register_exception(default=False):
	@export
	def wrapper(cls):
		if cls.code not in default_exceptions or default is True:
			default_exceptions[cls.code] = cls
		if cls.__name__ not in default_exceptions or default is True:
			default_exceptions[cls.__name__] = cls
		if cls.codename not in default_exceptions or default is True:
			default_exceptions[cls.codename] = cls
		return cls
	return wrapper



def _(text):
	return text

force_text = str


def http_error_handler(exc):
	if not isinstance(exc, HTTPException):
		if isinstance(exc, BaseHTTPException):
			cls = default_exceptions.get(exc.code, HTTPException)
			exc = cls(description=exc.description, code=exc.code, response=exc.response)
		elif isinstance(exc, Exception):
			if fl.current_app.config.get('DEBUG'):
				traceback.print_exc()
			exc = HTTPException()
		elif isinstance(exc, int):
			cls = default_exceptions.get(exc, HTTPException)
			exc = cls(code=exc)
		elif isinstance(exc, str) and exc in default_exceptions:
			cls = default_exceptions[exc]
			exc = cls()

	if not isinstance(exc, HTTPException):
		traceback.print_exc()
		raise RuntimeError(
			'http_error_handler unable to handle errors of type %s.' % type(exc)
		)
	return exc.get_response()



@register_exception()
class HTTPException(BaseHTTPException):
	"""
	Baseclass for all HTTP exceptions.  This exception can be called as WSGI
	application to render a default error page or you can catch the subclasses
	of it independently and render nicer error messages.
	"""
	code = status.HTTP_500_INTERNAL_SERVER_ERROR
	description = _('A server error occurred.')
	codename = 'server_error'
	template_names = [
		'exceptions/%(code)s.html',
		'exceptions/exception.html',
	]

	def __init__(self, detail=None, codename=None, code=None, description=None, response=None, payload=None):
		if code is not None:
			self.code = code
		super(HTTPException, self).__init__(description=description, response=response)

		if codename is not None:
			self.codename = codename

		if isinstance(detail, Mapping):
			self.payload.errors.update(detail.items())
		elif detail is not None:
			self.payload.errors.update([(self.codename, detail)])

		self.payload.body.description = self.description

		if payload is not None:
			self.payload.data = payload.data
			self.payload.errors.update(payload.errors)
			self.payload.context.update(payload.context)
			self.payload.headers.update(payload.headers)
			self.payload.mimetype = payload.mimetype or self.payload.mimetype

	@cached_property
	def payload(self):
		return Payload()

	def get_template_names(self):
		return [t % dict(code=self.code) for t in self.template_names]

	def get_response(self, environ=None):
		"""Get a response object.  If one was passed to the exception
		it's returned directly.

		:param environ: the optional environ for the request.  This
						can be used to modify the response depending
						on how the request looked like.
		:return: a :class:`Response` object or a subclass thereof.
		"""
		# if environ is not None:
		# 	environ = getattr(environ, 'environ', environ)
		response = self.response
		if response is None:
			self.payload.status = self.code
			self.payload.template_name = self.get_template_names()
			response = self.payload.to_response()

		return response

	def __repr__(self):
		code = self.code if self.code is not None else '???'
		return "<%s '%s: %r'>" % (self.__class__.__name__, code, self.payload)

	def __str__(self):
		return self.__repr__()


@register_exception()
class ParseError(HTTPException):
	code = status.HTTP_400_BAD_REQUEST
	description = _('Malformed request.')
	codename = 'parse_error'



@register_exception(default=True)
class ValidationError(HTTPException):
	code = status.HTTP_400_BAD_REQUEST
	description = _('Invalid input.')
	codename = 'invalid_input'

	# def __init__(self, detail=None, code=None, **kwargs):
	# 	if detail is None:
	# 		detail = self.default_detail
	# 	# For validation failures, we may collect many errors together,
	# 	# so the details should always be coerced to a list if not already.
	# 	if not isinstance(detail, dict) and not isinstance(detail, list):
	# 		detail = [detail]
	# 	super(ValidationError, self).__init__(detail, code, **kwargs)



@register_exception()
class AuthenticationFailed(HTTPException):
	code = status.HTTP_401_UNAUTHORIZED
	description = _('Incorrect authentication credentials.')
	codename = 'authentication_failed'



@register_exception(default=True)
class NotAuthenticated(HTTPException):
	code = status.HTTP_401_UNAUTHORIZED
	description = _('Authentication credentials were not provided.')
	codename = 'not_authenticated'




@register_exception()
class PermissionDenied(HTTPException):
	code = status.HTTP_403_FORBIDDEN
	description = _('You do not have permission to perform this action.')
	codename = 'permission_denied'



@register_exception()
class NotFound(HTTPException):
	code = status.HTTP_404_NOT_FOUND
	description = _('Not found.')
	codename = 'not_found'



@register_exception()
class MethodNotAllowed(HTTPException):
	code = status.HTTP_405_METHOD_NOT_ALLOWED
	description = _('Method "{method}" not allowed.')
	codename = 'method_not_allowed'

	def __init__(self, method=None, detail=None, **kwargs):
		try:
			method = method or fl.request.method
		except RuntimeError:
			method = method or ''
		self.description = force_text(self.description).format(method=method)
		super(MethodNotAllowed, self).__init__(detail, **kwargs)



@register_exception()
class NotAcceptable(HTTPException):
	code = status.HTTP_406_NOT_ACCEPTABLE
	description = _('Could not satisfy the request Accept header.')
	codename = 'not_acceptable'



@register_exception()
class UnsupportedMediaType(HTTPException):
	code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
	description = _('Unsupported media type "{media_type}" in request.')
	codename = 'unsupported_media_type'

	def __init__(self, media_type=None, detail=None, **kwargs):
		try:
			media_type = media_type or kwargs.pop('mimetype', fl.request.mimetype)
		except RuntimeError:
			media_type = media_type or ''

		self.description = force_text(self.description).format(media_type=media_type)
		super(UnsupportedMediaType, self).__init__(detail, **kwargs)



@register_exception()
class Throttled(HTTPException):
	code = status.HTTP_429_TOO_MANY_REQUESTS
	description = _('Request was throttled.')
	extra_detail = 'Try again in {wait} second(s).'
	codename = 'throttled'

	def __init__(self, wait=None, detail=None, **kwargs):
		self.description = force_text(self.description)
		if wait is not None:
			wait = math.ceil(wait)
			self.description += ' %s' % self.extra_detail.format(wait=wait)
		self.wait = wait
		super(Throttled, self).__init__(detail, **kwargs)



class Aborter(BaseAborter):
	"""docstring for Aborter"""

	def __call__(self, code, **kwargs):
		if code in self.mapping:
			raise self.mapping[code](**kwargs)

		if not kwargs:
			if not isinstance(code, (int, str)) \
				or (isinstance(code, str) and re.search(r'[\s]+', code)):
				raise HTTPException(response=code)

		raise LookupError('no exception for %r' % code)


_aborter = Aborter(extra=default_exceptions)


@export
def abort(status, *args, **kwargs):
	'''
	Raises an :py:exc:`HTTPException` for the given status code or WSGI
	application::

		abort(404)  # 404 Not Found
		abort(Response('Hello World'))

	Can be passed a WSGI application or a status code.  If a status code is
	given it's looked up in the list of exceptions and will raise that
	exception, if passed a WSGI application it will wrap it in a proxy WSGI
	exception and raise that::

	   abort(404)
	   abort(Response('Hello World'))

	'''
	return _aborter(status, *args, **kwargs)
