import functools
import logging
import socket

from flex.conf import config
from flex.utils.module_loading import import_string
from flex.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
from flex.utils.decorators import locked_cached_property

from redis.exceptions import ConnectionError, ResponseError, TimeoutError


REDIS_LOGGER = getattr(config, "REDIS_LOGGER", None)

logger = logging.getLogger((REDIS_LOGGER or __name__))

_connection_errors = (TimeoutError, ResponseError, ConnectionError, socket.timeout)


NOTHING = object()


def omit_exception(method=None, return_value=None):
	"""
	Simple decorator that intercepts connection
	errors and ignores these if settings specify this.
	"""

	if method is None:
		return functools.partial(omit_exception, return_value=return_value)

	@functools.wraps(method)
	def _decorator(self, *args, **kwargs):
		try:
			return method(self, *args, **kwargs)
		except _connection_errors as e:
			if self._ignore_exceptions:
				if self._log_ignored_exceptions:
					logger.error(str(e))

				return return_value
			raise e
	return _decorator


class RedisCache(BaseCache):
	def __init__(self, url, options):

		params = config.app.namespace('REDIS_').new()
		params.setdefaults(options)

		super(RedisCache, self).__init__(params)
		self._url = url or params.get('url')

		self._client_cls = params.get("client_class", "redis.StrictRedis")
		if isinstance(self._client_cls, str):
			self._client_cls = import_string(self._client_cls)

		self._client_options = params.get('client_options', {})
		self._ignore_exceptions = params.get("ignore_exceptions", False)
		self._log_ignored_exceptions = params.get("log_ignored_exceptions", True)

	@locked_cached_property
	def client(self):
		return self._client_cls.from_url(self._url, **self._client_options)

	@omit_exception
	def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
		return self.client.set(
					self.make_key(key, version),
					self.encode(value),
					self.get_timeout(timeout)
				)

	@omit_exception
	def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
		return self.client.set(
					self.make_key(key, version),
					self.encode(value),
					self.get_timeout(timeout),
					nx=True
				)

	@omit_exception
	def _get(self, key, version=None):
		return self.client.get(self.make_key(key, version))

	def get(self, key, default=None, version=None):
		rv = self._get(key, version)
		if rv is not None:
			return self.decode(rv)

	@omit_exception
	def incr_version(self, key, delta=1, version=None):
		return super(RedisCache, self).incr_version(key, delta, version)

	@omit_exception
	def delete(self, key, version=None):
		return self.client.delete(self.make_key(key, version))

	@omit_exception
	def delete_pattern(self, pattern, version=None, count=None):
		c = 0
		for key in self.client.scan_iter(self.make_key(pattern, version), count):
			self.client.delete(key)
			c += 1
		return c

	@omit_exception
	def delete_many(self, keys, version=None):
		return self.client.delete(*(self.make_key(k, version) for k in keys))

	@omit_exception
	def incr(self, key, delta=1, version=None):
		return self.client.incr(self.make_key(key, version), delta)

	@omit_exception
	def decr(self, key, delta=1, version=None):
		return self.client.decr(self.make_key(key, version), delta)

	@omit_exception
	def has_key(self, key, version=None):
		return self.client.exists(self.make_key(key, version))

	# @omit_exception
	# def keys(self, *args, **kwargs):
	# 	return self.client.keys(*args, **kwargs)

	# @omit_exception
	# def iter_keys(self, pattern='*', version=None, count=None):
	# 	return self.client.scan_iter(self.make_key(pattern, version))

	@omit_exception
	def ttl(self, key, version=None):
		return self.client.ttl(self.make_key(key, version))

	@omit_exception
	def persist(self, key, version=None):
		return self.client.persist(self.make_key(key, version))

	@omit_exception
	def expire(self, key, timeout, version=None):
		return self.client.expire(self.make_key(key, version), timeout)

	@omit_exception
	def lock(self, key, version=None, timeout=None, sleep=0.1, blocking_timeout=None):
		return self.client.lock(self.make_key(key, version),
					timeout=timeout, sleep=sleep,
					blocking_timeout=blocking_timeout
				)

	@omit_exception
	def close(self, **kwargs):
		pass
