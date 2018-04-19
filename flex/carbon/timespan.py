import re
import time
import datetime
from pytz import timezone
from dateutil import tz
from time import struct_time
import calendar
from collections import Sequence
from flex.utils.decorators import cached_class_property




class timespan(object):

	__slots__ = '_count', '_unit',

	# UNITS = dict(
	# 	'second'=None, 'minute'=None,
	# 	'hour'=None, 'day'=None,
	# 	'week'=None, 'month'=None,
	# 	'quarter'=None, 'year'=None
	# )
	class UNITS:
		second = None
		minute = None
		hour = None
		day = None
		week = None
		month = None
		quarter = None
		year = None

	_str_re_pattern = r'^(\d+) *?(%(units)s)s?$'

	@cached_class_property
	def UNIT_SET(self):
		return frozenset((u for u in dir(self.UNITS) if '_' not in (u[0], u[-1])))

	@cached_class_property
	def _str_re(self):
		return re.compile(self._str_re_pattern % dict(units='|'.join(self.UNIT_SET)))

	@classmethod
	def _parse_str(self, value, *, silent=False):
		m = self._str_re.search(value.lower())
		count, unit = m.groups()
		if not silent and not(count and unit):
			raise ValueError('Invalid timespan string.')
		return count and int(count), str(unit, 'utf-8')

	@classmethod
	def fromstr(self, value):
		return self(*self._parse_str(value))

	@classmethod
	def fromseq(self, value):
		return self(*value)

	fromlist = fromtuple = fromseq

	@classmethod
	def parse(self, value):
		if isinstance(value, (str, bytes)):
			return self.fromstr(value)
		elif isinstance(value, Sequence):
			return self.fromseq(value)
		else:
			raise ValueError('Invalid timespan value.')

	def __init__(self, count, unit):
		if not isinstance(count, int):
			raise TypeError('expected int, got %r.' % type(count))
		elif unit not in self.UNIT_SET:
			raise ValueError('Invalid unit. Allowed: %r.' % self.UNIT_SET)
		else:
			self._count = count
			self._unit = unit

	@property
	def count(self):
		return self._count

	@property
	def unit(self):
		return self._unit

	def __getnewargs__(self):
		return self.count, self.unit

	def __str__(self):
		return '%s %s%s' % (self.count, self.unit, '' if self.count == 1 else 's')

	def __repr__(self):
		return '%s("%s")' % (self.__class__.__name__, self)



class SecondSpan(timespan):

	__slots__ = ()

	_unit = 'second'


class MinuteSpan(timespan):

	__slots__ = ()

	_unit = 'minute'



class HourSpan(timespan):

	__slots__ = ()

	_unit = 'hour'



class DaySpan(timespan):

	__slots__ = ()

	_unit = 'day'



class WeekSpan(timespan):

	__slots__ = ()

	_unit = 'week'



class MonthSpan(timespan):

	__slots__ = ()

	_unit = 'month'



class QuarterSpan(timespan):

	__slots__ = ()

	_unit = 'quarter'



class YearSpan(timespan):

	__slots__ = ()

	_unit = 'year'
