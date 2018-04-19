import re
from .base import *
from marshmallow.fields import DateTime as BaseDateTime
from sqlalchemy_utils import (
	PhoneNumberParseException, PhoneNumber as _PhoneNumber
)

from flex.locale import locale
from flex.db import types
from flex.conf import config
from flex import carbon

import phonenumbers
from flex import intervals



class Slug(String):

	default_error_messages = {
		'invalid': 'Field may only contain letters, numbers, underscores and hyphens.',
		'invalid_unicode': 'Field may only contain Unicode letters, numbers, underscores and hyphens.',
	}

	ascii_re = r'^[-a-zA-Z0-9_]+\Z'
	unicode_re = r'^[-\w]+\Z'

	def __init__(self, *args, **kwargs):
		self._unicode = kwargs.pop('unicode', False)
		super(Slug, self).__init__(*args, **kwargs)
		self.regex = self.unicode_re if self._unicode else self.ascii_re
		self.regex = re.compile(self.regex)

	def _deserialize(self, value, attr, data):
		value = super(Slug, self)._deserialize(value, attr, data)
		if not bool(self.regex.search(value)):
			self._unicode and self.fail('invalid_unicode') or self.fail('invalid')
		return value


class DateTime(BaseDateTime):

	DATEFORMAT_SERIALIZATION_FUNCS = dict(
		**BaseDateTime.DATEFORMAT_SERIALIZATION_FUNCS
	)

	blank_to_none = True

	def __init__(self, format=None, local=None, load_local=None, **kwargs):
		if local is not None:
			self.localtime = local
		super(DateTime, self).__init__(format=format, **kwargs)
		self.load_localtime = self.localtime if load_local is None else load_local



class Carbon(DateTime):

	blank_to_none = True

	def _serialize(self, value, attr, obj):
		if value and carbon.arrow and isinstance(value, carbon.arrow.Arrow):
			value = value.datetime
		return super(Carbon, self)._serialize(value, attr, obj)

	def _deserialize(self, value, attr, data):
		rv = super(Carbon, self)._serialize(value, attr, data)
		if rv and carbon.arrow:
			rv = carbon.Carbon.fromdatetime(rv)
			if self.load_localtime:
				rv = rv.to('local')
		return rv


class Enum(Field):

	blank_to_none = True

	default_error_messages = {
		'invalid': 'Not a valid option.',
	}

	def __init__(self, type, **kwargs):
		super(Enum, self).__init__(**kwargs)
		self.enumcls = type

	def _serialize(self, value, attr, obj):
		if value is None:
			return value
		rv = getattr(value, 'label', None)
		return getattr(value, 'name') if rv is None else rv

	def _deserialize(self, value, attr, data):
		try:
			return self.enumcls[value]
		except KeyError:
			self.fail('invalid')


class Range(Field):

	blank_to_none = True
	range_class = intervals.Interval

	default_error_messages = {
		'invalid': 'Not a valid range.',
	}

	def __init__(self, type=None, as_string=True, **kwargs):
		super(Range, self).__init__(as_string=as_string, **kwargs)
		if type is not None:
			self.range_class = type

	def _serialize(self, value, attr, obj):
		if value is None:
			return value
		else:
			return str(value)

	def _deserialize(self, value, attr, data):
		try:
			if isinstance(value, str):
				return self.range_class.from_string(value)
			elif isinstance(value, (list, tuple)) and len(value) == 2:
				return self.range_class(value)
			else:
				self.fail('invalid')
		except (intervals.IntervalException, TypeError):
			self.fail('invalid')


class PhoneNumber(String):

	default_error_messages = {
		# 'required': 'This field is required.',
		# 'type': 'Invalid input type.', # used by Unmarshaller
		# 'null': 'This field is required.',
		'invalid': "This field must be a valid phone number ('+XXXXXXXXXX', or'0XXXXXXXXX' if local). 15 digits max.",
	}
	default_region = 'KE'
	blank_to_none = True

	def __init__(self, region=None, **kwargs):
		super(PhoneNumber, self).__init__(**kwargs)
		self._region = region

	@property
	def region(self):
		if self._region is None:
			return locale.territory or self.default_region
		return self._region

	def _deserialize(self, value, attr, data):
		value = super(PhoneNumber, self)._deserialize(value, attr, data)

		try:
			phn = _PhoneNumber(value, self.region)
		except PhoneNumberParseException as e:
			self.fail('invalid')
		else:
			if phn.is_valid_number():
				return phn
			self.fail('invalid')


class Money(Decimal):

	def __init__(self, places=2, rounding=None, thousand_sep=False, **kwargs):
		super(Money, self).__init__(places, rounding, **kwargs)
		self.thousand_sep = thousand_sep

	# override Number
	def _format_num(self, value):
		if value is None:
			return None

		if isinstance(value, str):
			value = value.replace(',', '')

		return super(Money, self)._format_num(value)

	def _to_string(self, value):
		sep = ',' if self.thousand_sep is True else self.thousand_sep or ''
		return format(value, '%sf' % (sep,))


