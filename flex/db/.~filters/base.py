from . import exc
from ..query import Query as BaseQuery
from .const import NOTHING

class Filter(object):
	"""docstring for Filter"""
	def __init__(self, **kwargs):
		self._options = kwargs

	def apply(self, *args, **kwargs):
		raise NotImplementedError("Method apply() in filter: %s." % self.__class__.__name__)

	def __call__(self, *args, **kwargs):
		return self.apply(*args, **kwargs)


class QueryFilter(Filter):

	@classmethod
	def get_query_model_attr(cls, query, name, default=NOTHING):
		model_class = query.model_class
		if model_class:
			return cls.get_model_attr(model_class, name, default)
		elif default is not NOTHING:
			return default

		raise exc.FilterRequestError("Filter %s requires a single mapped"
				" class query object." % cls.__name__)

	@classmethod
	def get_model_attr(cls, model_class, name, default=NOTHING):
		attr = getattr(model_class, name, default)
		if attr is NOTHING:
			raise exc.FilterRequestError(
				"Filter {} expects attribute {} in model {}."
				.format(cls.__name__, name, model_class.__name__))
		return attr

	@classmethod
	def get_field(cls, source, name, default=NOTHING):
		if isinstance(source, BaseQuery):
			return cls.get_query_model_attr(source, name, default)
		else:
			return cls.get_model_attr(source, name, default)

	def apply(self, query, params):
		raise NotImplementedError("Method apply() in filter: %s." % self.__class__.__name__)
