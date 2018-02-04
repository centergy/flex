import re
from flask.views import View

from .core import View
from flask import current_app
from .config import config
from . import mixins


__all__ = [
	'GenericView', 'APIView', 'HTMLView', 'CreateAPIView', 'ListAPIView',
	'RetrieveAPIView', 'ListCreateAPIView'
]

NOTHING = object()



class GenericView(View):

	lookup_field = 'pk'
	lookup_kwarg = None

	serializer_class = None
	manager = None

	filter_class = None
	filter_fields = None
	filter_backends = config.filter_backends

	ordering_arg = 'ordering'
	ordering_fields = None
	ordering = None

	@property
	def model_class(self):
		return self.manager.model_class

	def get_model_class(self, query=None):
		assert self.model_class is not None, (
				"'%s' should either include a `manager` attribute that contains"
				" a `model_class` attribute, include a `model_class` attribute"
				"or override the `get_model_class()` method."
				% self.__class__.__name__
			)
		return self.model_class

	def get_query(self):
		"""Return the Query instance to be used for fetching models.

		You may want to override this if you need to provide different
		query objects depending on the incoming request.
		"""
		if self.manager:
			return self.manager
		else:
			return self.get_model_class().mgr

	def query(self, *, apply_filters=False):
		"""Return the Query instance to be used for fetching models. If
		:param:`apply_filters` is given and is True, the query will filtered
		with the current filter backend(s). Otherwise, this method is just the
		same a calling :meth:`get_query()`.

		You are unlikely to want to override this method, given that it's only
		difference from :meth:`get_query()` is that it provides the optional
		:param:`apply_filters` parameter. Override :meth:`get_query()` to
		customize the returned query object.
		"""
		if apply_filters:
			return self.apply_filters(self.get_query())
		return self.get_query()

	def apply_filters(self, query):
		"""Given a query, filter it with whichever filter backend is in use.

		You are unlikely to want to override this method, although you may need
		to call it either from a list view, or from a custom `get_object`
		method if you want to apply the configured filtering backend to the
		default query.
		"""
		backends = self.filter_backends
		if backends:
			for backend in backends:
				query = backend().apply(self.request, query, self)

		return query # self.apply_query_ordering(query)

	def apply_pagination(self, query):
		"""Given a query, return a single page of results using the current
		pagination backend if any.
		"""
		return query

	def get_object(self):
		query = self.query(apply_filters=True)

		lookup_kwarg = self.lookup_kwarg or self.lookup_field

		assert lookup_kwarg in self.kwargs, (
			'Expected view %s to be called with a URL keyword argument '
			'named "%s". Fix your URL rule, or set the `.lookup_field` '
			'attribute on the view correctly.' %
			(self.__class__.__name__, lookup_kwarg)
		)

		model_class = self.get_model_class()

		lookup_field = getattr(model_class, self.lookup_field)
		return query.filter(lookup_field == self.kwargs[lookup_kwarg]).one()

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



class HTMLView(GenericView):

	mimetype = 'text/html'
	template_name = None

	def get_payload_context(self):
		ctx = super(HTMLView, self).get_payload_context() or {}
		ctx['template_name'] = self.template_name
		return ctx


class APIView(GenericView):
	pass



# Concrete view classes that provide method handlers
# by composing the mixin classes with the base view.

class CreateAPIView(mixins.CreateModelMixin, APIView):
	"""	Concrete view for creating a model instance.
	"""
	def post(self, *args, **kwargs):
		return self.create(*args, **kwargs)


class ListAPIView(mixins.ListModelMixin, APIView):
	"""Concrete view for listing a query results.
	"""
	def get(self, *args, **kwargs):
		return self.list(*args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin, APIView):
	"""Concrete view for retrieving a model instance.
	"""
	def get(self, *args, **kwargs):
		 return self.retrieve(*args, **kwargs)



# class DestroyAPIView(mixins.DestroyModelMixin, APIView):
# 	"""Concrete view for deleting a model instance.
# 	"""
# 	def delete(self, *args, **kwargs):
# 		return self.destroy(*args, **kwargs)


# class UpdateAPIView(mixins.UpdateModelMixin, APIView):
# 	"""Concrete view for updating a model instance.
# 	"""
# 	def put(self, request, *args, **kwargs):
# 		return self.update(request, *args, **kwargs)

# 	def patch(self, request, *args, **kwargs):
# 		return self.partial_update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,mixins.CreateModelMixin,APIView):
	"""Concrete view for listing query results or creating a model instance.
	"""
	def get(self, *args, **kwargs):
		return self.list(*args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self.create(*args, **kwargs)


# class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
# 							mixins.UpdateModelMixin,
# 							GenericAPIView):
# 	"""
# 	Concrete view for retrieving, updating a model instance.
# 	"""
# 	def get(self, request, *args, **kwargs):
# 		return self.retrieve(request, *args, **kwargs)

# 	def put(self, request, *args, **kwargs):
# 		return self.update(request, *args, **kwargs)

# 	def patch(self, request, *args, **kwargs):
# 		return self.partial_update(request, *args, **kwargs)


# class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
# 							 mixins.DestroyModelMixin,
# 							 GenericAPIView):
# 	"""
# 	Concrete view for retrieving or deleting a model instance.
# 	"""
# 	def get(self, request, *args, **kwargs):
# 		return self.retrieve(request, *args, **kwargs)

# 	def delete(self, request, *args, **kwargs):
# 		return self.destroy(request, *args, **kwargs)


# class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
# 								   mixins.UpdateModelMixin,
# 								   mixins.DestroyModelMixin,
# 								   GenericAPIView):
# 	"""
# 	Concrete view for retrieving, updating or deleting a model instance.
# 	"""
# 	def get(self, request, *args, **kwargs):
# 		return self.retrieve(request, *args, **kwargs)

# 	def put(self, request, *args, **kwargs):
# 		return self.update(request, *args, **kwargs)

# 	def patch(self, request, *args, **kwargs):
# 		return self.partial_update(request, *args, **kwargs)

# 	def delete(self, request, *args, **kwargs):
# 		return self.destroy(request, *args, **kwargs)
