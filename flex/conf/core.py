import os
import types
import errno
from importlib import import_module
from threading import Lock
from flask.config import ConfigAttribute
from collections import namedtuple, Mapping
from flex.datastructures import AttrDict, AttrChainMap


from flex.utils.module_loading import import_string, import_strings
from flex.utils.local import Proxy


NOTHING = object()

# class ConfigProxy(LocalProxy):

# 	__slots__ = '__config_object__', ''

# 	def __init__(self, func, remember=False):
# 		object.__setattr__(self, '_ConfigProxy__config', None)
# 		def fn():
# 			rv = func(self.__current_config__)

# 		super(ConfigProxy, self).__init__()
# 		self.func = func
# 		self.remember = remember



class LazyConfigVar(object):

	__slots__ = ('_func', '_cached', '_config', '__name__', '_lock')

	def __init__(self, func, cached=True, name=None, config=None):
		self._func = func
		self.__name__ = name or func.__name__
		self._cached = cached
		self._config = config
		if self._cached and self._config is not None:
			self._lock = Lock()

	def clone(self, config=None, name=None, cached=None):
		config = self._config if config is None else config
		cached = self._cached if cached is None else cached
		name = name or self.__name__
		return self.__class__(self._func, cached=cached, name=name, config=config)

	def proxy(self, config=None, name=None, cached=None):
		return Proxy(self.clone(config=config, name=name, cached=cached))

	def __call__(self, *args, **kwargs):
		if self._cached and self._config is not None:
			with self._lock:
				rv = self._func(self._config, *args, **kwargs)
				self._config[self.__name__] = rv
				return rv
		else:
			return self._func(self._config, *args, **kwargs)


def lazy(*func, cached=True, name=None):
	def wrapped(fn):
		return LazyConfigVar(fn, cached=cached, name=name)
	return wrapped if not func else wrapped(func[0])


def lazy_import(value, name=None, package=None, silent=False):
	def import_func(config):
		return import_strings(value, package=package, silent=silent)
	return LazyConfigVar(import_func, cached=True, name=name)



