from flask import current_app
from threading import Lock
from flex.utils.module_loading import import_string


__all__ = ('RedisManager', 'redis')


class _Connector(object):

	__slots__ = ('app', 'lock', '_client', 'config')

	def __init__(self, app, config):
		self.app = app
		self.config = config
		self._client = None
		self.lock = Lock()

	@property
	def client(self):
		with self.lock:
			if self._client is None:
				cls = self.config.CLIENT_CLASS
				if isinstance(cls, str):
					cls = import_string(cls)
				self._client = cls.from_url(
						self.config.URL,
						**self.config.CLIENT_OPTIONS
					)
			return self._client


class RedisManager(object):

	__slots__ = ('_app', )

	config_prefix = 'REDIS_'

	default_config = dict(
		url='redis://localhost:6379/0',
		client_class='redis.StrictRedis',
		client_options={}
	)

	def __init__(self, app=None):
		self._app = None
		if app is not None:
			self.init_app(app)
			self._app = app

	@property
	def _redis_client(self):
		try:
			return self._get_app().extensions['redis'].client
		except KeyError:
			raise RuntimeError('Redis not setup on app.')

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

	def init_app(self, app, **kwargs):
		config = app.config.namespace(self.config_prefix)
		config.setdefaults(self.default_config)

		app.extensions['redis'] = _Connector(app, config)

	def __getattr__(self, name):
		return getattr(self._redis_client, name)

	def __getitem__(self, name):
		return self._redis_client[name]

	def __setitem__(self, name, value):
		self._redis_client[name] = value

	def __delitem__(self, name):
		del self._redis_client[name]


redis = RedisManager()