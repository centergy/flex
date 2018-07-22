import re
from collections import MutableMapping, Mapping, Sequence, MutableSequence
from abc import abstractmethod
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

	def __eq__(self, other):
		dict.__eq__(self, other)

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



_sequence_index_re = re.compile(r'^\[([0-9]+)\]$')


@export
class BaseMutableNestedMapping(object):

	__slots__ = (
		# '_pathsep', '_mapping_factory', '_sequence_factory',
		# '_mapping_types', '_sequence_types'
	)
	__pathsep__ = '.'
	__mapping_factory__ = lambda s, k, p: dict()
	__sequence_factory__ = lambda s, k, p: list()
	__mapping_types__ = (MutableMapping,)
	__sequence_types__ = (MutableSequence,)

	def __init__(self, pathsep=None, mapping_factory=None, sequence_factory=None,
				mapping_types=None, sequence_types=None):
		if pathsep is not None and not(pathsep and isinstance(pathsep, str)):
			raise ValueError(
				'BaseMutableNestedMapping pathsep arg must be a non-empty string if '
				'provided. %s was given.' % (type(pathsep),)
			)
		object.__setattr__(self, '_pathsep', pathsep or self.__pathsep__)

		if mapping_factory is not None and not callable(mapping_factory):
			raise ValueError(
				'BaseMutableNestedMapping mapping_factory arg must be a callable if '
				'provided. %s was given.' % (type(mapping_factory),)
			)
		object.__setattr__(self, '_mapping_factory', mapping_factory or self.__mapping_factory__)

		if sequence_factory is not None and not callable(sequence_factory):
			raise ValueError(
				'BaseMutableNestedMapping sequence_factory arg must be a callable if '
				'provided. %s was given.' % (type(sequence_factory),)
			)
		object.__setattr__(self, '_sequence_factory', sequence_factory or self.__sequence_factory__)

		object.__setattr__(self, '_mapping_types', mapping_types or self.__mapping_types__)
		object.__setattr__(self, '_sequence_types', sequence_types or self.__sequence_types__)

	@abstractmethod
	def __getrootitem__(self, key):
		raise KeyError

	@abstractmethod
	def __setrootitem__(self, key, value):
		raise KeyError

	@abstractmethod
	def __delrootitem__(self, key):
		raise KeyError

	def __pathsegment__(self, seg):
		if isinstance(seg, str):
			sim = _sequence_index_re.search(seg)
			if sim:
				return int(sim.group(1))
		return seg

	def __parsepath__(self, path):
		if isinstance(path, str):
			return tuple(map(self.__pathsegment__, path.split(self._pathsep)))
		elif isinstance(path, Sequence):
			return tuple(map(self.__pathsegment__, path))
		else:
			return (self.__pathsegment__(path),)

	def __getpath__(self, _path):
		path = self.__parsepath__(_path)

		if len(path) == 0:
			raise ValueError('Invalid path %s' % (_path,))

		target = self.__getrootitem__(path[0])
		for i, key in enumerate(path[1:], 2):
			try:
				target = target.__getitem__(key)
			except (KeyError, IndexError) as e:
				raise KeyError('Path %s not found.' % (path[:i],)) from e
		return target

	def __setpath__(self, _path, value, mapping_factory=None, sequence_factory=None):
		path = self.__parsepath__(_path)
		lpath = len(path)

		if lpath == 0:
			raise ValueError('Invalid path %s' % (_path,))
		elif lpath == 1:
			return self.__setrootitem__(path[0], value)

		mapping_factory = mapping_factory or self._mapping_factory
		sequence_factory = sequence_factory or self._sequence_factory

		try:
			target = root = self.__getrootitem__(path[0])
		except (KeyError, IndexError):
			if isinstance(path[1], int):
				target = root = sequence_factory(path[0], path[:1])
			else:
				target = root = mapping_factory(path[0], path[:1])

		for i, key in enumerate(path[1:-1], 2):
			try:
				target = target.__getitem__(key)
			except (KeyError, IndexError):
				if isinstance(path[i], int):
					tv = sequence_factory(key, path[:i])
				else:
					tv = mapping_factory(key, path[:i])

				if isinstance(target, self._sequence_types):
					target.insert(key, tv)
				else:
					target.__setitem__(key, tv)
				target = tv

		if isinstance(target, self._sequence_types) and path[-1] not in target:
			target.insert(path[-1], value)
		else:
			target.__setitem__(path[-1], value)

		#call this to explicitly register the change.
		self.__setrootitem__(path[0], root)

	def __poppath__(self, _path):
		path = self.__parsepath__(_path)
		lpath = len(path)

		if lpath == 0:
			raise ValueError('Invalid path %s' % (_path,))
		elif lpath == 1:
			rv = self.__getrootitem__(path[0])
			self.__delrootitem__(path[0])
			return rv

		target = root = self.__getrootitem__(path[0])
		for i, key in enumerate(path[1:-1], 2):
			try:
				target = target.__getitem__(key)
			except (KeyError, IndexError) as e:
				raise KeyError('Path %s not found.' % (path[:i],)) from e

		try:
			rv = target.__getitem__(path[-1])
			target.__delitem__(path[-1])
		except (KeyError, IndexError) as e:
			raise KeyError('Path %s not found.' % (path,)) from e
		else:
			#call this to explicitly register the change.
			self.__setrootitem__(path[0], root)
			return rv

	def __contains__(self, path):
		try:
			self[path]
		except KeyError:
			return False
		else:
			return True

	def __getitem__(self, path):
		return self.__getpath__(path)

	def __setitem__(self, path, value):
		self.__setpath__(path, value)

	def __delitem__(self, path):
		self.__poppath__(path)

	def get(self, path, default=None):
		try:
			return self[path]
		except KeyError:
			return default

	def set(self, path, value, mapping_factory=None, sequence_factory=None):
		self.__setpath__(path, value, mapping_factory, sequence_factory)

	def pop(self, path, default=NOTHING):
		try:
			value = self.__poppath__(path)
		except KeyError:
			if default is NOTHING:
				raise
			return default
		else:
			return value

	def 	setdefault(self, path, default=None):
		try:
			return self[path]
		except KeyError:
			self[path] = default
		return default


@export
class MutableNestedMapping(BaseMutableNestedMapping):

	__slots__ = (
		'_pathsep', '_mapping_factory', '_sequence_factory',
		'_mapping_types', '_sequence_types'
	)



@export
class NestedDict(BaseMutableNestedMapping, dict):

	__slots__ = (
		'_pathsep', '_mapping_factory', '_sequence_factory',
		'_mapping_types', '_sequence_types'
	)

	def __init__(self, *args, **kw):
		BaseMutableNestedMapping.__init__(self)
		dict.__init__(self, *args, **kw)

	def __getrootitem__(self, key):
		return dict.__getitem__(self, key)

	def __setrootitem__(self, key, value):
		return dict.__setitem__(self, key, value)

	def __delrootitem__(self, key):
		return dict.__delitem__(self, key)

	def __len__(self):
		return dict.__len__(self)

	def __iter__(self):
		return dict.__iter__(self)

	def __eq__(self, other):
		dict.__eq__(self, other)

