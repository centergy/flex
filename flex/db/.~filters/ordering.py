from sqlalchemy import asc, desc
from .const import NOTHING
from . import sanitize, base
import six


class Ordering(base.QueryFilter):
	param = None
	fields = '__all__'
	ordering = None
	default_ordering = None

	def __init__(self, *args, **kwargs):
		self.param = kwargs.pop('param', None) or self.param
		self.fields = kwargs.pop('fields', None) or self.fields
		self.ordering = self.ordering if kwargs.get('ordering') is None else kwargs.pop('ordering')
		self.default_ordering = self.default_ordering \
			if kwargs.get('default_ordering') is None else kwargs.pop('default_ordering')

		super(Ordering, self).__init__(*args, **kwargs)

	def apply(self, query, params, fields=None):
		ordering = self.parse_params(params, fields)
		if ordering and isinstance(ordering, (list, tuple)):
			for field, order in ordering:
				method = getattr(query, 'order_by_{}'.format(field), None)
				if method:
					query = method(order)
				else:
					field = self.get_field(query, field)
					if field:
						query = query.order_by(order(field))
		elif ordering:
			if ordering in (asc, desc):
				query = query.order(ordering)
			else:
				query = query.order()
		return query

	def parse_params(self, params, allowed_fields=None):
		if self.param:
			ordering = params.get(self.param, self.ordering)
		else:
			ordering = self.ordering

		if isinstance(ordering, six.string_types):
			if ordering in ('-1', '0', '1'):
				ordering = int(ordering)
			else:
				ordering = ordering.split(',')

		if ordering is None or isinstance(ordering, (int, bool)):
			return self.get_default_ordering(ordering)

		allowed = self.fields or allowed_fields

		results = []
		if allowed and isinstance(ordering, (list, tuple)):
			for field in ordering:
				field = sanitize.force_text(field).strip()
				if len(field) > 1:
					order = desc if field[0] == '-' else asc
					field = field[1:].strip() if field[0] == '-' else field
					if allowed == '__all__' or field in allowed:
						results.append((field, order))
		return results

	def get_default_ordering(self, param):
		if isinstance(param, bool):
			return param
		elif param is 1:
			return asc
		elif param is -1:
			return desc
		elif param is 0:
			return False
		else:
			return self.default_ordering
