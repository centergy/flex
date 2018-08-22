"""
Caching framework.

This package defines set of cache backends that all conform to a simple API.
In a nutshell, a cache is a set of values -- which can be any object that
may be pickled -- identified by string keys.  For the complete API, see
the abstract BaseCache class in django.core.cache.backends.base.

Client code should use the `cache` variable defined here to access the default
cache backend and look up non-default cache backends in the `caches` dict-like
object.

See docs/topics/cache.txt for information on the public API.
"""
from warnings import warn
from threading import Lock
from flask import current_app
from collections import defaultdict

from flex.conf import config
from flex.core import signals
from .backends.base import (
	BaseCache, CacheKeyWarning, InvalidCacheBackendError,
)
from flex.utils.module_loading import import_string

__all__ = [
	'cache', 'DEFAULT_CACHE_ALIAS', 'InvalidCacheBackendError',
	'CacheKeyWarning', 'BaseCache',
]


DEFAULT_CACHE_ALIAS = 'default'


class _AppCacheContainer(object):

	__slots__ = ('app', 'lock', 'caches')

	def __init__(self, app):
		self.app = app
		self.caches = {}
		self.lock = Lock()

	def get_cache(self, alias):
		with self.lock:
			rv = self.caches.get(alias)
			if rv is None:
				rv = self.caches[alias] = self.create_cache(alias)
			return rv

	def create_cache(self, backend, **kwargs):
		try:
			# Try to get the CACHES entry for the given backend name first
			try:
				conf = self.app.config.CACHES[backend]
			except KeyError:
				try:
					# Trying to import the given backend, in case it's a dotted path
					import_string(backend)
				except ImportError as e:
					raise InvalidCacheBackendError("Could not find backend '%s': %s" % (
						backend, e))
				location = kwargs.pop('location', '')
				params = kwargs
			else:
				params = conf.copy()
				params.update(kwargs)
				backend = params.pop('backend')
				location = params.pop('location', '')
			backend_cls = import_string(backend)
		except ImportError as e:
			raise InvalidCacheBackendError(
				"Could not find backend '%s': %s" % (backend, e))
		return backend_cls(location, params)

	def all(self):
		return self.caches.values()


class CacheManager(object):

	__slots__ = '_app',

	def __init__(self):
		super(CacheManager, self).__setattr__('_app', None)

	def set_app(self, app):
		self.init_app(app)
		super(CacheManager, self).__setattr__('_app', app)

	def init_app(self, app):
		if 'cache' in app.extensions:
			warn('Cache already setup on app %s. Resetting.' % app.name, RuntimeWarning)

		app.config.setdefault('CACHES', {})
		app.extensions['cache'] = _AppCacheContainer(app)

		# @app.teardown_appcontext
		# def close_caches(response_or_exc):
		# 	# Some caches -- python-memcached in particular -- need to do a cleanup at the
		# 	# end of a request cycle. If not implemented in a particular backend
		# 	# cache.close is a no-op
		# 	for cache in app.extensions['cache'].all():
		# 		cache.close()

		# 	return response_or_exc

	def _get_app(self, app=None):
		"""Helper method that implements the logic to look up an application."""
		if app is not None:
			return app

		if current_app:
			return current_app

		if self._app is not None:
			return self._app

		raise RuntimeError(
			'Application not registered on cache instance and no application'\
			'bound to current context'
		)

	def backend(self, alias=DEFAULT_CACHE_ALIAS, app=None):
		app = self._get_app(app)
		return app.extensions['cache'].get_cache(alias)

	def __getitem__(self, alias):
		return self.backend(alias)

	def __getattr__(self, name):
		return getattr(self.backend(), name)

	def __setattr__(self, name, value):
		return setattr(self.backend(), name, value)

	def __delattr__(self, name):
		return delattr(self.backend(), name)

	def __contains__(self, key):
		return key in self.backend()

	def __eq__(self, other):
		return self.backend() == other

	def __ne__(self, other):
		return self.backend() != other


cache = CacheManager()
