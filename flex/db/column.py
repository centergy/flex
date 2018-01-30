import inspect
from sqlalchemy import func as sa_func
from sqlalchemy import Column as BaseColumn


lower = sa_func.lower


class ExtraColumnOperators(object):
	"""docstring for ExtraColumnOperators"""

	def i_eq(self, other):
		"""Case insensitive == operator"""
		return lower(self) == lower(other)

	def i_ne(self, other):
		"""Case insensitive != operator"""
		return lower(self) != lower(other)

	def i_lt(self, other):
		"""Case insensitive < operator"""
		return lower(self) < lower(other)

	def i_le(self, other):
		"""Case insensitive <= operator"""
		return lower(self) <= lower(other)

	def i_gt(self, other):
		"""Case insensitive > operator"""
		return lower(self) > lower(other)

	def i_ge(self, other):
		"""Case insensitive >= operator"""
		return lower(self) >= lower(other)

	def i_has(self, other):
		"""Case insensitive in operator"""
		return lower(other) in lower(self)

	def i_in_(self, other):
		"""Case insensitive in_ operator"""
		return lower(self).in_([lower(i) for i in other])

	def i_notin_(self, other):
		"""Case insensitive notin_ operator"""
		return lower(self).notin_([lower(i) for i in other])

	def i_is_(self, other):
		"""Case insensitive is_ operator"""
		return lower(self).is_(lower(other))

	def i_isnot(self, other):
		"""Case insensitive is_ operator"""
		return lower(self).isnot(lower(other))

	def i_like(self, other, escape=None):
		"""Case insensitive LIKE operator. Alias for ilike()."""
		return self.ilike(other, escape=escape)

	def i_notlike(self, other, escape=None):
		"""Case insensitive NOT LIKE operator. Alias for notilike()"""
		return self.notilike(other, escape=escape)

	def i_contains(self, other, **kwargs):
		"""Case insensitive startswith operator"""
		return lower(self).contains(lower(other), **kwargs)

	def i_match(self, other, **kwargs):
		"""Case insensitive startswith operator"""
		return lower(self).match(lower(other), **kwargs)

	def i_startswith(self, other, **kwargs):
		"""Case insensitive startswith operator"""
		return lower(self).startswith(lower(other), **kwargs)

	def i_endswith(self, other, **kwargs):
		"""Case insensitive endswith operator"""
		return lower(self).endswith(lower(other), **kwargs)

	def i_between(self, cleft, cright, symmetric=False):
		"""Case insensitive between operator"""
		return lower(self).between(lower(cleft), lower(cright), symmetric=symmetric)


class Column(BaseColumn, ExtraColumnOperators):
	def __init__(self, *args, **kwargs):
		self.validators = kwargs.pop('validators', None)
		self._creation_order_val = None
		self._sa_attr_declaration = None

		# kwargs.setdefault('nullable', False)
		super(Column, self).__init__(*args, **kwargs)

	@property
	def _creation_order(self):
		if self._sa_attr_declaration:
			return self._sa_attr_declaration._creation_order
		return self._creation_order_val

	@_creation_order.setter
	def _creation_order(self, value):
		if self._sa_attr_declaration:
			self._sa_attr_declaration._creation_order = value
		else:
			self._creation_order_val = value

def is_orderable_member(obj):
	return hasattr(obj, '_creation_order')\
		and isinstance(obj._creation_order, int)\
		and obj._creation_order > 0


def get_orderable_members(cls, sort=True):
	"""Get class members with '_creation_order'."""
	members = inspect.getmembers(cls, predicate=is_orderable_member)
	if sort:
		members.sort(key=lambda kv: kv[1]._creation_order)
	return members


def defer_column_creation(cls, reorder=False):
	"""Assign a large '_creation_order' sequence to valid attributes of cls."""
	for name, value in get_orderable_members(cls):
		if reorder or value._creation_order < 999999999:
			set_late_creation_order(value)
	return cls



_late_creation_order = 999999999


def set_late_creation_order(instance):
	"""Assign a large '_creation_order' sequence to the given instance.

	This allows multiple instances to be sorted in order of creation
	(typically within a single thread; the counter is not particularly
	threadsafe).
	see:~ :func:`sqlalchemy.util.set_creation_order`
	"""
	global _late_creation_order
	instance._creation_order = _late_creation_order
	_late_creation_order += 1

