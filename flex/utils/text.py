import re
import sys
import base64
import datetime
import six
from decimal import Decimal

from .lazy import Promise


class _UnicodeDecodeError(UnicodeDecodeError):
	def __init__(self, obj, *args):
		self.obj = obj
		UnicodeDecodeError.__init__(self, *args)

	def __str__(self):
		original = UnicodeDecodeError.__str__(self)
		return '%s. You passed in %r (%s)' % (original, self.obj, type(self.obj))



def begin(text, begin, n=1):
	"""
	Start a string with only n instances of a given value.
	"""
	text = re.sub('^'+re.escape(begin)+'+', '', text)
	return (begin*n)+text


def compact(text, strip=True, space=' '):
	"""
	Remove all repeating spaces and replace space with a single instance of
	the given (space) value.
	If strip is True, the string will also be striped.
	"""
	if strip:
		text = text.strip()
	return re.sub(' +', space, text)


def concat(iterable, sep = ' ', minified = False):
	text = sep.join(iterable)
	return minified(text, sep) if minified else compact(text)


def humanize(value):
	if not value:
		return str(value)
	text = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', str(value))
	text = re.sub('([a-z0-9])([A-Z])', r'\1 \2', text)
	return re.sub('_+', ' ', text)


def finish(text, finish, n=1):
	"""
	End a string with n instances of a given value.
	"""
	text = re.sub(re.escape(finish)+'+$', '', text)
	return text+(finish*n)


def matches(pattern, text):
	"""Determine if a given string matches a given pattern."""
	pattern = re.escape(pattern).replace('\*', '.*')
	if re.match(pattern, text):
		return True
	else:
		return False


def minify(text, replace=' '):
	text = re.sub('[\t\n\r\f\v]+', replace, text)
	return compact(text)



def replace(text, search, replace = ''):
	if isinstance(search, dict):
		items = dict((re.escape(k), search[k]) for k in search.keys())
	elif isinstance(search, str):
		if not isinstance(replace, str):
			m = "The replacement value for strings ({0}) should also be string. {1} given."
			raise ValueError(m.format(search, type(replace).title()))
		items = {re.escape(search) : replace}
	else:
		if isinstance(replace, str):
			items = dict((re.escape(s), replace) for s in search)
		else:
			items = dict((re.escape(s), r) for s, r in zip(search, replace))

	pattern = re.compile("|".join(items.keys()))
	return pattern.sub(lambda m: items[re.escape(m.group(0))], text)


def slice(text, length=100, offset = 0, last_word=True):
	"""
	Slice a string.
	"""
	text = text[offset:]
	if len(text) <= length or not last_word:
		return text[:length]
	return re.sub('(\s+\S+\s*)$', '', text[:length])


def truncate(text, length=100, offset=0, words=False):
	"""Truncate a string."""
	return slice(text, length=length, offset=offset, last_word=words)


def slug(text, delimeter = '-' , num = None, zeropad = 0):
	text = text.lower()
	text = re.sub(r'[^0-9a-zA-Z_-]+', ' ', text)

	if num is not None:
		numf = '{:0>'+str(zeropad)+'}'
		text += ' ' + numf.format(num)

	return compact(text, space=delimeter)


def snake(text):
	text = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)
	text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text).lower()
	# return text
	return re.sub(r'[^0-9a-z_]+', '_', text)


def startcase(val):
	return re.sub(r'_+', ' ', slug(val)).title()


def words(text, words=100, end ='...'):
	pattern = re.compile('(\s*\S+\s*){1,'+str(words)+'}')
	matches = pattern.match(text)

	if not matches:
		return text

	short = matches.group(0)
	if len(text) > len(short):
		return short.rstrip() + end
	else:
		return short


def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
	if x is None:
		return None
	if isinstance(x, (bytes, bytearray, memoryview)):
		return bytes(x)
	if isinstance(x, str):
		return x.encode(charset, errors)
	raise TypeError('Expected bytes')


def is_hex(s):
	return re.fullmatch(r"^[0-9a-fA-F]+$", s or "") is not None


def tobase64(s, padding=int, altchars=b'-_'):
	rv = base64.b64encode(to_bytes(s), altchars).decode()
	if padding is int:
		lenb4, rv = len(rv), rv.rstrip('=')
		rv = '%s%s' % (rv, str(lenb4-len(rv)))
	elif padding:
		rv = rv.replace('=', padding)
	return rv


def debase64(s, padding=int, altchars=b'-_', validate=False):
	if padding is int:
		pad, s = int(s[-1]), s[:-1]
		s = '%s%s' % (s, '='*pad)
	elif padding:
		pattern = '^(.*)[%s]+$' % re.escape(padding)
		s = re.sub(pattern, r'\1\=')
	rv = base64.b64decode(s, altchars=altchars, validate=validate)
	return rv.decode()



def smart_text(s, encoding='utf-8', strings_only=False, errors='strict'):
	"""
	Returns a text object representing 's' -- unicode on Python 2 and str on
	Python 3. Treats bytestrings using the 'encoding' codec.

	If strings_only is True, don't convert (some) non-string-like objects.
	"""
	if isinstance(s, Promise):
		# The input is the result of a gettext_lazy() call.
		return s
	return force_text(s, encoding, strings_only, errors)


_PROTECTED_TYPES = six.integer_types + (
	type(None), float, Decimal, datetime.datetime, datetime.date, datetime.time
)


def is_protected_type(obj):
	"""Determine if the object instance is of a protected type.

	Objects of protected types are preserved as-is when passed to
	force_text(strings_only=True).
	"""
	return isinstance(obj, _PROTECTED_TYPES)



def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
	"""
	Similar to smart_text, except that lazy instances are resolved to
	strings, rather than kept as lazy objects.

	If strings_only is True, don't convert (some) non-string-like objects.
	"""
	# Handle the common case first for performance reasons.
	if issubclass(type(s), six.text_type):
		return s
	if strings_only and is_protected_type(s):
		return s
	try:
		if not issubclass(type(s), six.string_types):
			if six.PY3:
				if isinstance(s, bytes):
					s = six.text_type(s, encoding, errors)
				else:
					s = six.text_type(s)
			elif hasattr(s, '__unicode__'):
				s = six.text_type(s)
			else:
				s = six.text_type(bytes(s), encoding, errors)
		else:
			# Note: We use .decode() here, instead of six.text_type(s, encoding,
			# errors), so that if s is a SafeBytes, it ends up being a
			# SafeText at the end.
			s = s.decode(encoding, errors)
	except UnicodeDecodeError as e:
		if not isinstance(s, Exception):
			raise _UnicodeDecodeError(s, *e.args)
		else:
			# If we get to here, the caller has passed in an Exception
			# subclass populated with non-ASCII bytestring data without a
			# working unicode method. Try to handle this without raising a
			# further exception by individually forcing the exception args
			# to unicode.
			s = ' '.join(force_text(arg, encoding, strings_only, errors)
						 for arg in s)
	return s
