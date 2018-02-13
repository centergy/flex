from flask import current_app
from threading import Lock
from flex.utils.decorators import export
from babel import Locale as BaseLocale
from flask.ctx import _app_ctx_stack
from flex.signal import pipeline
from flex.utils.local import Proxy


locale_selector = pipeline('locale_selector')
timezone_selector = pipeline('timezone_selector')


class LocaleProvider(object):

	__slots__ = ('lock', 'cached', 'config')

	def __init__(self, config):
		self.config = config
		self.cached = {}
		self.lock = Lock()

	@property
	def _ctx(self):
		rv = _app_ctx_stack.top
		if rv is None:
			raise RuntimeError('Application context not pushed.')
		return rv

	@property
	def locale(self):
		ctx = self._ctx
		if not hasattr(ctx, '_locale_key'):
			code = locale_selector.pipe(ctx.app, self.config.code)
			tzname = timezone_selector.pipe(ctx.app, self.config.timezone)
			if not code:
				code = '_'.join((self.config.language, self.config.territory))
			key = (code, tzname or self.config.timezone)
			setattr(ctx, '_locale_key', key)
		else:
			key = ctx._locale_key
		return self._get_local(key)

	def _get_local(self, key):
		with self.lock:
			if key not in self.cached:
				self.cached[key] = Locale.parse(key[0])
			return self.cached[key]

@export
class Locale(BaseLocale):
	pass


@export
class LocaleManager(Proxy):

	__slots__ = ('_app')

	_config_prefix = 'LOCALE_'

	_default_config = dict(
		code=None,
		# code_sep='_',
		timezone='UTC',
		language='en',
		territory='KE',
		# CLASS='flex.locale.Locale'
	)

	def __init__(self, app=None):
		super(LocaleManager, self).__init__(None, 'Locale')
		if app is not None:
			self.init_app(app)
		object.__setattr__(self, '_app', app)

	def _get_current_object(self):
		try:
			return self._get_app().extensions['flex.locale'].locale
		except KeyError:
			raise RuntimeError(
				'Locale not setup on app. %s' % self._get_app().name
			)

	def _get_app(self, app=None):
		"""Helper method that implements the logic to look up an application."""
		if app is not None:
			return app

		if current_app:
			return current_app

		if self._app is not None:
			return self._app

		raise RuntimeError(
			'Application not registered on LocaleManager instance and '
			'no application bound to current context'
		)

	def init_app(self, app, **kwargs):
		config = app.config.namespace(self._config_prefix)
		config.setdefaults(self._default_config)
		app.extensions['flex.locale'] = LocaleProvider(config)



locale = LocaleManager()