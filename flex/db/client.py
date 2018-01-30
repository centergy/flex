import warnings
from sqlservice import SQLClient
from sqlalchemy import orm
from .query import Query
from .session import Session
from .model import declarative_base
from .utils import _set_app_state, _get_app_state
from flask import current_app, _app_ctx_stack
from threading import Lock
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.engine.url import make_url
import sqlalchemy_utils as sa_utils

from .cli import console
from .migrations import Migrate
import copy

from flex.utils.module_loading import import_strings
from flex.datastructures import ChainMap
from flex.utils.local import Proxy

try:
	from sqlalchemy_mptt import mptt_sessionmaker
	mptt_session = True
except ImportError as e:
	mptt_session = False

from .managers import manager_property, archives_manager_property

_confkey = 'SQLALCHEMY'

_config_namespace = 'SQLALCHEMY_'

NOTHING = object()


class _EngineConnector(object):

	__slots__ = ('_client',
				'_engine', '_connected_for',
				'_bind', '_lock', '_config')

	def __init__(self, client, app, bind=None, config=None):
		self._client = client
		# self._app = app
		self._engine = None
		self._connected_for = None
		self._bind = bind
		self._lock = Lock()
		self._config = config or app.config.namespace(_config_namespace)

	def get_uri(self):
		return self._client.get_bind_uri(self._bind, config=self._config)

	def get_engine(self):
		with self._lock:
			uri = self.get_uri()
			echo = self._config['ECHO']
			if (uri, echo) == self._connected_for:
				return self._engine

			options = self._client.make_engine_options(self._config)
			rv = self._engine = self._client.create_engine(uri, options)
			self._connected_for = (uri, echo)
			return rv


class _QueryProperty(object):
	def __init__(self, client):
		self.client = client

	def __get__(self, obj, type):
		try:
			mapper = orm.class_mapper(type)
			if mapper:
				return type._opts.query_class(mapper, session=self.client.session)
		except UnmappedClassError:
			return None


