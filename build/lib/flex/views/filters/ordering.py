from sqlalchemy import desc, asc


class OrderingFilterBackend(object):

	def get_view_ordering(self, view, request):
		rv = request.args.get(view.ordering_arg) if view.ordering_arg else None
		if rv:
			rv = rv.split(',')
			allowed_fields = view.ordering_fields
			if allowed_fields:
				rv = (v for v in rv if v.lstrip('-') in allowed_fields)
		return rv or view.ordering or ()

	def orderby_criterion(self, fields, model_class):
		for field in fields:
			if field[0] == '-':
				yield desc(getattr(model_class, field[1:]))
			else:
				yield asc(getattr(model_class, field))

	def apply(self, request, query, view):
		fs = self.get_view_ordering(view, request)
		mcls = getattr(query, 'model_class', None) \
				or getattr(view, 'model_class', None)

		if fs and mcls:
			query = query.order_by(*self.orderby_criterion(fs, mcls))
		return query
