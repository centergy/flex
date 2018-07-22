from .models import Option
from flex.cache import cache, DEFAULT_CACHE_ALIAS
from flex.datastructures.collections import MutableNestedMapping
from collections import MutableMapping
import flask as fl
from flex.db import db


class OptionsManager(MutableNestedMapping):
	__slots__ = ()

	_default_config = dict(
		CACHE_BACKEND='options',

	)

	_default_cache_backend_config = dict(
		timeout=86400,
	)

	@property
	def cache_backend_alias(self):
		return fl.current_app.config['OPTIONS_CACHE_BACKEND']

	@property
	def cache_backend(self):
		return cache.backend(self.cache_backend_alias)

	def init_app(self, app):
		config = app.config.namespace('OPTIONS_')
		config.setdefaults(self._default_config)

		if not app.config.CACHES:
			raise RuntimeError(
				'App flex.apps.options requires flex.cache.cache '
				'installed and configured.'
			)

		cacheconf = app.config.CACHES.setdefault(config.CACHE_BACKEND, {})
		default_cacheconf = app.config.CACHES.get(DEFAULT_CACHE_ALIAS, {})

		assert cacheconf is not default_cacheconf, (
			'Options cannot use the default cache backend.'
		)
		default_cacheconf = default_cacheconf.copy()
		default_cacheconf.update(self._default_cache_backend_config)

		keyprefix = default_cacheconf.get('key_prefix') or app.config.get('APP_NAME')
		cacheconf.setdefault('key_prefix', keyprefix and '%s:APP_OPTION' % (keyprefix,))
		for k, v in default_cacheconf.items():
			cacheconf.setdefault(k, v)

	def __getrootitem__(self, key):
		rv = self.cache_backend.get(key)
		if rv is None:
			rv = Option.mgr.get_by_key(key)
			if rv:
				self.cache_backend.set(key, rv.value)
				return rv.value
		else:
			return rv
		raise KeyError('Option %s not found.' % (key,))

	def __setrootitem__(self, key, value):
		kv = Option.mgr.get_by_key(key)
		if value is None:
			kv and kv.delete()
			self.cache_backend.delete(key)
		else:
			self.cache_backend.set(key, value)
			kv = kv or Option(key=key)
			kv.value = value
			kv.save()

	def __delrootitem__(self, key):
		kv = Option.mgr.get_by_key(key)
		if not kv:
			raise KeyError('Option %s not found.' % (key,))

		self.cache_backend.delete(key)
		kv and kv.delete()


options = OptionsManager()