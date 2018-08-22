import sys
from threading import RLock
from functools import update_wrapper, wraps
from warnings import warn

NOTHING = object()


class class_only_method(classmethod):
	"""Creates a classmethod available only to the class. Raises AttributeError
	when called from an instance of the class.
	"""
	def __init__(self, func, name=None):
		super(class_only_method, self).__init__(func)
		self.__name__ = name or func.__name__

	def __get__(self, obj, cls):
		if obj is not None:
			raise AttributeError('Class method {}.{}() is available only to '\
				'the class, and not it\'s instances.'\
				.format(cls.__name__, self.__name__))
		return super(class_only_method, self).__get__(obj, cls)


class class_property(object):
	"""A decorator that converts a function into a lazy class property."""

	def __init__(self, func, name=None, doc=None):
		self.__name__ = name or func.__name__
		self.__module__ = func.__module__
		self.__doc__ = doc or func.__doc__
		self.func = func

	def __get__(self, obj, cls):
		return self.func(cls)


class cached_class_property(class_property):
	"""A decorator that converts a function into a lazy class property."""

	def __init__(self, func, name=None, doc=None):
		super(cached_class_property, self).__init__(func, name, doc)
		self.lock = RLock()

	def resolve(self, obj, cls):
		return super(cached_class_property, self).__get__(obj, cls)

	def __get__(self, obj, cls):
		with self.lock:
			if self.__name__ not in cls.__dict__:
				rv = self.resolve(obj, cls)
				setattr(cls, self.__name__, rv)
				return rv
			else:
				return getattr(cls, self.__name__)


class cached_property(object):
	"""A decorator that converts a function into a lazy property.  The
	function wrapped is called the first time to retrieve the result
	and then that calculated result is used the next time you access
	the value::

		class Foo(object):

			@cached_property
			def foo(self):
				# calculate something important here
				return 42
	"""

	__slots__ = ('__name__', '____doc__', 'fget', 'fset', 'fdel', 'lock')

	def __init__(self, fget, fset=None, fdel=None, lock=False, name=None, doc=None):
		self.__name__ = name or fget.__name__
		self.____doc__ = doc or fget.__doc__
		self.fget = fget
		self.fset = fset
		self.fdel = fdel
		self.lock = (lock or None) and RLock()

	def getter(self, fn):
		self.fget = fn

	def setter(self, fn):
		self.fset = fn

	def deleter(self, fn):
		self.fdel = fn

	def __get__(self, obj, owner):
		if obj is None:
			return self
		if self.lock is None:
			return self._resolve(obj)
		else:
			with self.lock:
				return self._resolve(obj)

	def __set__(self, obj, value):
		fn = self.fset or self._set_value
		if self.lock is None:
			return fn(obj, value)
		else:
			with self.lock:
				return fn(obj, value)

	def __delete__(self, obj):
		fn = self.fdel or self._del_value
		if self.lock is None:
			return fn(obj)
		else:
			with self.lock:
				return fn(obj)

	def _set_value(self, obj, value):
		obj.__dict__[self.__name__] = value

	def _get_value(self, obj):
		return obj.__dict__[self.__name__]

	def _del_value(self, obj):
		if self.fdel:
			self.fdel(obj)
		else:
			obj.__dict__.pop(self.__name__, None)

	def _resolve(self, obj):
		try:
			return self._get_value(obj)
		except (KeyError, AttributeError):
			value = self.fget(obj)
			self._set_value(obj, value)
			return value



class locked_cached_property(cached_property):
	"""A decorator that converts a function into a lazy property.  The
	function wrapped is called the first time to retrieve the result
	and then that calculated result is used the next time you access
	the value.  Works like the one in Werkzeug but has a lock for
	thread safety.
	"""

	def __init__(self, fget, name=None, doc=None):
		super(locked_cached_property, self).__init__(fget, lock=True, name=name, doc=doc)



