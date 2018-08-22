import os
from warnings import warn
from flask import current_app
from .core import Config, lazy
from . import default_config
from flex.utils.local import LocalProxy
from flex.utils.lazy import LazyObject, empty
from flex.core.exc import ImproperlyConfigured


ENVIRONMENT_VARIABLE = 'FLEX_CONFIG_PATH'

ROOT_PATH_ENVAR = 'FLEX_ROOT_DIR'


class LazyConfig(LazyObject):
	"""
	A lazy proxy for either global Django settings or a custom settings object.
	The user can manually configure settings prior to using them. Otherwise,
	Django uses the settings module pointed to by DJANGO_SETTINGS_MODULE.
	"""
	__slots__ = ()

	def _setup(self, name=None):
		"""Load the config path pointed to by the environment variable.
		"""
		config_path = os.environ.get(ENVIRONMENT_VARIABLE)
		if not config_path:
			desc = ("config %s" % name) if name else "config"
			raise ImproperlyConfigured(
				"Requested %s, but configuration has not been initialized. "
				"You must either define the environment variable %s "
				"or call config.initialize() before accessing configurations."
				% (desc, ENVIRONMENT_VARIABLE))

		root_path = os.environ.get(ROOT_PATH_ENVAR)
		if not root_path:
			root_path = os.getcwd()
			warn(
				'Environment variable %s for config root path not defined. '
				'The current working directory %s will be used instead.'
				% (ROOT_PATH_ENVAR, root_path), RuntimeWarning
			)

		self._wrapped = Config(root_path)
		self._wrapped.from_object(default_config)
		self._wrapped.from_envvar(ENVIRONMENT_VARIABLE)

	def __repr__(self):
		if self._wrapped is empty:
			return '<LazyConfig [Unevaluated]>'
		return '<LazyConfig %s>' % str(self._wrapped)

	@property
	def top(self):
		"""Returns configuration for the current_app if any."""
		if current_app:
			return current_app.config
		return self

	@property
	def _config(self):
		if self._wrapped is empty:
			self._setup()
		return self._wrapped

	@property
	def has_init(self):
		"""Returns True if the configuration has already been initialized."""
		return self._wrapped is not empty



config = LazyConfig()