class Client(SQLClient):

	default_config = {
		'DATABASE_URI': 'sqlite:///:memory:',
		'BINDS': {},
		'DEFAULT_BINDS': {},
		'BIND_KEY_CONTEXT': {},
		'BIND_KEY_PROCESSORS' : (),
		'BIND_PROVIDERS': (),
		'ECHO': False,
		'ECHO_POOL': False,
		'ENCODING': 'utf8',
		'CONVERT_UNICODE': None,
		'ISOLATION_LEVEL': None,
		'POOL_SIZE': None,
		'POOL_TIMEOUT': None,
		'POOL_RECYCLE': None,
		'MAX_OVERFLOW': None,
		'AUTOCOMMIT': False,
		'AUTOFLUSH': True,
		'EXPIRE_ON_COMMIT': True,
		'COMMIT_ON_TEARDOWN' : False,
	}

	def __init__(self, app=None, model_class=None, metadata=None, query_class=Query,
				 session_class=Session,  session_options=None):
		self.app = None
		self.query_class = query_class
		self.model_class = self.make_declarative_base(model_class, metadata=metadata)

		self.session_class = session_class
		self._engine_lock = Lock()

		if session_options is None:
			session_options = {}

		self.session = self.create_scoped_session(**session_options)

		self.update_models_registry()

		self.migrations = Migrate(db=self)

		if app is not None:
			self.set_app(app)

	@property
	def Model(self):
		return self.model_class

	@property
	def engine(self):
		return self.get_engine()

	def make_declarative_base(self, model_class, metadata=None):
		model = declarative_base(cls=model_class, metadata=metadata)
		model.query = _QueryProperty(self)
		model.objects = manager_property(using=self)
		model.archives = archives_manager_property(using=self)
		model._db_client = self
		return model

	def database_exists(self, bind=None, engine=None):
		engine = engine or self.get_engine(bind=bind)
		return sa_utils.database_exists(engine.url)

	def create_database(self, *binds, encoding='utf8', template=None):
		binds = binds or (None,) + tuple(self.get_config().BINDS.keys())
		for bind in binds:
			engine = self.get_engine(bind=bind)
			if not self.database_exists(engine=engine):
				sa_utils.create_database(engine.url, encoding, template)

	def drop_database(self, *binds):
		binds = binds or (None,) + tuple(self.get_config().BINDS.keys())
		for bind in binds:
			engine = self.get_engine(bind=bind)
			if self.database_exists(engine=engine):
				sa_utils.drop_database(engine.url)

	def make_engine_connector(self, app=None, bind=None, config=None):
		"""Creates the connector for a given state and bind."""
		return _EngineConnector(self, self.get_app(app), bind=bind, config=config)

	def get_engine(self, app=None, bind=None):
		"""Returns a specific engine."""
		app = self.get_app(app)
		state = _get_app_state(app)
		config = self.get_config(app)

		with self._engine_lock:
			bind = self.get_bind_key(bind, config=config)

			connector = state.connectors.get(bind)

			if connector is None:
				connector = self.make_engine_connector(app, bind, config)
				state.connectors[bind] = connector

			return connector.get_engine()

	def get_bind_uri(self, bind_key, config=None, app=None, silent=False):
		if config is None:
			config = self.get_config(app)

		if bind_key is None:
			return config.DATABASE_URI

		try:
			return config.BINDS[bind_key]
		except KeyError:
			if not silent:
				raise KeyError(
					'Invalid bind key %r. Set it in the SQLALCHEMY_BINDS '\
					'configuration variable or provide it via '\
					'SQLALCHEMY_BIND_PROVIDERS' % bind_key
				)

	def get_bind_key(self, bind_key, config=None, app=None):
		if not bind_key:
			return bind_key

		if config is None:
			config = self.get_config(app)

		return bind_key % config.BIND_KEY_CONTEXT

	def get_app(self, reference_app=None):
		"""Helper method that implements the logic to look up an application."""
		if reference_app is not None:
			return reference_app

		if current_app:
			return current_app

		if self.app is not None:
			return self.app

		raise RuntimeError(
			'Application not registered on db instance and no application'\
			'bound to current context'
		)

	def get_config(self, app=None):
		app = self.get_app(app)
		return app.config.namespace(_config_namespace)

	def set_app(self, app):
		self.app = app
		self.init_app(app)

	def init_app(self, app):
		"""This callback can be used to initialize an application for the
		use with this database setup.  Never use a database in the context
		of an application not initialized that way or connections will
		leak.
		"""

		config = self.get_config(app)

		if not config:
			warnings.warn(
				'DATABASE config not set. Defaulting to %s' % (self.default_config,),
				RuntimeWarning
			)

		self.init_config(config)

		_set_app_state(self, app)

		self.migrations.init_app(app)

		app.add_cli_command('db', console)

		@app.teardown_appcontext
		def shutdown_session(response_or_exc):
			if self.get_config(app).get('COMMIT_ON_TEARDOWN'):
				if response_or_exc is None:
					self.commit()

			self.remove()
			return response_or_exc

	def init_config(self, config):
		config.setdefaults(self.default_config)

		config.BIND_KEY_PROCESSORS = import_strings(config.BIND_KEY_PROCESSORS)
		if not isinstance(config.BIND_KEY_PROCESSORS, (list, tuple)):
			config.BIND_KEY_PROCESSORS = [config.BIND_KEY_PROCESSORS,]

		bind_key_cxt = ChainMap()
		for processor in config.BIND_KEY_PROCESSORS:
			bind_key_cxt.shift(Proxy(processor))

		config.BIND_KEY_CONTEXT = bind_key_cxt

		config.BIND_PROVIDERS = import_strings(config.BIND_PROVIDERS)
		if not isinstance(config.BIND_PROVIDERS, (list, tuple)):
			config.BIND_PROVIDERS = [config.BIND_PROVIDERS,]

		config.DEFAULT_BINDS = config.BINDS

		binds = ChainMap(config.DEFAULT_BINDS)
		for provider in config.BIND_PROVIDERS:
			binds.shift(Proxy(provider))
		config.BINDS = binds

	def make_engine_options(self, config):
		"""Return engine options from :attr:`config` for use in
		``sqlalchemy.create_engine``.
		"""
		return self._make_options(config, (
			('ECHO', 'echo'),
			('ECHO_POOL', 'echo_pool'),
			('ENCODING', 'encoding'),
			('CONVERT_UNICODE', 'convert_unicode'),
			('ISOLATION_LEVEL', 'isolation_level'),
			('POOL_SIZE', 'pool_size'),
			('POOL_TIMEOUT', 'pool_timeout'),
			('POOL_RECYCLE', 'pool_recycle'),
			('MAX_OVERFLOW', 'max_overflow')
		))

	def make_session_options(self, config, extra_options=None):
		"""Return session options from :attr:`config` for use in
		``sqlalchemy.orm.sessionmaker``.
		"""
		options = self._make_options(config, (
			('AUTOCOMMIT', 'autocommit'),
			('AUTOFLUSH', 'autoflush'),
			('EXPIRE_ON_COMMIT', 'expire_on_commit')
		))

		if extra_options:
			options.update(extra_options)

		return options

	def _make_options(self, config, key_mapping):
		"""Return mapped :attr:`config` options using `key_mapping` which is a
		tuple having the form ``((<config_key>, <sqlalchemy_key>), ...)``.
		Where ``<sqlalchemy_key>`` is the corresponding option keyword for a
		SQLAlchemy function.
		"""
		return {opt_key: config[cfg_key]
				for cfg_key, opt_key in key_mapping
				if config.get(cfg_key) is not None}

	def get_model(self, name, default=NOTHING):
		model = self.models.get(name, default)
		if model is not NOTHING:
			return model
		raise KeyError('Invalid model name "{}"'.format(name))

	def create_session(self, **options):
		session_class = options.pop('session_class', self.session_class)
		options.setdefault('query_cls', self.query_class)
		factory = orm.sessionmaker(class_=session_class, db=self, **options)
		return mptt_sessionmaker(factory) if mptt_session else factory

	def create_scoped_session(self, **options):
		scopefunc = options.pop('scopefunc', _app_ctx_stack.__ident_func__)
		factory = self.create_session(**options)
		return orm.scoped_session(factory, scopefunc=scopefunc)

	def __getattr__(self, key):
		raise AttributeError(key)