def method_decorator(decorator, name=''):
	"""
	Convert a function decorator into a method decorator
	"""
	# 'obj' can be a class or a function. If 'obj' is a function at the time it
	# is passed to _dec,  it will eventually be a method of the class it is
	# defined on. If 'obj' is a class, the 'name' is required to be the name
	# of the method that will be decorated.
	def _dec(obj):
		is_class = isinstance(obj, type)
		if is_class:
			if name and hasattr(obj, name):
				func = getattr(obj, name)
				if not callable(func):
					raise TypeError(
						"Cannot decorate '{0}' as it isn't a callable "
						"attribute of {1} ({2})".format(name, obj, func)
					)
			else:
				raise ValueError(
					"The keyword argument `name` must be the name of a method "
					"of the decorated class: {0}. Got '{1}' instead".format(
						obj, name,
					)
				)
		else:
			func = obj

		def decorate(function):
			"""
			Apply a list/tuple of decorators if decorator is one. Decorator
			functions are applied so that the call order is the same as the
			order in which they appear in the iterable.
			"""
			if hasattr(decorator, '__iter__'):
				for dec in decorator[::-1]:
					function = dec(function)
				return function
			return decorator(function)

		def _wrapper(self, *args, **kwargs):
			@decorate
			def bound_func(*args2, **kwargs2):
				return func.__get__(self, type(self))(*args2, **kwargs2)
			# bound_func has the signature that 'decorator' expects i.e.  no
			# 'self' argument, but it is a closure over self so it can call
			# 'func' correctly.
			return bound_func(*args, **kwargs)
		# In case 'decorator' adds attributes to the function it decorates, we
		# want to copy those. We don't have access to bound_func in this scope,
		# but we can cheat by using it on a dummy function.

		@decorate
		def dummy(*args, **kwargs):
			pass
		update_wrapper(_wrapper, dummy)
		# Need to preserve any existing attributes of 'func', including the name.
		update_wrapper(_wrapper, func)

		if is_class:
			setattr(obj, name, _wrapper)
			return obj

		return _wrapper
	# Don't worry about making _dec look similar to a list/tuple as it's rather
	# meaningless.
	if not hasattr(decorator, '__iter__'):
		update_wrapper(_dec, decorator)
	# Change the name to aid debugging.
	if hasattr(decorator, '__name__'):
		_dec.__name__ = 'method_decorator(%s)' % decorator.__name__
	else:
		_dec.__name__ = 'method_decorator(%s)' % decorator.__class__.__name__
	return _dec


class dict_lookup_property(object):

	"""Baseclass for `environ_property` and `header_property`."""
	read_only = False

	def __init__(self, name, default=None, lookup=None, load_func=None, dump_func=None,
				 read_only=None, doc=None):
		self.name = name
		self.default = default
		self.load_func = load_func
		self.dump_func = dump_func
		if lookup and isinstance(lookup, str):
			def attr_lookup(obj):
				return getattr(obj, attr_lookup.attr)
			attr_lookup.attr = lookup
			self.lookup_func = attr_lookup
		else:
			self.lookup_func = lookup

		if read_only is not None:
			self.read_only = read_only
		self.__doc__ = doc

	def lookup(self, obj):
		return self.lookup_func(obj)

	def __get__(self, obj, type=None):
		if obj is None:
			return self
		storage = self.lookup(obj)
		if self.name not in storage:
			return self.default
		rv = storage[self.name]
		if self.load_func is not None:
			try:
				rv = self.load_func(rv)
			except (ValueError, TypeError):
				rv = self.default
		return rv

	def __set__(self, obj, value):
		if self.read_only:
			raise AttributeError('read only property')
		if self.dump_func is not None:
			value = self.dump_func(value)
		self.lookup(obj)[self.name] = value

	def __delete__(self, obj):
		if self.read_only:
			raise AttributeError('read only property')
		self.lookup(obj).pop(self.name, None)

	def __repr__(self):
		return '<%s %s>' % (
			self.__class__.__name__,
			self.name
		)


def export(obj=NOTHING, *, name=None, exports=None, module=None):
	def add_to_all(_obj):
		_module = sys.modules[module or _obj.__module__]
		_exports = exports or getattr(_module, '__all__', None)
		if _exports is None:
			_exports = []
			setattr(_module, '__all__', _exports)
		_exports.append(name or _obj.__name__)
		return _obj
	return add_to_all if obj is NOTHING else add_to_all(obj)


def _attr_is_sloted(cls, attr):
	"""Check if given attribute is in the given class's __slots__.

	Checks recursively from the class to it's bases."""
	if not hasattr(cls, '__slots__'):
		return False

	if attr in cls.__slots__:
		return True

	for base in cls.__bases__:
		if base is not object and _attr_is_sloted(base, attr):
			return True

	return False



def deprecated(*fn, alt=None, version=None, message=None, once=False, onload=False):
	"""Issues a deprecated warning on module load or when the decorated function is invoked.
	"""
	def decorate(func, alt=alt, version=version, message=message, once=once, onload=onload):
		if message is None:
			data = dict(
				name='%s.%s()' % (func.__module__, func.__name__),
				alt=None if alt is None else alt if isinstance(alt, str) else '%s.%s()' % (alt.__module__, alt.__name__),
			)

			message = ''.join([
				'{name} is deprecated',
				' in favor of {alt}.' if data['alt'] else '.',
			])
			message.format(**data)

		if onload:
			warn(message, DeprecationWarning, 2)
			return func
		else:
			@wraps(func)
			def wrapper(*a, **kw):
				if not once or not func.__deprecation_warned__:
					warn(message, DeprecationWarning, 2)
					func.__deprecation_warned__ = once
				return func(*a, **kw)

			func.__deprecation_warned__ = False
			return wrapper

	decorate.alt, decorate.message, decorate.version, decorate.once, decorate.onload = alt, message, version, once, onload

	return decorate(fn[0]) if fn else decorate