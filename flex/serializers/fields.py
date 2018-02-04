from marshmallow.fields import *
from marshmallow.fields import DateTime as BaseDateTime

from flex import carbon
from sqlalchemy_utils.types import PhoneNumber as _PhoneNumber

import phonenumbers



class DateTime(BaseDateTime):

	DATEFORMAT_SERIALIZATION_FUNCS = dict(
		**BaseDateTime.DATEFORMAT_SERIALIZATION_FUNCS
	)

	def __init__(self, format=None, local=None, load_local=None, **kwargs):
		if local is not None:
			self.localtime = local
		super(DateTime, self).__init__(format=format, **kwargs)
		self.load_localtime = self.localtime if load_local is None else load_local



class Carbon(DateTime):

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

	default_error_messages = {
		'required': 'This field is required.',
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


class PhoneNumber(String):

	default_error_messages = {
		'invalid': "This field must be a valid phone number ('+XXXXXXXXXX', or'0XXXXXXXXX' if local). 15 digits max.",
	}

	def __init__(self, region=None, **kwargs):
		super(PhoneNumber, self).__init__(**kwargs)
		self.region = region

	def _deserialize(self, value, attr, data):
		value = super(PhoneNumber, self)._deserialize(value, attr, data)
		phn = _PhoneNumber(value, self.region)
		if not phn.is_valid_number():
			self.fail('invalid')
		return phn
