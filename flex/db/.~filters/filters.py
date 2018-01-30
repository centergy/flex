from tea.collections import to_list
from cached_property import cached_property
from sqlalchemy import exc as sa_exc, asc, desc
from .const import NOTHING
from . import sanitize, exc, base



class FilterSet(Filter):
	fields = None
	sanitizer = None

	def __init__(self, *args, **kwargs):
		self.fields = kwargs.pop('fields', self.fields)
		self.sanitizer = kwargs.pop('sanitizer', self.sanitizer)
		super(FilterSet, self).__init__(*args, **kwargs)

	def get_sanitizer(self):
		return self.sanitizer

	def apply(self, query, params):
		if self.fields:
			for field in self.fields:
				if field in params:
					query = self.apply_field_filter(query, field, params)
		return query

	def parse_params(self, params):
		data = stack()
		for f in self.fields:
			if f in params:
				data[f] = params.get(f)

	def sanitize_params(self, params):
		data, errors = self.get_sanitizer().load(params)

	def apply_field_filter(self, query, name, params):
		method = getattr(self, "filter_%s" % name, self.apply_default_filter)
		return method(query, name, params)

	def apply_default_filter(self, query, name, params):
		value = self.parse_param(name, params)


	def parse_param(self, name, params):
		value = params.get(name)



class Search(Filter):
	pass

