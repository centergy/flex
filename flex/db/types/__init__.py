
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
	Choice,
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
	IntRangeType,
	IPAddressType,
	JSONType,
	LocaleType,
	LtreeType,
	NumericRangeType,
	Password,
	PasswordType as BasePasswordType,
	PhoneNumber,
	PhoneNumberParseException,
	register_composites,
	remove_composite_listeners,
	ScalarListException,
	ScalarListType,
	TimezoneType,
	TSVectorType,
	URLType,
	UUIDType,
	WeekDaysType
)

from .carbon import Carbon
from .phonenumber import PhoneNumberType

from sqlalchemy.dialects import postgresql as pg


class PasswordType(BasePasswordType):
	"""docstring for PasswordType"""
	def __init__(self, max_length=None, **kwargs):
		length = kwargs.pop('length', None)
		super(PasswordType, self).__init__(max_length, **kwargs)


