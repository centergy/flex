from .const import NOTHING
from . import sanitize, base

class BasePagination(base.QueryFilter):
	"""docstring for Pagination"""
	page_size = None
	max_page_size = None
	page_param = None
	page_size_param = None

	def __init__(self, *args, **kwargs):
		self.page_size = kwargs.pop('page_size', None) or self.page_size
		self.max_page_size = kwargs.pop('max_page_size', None) or self.max_page_size
		self.page_param = kwargs.pop('page_param', None) or self.page_param
		self.page_size_param = kwargs.pop('page_size_param', None) or self.page_size_param
		super(BasePagination, self).__init__(*args, **kwargs)

	def apply(self, query, params):
		limit, offset = self.parse_params(params)

		if limit:
			query = query.limit(limit)
		if offset:
			query = query.offset(offset)
		return query


class PageNumberPagination(BasePagination):
	"""docstring for PageNumberPagination"""

	def parse_params(self, params):
		if self.page_param:
			page = params.get(self.page_param, 1)
		else:
			page = 1

		if self.page_size_param:
			page_size = params.get(self.page_size_param, self.page_size)
		else:
			page_size = self.page_size

		page = sanitize.real_abs_int(page)
		page_size = sanitize.real_abs_int(page_size)

		if self.max_page_size and not(page_size and page_size <= self.max_page_size):
			page_size = int(self.max_page_size)

		return page_size, ((page-1)*page_size if page_size and page > 1 else 0)


class OffsetLimitPagination(BasePagination):

	def parse_params(self, params):
		offset = params.get(self.page_param, 0) if self.page_param else 0
		limit = params.get(self.page_size_param, self.page_size) \
				if self.page_size_param else self.page_size

		limit = sanitize.real_abs_int(limit)
		offset = sanitize.real_abs_int(offset)

		if self.max_page_size and (not limit or limit > self.max_page_size):
			limit = int(self.max_page_size)

		return (limit, offset or 0)
