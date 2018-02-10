import os
import sys
import inspect
from functools import partial
from flask.app import setupmethod
from flask import Blueprint as BaseBlueprint
from ..utils.module_loading import import_string, import_strings
from . import signals
from flask.helpers import safe_join
from flex.conf import config
from flex.utils.decorators import export, locked_cached_property

_nothing = object()

URL_CONF_MODULES = ('.urls', '.views')
LAZY_MODULES = ('.receivers',)

def _(self):
	pass



class Blueprint(BaseBlueprint):

	addons = ()
	cli_commands = ()
	_urlconf = URL_CONF_MODULES
	_lazy_modules = LAZY_MODULES
	warn_on_modifications = False

	def __init__(self, name, import_name, app=None, addons=None, cli=None,
			urlconf=None, public_folder=None, static_folder=None,
			lazy_modules=None, **blueprint_options):

		if public_folder is not None and  static_folder is None:
			public_folder = name if public_folder == True else public_folder
			static_folder = os.path.join(config.PUBLIC_PATH, public_folder)
		blueprint_options['static_folder'] = static_folder

		super(Blueprint, self).__init__(name, import_name, **blueprint_options)

		self._num_registrations = 0

		# urlconf = urlconf or self._urlconf
		if urlconf is not None:
			self.urlconf = urlconf

		self.addons = tuple(self.addons or ()) + tuple(addons or ())
		self.cli_commands = tuple(self.cli_commands or ()) + tuple(cli or ())

		lazy_modules = tuple(self._lazy_modules or ()) + tuple(lazy_modules or ())

		self.on_register(partial(
					import_strings, lazy_modules,
					self.import_name, silent=True
				), once=True)

		urlconf = urlconf or self._urlconf

		if not callable(urlconf):
			self.on_register(partial(
					import_strings, urlconf,
					self.import_name, silent=True
				), once=True)
		else:
			self.on_register(urlconf, withstate=True)

		if app is not None:
			self.init_app(app)
		# self.childern = {}

	@locked_cached_property
	def root_module(self):
		return sys.modules.get(self.import_name)

	def init_app(self, app):
		self.init_addons(app)
		self.register_cli_commands(app)

	def init_addons(self, app):
		for addon in self.addons:
			if isinstance(addon, str):
				addon = import_string(addon, self.import_name)
			addon.init_app(app)

	def register_cli_commands(self, app):
		for cmd in self.cli_commands:
			if not isinstance(cmd, (tuple, list)):
				command = cmd
				name = namespace = None
			elif len(cmd) == 1:
				command = cmd[0]
				name = namespace = None
			elif cmd:
				name, command = cmd
				if isinstance(command, (tuple, list)):
					command, namespace = command
				else:
					namespace = None
			else:
				raise RuntimeError(
					'Invalid command configuration. App %s' % self.name
				)

			if isinstance(command, str):
				command = import_string(command, self.import_name)

			if not name:
				app.add_cli_command(command)
			else:
				app.add_cli_command(name, command)

	def on_register(self, fn=None, *, once=False, first_registration=True,
					withapp=False, withstate=False):
		def decorator(func):
			def wrapper(state):
				if once and self._num_registrations > 0:
					return
				if not first_registration or state.first_registration:
					if withapp:
						func(state.app)
					elif withstate:
						func(state)
					else:
						func()
			self.record(wrapper)
			return func

		if withapp == True == withstate:
			raise TypeError(
				'Args withapp and withstate cannot both be True just 1.'
			)
		return decorator if fn is None else decorator(fn)

	def register(self, app, options, first_registration=False):
		signals.blueprint_registering.send(self, app=app, options=options,
									first_registration=first_registration)

		super(Blueprint, self).register(app, options, first_registration)

		self._num_registrations += 1

		signals.blueprint_registered.send(self, app=app, options=options,
									first_registration=first_registration)

	def route(self, rule, view_func=None, endpoint=None, **options):
		"""Registers a view function for a given URL rule. If a function is not
		provided, returns a decorator to be used on the intended function. The
		endpoint for the :func:`url_for` function is prefixed with the name of
		the blueprint.

		usage::

			# As a decorator. Registers the index function to endpoint 'home'.
			@bp.route('/', endpoint='home')
			def index():
				return 'Hello World'

			# OR: By passing a view_func.

			# Define the function.
			def login():
				return 'Hello World'

			# Then register the login function to the 'login' endpoint somewhere
			# else in your application.
			bp.route('/', login, 'login')

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
		"""Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
		:func:`url_for` function is prefixed with the name of the blueprint.
		"""
		func = super(Blueprint, self).route(rule, endpoint=endpoint, **options)
		return func if view_func is None else func(view_func)


