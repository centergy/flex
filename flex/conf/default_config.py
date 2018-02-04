from flask.helpers import get_debug_flag
from datetime import timedelta
from .core import lazy, lazy_import



DEBUG = get_debug_flag(default=False)


TESTING = False


PROPAGATE_EXCEPTIONS = None


PRESERVE_CONTEXT_ON_EXCEPTION = None


SECRET_KEY = None


PERMANENT_SESSION_LIFETIME = timedelta(days=31)


USE_X_SENDFILE = False

LOGGER_NAME = None


LOGGER_HANDLER_POLICY = 'always'


SERVER_NAME = None
APPLICATION_ROOT = None


SESSION_COOKIE_NAME = 'session'
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_REFRESH_EACH_REQUEST = True


MAX_CONTENT_LENGTH =  None
SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)


TRAP_BAD_REQUEST_ERRORS = False
TRAP_HTTP_EXCEPTIONS = False
EXPLAIN_TEMPLATE_LOADING = False
TEMPLATES_AUTO_RELOAD = None


PREFERRED_URL_SCHEME = 'http'

JSON_ENCODER = lazy_import('flex.utils.json.JSONEncoder')
JSON_DECODER = lazy_import('flex.utils.json.JSONDecoder')

JSON_AS_ASCII = True
JSON_SORT_KEYS = False

JSON_PRETTYPRINT = False
JSONIFY_PRETTYPRINT_REGULAR = True
JSONIFY_MIMETYPE = 'application/json'

CONTENT_NEGOTIATOR = lazy_import('flex.http.negotiators.DefaultContentNegotiator')

RENDERERS = lazy_import([
	'flex.http.renderers.HTMLRenderer',
	'flex.http.renderers.JSONRenderer'
])


DEFAULT_ADDONS = [
	'flex.http.addon',
]


PASSLIB_SCHEMES = [
	'pbkdf2_sha512',
]