class Config(AttrChainMap):

	__slots__ = 'root_path',

	def __init__(self, root_path, *bases):
		super(Config, self).__init__(*bases)
		self.setattr('root_path', root_path)
		self.setdefault('bootstrapped', False)

	def bootstrap(self):
		for k in self:
			v = str(self.get(k))
		self.bootstrapped = True

	def from_envvar(self, variable_name, silent=False):
		"""Loads a configuration from an environment variable pointing to
		a configuration file.  This is basically just a shortcut with nicer
		error messages for this line of code::

			app.config.from_pyfile(os.environ['YOURAPPLICATION_SETTINGS'])

		:param variable_name: name of the environment variable
		:param silent: set to ``True`` if you want silent failure for missing
					   files.
		:return: bool. ``True`` if able to load config, ``False`` otherwise.
		"""
		paths = os.environ.get(variable_name)
		if not paths:
			if silent:
				return False
			raise RuntimeError('The environment variable %r is not set '
					'and as such configuration could not be '
					'loaded.  Set this variable and make it '
					'point to a configuration file' %
					variable_name
				)
		rv = False
		for path in paths.split(os.pathsep):
			path = path.strip()
			if path:
				rv = self.from_pyfile(path, silent=silent)
		return rv

	def from_pyfile(self, name, silent=False):
		"""Updates the values in the config from a Python file.  This function
		behaves as if the file was imported as module with the
		:meth:`from_object` function.

		:param name: the filename or module name of the config. This can either
					be a module name, an absolute filename or a filename relative
					to the root path.
		:param silent: set to ``True`` if you want silent failure for missing
					   files.
		"""

		# If the given name does not look like a filename, we try loading as a module.
		if os.sep not in name and name[-3:] != '.py' and name[-4:] != '.cfg':
			try:
				module = import_module(name)
			except ImportError:
				pass
			else:
				if module is not None:
					self.from_object(module)
					return True

		filename = os.path.join(self.root_path, name)
		d = types.ModuleType('config')
		d.__file__ = filename
		try:
			with open(filename, mode='rb') as config_file:
				exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
		except IOError as e:
			if silent and e.errno in (errno.ENOENT, errno.EISDIR):
				return False
			e.strerror = 'Unable to load configuration file (%s)' % e.strerror
			raise e

		self.from_object(d)
		return True

	def from_object(self, obj):
		"""Updates the values from the given object.  An object can be of one
		of the following two types:

		-   a string: in this case the object with that name will be imported
		-   an actual object reference: that object is used directly

		Objects are usually either modules or classes. :meth:`from_object`
		loads only the uppercase attributes of the module/class. A ``dict``
		object will not work with :meth:`from_object` because the keys of a
		``dict`` are not attributes of the ``dict`` class.

		Example of module-based configuration::

			app.config.from_object('yourapplication.default_config')
			from yourapplication import default_config
			app.config.from_object(default_config)

		You should not use this function to load the actual configuration but
		rather configuration defaults.  The actual config should be loaded
		with :meth:`from_pyfile` and ideally from a location not within the
		package because the package might be installed system wide.

		See :ref:`config-dev-prod` for an example of class-based configuration
		using :meth:`from_object`.

		:param obj: an import name or object
		"""
		if isinstance(obj, str):
			obj = import_string(obj)
		for key in dir(obj):
			if key.isupper():
				self[key] = getattr(obj, key)

	def from_json(self, filename, silent=False):
		"""Updates the values in the config from a JSON file. This function
		behaves as if the JSON object was a dictionary and passed to the
		:meth:`from_mapping` function.

		:param filename: the filename of the JSON file.  This can either be an
						 absolute filename or a filename relative to the
						 root path.
		:param silent: set to ``True`` if you want silent failure for missing
					   files.
		"""
		filename = os.path.join(self.root_path, filename)

		from flex.utils import json

		try:
			with open(filename) as json_file:
				obj = json.loads(json_file.read())
		except IOError as e:
			if silent and e.errno in (errno.ENOENT, errno.EISDIR):
				return False
			e.strerror = 'Unable to load configuration file (%s)' % e.strerror
			raise
		return self.from_mapping(obj)

	def from_mapping(self, *mapping, **kwargs):
		"""Updates the config like :meth:`update` ignoring items with non-upper
		keys.
		"""
		mappings = []
		if len(mapping) == 1:
			if hasattr(mapping[0], 'items'):
				mappings.append(mapping[0].items())
			else:
				mappings.append(mapping[0])
		elif len(mapping) > 1:
			raise TypeError(
				'expected at most 1 positional argument, got %d' % len(mapping)
			)
		mappings.append(kwargs.items())
		for mapping in mappings:
			for (key, value) in mapping:
				if key.isupper():
					self[key] = value
		return True

	def from_(self, *methods, silent=False):
		"""Updates the config from given (method, value) iterable.
		"""
		rv = {}
		for src, value in methods:
			meth = getattr(self, 'from_%s' % (src or '?'), None)
			if not meth:
				raise ValueError('Invalid configuration method %s.' % (src,))
			rv[src] = meth(value, silent=silent)
		return rv

	def setdefaults(self, *mapping, **kwargs):
		"""Updates the config like :meth:`update` ignoring existing items.
		"""
		mappings = []
		if len(mapping) == 1:
			if hasattr(mapping[0], 'items'):
				mappings.append(mapping[0].items())
			else:
				mappings.append(mapping[0])
		elif len(mapping) > 1:
			raise TypeError(
				'expected at most 1 positional argument, got %d' % len(mapping)
			)
		mappings.append(kwargs.items())
		for mapping in mappings:
			for key, value in mapping:
				self.setdefault(key, value)

	def namespace(self, namespace, lowercase=True, trim_namespace=True):
		"""Returns a Config object containing a subset of configuration options
		that match the specified namespace/prefix. Example usage::

			app.config['IMAGE_STORE_TYPE'] = 'fs'
			app.config['IMAGE_STORE_PATH'] = '/var/app/images'
			app.config['IMAGE_STORE_BASE_URL'] = 'http://img.website.com'
			image_store_config = app.config.get_namespace('IMAGE_STORE_')

		The resulting dictionary `image_store_config` would look like::

			{
				'type': 'fs',
				'path': '/var/app/images',
				'base_url': 'http://img.website.com'
			}

		This is often useful when configuration options map directly to
		keyword arguments in functions or class constructors.

		:param namespace: a configuration namespace
		:param lowercase: a flag indicating if the keys of the resulting
						  dictionary should be lowercase
		:param trim_namespace: a flag indicating if the keys of the resulting
						  dictionary should not include the namespace

		.. versionadded:: 0.11
		"""
		return Config(
				self.root_path,
				self.get_namespace_view(namespace, lowercase, trim_namespace)
			)

	def get_namespace(self, namespace, lowercase=True, trim_namespace=True):
		"""Returns a dictionary containing a subset of configuration options
		that match the specified namespace/prefix. Example usage::

			app.config['IMAGE_STORE_TYPE'] = 'fs'
			app.config['IMAGE_STORE_PATH'] = '/var/app/images'
			app.config['IMAGE_STORE_BASE_URL'] = 'http://img.website.com'
			image_store_config = app.config.get_namespace('IMAGE_STORE_')

		The resulting dictionary `image_store_config` would look like::

			{
				'type': 'fs',
				'path': '/var/app/images',
				'base_url': 'http://img.website.com'
			}

		This is often useful when configuration options map directly to
		keyword arguments in functions or class constructors.

		:param namespace: a configuration namespace
		:param lowercase: a flag indicating if the keys of the resulting
						  dictionary should be lowercase
		:param trim_namespace: a flag indicating if the keys of the resulting
						  dictionary should not include the namespace
		"""
		return self.get_namespace_view(namespace, lowercase, trim_namespace).copy()

	def get_namespace_view(self, namespace, lowercase=True, trim_namespace=True):
		"""Returns a ConfigView of config options that match the specified
		namespace/prefix.
		"""
		return ConfigView(
				self,
				namespace_key_func(
					namespace,
					lowercase=lowercase,
					trim_namespace=trim_namespace
				)
			)

	def __setitem__(self, key, value):
		if isinstance(value, LazyConfigVar):
			value = value.proxy(self, name=key)
		super(Config, self).__setitem__(key, value)




def namespace_key_func(namespace, lowercase=True, trim_namespace=True):
	def make_key(key, reverse=False):
		if reverse:
			if lowercase:
				key = key.upper()
			if trim_namespace:
				key = namespace + key
			return key

		if key.startswith(namespace):
			if lowercase:
				key = key.lower()
			if trim_namespace:
				key = key[len(namespace):]
			return key

	return make_key



class ConfigView(AttrDict):

	__slots__ = '_base', 'make_key',

	def __init__(self, config, key_func):
		super(ConfigView, self).__init__()
		self.setattr('_base', config)
		self.setattr('make_key', key_func)

	def __len__(self):
		return sum((1 for k in self))

	def __iter__(self):
		for key in self._base:
			yv = self.make_key(key)
			if yv is not None:
				yield yv

	def __bool__(self):
		return any(self)

	def __getitem__(self, key):
		return self._base[self.make_key(key, True)]

	def __setitem__(self, key, value):
		self._base[self.make_key(key, True)] = value

	def __delitem__(self, key):
		del self._base[self.make_key(key, True)]

	def copy(self):
		return AttrDict(self.items())




