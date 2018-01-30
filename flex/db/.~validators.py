from tea.gap import rules
from tea.utils import isiterable
from sqlalchemy.orm import object_session
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Query as AlchemyQuery
from tea.decorators import locked_cached_property
from .model import BaseModel
from . import utils

__all__ = [
	'Unique', 'Exists',
]

class Unique(rules.Rule):
	message = "The `{__name__}` should be unique. `{__value__}` already exists."
	model = None
	_columns = None
	pk = None

	def __init__(self, model, cols, query=None, pk=None, pk_key='id', filter=None, db=None, **kwargs):
		super(Unique, self).__init__(**kwargs)
		self.model = model
		self._columns = cols if isinstance(cols, (tuple, list)) else (cols,)
		self.pk = pk
		self.pk_key = pk_key
		self.query = query
		self.filter = filter
		if db is not None:
			self.db = db

	@locked_cached_property
	def columns(self):
		rv = []
		for col in self._columns:
			if isinstance(col, str):
				rv.append(self.model.column(col))
			elif isinstance(col, (tuple, list)):
				col, value = col
				if isinstance(col, str):
					col = self.model.column(col)
				rv.append((col, value))
			else:
				rv.append(col)
		return rv

	def check(self, value, data_set=None):
		if self.should_ignore(value):
			return True
		#column = self.model.column(self.column) if isinstance(self.column, str) else self.column
		pkcols = self.model.pk_columns()
		query = self.get_query(data_set)
		ident = self.pk_value(data_set)
		if ident is not None:
			query = query.filter(*utils.pk_not_eq_criterion(self.model, ident))

		query = self.apply_column_filters(query, data_set)

		if self.filter is not None:
			query = self.filter(query, value, data_set)

		count = query.limit(1).count()
		return count == 0

	def get_query(self, data):
		if not self.query:
			if isinstance(data.data, BaseModel):
				session = object_session(data.data)
				if session:
					return session.query(self.model).autoflush(False)
			return self.db.query(self.model).autoflush(False)

		if isinstance(self.query, AlchemyQuery):
			return self.query.autoflush(False)
		elif callable(self.query):
			query = self.query()
			if isinstance(query, AlchemyQuery):
				return query.autoflush(False)
		raise ValueError('Invalid query given in {}'.format(self))

	def pk_value(self, data):
		if self.pk:
			return self.pk
		if self.pk_key:
			if not isinstance(self.pk_key, (tuple, list)):
				self.pk_key = (self.pk_key,)
			pks = []
			nulls = 0
			for k in self.pk_key:
				v = data.get(k, None)
				if v is None:
					nulls += 1
				pks.append(v)
			return pks if len(pks) > nulls else None
		return None

	def apply_column_filters(self, query, data):
		for col in self.columns:
			if isinstance(col, tuple):
				col, value = col
			else:
				value = data.get(col.name, None)
			query = query.filter(col == value)
		return query



class Exists(rules.Rule):
	message = "The selected {__name__} is invalid."
	model = None
	column = None
	pk = None

	def __init__(self, model, column, pk=None, filter=None, db=None, **kwargs):
		super(Exists, self).__init__(**kwargs)
		self.model = model
		self.column = column
		self.pk = pk
		self.filter = filter
		if db is not None:
			self.db = db

	def check(self, value, data_set=None):
		if self.should_ignore(value):
			return True
		column = self.model.column(self.column) if isinstance(self.column, str) else self.column
		pkcols = self.model.pk_columns()
		entries = db.query(*pkcols).filter(column == value)
		if self.pk is not None:
			pkcol = pkcols[0]
			entries = entries.filter(pkcol != self.pk)
		if self.filter is not None:
			entries = self.filter(entries, value, data_set)
		return entries.first() is not None

