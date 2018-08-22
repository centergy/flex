from .payload import Payload
from .request import Request
from .response import Response
from .exc import http_error_handler, HTTPException, BaseHTTPException, abort
from flex.utils.module_loading import import_strings
from .status import HTTP_STATUS_CODES
from flex.core.blueprints import Blueprint
from . import exc


class HttpAddon(Blueprint):

	default_config = dict(
		ERROR_HANDLER=http_error_handler,
		ERROR_CLASSES=[HTTPException, BaseHTTPException]
	)

	def init_app(self, app):
		if '_http_addon' not in app.extensions:
			config = self.init_config(app)
			for error in config.ERROR_CLASSES:
				app.register_error_handler(error, config.ERROR_HANDLER)

			for e in exc.default_exceptions.values():
				if issubclass(e, BaseHTTPException):
					app.register_error_handler(e, config.ERROR_HANDLER)

			from werkzeug import exceptions

			for e in exceptions.default_exceptions.values():
				if issubclass(e, BaseHTTPException):
					app.register_error_handler(e, config.ERROR_HANDLER)

			app.register_blueprint(self)
			app.extensions['_http_addon'] = True

	def init_config(self, app):
		config = app.config.namespace('HTTP_')
		config.setdefaults(self.default_config)
		config.ERROR_HANDLER = import_strings(config.ERROR_HANDLER)
		config.ERROR_CLASSES = import_strings(config.ERROR_CLASSES)
		return config


addon = HttpAddon('flex.http', __name__,
			template_folder='templates')
