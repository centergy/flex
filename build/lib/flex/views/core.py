import re
import inspect
from werkzeug.wrappers import Response as BaseResponse
from flask.views import View as FlaskView
from ..utils import json
from flask import request, current_app, session
from werkzeug.datastructures import Headers
from ..core.exc import ImproperlyConfigured
from ..http import exc, status, Payload, Response
from ..utils.decorators import cached_property, export
from ..http.status import is_http_status_code
from ..helpers import uzi
from .. import helpers

from .options import BaseViewOptions, viewoption


__all__ = [
	'View',
]


def has_own_attr(obj, name):
	return name in obj.__dict__


http_method_funcs = frozenset(['get', 'post', 'head', 'options', 'delete', 'put', 'trace', 'patch'])



def declared_http_methods(cls):
	""" declared
	Returns a list of methods that can be routed to.

	This a monkey patch for flask_classy.get_interesting_members.
	to allow definition of non-routable methods.
	"""
	for name, fn in inspect.getmembers(cls, predicate=inspect.isfunction):
		if name in http_method_funcs and is_instance_method(fn) and not inspect.ismethod(fn):
			yield name

	# for name, fn in ((n, getattr(cls, n)) for n in dir(cls)):
	# 	if inspect.ismethod(fn) and name in http_method_funcs:
	# 		yield name

def is_instance_method(method):
	if inspect.isfunction(method):
		argspec = inspect.getfullargspec(method)
		args = argspec[0]
		return args and args[0] == 'self'
	return False


@export
class ViewType(type):

	def __new__(mcls, name, bases, dct):
		dct.setdefault('endpoint', None)
		cls = super(ViewType, mcls).__new__(mcls, name, bases, dct)

		if 'methods' not in dct:
			methods = set(cls.methods or [])
			for key in dct:
				if key in http_method_funcs:
					methods.add(key.upper())
			# If we have no method at all in there we don't want to
			# add a method list.  (This is for instance the case for
			# the base class or another subclass of a base method view
			# that does not introduce new methods).
			if methods:
				cls.methods = list(sorted(methods))

		decorators = []
		for c in cls.mro():
			if hasattr(c, 'decorators') and isinstance(c.decorators, (list, tuple)):
				for d in reversed(c.decorators):
					if d not in decorators:
						decorators.append(d)

		cls.decorators = decorators
		cls.declared_methods = set(declared_http_methods(cls))

		# cls._meta = cls._create_options()
		# cls._meta._prepare()

		return cls

	def _create_options(cls):
		opts_cls = cls._get_options_cls()
		meta = getattr(cls, 'Meta', None)
		base = getattr(cls, '_meta', None)
		return opts_cls(cls, meta, base)

	def _get_options_cls(cls):
		bases = []
		for c in cls.mro():
			oc = getattr(cls, 'OPTIONS_CLASS', None)
			if oc and not list(filter(lambda x: issubclass(x, oc), bases)):
				bases.append(oc)
		return type('%sOptions' % cls.__name__, tuple(bases), {})



@export
class ViewOptions(BaseViewOptions):

	declared_methods = viewoption(lambda o,*a: set(declared_http_methods(o.view)))

	@viewoption(default=Void)
	def methods(self, value, base_value=None):
		"""List of declared Http methods.
		"""
		if value is Void:
			value = set(base_value or [])
			for key, val in self.view.__dict__.items():
				if key in http_method_funcs and is_instance_method(val):
					value.add(key.upper())
		# If we have no method at all in there we don't want to
		# add a method list.  (This is for instance the case for
		# the base class or another subclass of a base method view
		# that does not introduce new methods).
		return value and list(sorted(value)) or None

	@viewoption
	def decorators(self, value, bv=None):
		value = list(reversed(value or ()))
		for c in self.view.mro():
			if c is self.view or not isinstance(c, ViewType):
				continue
			for d in c._meta.decorators:
				if d not in value:
					value.append(d)
		print('decorators:', self.view.__name__, value)

		return value



