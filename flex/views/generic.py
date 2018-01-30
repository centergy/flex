import re
from flask.views import View

from .core import View
from flask import current_app
from .config import config


__all__ = [
	'GenericView', 'APIView', 'HTMLView'
]

NOTHING = object()



class GenericView(View):

	lookup_field = 'pk'
	lookup_url_kwarg = None

	serializer_class = None
	model_class = None

	filter_class = None
	filter_fields = None
	filter_backends = config.filter_backends

	ordering_arg = 'ordering'
	ordering_fields = None
	ordering = None

	def get_query(self, apply_filters=False):
		"""Return the Query instance to be used for fetching models."""
		return self.apply_filters(self.new_query()) if apply_filters else self.new_query()

	def new_query(self):
		"""Return the Query instance to be used for fetching models."""
		model_class = self.get_model_class()
		return model_class and model_class.objects

	def get_model_class(self, query=None):
		assert self.model_class is not None, (
				"'%s' should either include a `model_class` attribute, "
				"or override the `get_model_class()` method."
				% self.__class__.__name__
			)
		return self.model_class

	def get_object(self):
		query = self.get_query(True)
		lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

		# Perform the lookup filtering.
		lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

		assert lookup_url_kwarg in self.kwargs, (
			'Expected view %s to be called with a URL keyword argument '
			'named "%s". Fix your URL conf, or set the `.lookup_field` '
			'attribute on the view correctly.' %
			(self.__class__.__name__, lookup_url_kwarg)
		)

		model_class = getattr(query, 'model_class', None) or self.get_model_class()

		lookup_field = getattr(model_class, self.lookup_field)
		return query.filter(lookup_field == self.kwargs[lookup_url_kwarg]).first()

	def get_serializer(self, *args, **kwargs):
		"""
		Return the serializer instance that should be used for validating and
		deserializing input, and for serializing output.
		"""
		serializer_class = self.get_serializer_class()
		kwargs['context'] = self.get_serializer_context(kwargs.get('context'))
		return serializer_class(*args, **kwargs)

	def get_serializer_class(self):
		"""
		Return the class to use for the serializer.
		Defaults to using `self.serializer_class`.
		"""
		assert self.serializer_class is not None, (
				"'%s' should either include a `serializer_class` attribute, "
				"or override the `get_serializer_class()` method."
				% self.__class__.__name__
			)
		return self.serializer_class

	def get_serializer_context(self, context=None):
		"""Extra context provided to the serializer class."""
		context = context or {}
		context.setdefault('request', self.request)
		context.setdefault('view', self)
		return context

	def apply_filters(self, query):
		backends = self.filter_backends
		if backends:
			for backend in backends:
				query = backend().apply(self.request, query, self)

		return query # self.apply_query_ordering(query)

	def filtered_query(self):
		return self.apply_filters(self.query())

	def paginate_query(self, query):
		return None



class APIView(GenericView):
	pass



class HTMLView(GenericView):

	mimetype = 'text/html'
	template_name = None

	def get_payload_context(self):
		ctx = super(HTMLView, self).get_payload_context()
		ctx['template_name'] = self.template_name
		return ctx

	def build_response(self):
		self.payload.mimetype = self.payload.mimetype or self.mimetype
		return super(HTMLView, self).build_response()

