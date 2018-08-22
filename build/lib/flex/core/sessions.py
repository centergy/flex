import pickle
from . import exc, signals
from uuid import uuid4
from datetime import timedelta, datetime
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionMixin
from flask import request as reqst, get_flashed_messages
from flask.sessions import (
	SessionInterface as BaseSessionInterface, total_seconds,
	SecureCookieSessionInterface as BaseCookieInterface, BadSignature
)
from warnings import warn

try:
	from redis import Redis
	redis_available=True
except ImportError:
	redis_available = False

NOTHING = object()

REPLACEABLE_TYPES = (type(None), str, int, float, bool)

class Session(object):
	"""Session Object."""

	__fields__ = dict(
		id = lambda s: generate_session_id(),
		name = None,
		data = lambda s: {},
		flashed = lambda s: set(),
		xflashed = lambda s: set(),
		immortals = lambda s: set(),
		permanent = True,
		lifespan = lambda s: timedelta(hours=24),
		last_updated = lambda s: datetime.now()
	)

	new = False
	modified = True
	_started = None
	invalidated = None

	def __init__(self, initial=None, **kwargs):
		if initial is not None:
			initial.update(kwargs)
		else:
			initial = kwargs
		self._initial = initial


	#####################
	# Extra goodies.
	#####################

	def flash(self, key, value):
		"""Flash the given key, value. The value will only be available in
		the next request after which it's automatically deleted.
		"""
		self[key] = value
		self.flashed.add(key)
		self.xflashed.discard(key)

	def forget(self, *keys):
		"""Remove all items with the given keys from the session."""
		for key in keys:
			self.pop(key, None)

	def forever(self, key, value=NOTHING):
		"""Set the value for key in the session if provided and mark it as
		immortal. If value is not provided, the key is marked as immortal.
		This means that the key's value will not be deleted even after the
		session data expires. The value will only be deleted after the
		session cookie expires (WHICH COULD BE FOREVER).
		"""
		if value is not NOTHING:
			self[key] = value
		self.immortals.add(key)

	def now(self, key, value):
		"""Set the value for key available only to the current request."""
		self[key] = value
		self.xflashed.add(key)
		self.flashed.discard(key)

	def swap(self, key, new=None, flash=False):
		"""Swap the current value for key with the new value and return
		the old value. If the value was flashed, the new value will also be
		flashed.
		"""
		value = self.get(key, NOTHING)
		if value is NOTHING:
			if flash:
				self.flash(key, new)
			else:
				self[key] = new
		else:
			if self.was_flashed(key):
				self.flash(key, new)
			else:
				self[key] = new
		return None if value is NOTHING else value

	def was_flashed(self, key):
		"""Return true if the value for key was flashed from the previous
		request.
		"""
		return key in self.xflashed

	def will_flash(self, key):
		"""Return true if the value for key will be flashed to the
		next request.
		"""
		return key in self.flashed

	#####################
	# Dict Methods.
	#####################
	def get(self, key, default=None):
		"""Return the value for key if key is in the session, else default.
		If default is not given, it defaults to None, so that this method never
		raises a KeyError.
		"""
		return self.data.get(key, default)

	def set(self, key, value):
		"""Set the value for key in the session."""
		self.data[key] = value

	def keys(self):
		"""Return a new view of the sessions data's keys."""
		return self.data.keys()

	def items(self):
		"""Return a new view of the session’s items ((key, value) pairs)."""
		return self.data.items()

	def pop(self, key, default=NOTHING):
		"""If key is in the session, remove it and return its value, else
		return default. If default is not given and key is not in the session,
		a KeyError is raised.
		"""
		value = self.data.pop(key, NOTHING)
		if value is NOTHING:
			value = default
		else:
			self._clear_refs(key)

		if value is NOTHING:
			raise KeyError('Key {} not set in the session.'.format(key))
		else:
			return value

	def popitem(self):
		"""Remove and return an arbitrary (key, value) pair from the session."""
		raise NotImplementedError("And might not be implemented any time soon.")

	def setdefault(self, key, default=None):
		"""If key is in the session, return its value. If not, insert key
		with a value of default and return default. default defaults to None.
		"""
		return self.data.setdefault(key, default)

	def update(self, *other, **kwargs):
		"""Update the session with the key/value pairs from other, or kwargs
		overwriting existing keys. Return None.
		"""
		return self.data.update(*other, **kwargs)

	def values(self):
		"""Return a new view of the session's values."""
		return self.data.values()

	def clear(self, confirm):
		"""Clear all the current session data."""
		if confirm:
			self.data.clear()
			self._reset_attrs('flashed', 'xflashed', 'immortals')

	def copy(self):
		"""Return a shallow copy of the session"""
		return self.__class__(self._todict())

	#####################
	# Internal Methods
	#####################

	def reset(self):
		self.invalidated = self.id
		self._reset_attrs(
					'id', 'data', 'flashed', 'xflashed',
					'immortals', 'last_updated')

	def start_session(self, app, request):
		if self._started is True:
			raise RuntimeError("Error starting session. Session already active.")

		signals.session_starting.send(self, app=app)

		if self._initial:
			self._init_attrs(**self._initial)
			del self._initial
		else:
			self._init_attrs()

		if self.lifespan and (datetime.now() - self.last_updated) >= self.lifespan:
			self._clear_expired_data()
			self.invalidated = self.id
			self._reset_attrs('id')
		self._started = True

		signals.session_started.send(self, app=app)

		if hasattr(request, 'init_session'):
			request.init_session(self)

		return self

	def end_session(self, app, response):
		if self._started is not True:
			raise RuntimeError("Error ending session. Session not active.")

		signals.session_ending.send(self, app=app)

		self._age_flashed_data()
		self.last_updated = datetime.now()
		data = self._gather_storage_data()
		self._started = False

		signals.session_ended.send(self, app=app)

		return data

	def _clear_expired_data(self):
		self.immortals = self.immortals & set(self.keys())
		data = {key : self.data[key] for key in self.immortals}
		self.data = data
		self.flashed = self.immortals & self.flashed
		self.xflashed = self.immortals & self.xflashed

	def _age_flashed_data(self):
		old_keys = (self.xflashed - self.flashed) & set(self.keys())
		for key in old_keys:
			del self.data[key]
		self.xflashed = self.flashed & set(self.keys())
		self._reset_attrs('flashed')

	def _init_attrs(self, **kwargs):
		"""Set the initial values of all attributes from given kwargs. For
		attributes missing in kwargs, their default value is used instead.
		"""
		for key, default in self.__fields__.items():
			if key not in kwargs:
				value = default(self) if callable(default) else default
			else:
				value = kwargs.pop(key)
			setattr(self, key, value)

	def _update_attrs(self, **kwargs):
		"""Update the values of the given attributes."""
		for key, value in self.kwargs.items():
			current = getattr(self, key, NOTHING)
			if current is NOTHING or isinstance(current, REPLACEABLE_TYPES):
				current = value
			elif isinstance(current, (tuple, list)):
				tp = type(current)
				current = tp(list(current).extend(list(value)))
			elif isinstance(current, dict):
				current.update(value)
			elif isinstance(current, set):
				current = current | value
			else:
				current = value
			setattr(self, key, current)

	def _reset_attrs(self, *keys):
		"""Reset the values for the given attributes to their defaults."""
		for key in keys:
			default = self.__fields__[key]
			setattr(self, key, default(self) if callable(default) else default)

	def _todict(self):
		"""Return a real dict representation of the session object."""
		rv = {}
		for k in self.__fields__.keys():
			rv[k] = getattr(self, k)
		return rv

	def _gather_storage_data(self):
		return self._todict()

	def _clear_refs(self, *keys):
		for key in keys:
			self.flashed.discard(key)
			self.xflashed.discard(key)
			self.immortals.discard(key)

	#######################
	# The magic goes here
	#######################
	def __len__(self):
		return len(self.data)

	def __contains__(self, other):
		return self.data.__contains__(other)

	def __iter__(self):
		return iter(self._todict().items())

	def __getitem__(self, key):
		return self.data.__getitem__(key)

	def __setitem__(self, key, value):
		self.data.__setitem__(key, value)

	def __delitem__(self, key):
		self.data.__delitem__(key)
		self._clear_refs(key)

	def __getattr__(self, key):
		if not self._started and '_initial' in self.__dict__:
			raise RuntimeError(
					'Error accessing session data. '\
					'The session is not active. The session must '\
					'be explicitly started by calling start_session() '\
					'from the application\'s session_interface.')
		else:
			raise AttributeError('Session has no attribute {}.'.format(key))

	def __repr__(self):
		return '<Session[{}] {} #{}\n  Last Updated: {}\n  data: {}>'.format(
								self.__class__.__name__,
								self.name, self.id,
								self.last_updated,
								str(self.data))
								# str(self.data)[:70])