class View(FlaskView, metaclass=ViewType):
	#: A list of methods this view can handle.

	OPTIONS_CLASS = ViewOptions

	methods = None

	decorators = ()

	endpoint = None

	payload_class = Payload

	mimetype = None

	default_status = 200

	default_response_headers = None

	@property
	def app(self):
		return current_app._get_current_object()

	@property
	def session(self):
		return session._get_current_object()

	@cached_property
	def payload(self):
		return self.created_payload()

	@property
	def headers(self):
		return self.payload.headers

	@classmethod
	def _get_default_view(cls):
		if not hasattr(cls, '_default_view'):
			def view(*args, **kwargs):
				self = view.view_class()
				response = self(*args, **kwargs)
				return response

			name = cls.endpoint or uzi.snake(cls.__name__)
			if cls.decorators:
				view.__name__ = name
				view.__module__ = cls.__module__
				for decorator in cls.decorators:
					view = decorator(view)

			# We attach the view class to the view function for two reasons:
			# first of all it allows us to easily figure out what class-based
			# view this thing came from, secondly it's also used for instantiating
			# the view class so you can actually replace it with something else
			# for testing purposes and debugging.
			view.view_class = cls
			view.__name__ = name
			view.__doc__ = cls.__doc__
			view.__module__ = cls.__module__
			view.methods = cls.methods
			cls._default_view = view
		return cls._default_view

	@classmethod
	def as_view(cls, name=None, *class_args, **class_kwargs):
		"""Converts the class into an actual view function that can be used
		with the routing system.  Internally this generates a function on the
		fly which will instantiate the :class:`View` on each request and call
		the :meth:`dispatch_request` method on it.

		The arguments passed to :meth:`as_view` are forwarded to the
		constructor of the class.
		"""
		if name is None:
			if class_args or class_kwargs:
				raise TypeError(
						'View name is required when class_args or class_kwargs '
						'are provided was not set on view. %s.')
			else:
				return cls._get_default_view()

		def view(*args, **kwargs):
			self = view.view_class(*class_args, **class_kwargs)
			response = self(*args, **kwargs)
			return response

		if cls.decorators:
			view.__name__ = name
			view.__module__ = cls.__module__
			for decorator in cls.decorators:
				view = decorator(view)

		# We attach the view class to the view function for two reasons:
		# first of all it allows us to easily figure out what class-based
		# view this thing came from, secondly it's also used for instantiating
		# the view class so you can actually replace it with something else
		# for testing purposes and debugging.
		view.view_class = cls
		view.__name__ = name
		view.__doc__ = cls.__doc__
		view.__module__ = cls.__module__
		view.methods = cls.methods
		return view

	def created_payload(self):
		cls = self.payload_class
		return cls(
			status=self.default_status,
			mimetype=self.mimetype,
			headers=self.default_response_headers,
			data=self.create_payload_data_store(),
			errors=self.create_payload_error_store(),
			context=self.get_payload_context()
		)

	def create_payload_data_store(self):
		return None

	def create_payload_error_store(self):
		return None

	def get_payload_context(self):
		return {}

	def abort(self, status, *args, **kwargs):
		if status and not is_http_status_code(status):
			raise ValueError('%s is not a valid HTTP status code.' % (status,))

		kwargs.setdefault('payload', self.payload)
		return exc.abort(status, *args, **kwargs)

	def dispatch(self):
		return self.build_response()

	def build_response(self):
		return self.payload.to_response()

	def http_method_not_allowed(self, *args, **kwargs):
		"""
		If `request.method` does not correspond to a handler method,
		determine what kind of exception to raise.
		"""
		return self.abort(status.HTTP_405_METHOD_NOT_ALLOWED)

	def initial(self, request, *args, **kwargs):
		"""Runs anything that needs to occur prior to calling the method handler.
		"""
		# Ensure that the incoming request is permitted
		# self.perform_authentication(request)
		# self.check_permissions(request)
		# self.check_throttles(request)
		pass

	def finalize_response(self, request, response, *args, **kwargs):
		"""
		Returns the final response object.
		"""
		# Make the error obvious if a proper response is not returned
		assert isinstance(response, BaseResponse), (
			'Expected a `Response` object '
			'to be returned from the view, but received a `%s`'
			% type(response)
		)
		return response

	def handle_exception(self, e):
		"""
		Handle any exception that occurs, by returning an appropriate response,
		or re-raising the error.
		"""
		# if isinstance(exc, (exc.NotAuthenticated, exc.AuthenticationFailed)):
		# 	# WWW-Authenticate header for 401 responses, else coerce to 403
		# 	auth_header = self.get_authenticate_header(self.request)

		# 	if auth_header:
		# 		exc.auth_header = auth_header
		# 	else:
		#		exc.status_code = status.HTTP_403_FORBIDDEN
		self.raise_uncaught_exception(e)

	def raise_uncaught_exception(self, e):
		raise

	# Note: Views are made CSRF exempt from within `as_view` as to prevent
	# accidental removal of this exemption in cases where `handle` needs to
	# be overridden.
	def __call__(self, *args, **kwargs):
		"""
		`.dispatch()` is pretty much the same as Django's regular dispatch,
		but with extra hooks for startup, finalize, and exception handling.
		"""
		self.args = args
		self.kwargs = kwargs
		self.request = request

		try:
			self.initial(request, *args, **kwargs)

			# Get the appropriate handler method
			if request.method.lower() in self.declared_methods:
				handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
			else:
				handler = self.http_method_not_allowed

			response = handler(*args, **kwargs)
			if response is None:
				response = self.dispatch()

		except Exception as e:
			response = self.handle_exception(e)

		return self.finalize_response(request, response, *args, **kwargs)
