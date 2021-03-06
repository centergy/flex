import os
import inspect
import traceback
from flask import Flask
from threading import local
from flask.helpers import find_package
from flask.app import setupmethod
from functools import update_wrapper

from flex.utils import json
from flex.http import Request, Response
from flex.datastructures import AttrDict
from flex.conf import Config, config as global_config
from flex.utils.decorators import locked_cached_property
from flex.utils.module_loading import import_string, import_strings

from . import signals
from .cli import Manager, Shell, Server, install_command
from .sessions import SecureCookieSessionInterface
from .exc import ImproperlyConfigured



def postboot_method(f):
	"""Wraps a method so that it performs a check if the application has been
	bootstrapped.
	"""
	def wrapper_func(self, *args, **kwargs):
		if not self._has_booted:
			raise AssertionError('A startup function was called before the '
				'application was bootstrapped. Make sure the you bootstrap '
				'the application before running it.')
		return f(self, *args, **kwargs)
	return update_wrapper(wrapper_func, f)



def preboot_method(f):
	"""Wraps a method so that it performs a check if the application has been
	bootstrapped.
	"""
	def wrapper_func(self, *args, **kwargs):
		if self._has_booted:
			raise AssertionError('A pre-bootstrap function was called after '
				'the application was bootstrapped.')
		return f(self, *args, **kwargs)
	return update_wrapper(wrapper_func, f)



