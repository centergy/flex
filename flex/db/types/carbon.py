import six
import arrow
from dateutil import tz
from collections import Iterable
from datetime import datetime, date
from sqlalchemy_utils import types
from arrow.util import is_timestamp

from flex.utils.carbon import carbon


class Carbon(types.ArrowType):

	arrow_factory = carbon

	def __init__(self, timezone=True, utc=True, factory=None, **kwargs):
		self.arrow_factory = factory or self.arrow_factory
		self.to_utc = utc
		super(Carbon, self).__init__(timezone=timezone, **kwargs)

	def process_bind_param(self, value, dialect):
		if not value:
			return value
		value = self._coerce(value)
		if self.to_utc:
			value = value.to('UTC')
		return value.datetime if self.impl.timezone else value.naive

	def _coerce(self, value):
		if value is None or isinstance(value, self.arrow_factory.type):
			return value
		if isinstance(value, six.string_types):
			value = self.arrow_factory.get(value)
		elif is_timestamp(value):
			value = self.arrow_factory.get(value)
		elif isinstance(value, Iterable):
			value = self.arrow_factory.get(*value)
		elif isinstance(value, datetime):
			value = self.arrow_factory.get(value)
		elif isinstance(value, arrow.Arrow):
			value = self.arrow_factory.get(value)
		return value

