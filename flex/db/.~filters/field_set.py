from .const import NOTHING
from . import sanitize, base, exc
from .operators import operators, Operator
from tea.collections import stack
from warnings import warn
import copy
from sqlalchemy import and_, or_

class Field(object):
	"""docstring for Field"""
	def __init__(self, param, operator=None, name=None):
		self.param = param
		self.operator = operator
		self.name = name or param

	def __str__(self):
		return self.name


class FieldSet(base.QueryFilter):
	fields = None
	operators = operators
	default_operator = '='
	fieldset = stack()
	expression = None

	def __init__(self, *args, **kwargs):
		self.fields = self.fields if kwargs.get('fields') is None else kwargs.pop('fields')
		self.operators = self.operators if kwargs.get('operators') is None else kwargs.pop('operators')
		self.default_operator = self.default_operator \
			if kwargs.get('default_operator') is None else kwargs.pop('default_operator')
		super(FieldSet, self).__init__(*args, **kwargs)
		self._init_fieldset()

	def _init_fieldset(self):
		fieldset = stack()
		for key in self.__class__.fieldset.keys():
			fieldset[key] = copy.deepcopy(self.__class__.fieldset[key])

		if self.fields and isinstance(self.fields, (list, tuple)):
			for f in self.fields:
				if f and isinstance(f, str):
					field = Field(*f.split(','))
					fieldset[field.param] = field
				else:
					raise exc.FilterFieldError(
						"Invalid field {} in {}".format(f, self.__class__.__name__))
		elif not(self.fields is None or self.fields == '__all__'):
			raise exc.FilterFieldError(
					"Fields attribute should be a list, tuple, None or str('__all__')."
					" {} given in {}.".format(type(self.fields), self.__class__.__name__))

		if self.fields == '__all__':
			warn('Setting FieldSet filter fields to "__all__" is not well'\
				'implemtend and will change in near future.', FutureWarning)

		for key, field in fieldset.items():
			if not field.operator:
				if self.default_operator:
					field.operator = self.default_operator
				else:
					raise exc.FilterFieldError(
						"Error setting operator for field {}. Default operator not set {}"
						.format(field.param, self.__class__.__name__))
			if field.operator not in self.operators:
				raise exc.FilterFieldError(
						"Invalid field operator {} in {} {}."
						.format(field.operator, field.param, self.__class__.__name__))
		if not(self.default_operator and self.default_operator in self.operators):
			raise exc.FilterFieldError(
						"Invalid value default_operator {} in {}."
						.format(self.default_operator, self.__class__.__name__))
		self.fieldset = fieldset

	@property
	def params(self):
		return self.fieldset.keys()

	def apply(self, query, params, all_params=None):
		expr, operators = self.parse_params(query, params, all_params)
		if operators:
			if expr:
				query = query.filter(expr(*(op() for op in operators)))
			else:
				for op in operators:
					query = query.filter(op())
		return query

	def parse_params(self, query, params, all_params=None):
		operators = []
		params = params.copy()
		for param, field in self.fieldset.items():
			value = params.pop(param, NOTHING)
			if value is not NOTHING:
				operator = self.get_field_operator(field, value, query)
				if operator:
					operators.append(operator)

		if self.fields == '__all__':
			for key, value in params.items():
				field = Field(key, self.default_operator)
				operator = self.get_field_operator(field, value, query)
				if operator:
					operators.append(operator)
		return self.expression, operators

	def get_field_operator(self, field, value, query):
		operator = value
		if not isinstance(operator, Operator):
			operator = self.operators.make(field.operator, value)
		return operator.on(self.get_field(query, field.name))

	def apply_field_filter(self, query, field, operator):
		if operator.source:
			query = operator(query, source=None)
		elif not operator.source:
			query_method = 'filter_by_{}'.format(field.name)
			if hasattr(query, query_method):
				operator.concrete = query_method
				query = operator(query, operator.abstract)
			else:
				model_attr = self.get_field(query, field.name)
				query = query.filter(operator(model_attr))
		return query