class SessionInterface(BaseSessionInterface):

	session_class = Session

	def __init__(self, **opts):
		self.session_class = self.session_class \
			if opts.get('session_class') is None else opts.pop('session_class')
		self.serializer = self.serializer \
			if opts.get('serializer') is None else opts.pop('serializer')
		self.options = opts

	def get_session_data_lifespan(self, app):
		lifespan = app.config.setdefault('SESSION_DATA_LIFESPAN', timedelta(hours=12))
		if not isinstance(lifespan, timedelta):
			if not isinstance(lifespan, int) or lifespan < 3:
				warn('Config: SESSION_DATA_LIFESPAN should be a timedelta '
					'instance or an int representing the number of hours (at least 3).')
				lifespan = timedelta(hours=12)
			elif lifespan <= 72:
				lifespan = timedelta(hours=lifespan)
			elif lifespan <= 4320:
				lifespan = timedelta(minutes=lifespan if lifespan >= 180 else 180)
			else:
				lifespan = timedelta(seconds=lifespan if lifespan >= 10800 else 10800)

			app.config['SESSION_DATA_LIFESPAN'] = lifespan

		return lifespan

SessionInterface.__doc__ = BaseSessionInterface.__doc__


class SecureCookieSessionInterface(SessionInterface,
								BaseCookieInterface):
	session_class = Session

	def open_session(self, app, request):
		session = BaseCookieInterface.open_session(self, app, request)
		if session is None:
			return None
		if not isinstance(session, self.session_class):
			session = self.session_class(dict(session))
		session.start_session(app, request)
		session.lifespan = self.get_session_data_lifespan(app)
		return session

	def save_session(self, app, session, response):
		session.end_session(app, response)
		BaseCookieInterface.save_session(self, app, session, response)


