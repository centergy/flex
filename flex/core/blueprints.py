import os
import sys
import inspect
from flask import Blueprint as BaseBlueprint
from flask.blueprints import BlueprintSetupState as BaseBlueprintSetupState
from ..utils.module_loading import import_string, import_strings
from . import signals


URLS_MODULES = ['.urls', '.views']


class BlueprintSetupState(BaseBlueprintSetupState):
	"""Temporary holder object for registering a blueprint with the
	application.  An instance of this class is created by the
	:meth:`~flask.Blueprint.make_setup_state` method and later passed
	to all register callback functions.
	"""

	def __init__(self, blueprint, app, options, first_registration, parent=None):
		#: a reference to the current application
		self.app = app

		#: a reference to the blueprint that created this setup state.
		self.blueprint = blueprint

		#: a dictionary with all options that were passed to the
		#: :meth:`~flask.Flask.register_blueprint` method.
		self.options = options

		#: as blueprints can be registered multiple times with the
		#: application and not everything wants to be registered
		#: multiple times on it, this attribute can be used to figure
		#: out if the blueprint was registered in the past already.
		self.first_registration = first_registration

		self.parent = parent

		subdomain = self.options.get('subdomain')
		if subdomain is None:
			subdomain = self.blueprint.subdomain

		#: The subdomain that the blueprint should be active for, ``None``
		#: otherwise.
		self.subdomain = subdomain

		url_prefix = self.options.get('url_prefix')
		if url_prefix is None:
			url_prefix = self.blueprint.url_prefix

		#: The prefix that should be used for all URLs defined on the
		#: blueprint.
		self.url_prefix = url_prefix

		#: A dictionary with URL defaults that is added to each and every
		#: URL that was defined with the blueprint.
		self.url_defaults = dict(self.blueprint.url_values_defaults)
		self.url_defaults.update(self.options.get('url_defaults', ()))

	def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
		"""A helper method to register a rule (and optionally a view function)
		to the application.  The endpoint is automatically prefixed with the
		blueprint's name.
		"""
		if self.url_prefix:
			rule = self.url_prefix + rule
		options.setdefault('subdomain', self.subdomain)
		if endpoint is None:
			endpoint = _endpoint_from_view_func(view_func)
		defaults = self.url_defaults
		if 'defaults' in options:
			defaults = dict(defaults, **options.pop('defaults'))
		self.app.add_url_rule(rule, '%s.%s' % (self.blueprint.name, endpoint),
							  view_func, defaults=defaults, **options)



class Blueprint(BaseBlueprint):

	addons = ()
	cli_commands = ()

	def __init__(self, name, import_name, addons=None, cli=None,
			urlconf=URLS_MODULES, **blueprint_options):
		super(Blueprint, self).__init__(name, import_name, **blueprint_options)

		self.urls_modules = urlconf

		self.addons = tuple(self.addons or ()) + tuple(addons or ())
		self.cli_commands = tuple(self.cli_commands or ()) + tuple(cli or ())
		# self.childern = {}

	@property
	def root_module(self):
		return sys.modules.get(self.import_name)

	def init_app(self, app):
		self.init_addons(app)
		self.register_cli_commands(app)

	def init_addons(self, app):
		for addon in self.addons:
			if isinstance(addon, str):
				addon = import_string(addon, self.root_module)
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
				command = import_string(command, self.root_module)

			if not name:
				app.add_cli_command(command)
			else:
				app.add_cli_command(name, command)

	def _import_urls_module(self):
		if inspect.isfunction(self.urls_modules):
			mods = self.urls_modules()
		else:
			mods = self.urls_modules

		if mods:
			import_strings(mods, self.import_name, silent=True)

	def register(self, app, options, first_registration=False):
		self._import_urls_module()
		signals.blueprint_registering.send(self, app=app, options=options,
									first_registration=first_registration)

		super(Blueprint, self).register(app, options, first_registration)

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