class Kernel(Flask):

	is_cli = True

	config_class = Config

	request_class = Request

	response_class = Response

	session_interface = SecureCookieSessionInterface()

	#: The JSON encoder class to use. Defaults to :class:`~flex.utils.json.JSONEncoder`.
	json_encoder = json.JSONEncoder

	#: The JSON decoder class to use.  Defaults to :class:`~flex.utils.json.JSONDecoder`.
	json_decoder = json.JSONDecoder

	def __init__(self, import_name, static_url_path=None,
				public_folder=None, static_folder=None, template_folder='templates',
				instance_path=None,	instance_relative_config=False,
				root_path=None):


		if public_folder is not None and  static_folder is None:
			public_folder = '' if public_folder is True else public_folder
			static_folder = os.path.join(global_config.PUBLIC_PATH, public_folder)
		elif static_folder is None:
			static_folder = 'static'

		kwargs = dict(static_url_path=static_url_path,
			static_folder=static_folder,template_folder=template_folder,
			instance_path=instance_path, root_path=root_path,
			instance_relative_config=instance_relative_config
		)

		super(Kernel, self).__init__(import_name, **kwargs)
		self.extensions = AttrDict()
		self._has_booted = False

	@locked_cached_property
	def console(self):
		if self.is_cli:
			rv = Manager(self, with_default_commands=False)
			rv.add_command("start", Server(host=self.config.HOST, port=self.config.PORT))
			rv.add_command("shell", Shell())
			rv.command(install_command, name="install")
			return rv

	@locked_cached_property
	def content_negotiator(self):
		return import_strings(self.config.CONTENT_NEGOTIATOR)()

	@locked_cached_property
	def renderers(self):
		return [r() for r in import_strings(self.config.RENDERERS)]

	@setupmethod
	@preboot_method
	def bootstrap(self):
		signals.app_booting.send(self)
		self.config.bootstrap()
		self.init_default_addons()
		self.init_configured_addons()
		self._has_booted = True
		signals.app_booted.send(self)

	def make_config(self, instance_relative=False):
		"""Used to create the config attribute by the Flask constructor.
		The `instance_relative` parameter is passed in from the constructor
		of Flask (there named `instance_relative_config`) and indicates if
		the config should be relative to the instance path or the root path
		of the application.
		"""
		assert issubclass(self.config_class, Config), (
			"Class/subclass of '%s' is the preferred type for configuration." \
			% (Config,)
		)

		root_path = self.instance_path if instance_relative else self.root_path
		rv = self.config_class(root_path, {}, global_config)
		rv.setdefaults(self.default_config)
		# rv.bootstrap()
		return rv

	def auto_find_instance_path(self):
		"""Tries to locate the instance path if it was not provided to the
		constructor of the application class.  It will basically calculate
		the path to a folder named ``instance`` next to your main file or
		the package.
		"""
		prefix, package_path = find_package(self.import_name)
		dir_name = self.get_instance_path_dir_name()
		if prefix is None:
			rv = os.path.abspath(os.path.join(package_path, dir_name))
			if not os.path.exists(rv):
				cwd = os.getcwd().rstrip('/')
				package_path = package_path.rstrip('/')
				if cwd != package_path and package_path.startswith(cwd):
					return os.path.abspath(os.path.join(cwd, dir_name))
		return os.path.abspath(os.path.join(prefix, 'var', dir_name))

	def get_instance_path_dir_name(self):
		return '.local/%s' % self.name

	@preboot_method
	def init_default_addons(self):
		"""Initialize addons configured under the ADDONS config key.
		"""
		# for addon in import_strings(self.config.get('DEFAULT_ADDONS', ())):
		# 	self.init_addon(addon)
		for addon in self._iter_default_addons():
			self.init_addon(addon)

	@preboot_method
	def init_configured_addons(self):
		"""Initialize addons configured under the ADDONS config key.
		"""
		# try:
		# 	addons = import_strings(self.config.get('ADDONS', ()))
		# except ImportError as e:
		# 	raise ImproperlyConfigured(
		# 			'ADDONS configuration for kernel: %r.' % self.name
		# 		) from e
		# else:
		# 	for addon in addons:
		# 		self.init_addon(addon)
		for addon in self._iter_configured_addons():
			self.init_addon(addon)

	@setupmethod
	def init_addon(self, addon):
		# if isinstance(addon, str):
		# 	try:
		# 		addon = import_string(addon)
		# 	except Exception as e:
		# 		raise ImproperlyConfigured(
		# 				'Addon %r for kernel %r.' % (addon, self.name)
		# 			) from e

		addon = self._load_addon(addon)

		if inspect.isfunction(addon):
			addon(self)
		else:
			if not(hasattr(addon, 'init_app') and callable(addon.init_app)):
				raise ImproperlyConfigured(
					'init_app method not implemented in addon %s.' % (addon,)
				)
			addon.init_app(self)
		return addon

	def _iter_default_addons(self):
		for addon in self.config.get('DEFAULT_ADDONS', ()):
			yield self._load_addon(addon)

	def _iter_configured_addons(self):
		for addon in self.config.get('ADDONS', ()):
			yield self._load_addon(addon)

	def _load_addon(self, addon):
		try:
			return import_string(addon) if isinstance(addon, str) else addon
		except ImportError as e:
			raise ImproperlyConfigured(
					'Addon %r for kernel %r.' % (addon, self.name)
				) from e

	def route(self, rule, view_func=None, endpoint=None, **options):
		"""Registers a view function for a given URL rule. If a function is not
		provided, returns a decorator to be used on the intended function.

		usage::

			# As a decorator. Registers the index function to endpoint 'home'.
			@app.route('/', endpoint='home')
			def index():
				return 'Hello World'

			# OR: By passing a view_func.

			# Define the function.
			def login():
				return 'Hello World'

			# Then register the login function to the 'login' endpoint somewhere
			# else in your application.
			app.route('/', login, 'login')


		:param rule: the URL rule as string.
		:param view_func: the function to call when serving a request to the
						provided endpoint
		:param endpoint: the endpoint for the registered URL rule.  Flask
						itself assumes the name of the view function as
						endpoint
		:param options: the options to be forwarded to the underlying
						:class:`~werkzeug.routing.Rule` object.  A change
						to Werkzeug is handling of method options.  methods
						is a list of methods this rule should be limited
						to (``GET``, ``POST`` etc.).  By default a rule
						just listens for ``GET`` (and implicitly ``HEAD``).
						Starting with Flask 0.6, ``OPTIONS`` is implicitly
						added and handled by the standard request handling.
		"""
		func = super(Kernel, self).route(rule, endpoint=endpoint, **options)
		return func if view_func is None else func(view_func)

	@setupmethod
	def add_cli_command(self, *args, **kwargs):
		if self.is_cli:
			self.console.add_command(*args, **kwargs)

	@setupmethod
	def cli_command(self, *args, **kwargs):
		if self.is_cli:
			return self.console.command(*args, **kwargs)

		if args and callable(args[0]):
			return args[0]

	@setupmethod
	def register_blueprint(self, blueprint, **options):
		"""Registers a blueprint on the application.
		"""
		if isinstance(blueprint, str):
			blueprint = import_string(blueprint)
		return super(Kernel, self).register_blueprint(blueprint, **options)

	@postboot_method
	def run(self, host=None, port=None, debug=None, **options):
		signals.app_starting.send(
			self, host=host, port=port, debug=debug, options=options)
		if 'ssl_context' not in options or options['ssl_context'] is None:
			options['ssl_context'] = self.config.get('SSL_CERTS')
		return super(Kernel, self).run(host, port, debug, **options)

	@postboot_method
	def wsgi_app(self, environ, start_response):
		return super(Kernel, self).wsgi_app(environ, start_response)

	@postboot_method
	def test_client(self, use_cookies=True, **kwargs):
		return super(Kernel, self).test_client(host, port, debug, **options)

	@postboot_method
	def test_request_context(self, *args, **kwargs):
		return super(Kernel, self).test_request_context(*args, **kwargs)

	def perform_content_negotiation(self, renderers=None, *, force=False, **options):
		"""Determine which renderer and mimetype to use to render the response.
		"""
		renderers = renderers or self.renderers
		conneg = self.content_negotiator

		try:
			return conneg.select_renderer(renderers, **options)
		except Exception:
			if force:
				return renderers[0], renderers[0].mimetype
			raise



# def create_app(import_name, config=None, boot=True, root_path=None, **options):
# 	"""Create a new Flask app with given import_name, config and options."""

# 	rv = Flask(import_name, **options)
# 	rv.config.from_envvar('MLOAN_CONFIG_PATH', silent=True)
# 	for conf in configs:
# 		rv.config.from_object(conf)

# 	rv.register_error_handler(Exception, http_exception_handler)
# 	rv.register_error_handler(HTTPException, http_exception_handler)
# 	rv.register_error_handler(BaseHTTPException, http_exception_handler)

# 	if boot:
# 		rv.boot()

# 	return rv

