from tea.utils.encoding import force_text
from tea.collections import yielder
import six


class Sanitizer(object):

	def __call__(self, *args, **kwargs):
		return self.sanitize(*args, **kwargs)

	def sanitize(self, value):
		msg = "Sanitizer method sanitize() not implemented in {}"
		raise NotImplementedError(msg.format(self.__class__))


class strip(Sanitizer):
	"""docstring for TrimWhitespaces"""
	func_names = {
		'' : 'strip',
		'lr' : 'strip',
		'rl' : 'strip',
		'both' : 'strip',
		'l' : 'lstrip',
		'left' : 'lstrip',
		'r' : 'rstrip',
		'right' : 'rstrip',
	}
	def __init__(self, side=''):
		self.func = self.func_names[side]

	def sanitize(self, value):
		value = force_text(value, strings_only=True)
		if isinstance(value, six.string_types):
			func = getattr(value, self.func)
			return func()
		return value


class lstrip(strip):
	def __init__(self):
		super(lstrip, self).__init__('l')


class rstrip(strip):
	def __init__(self):
		super(rstrip, self).__init__('r')


class split(Sanitizer):
	
	def __init__(self, sep=' ', coercer=str, sanitize=None, maxsplits=-1):
		self.sep = sep
		self.coercers = yielder(coercer)
		self.maxsplits = maxsplits
		self.sanitizers = yielder(sanitize)
	
	def split(self, value):
		return value.split(self.sep, self.maxsplits)
	
	def coerce(self, value):
		for coercer in self.coercers:
			value = coercer(value)
		return value
	
	def isanitize(self, value):
		for sanitizer in self.sanitizers:
			sanitizer = _get_sanitizer(sanitizer)
			value = sanitizer(value)
		return value

	def sanitize(self, value):
		value = force_text(value, strings_only=True)
		if isinstance(value, six.string_types):
			rv = []
			for v in self.split(value):
				rv.append(self.isanitize(self.coerce(v)))
			return rv
		return value


class rsplit(split):
	def split(self, value):
		return value.rsplit(self.sep, self.maxsplits)


class nonelike(Sanitizer):
	like_values = set(('', 'none', 'None', 'NONE', 'null', 'Null', 'NULL', None))

	def __init__(self, like_values=None):
		if like_values:
			self.like_values = like_values

	def sanitize(self, value):
		return None if value in self.like_values else value
		

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

	def sanitize(self, value):
		if value in self.true_like:
			return True
		elif value in self.false_like:
			return False
		return value



def _get_sanitizer(obj):
	return obj() if isinstance(obj, type) else obj