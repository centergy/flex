import six
import sys
from collections import Iterable
from flex.utils.decorators import export


@export
class Sanitizer(object):

	__slots__ = ()

	def __call__(self, value):
		raise NotImplementedError(
			"Sanitizer method sanitize() not implemented in %s."\
			% self.__class__.__name__
		)


@export
class strip(Sanitizer):
	"""Wrapper for str.strip"""

	__slots__ = ('chars',)

	def __init__(self, chars=None):
		self.chars = chars

	def _strip(self, value):
		return value.strip() if self.chars is None else value.strip(self.chars)

	def __call__(self, value):
		return self._strip(value) if isinstance(value, str) else value


@export
class lstrip(strip):

	def _strip(self, value):
		return value.lstrip() if self.chars is None else value.lstrip(self.chars)


@export
class rstrip(strip):

	def _strip(self, value):
		return value.rstrip() if self.chars is None else value.rstrip(self.chars)


@export
class split(Sanitizer):

	def __init__(self, sep=' ', coercer=str, sanitize=None, maxsplits=-1):
		self.sep = sep
		self.coercers = _to_list(coercer)
		self.maxsplits = maxsplits
		self.sanitizers = _to_list(sanitize)

	def split(self, value):
		return value.split(self.sep, self.maxsplits)

	def coerce(self, value):
		for coercer in self.coercers:
			value = coercer(value)
		return value

	def isanitize(self, value):
		for sanitizer in self.sanitizers:
			value = sanitizer(value)
		return value

	def __call__(self, value):
		if isinstance(value, str):
			value = [self.isanitize(self.coerce(v)) for v in self.split(value)]
		return value


@export
class rsplit(split):

	def split(self, value):
		return value.rsplit(self.sep, self.maxsplits)


@export
class nonelike(Sanitizer):

	like_values = set(('', 'none', 'None', 'NONE', 'null', 'Null', 'NULL', None))

	def __init__(self, like_values=None):
		if like_values:
			self.like_values = like_values

	def __call__(self, value):
		return None if value in self.like_values else value


@export
class boollike(Sanitizer):
	#  value will deserialize to `True`. primitive boolly
	true_like = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
	#: Values that will (de)serialize to `False`.
	false_like = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))

	def __init__(self, true_like=None, false_like=None):
		if true_like:
			self.true_like = true_like
		if false_like:
			self.false_like = false_like

	def __call__(self, value):
		if value in self.true_like:
			return True
		elif value in self.false_like:
			return False
		return value



def _to_list(x, default=(), ignore=six.string_types):
	x = default if x is None else x
	if isinstance(x, Iterable) and (not ignore or not isinstance(x, ignore)):
		return list(x)
	else:
		return [x]