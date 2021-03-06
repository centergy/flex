"Base Cache class."

import time
import warnings
from datetime import timedelta

from flex.core.exc import ImproperlyConfigured
from flex.utils.module_loading import import_string


class InvalidCacheBackendError(ImproperlyConfigured):
	pass


class CacheKeyWarning(RuntimeWarning):
	pass


# Stub class to ensure not passing in a `timeout` argument results in
# the default timeout
DEFAULT_TIMEOUT = object()

# Memcached does not accept keys longer than this.
MEMCACHE_MAX_KEY_LENGTH = 250


def default_key_func(key, prefix=None, version=None, reverse=False):
	"""Default function to generate keys.

	Constructs the key used by all other methods. By default it prepends
	the `key_prefix'. KEY_FUNCTION can be used to specify an alternate
	function with custom key making behavior.
	"""
	if reverse:
		return key.split(':', 2)[-1]
	else:
		return ':'.join(str(v) for v in (prefix, version, key) if v)


def get_key_func(key_func):
	"""Function to decide which key function to use.

	Defaults to ``default_key_func``.
	"""
	if key_func is not None:
		if callable(key_func):
			return key_func
		else:
			return import_string(key_func)
	return default_key_func



class BaseCache(object):

	def __init__(self, params):
		timeout = params.get('timeout', 300)
		if timeout is not None:
			try:
				if isinstance(timeout, timedelta):
					timeout = timeout.total_seconds()
				timeout = int(timeout)
			except (ValueError, TypeError):
				timeout = 300
		self.default_timeout = timeout

		max_entries = params.get('max_entries', 300)
		try:
			self._max_entries = int(max_entries)
		except (ValueError, TypeError):
			self._max_entries = 300

		cull_frequency = params.get('cull_frequency', 3)
		try:
			self._cull_frequency = int(cull_frequency)
		except (ValueError, TypeError):
			self._cull_frequency = 3

		self._serializer = params.get('serializer', 'pickle')
		if self._serializer and isinstance(self._serializer, str):
			self._serializer = import_string(self._serializer)

		self.key_prefix = params.get('key_prefix')
		self.version = params.get('version', 1)
		self.key_func = self.get_key_func(params.get('key_function'))

	def get_key_func(self, func):
		return get_key_func(func)

	def get_timeout(self, timeout=DEFAULT_TIMEOUT):
		"""Returns the timeout value usable by this backend based upon the provided
		timeout.
		"""
		if timeout is None:
			return None
		elif timeout == DEFAULT_TIMEOUT:
			return self.default_timeout
		elif timeout == 0:
			return -1
		return int(timeout)

	def make_key(self, key, version=None, reverse=False):
		"""Constructs the key used by all other methods. By default it
		uses the key_func to generate a key (which, by default,
		prepends the `key_prefix' and 'version'). A different key
		function can be provided at the time of cache construction;
		alternatively, you can subclass the cache backend to provide
		custom key making behavior.
		"""
		if reverse:
			return self.key_func(key, self.key_prefix, reverse=True)

		if version is None:
			version = self.version

		return self.key_func(key, self.key_prefix, version=version)

	def encode(self, value):
		return value if not self._serializer else self._serializer.dumps(value)

	def decode(self, value):
		return value if not self._serializer else self._serializer.loads(value)

	def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Set a value in the cache if the key does not already exist. If
		timeout is given, that timeout will be used for the key; otherwise
		the default cache timeout will be used.

		Returns True if the value was stored, False otherwise.
		"""
		raise NotImplementedError('subclasses of BaseCache must provide an add() method')

	def get(self, key, default=None, version=None):
		"""
		Fetch a given key from the cache. If the key does not exist, return
		default, which itself defaults to None.
		"""
		raise NotImplementedError('subclasses of BaseCache must provide a get() method')

	def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Set a value in the cache. If timeout is given, that timeout will be
		used for the key; otherwise the default cache timeout will be used.
		"""
		raise NotImplementedError('subclasses of BaseCache must provide a set() method')

	def delete(self, key, version=None):
		"""
		Delete a key from the cache, failing silently.
		"""
		raise NotImplementedError('subclasses of BaseCache must provide a delete() method')

	def get_many(self, keys, version=None):
		"""
		Fetch a bunch of keys from the cache. For certain backends (memcached,
		pgsql) this can be *much* faster when fetching multiple values.

		Returns a dict mapping each key in keys to its value. If the given
		key is missing, it will be missing from the response dict.
		"""
		d = {}
		for k in keys:
			val = self.get(k, version=version)
			if val is not None:
				d[k] = val
		return d

	def get_or_set(self, key, default, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Fetch a given key from the cache. If the key does not exist,
		the key is added and set to the default value. The default value can
		also be any callable. If timeout is given, that timeout will be used
		for the key; otherwise the default cache timeout will be used.

		Return the value of the key stored or retrieved.
		"""
		val = self.get(key, version=version)
		if val is None and default is not None:
			if callable(default):
				default = default()
			self.add(key, default, timeout=timeout, version=version)
			# Fetch the value again to avoid a race condition if another caller
			# added a value between the first get() and the add() above.
			return self.get(key, default, version=version)
		return val

	def has_key(self, key, version=None):
		"""
		Returns True if the key is in the cache and has not expired.
		"""
		return self.get(key, version=version) is not None

	def incr(self, key, delta=1, default=None, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Add delta to value in the cache. If the key does not exist, raise a
		ValueError exception.
		"""
		value = self.get(key, version=version)
		if value is None:
			if default is not None:
				self.set(key, default, timeout=timeout, version=version)
				return default
			else:
				raise ValueError("Key '%s' not found" % key)

		new_value = value + delta
		self.set(key, new_value, version=version)
		return new_value

	def decr(self, key, delta=1, default=None, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Subtract delta from value in the cache. If the key does not exist, raise
		a ValueError exception.
		"""
		return self.incr(key, -delta, default=default, timeout=timeout, version=version)

	def __contains__(self, key):
		"""
		Returns True if the key is in the cache and has not expired.
		"""
		# This is a separate method, rather than just a copy of has_key(),
		# so that it always has the same functionality as has_key(), even
		# if a subclass overrides it.
		return self.has_key(key)

	def lock(self, key, version=None, timeout=None, blocking_timeout=None):
		"""Return a new Lock object for key that mimics the behavior of threading.Lock.
		"""
		raise NotImplementedError('subclasses of BaseCache must provide a lock() method')

	def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
		"""
		Set a bunch of values in the cache at once from a dict of key/value
		pairs.  For certain backends (memcached), this is much more efficient
		than calling set() multiple times.

		If timeout is given, that timeout will be used for the key; otherwise
		the default cache timeout will be used.
		"""
		for key, value in data.items():
			self.set(key, value, timeout=timeout, version=version)

	def delete_many(self, keys, version=None):
		"""
		Delete a bunch of values in the cache at once. For certain backends
		(memcached), this is much more efficient than calling delete() multiple
		times.
		"""
		for key in keys:
			self.delete(key, version=version)

	def clear(self):
		"""Remove *all* values from the cache at once."""
		raise NotImplementedError('subclasses of BaseCache must provide a clear() method')

	def validate_key(self, key):
		"""
		Warn about keys that would not be portable to the memcached
		backend. This encourages (but does not force) writing backend-portable
		cache code.
		"""
		if len(key) > MEMCACHE_MAX_KEY_LENGTH:
			warnings.warn(
				'Cache key will cause errors if used with memcached: %r '
				'(longer than %s)' % (key, MEMCACHE_MAX_KEY_LENGTH), CacheKeyWarning
			)
		for char in key:
			if ord(char) < 33 or ord(char) == 127:
				warnings.warn(
					'Cache key contains characters that will cause errors if '
					'used with memcached: %r' % key, CacheKeyWarning
				)
				break

	def incr_version(self, key, delta=1, version=None):
		"""Adds delta to the cache version for the supplied key. Returns the
		new version.
		"""
		if version is None:
			version = self.version

		value = self.get(key, version=version)
		if value is None:
			raise ValueError("Key '%s' not found" % key)

		self.set(key, value, version=version + delta)
		self.delete(key, version=version)
		return version + delta

	def decr_version(self, key, delta=1, version=None):
		"""Subtracts delta from the cache version for the supplied key. Returns
		the new version.
		"""
		return self.incr_version(key, -delta, version)

	def close(self, **kwargs):
		"""Close the cache connection"""
		pass