SecureCookieSessionInterface.__doc__ = BaseCookieInterface.__doc__



class RedisSessionInterface(SessionInterface, BaseCookieInterface):
	redis_serializer = pickle
	redis = None
	prefix = 'session:'
	salt = 'redis-session'

	def __init__(self, redis=None, prefix=None, **opts):
		super(RedisSessionInterface, self).__init__(**opts)
		self.redis = redis or self.redis
		self.prefix = prefix or self.prefix

	def get_prefix(self, app):
		return self.prefix or app.config.get('SESSION_REDIS_PREFIX', '%s_user_session:' % app.name)

	def get_redis_session_lifetime(self, app, session):
		if session.permanent:
			return app.permanent_session_lifetime
		return timedelta(days=14)

	def load_session_id(self, app, request):
		s = self.get_signing_serializer(app)
		if s is None:
			warn('Session cannot loaded as there might be something '\
				'wrong or missing in your configuration. Please make sure'
				'the SECRET_KEY is set to enable secure cookies.')

		val = request.cookies.get(app.session_cookie_name)
		if not val or s is None:
			return val

		max_age = total_seconds(app.permanent_session_lifetime)
		try:
			sid = s.loads(val, max_age=max_age)
			return sid
		except BadSignature:
			return None

	def open_session(self, app, request):
		if not self.redis:
			warn("RedisSessionInterface requires a redix client instance.")
			return None

		sid = self.load_session_id(app, request)
		if sid:
			val = self.redis.get(self.get_prefix(app) + sid)
			if val is not None:
				data = self.redis_serializer.loads(val)
			else:
				data = None
		else:
			data = None

		session = self.session_class(data)
		session.start_session(app, request)
		session.lifespan = self.get_session_data_lifespan(app)
		return session

	def save_session(self, app, session, response):
		if not self.redis:
			warn("RedisSessionInterface requires a redix client instance.")
			return

		domain = self.get_cookie_domain(app)
		path = self.get_cookie_path(app)

		if not session:
			if hasattr(session, 'id'):

				self.redis.delete(self.get_prefix(app) + session.id)

			if session.modified:
				response.delete_cookie(
					app.session_cookie_name,
					domain=domain, path=path
				)
			return

		prefix = self.get_prefix(app)
		if session.invalidated:
			self.redis.delete(prefix + session.invalidated)

		data = session.end_session(app, response)

		redis_exp = self.get_redis_session_lifetime(app, session)
		cookie_exp = self.get_expiration_time(app, session)

		val = self.redis_serializer.dumps(data)
		cls = getattr(self.redis, 'provider_class', self.redis.__class__)

		if cls is Redis or issubclass(cls, Redis):
			self.redis.setex(prefix + session.id, val, redis_exp)
		else:
			self.redis.setex(prefix + session.id, redis_exp, val)

		httponly = self.get_cookie_httponly(app)
		secure = self.get_cookie_secure(app)
		val = self.get_signing_serializer(app).dumps(session.id)

		response.set_cookie(app.session_cookie_name, val,
							expires=cookie_exp, httponly=httponly,
							domain=domain, path=path, secure=secure)




def generate_session_id(app=None):
	return str(uuid4())

def _make_timedelta(value, prop='seconds'):
	if not isinstance(value, timedelta):
		return timedelta(**{prop:value})
	return value
