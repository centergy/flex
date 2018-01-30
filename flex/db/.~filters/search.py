from .field_set import FieldSet
from .const import NOTHING
from . import sanitize, base, exc
from .operators import operators
from tea.collections import stack
from sqlalchemy import or_, and_

class Search(FieldSet):
	param = None

	def __init__(self, *args, **kwargs):
		self.param = kwargs.pop('param', None) or self.param
		super(Search, self).__init__(*args, **kwargs)


	def parse_params(self, query, params, all_params=None):
		if self.param and len(self.fieldset) > 0:
			operators = []
			value = params.get(self.param, '').strip()
			if value:
				for param, field in self.fieldset.items():
					operator = self.get_field_operator(field, value, query)
					if operator:
						operators.append(operator)
			return or_, operators
		return None, None



