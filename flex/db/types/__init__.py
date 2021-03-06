
from sqlalchemy.types import (
	adapt_type,
	TypeEngine,
	TypeDecorator,
	Variant,
	to_instance,
	UserDefinedType,
	ARRAY,
	BIGINT,
	BINARY,
	BLOB,
	BOOLEAN,
	BigInteger,
	Binary,
	_Binary,
	Boolean,
	CHAR,
	CLOB,
	Concatenable,
	DATE,
	DATETIME,
	DECIMAL,
	Date,
	DateTime,
	Enum,
	FLOAT,
	Float,
	Indexable,
	INT,
	INTEGER,
	Integer,
	Interval,
	JSON,
	LargeBinary,
	MatchType,
	NCHAR,
	NVARCHAR,
	NullType,
	NULLTYPE,
	NUMERIC,
	Numeric,
	PickleType,
	REAL,
	SchemaType,
	SMALLINT,
	SmallInteger,
	String,
	STRINGTYPE,
	TEXT,
	TIME,
	TIMESTAMP,
	Text,
	Time,
	Unicode,
	UnicodeText,
	VARBINARY,
	VARCHAR,
)


from sqlalchemy_utils.types import (
	ArrowType as BaseArrowType,
	ChoiceType,
	ColorType,
	CompositeArray,
	CompositeType,
	CountryType,
	CurrencyType,
	DateRangeType,
	DateTimeRangeType,
	EmailType,
	EncryptedType,
	instrumented_list,
	InstrumentedList,
	IntRangeType as IntRange,
	IPAddressType as IPAddress,
	LocaleType as Locale,
	LtreeType as Ltree,
	NumericRangeType as NumericRange,
	Password as PasswordMutable,
	PasswordType as BasePasswordType,
	PhoneNumberType as BasePhoneNumberType,
	PhoneNumberParseException,
	register_composites,
	remove_composite_listeners,
	ScalarListException,
	ScalarListType as ScalarList,
	TimezoneType as Timezone,
	TSVectorType as TSVector,
	URLType,
	WeekDaysType as WeekDays,
)

__all__ = []

from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.util import generic_repr

import six
import arrow
from collections import Iterable
from datetime import datetime
from sqlalchemy_utils import types
from flex import carbon
from flex.conf import config
from flex.locale import locale


class _GenericReprMixin(object):

	def __repr__(self):
		return generic_repr(self)



class Choice(_GenericReprMixin, ChoiceType):
	pass

class Color(_GenericReprMixin, ColorType):
	pass


class Country(_GenericReprMixin, CountryType):
	pass


class Currency(_GenericReprMixin, CurrencyType):
	pass


class Composite(_GenericReprMixin, CompositeType):
	pass


class DateRange(_GenericReprMixin, DateRangeType):
	pass


class DateTimeRange(_GenericReprMixin, DateTimeRangeType):
	pass


class Encrypted(_GenericReprMixin, EncryptedType):
	pass


class Email(_GenericReprMixin, EmailType):
	pass


class URL(_GenericReprMixin, URLType):
	pass



class Carbon(_GenericReprMixin, BaseArrowType):

	carbon_factory = carbon.carbon

	def __init__(self, timezone=True, utc=True, factory=None, **kwargs):
		self.carbon_factory = factory or self.carbon_factory
		self.to_utc = utc
		super(Carbon, self).__init__(timezone=timezone, **kwargs)

	def process_bind_param(self, value, dialect):
		if not value:
			return value
		value = self._coerce(value)
		if self.to_utc:
			value = value.to('UTC')
		return value.datetime if self.impl.timezone else value.naive

	def process_result_value(self, value, dialect):
		if value:
			return self.carbon_factory.get(value)
		return value

	def _coerce(self, value):
		if value is None or isinstance(value, self.carbon_factory.type):
			return value
		if isinstance(value, six.string_types):
			value = self.carbon_factory.get(value)
		elif carbon.is_timestamp(value):
			value = self.carbon_factory.get(value)
		elif isinstance(value, Iterable):
			value = self.carbon_factory.get(*value)
		elif isinstance(value, datetime):
			value = self.carbon_factory.get(value)
		elif isinstance(value, arrow.Arrow):
			value = self.carbon_factory.get(value)
		return value

ArrowType = Carbon


# class Timespan(TypeDecorator):

# 	impl = Unicode(40)
# 	timespan_class = carbon.timespan
# 	python_type = carbon.timespan

# 	def process_bind_param(self, value, dialect):
# 		return None if value is None else str(self._coerce(value))

# 	def process_result_value(self, value, dialect):
# 		return value and self.timespan_class.parse(value) or None

# 	def process_literal_param(self, value, dialect):
# 		return None if value is None else str(self._coerce(value))

# 	def _coerce(self, value):
# 		if value is None:
# 			return None
# 		elif isinstance(value, self.timespan_class):
# 			return value
# 		else:
# 			return self.timespan_class.parse(value)

# 	@property
# 	def python_type(self):
# 		return self.impl.type.python_type



class Password(_GenericReprMixin, BasePasswordType):
	"""docstring for PasswordType"""
	def __init__(self, max_length=None, onload=None, **kwargs):
		length = kwargs.pop('length', None)

		def load_config(**kw):
			opts = config.top.get_namespace('PASSLIB_')
			opts.update(kw)
			return onload and onload(opts) or opts

		kwargs['onload'] = load_config
		super(Password, self).__init__(max_length, **kwargs)

PasswordMutable.associate_with(Password)



class PhoneNumber(_GenericReprMixin, BasePhoneNumberType):
	default_region = 'KE'

	def __init__(self, region=None, max_length=20, *args, **kwargs):
		self._region = None
		super(PhoneNumber, self).__init__(region, max_length, *args, **kwargs)

	@property
	def region(self):
		if self._region is None:
			return locale.territory or self.default_region
		return self._region

	@region.setter
	def region(self, value):
		self._region = value


