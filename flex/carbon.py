import datetime, time, re
from pytz import timezone
from dateutil import tz
from time import struct_time
import calendar


import arrow

from arrow.util import is_timestamp, isstr
	# from arrow import parser as arrow_parser


def ordinal(n):
	m100 = n % 100
	m10 = n % 10
	small = {1:'st', 2:'nd', 3:'rd'}
	return 'th' if 4 <= m100 <= 20 else small.get(m10, 'th')

ORDINAL_REGEX = re.compile(r'\{th\}')

def strftime(dtm, f, *args, **kwargs):
	# return dtm.strftime(f).replace('{th}', ordinal(dtm.day))
	th = ordinal(dtm.day) if isinstance(dtm, (datetime.datetime, datetime.date)) else ''
	return dtm.strftime(f).format(*args, th=th, **kwargs)


_localtz_func = tz.tzlocal

def _to_localtz_func(value):
	if callable(value):
		return value
	def localtz():
		return localtz.value
	localtz.value = value
	return localtz


def localtz(*func):
	global _localtz_func
	if func:
		_localtz_func = _to_localtz_func(func[0])
		return _localtz_func
	return _localtz_func()


def systz():
	tz.tzlocal()


class Carbon(arrow.Arrow):
	def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0,
				tzinfo=None):
		# if tzinfo is None: tzinfo = localtz()
		super(Carbon, self).__init__(year, month, day, hour, minute, second,
			microsecond, tzinfo)




class Factory(arrow.ArrowFactory):
	pass
	# def get(self, *args, **kwargs):
	# 	locale = kwargs.get('locale', 'en_us')
	# 	if len(args) == 1:
	# 		arg = args[0]
	# 		# (None) -> now, @ utc.
	# 		if arg is None:
	# 			return self.type.now()

	# 		# try (int, float, str(int), str(float)) -> utc, from timestamp.
	# 		if is_timestamp(arg):
	# 			return self.type.fromtimestamp(arg, tzinfo=localtz())

	# 		# (Arrow) -> from the object's datetime.
	# 		if isinstance(arg, arrow.Arrow):
	# 			return self.type.fromdatetime(arg.datetime)

	# 		# (datetime) -> from datetime.
	# 		if isinstance(arg, detime):
	# 			return self.type.fromdatetime(arg, tzinfo=arg.tzinfo or localtz())

	# 		# (date) -> from date.
	# 		if isinstance(arg, date):
	# 			return self.type.fromdate(arg, tzinfo=localtz())

	# 		# (tzinfo) -> now, @ tzinfo.
	# 		elif isinstance(arg, tzonei):
	# 			return self.type.now(arg)

	# 		# (str) -> now, @ tzinfo.
	# 		elif isstr(arg):
	# 			dt = arrow.parser.DateTimeParser(locale).parse_iso(arg)
	# 			return self.type.fromdatetime(dt, tzinfo=dt.tzinfo or localtz())

	# 		# (struct_time) -> from struct_time
	# 		elif isinstance(arg, struct_time):
	# 			return self.type.fromtimestamp(calendar.timegm(arg), tzinfo=localtz())

	# 		else:
	# 			raise TypeError('Can\'t parse single argument type of \'{0}\''.format(type(arg)))

	# 	kwargs.setdefault('tzinfo', localtz())
	# 	return super(Factory, self).get(*args, **kwargs)

	# def local(self, *args, **kwargs):
	# 	return self.get(*args, **kwargs).to('local')


carbon = Factory(Carbon)


def get(*args, **kwargs):
	"""Returns a :class:`Carbon` object based on flexible inputs."""
	return carbon.get(*args, **kwargs)


def utcnow():
	"""Returns a :class:`Carbon` object, representing "now" in UTC time."""
	return carbon.utcnow()


def now(tz=None):
	"""Returns a :class:`Carbon` object, representing "now".

		:param tz: (optional) An expression representing a timezone.  Defaults to local time.

		Recognized timezone expressions:

			- A ``tzinfo`` object.
			- A ``str`` describing a timezone, similar to 'US/Pacific', or 'Europe/Berlin'.
			- A ``str`` in ISO-8601 style, as in '+07:00'.
			- A ``str``, one of the following:  'local', 'utc', 'UTC'.
	"""
	return carbon.now(tz)




