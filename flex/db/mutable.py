from sqlalchemy.ext.mutable import (
	Mutable, MutableDict, MutableList, MutableSet, MutableComposite
)
from flex.datastructures import AttrDict


class MutableAttrDict(Mutable, AttrDict):

	__slots__ = ()

	def __setitem__(self, key, value):
		super(MutableAttrDict, self).__setitem__(key, value)
		self.changed()

	def __delitem__(self, key):
		super(MutableAttrDict, self).__delitem__(key)
		self.changed()

	@classmethod
	def coerce(cls, key, value):
		if not isinstance(value, cls):
			if isinstance(value, dict):
				return cls(value)
			return Mutable.coerce(key, value)
		else:
			return value
