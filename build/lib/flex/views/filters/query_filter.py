from ...url_filter.filtersets import ModelFilterSet


class FilterBackend(object):

	default_filter_set = ModelFilterSet

	def get_filter_class(self, view, query):
		"""Return the `FilterSet` used to filter the query."""
		filter_class = getattr(view, 'filter_class', None)
		filter_fields = getattr(view, 'filter_fields', None)

		if filter_class:
			filter_model = filter_class.Meta.model

			assert any((issubclass(m, filter_model) for m in query.model_classes)), (
				'FilterSet model %s does not match any query model %s' % \
				(filter_model, query.model_classes))

			return filter_class

		if filter_fields:
			class AutoFilterSet(self.default_filter_set):
				class Meta:
					model = query.model_class
					fields = filter_fields

			return AutoFilterSet

		return None

	def apply(self, request, query, view):
		filter_class = self.get_filter_class(view, query)

		if filter_class:
			return filter_class(request.args, query, request=request).filter()

		return query
