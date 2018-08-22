from threading import RLock

from .decorators import cached_class_property, export

NOTHING = object()

@export
class MetaField(object):

	__slots__ = ('__name__', 'field', 'fload', '_inherit', 'default', '__doc__', 'lock')

	def __init__(self, *opt, default=None, inherit=None, doc=None):
		self.fload = self.__name__ = self.field = None
		self.default = default
		self._inherit = inherit
		self.__doc__ = doc
		self.lock = RLock()

		lopt = len(opt)
		if lopt > 2:
			raise ValueError('expected at most 2 positional arg. got %d' % lopt)
		elif lopt == 1:
			assert isinstance(opt[0], str) or callable(opt[0]), (
					'Expected str and/or callable, got %s.' % type(opt[0])
				)
			if isinstance(opt[0], str):
				self.field = opt[0]
			else:
				self.loader(opt[0])
		elif lopt == 2:
			assert isinstance(opt[0], str) and callable(opt[1]), (
					'expected str and/or callable. got (%r, %r).'
					% (type(opt[0]), type(opt[1]))
				)
			self.field = opt[0]
			self.loader(opt[1])

	@property
	def name(self):
		return self.__name__

	@name.setter
	def name(self, value):
		self.__name__ = value
		if not self.field:
			self.field = value

	@property
	def inherit(self):
		return self._inherit is None or self._inherit

	def loader(self, fload):
		assert callable(fload), ('expected callable, got %s.' % type(fload))
		self.fload = fload
		self.__doc__ = self.__doc__ or fload.__doc__

	def get_field(self, value=None):
		if value is not None or self.default is None:
			return value
		elif callable(self.default):
			return self.default()
		else:
			return self.default

	def resolve(self, obj, value):
		base = getattr(obj, '_base', None)
		if self.fload is None:
			if value is None and self.inherit and base:
				value = getattr(base, self.name, None)
			return self.get_field(value)
		elif self.inherit:
			bv = base and getattr(base, self.name, None)
			return self.fload(obj, self.get_field(value), bv)
		else:
			return self.fload(obj, self.get_field(value))

	def set_value(self, obj, value):
		obj.__dict__[self.name] = value

	def get_value(self, obj, default=NOTHING):
		try:
			return obj.__dict__[self.name]
		except KeyError as e:
			if default is NOTHING:
				raise AttributeError(self.name) from e
			return default

	def load(self, obj, meta=None):
		self.__set__(obj, meta and getattr(meta, self.field, None))

	def __set__(self, obj, value):
		with self.lock:
			self.set_value(obj, self.resolve(obj, value))

	def __get__(self, obj, cls):
		if obj is None:
			return self

		with self.lock:
			try:
				return self.get_value(obj)
			except AttributeError:
				meta = getattr(obj, '_meta', None)
				rv = self.resolve(obj, meta and getattr(meta, self.field, None))
				self.set_value(obj, rv)
				return rv

	def __call__(self, fload):
		assert self.fload is None, ('MetaField option already has a loader.')
		self.loader(fload)
		return self



@export
class BaseMetadata(object):

	def __init__(self, meta, base=None):
		self._meta = meta
		self._base = base

	@cached_class_property
	def __fields__(cls):
		rv = {}
		for k in dir(cls):
			if k != '__fields__' and k not in rv and isinstance(getattr(cls, k), MetaField):
				rv[k] = getattr(cls, k)
				rv[k].name = k
		return rv

	def _prepare(self):
		for k, field in self.__fields__.items():
			field.load(self, self._meta)

		del self._meta
		del self._base

