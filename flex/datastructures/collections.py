from collections import MutableMapping, Mapping
from flex.utils.decorators import export


__all__ = []

NOTHING = object()

@export
class AttrMap(Mapping):

	__slots__ = ()

	def __getattr__(self, name):
		try:
			return self.__getitem__(name)
		except KeyError:
			raise AttributeError(
				"'%s' object has no attribute '%s'."\
				% (self.__class__.__name__, name)
			)

@export
class MutableAttrMap(MutableMapping, AttrMap):

	__slots__ = ()

	def setattr(self, name, value):
		super(MutableAttrMap, self).__setattr__(name, value)

	def delattr(self, name):
		super(MutableAttrMap, self).__delattr__(name)

	def __setattr__(self, name, value):
		try:
			self.setattr(name, value)
		except AttributeError as e:
			try:
				self.__setitem__(name, value)
			except KeyError:
				raise e

	def __delattr__(self, name):
		try:
			self.delattr(name)
		except AttributeError as e:
			try:
				self.__delitem__(name)
			except KeyError:
				raise e

@export
class AttrDict(MutableAttrMap, dict):

	__slots__ = ()

	def __len__(self):
		return dict.__len__(self)

	def __iter__(self):
		return dict.__iter__(self)

	def __contains__(self, key):
		return dict.__contains__(self, key)

	def __getitem__(self, key):
		return dict.__getitem__(self, key)

	def __setitem__(self, key, value):
		dict.__setitem__(self, key, value)

	def __delitem__(self, key):
		dict.__delitem__(self, key)

	def __repr__(self):
		return '%s({%s})' % (self.__class__.__name__,
			', '.join(('%r: %r' % i for i in self.items()))
			)

	def __str__(self):
		return self.__repr__()


@export
class ChainMap(MutableMapping):

	__slots__ = '__mappings_chain__',

	def __init__(self, *maps):
		object.__setattr__(self, '__mappings_chain__', list(maps) or [{}])

	@property
	def maps(self):
		return self.__mappings_chain__

	@property
	def parents(self):
		return self.__class__(*self.maps[1:])

	def push(self, *maps, i=None):
		if i == 0:
			raise ValueError(
				'i must be > 0. Use shift() to add mappings to the beginning'\
				' of the chain.')
		i = i or len(self.maps)
		self[i:i] = maps

	def shift(self, *maps):
		self[0:0] = maps

	def new(self, m=None):
		return self.__class__({} if m is None else m, *self.maps)

	def copy(self):
		return self.__class__(*self.maps)

	def __len__(self):
		return len(set().union(*self.maps))

	def __iter__(self):
		return iter(set().union(*self.maps))

	def __contains__(self, key):
		return any(key in m for m in self.maps)

	def __bool__(self):
		return any(self.maps)

	def __getitem__(self, index, *key):
		if isinstance(index, slice):
			chain = self.__class__(*self.maps[index])
			return chain[key[0]] if key else chain
		else:
			key = index

		for m in self.maps:
			try:
				return m[key]
			except KeyError:
				pass
		raise KeyError("Key '%s' not found in any mapping." % (key,))

	def __setitem__(self, key, value):
		if isinstance(key, slice):
			self.maps[key] = value
		else:
			self.maps[0][key] = value

	def __delitem__(self, key):
		try:
			del self.maps[0][key]
		except KeyError:
			raise KeyError("Key '%s' not found in first mapping." % (key,))

	def __repr__(self):
		return '%s(%s)' % (self.__class__.__name__, ', '.join((str(m) for m in self.maps)))

	def __str__(self):
		return self.__repr__()



@export
class AttrChainMap(ChainMap, MutableAttrMap):

	__slots__ = ()


@export
class AttrBag(object):
	"""A bag for storing."""

	__slots__ = ('__bag__',)

	__bag_factory__ = dict

	def __init__(self, *bag, **kwargs):
		if len(bag) > 1:
			raise TypeError('expected at most 1 arguments, got %d' % len(bag))

		bag = bag[0] if bag else self.__bag_factory__()
		if not isinstance(bag, MutableMapping):
			raise ValueError('expected a MutableMapping instance, got %r' % type(bag))

		object.__setattr__(self, '__bag__', bag)
		self.update(**kwargs)

	def get(self, name, default=None):
		return getattr(self, name, default)

	def pop(self, name, default=NOTHING):
		if default is NOTHING:
			return self.__bag__.pop(name)
		else:
			return self.__bag__.pop(name, default)

	def setdefault(self, name, default=None):
		return self.__bag__.setdefault(name, default)

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

	def update(self, *args, **kwargs):
		# if len(args) == 1 and isinstance(args[0], AttrBag):
		# 	self.__bag__.update(args[0].__bag__, **kwargs)
		# else:
		self.__bag__.update(*args, **kwargs)

	def get_bag(self):
		return self.__bag__

	def get_keys(self):
		return self.__bag__.keys()

	def get_values(self):
		return self.__bag__.values()

	def get_items(self):
		return self.__bag__.items()

	def copy(self):
		return self.__class__(**self.__bag__)

	def __contains__(self, item):
		return item in self.__bag__

	def __len__(self):
		return len(self.__bag__)

	def __iter__(self):
		return iter(self.__bag__.items())

	def __getitem__(self, key):
		return self.__bag__[key]

	def __setitem__(self, key, value):
		self.__bag__[key] = value

	def __delitem__(self, key):
		del self.__bag__[key]

	def __getattr__(self, key):
		try:
			return self.__bag__[key]
		except KeyError as e:
			raise AttributeError(key) from e

	def __setattr__(self, key, value):
		self.__bag__[key] = value

	def __delattr__(self, key):
		try:
			del self.__bag__[key]
		except KeyError as e:
			raise AttributeError(key) from e

	def __getstate__(self):
		return self.__bag__

	def __setstate__(self, state):
		object.__setattr__(self, '__bag__', state)

	def __repr__(self):
		return '%s(%s)' % (self.__class__.__name__,
			', '.join(('%r = %r' % i for i in self.__bag__.items()))
			)

	def __str__(self):
		return self.__repr__()

