import inspect
import sqlalchemy
from warnings import warn
from sqlservice.query import SQLQuery
from sqlalchemy import util, asc, desc, orm, Column as BaseColumn
from sqlalchemy.orm.base import _is_mapped_class
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.base import _generative
from sqlalchemy.sql.operators import Operators


from . import utils


_query_class_map = {}

class QueryMeta(type):
	pass


class BaseQuery(SQLQuery, metaclass=QueryMeta):
	pass


class Query(BaseQuery):

	# def archived(self, value=False):
	# 	cls = self.model_class
	# 	if cls and cls._opts.soft_deletes:
	# 		return self.filter(cls.is_archived == value)
	# 	return self

	def paginate(self, pagination, page=None):
		"""Return paginated query.

		Args:
			pagination (tuple|int): A ``tuple`` containing ``(per_page, page)``
				or an ``int`` value for ``per_page``.

		Returns:
			Query: New :class:`Query` instance with ``limit`` and ``offset``
				parameters applied.
		"""
		query = self
		per_page = None
		page = 1 if page is None else page

		if isinstance(pagination, (list, tuple)):
			per_page = pagination[0] if len(pagination) > 0 else per_page
			page = pagination[1] if len(pagination) > 1 else page
		else:
			per_page = pagination

		if per_page:
			query = query.limit(per_page)

		if page and page > 1 and per_page:
			query = query.offset((page - 1) * per_page)

		return query

	def search(self, *criterion, **kwargs):
		"""Return search query object.

		Args:
			*criterion (sqlaexpr, optional): SQLA expression to filter against.

		Keyword Args:
			per_page (int, optional): Number of results to return per page.
				Defaults to ``None`` (i.e. no limit).
			page (int, optional): Which page offset of results to return.
				Defaults to ``1``.
			order_by (sqlaexpr, optional): Order by expression. Defaults to
				``None``.

		Returns:
			Query: New :class:`Query` instance with criteria and parameters
				applied.
		"""
		order = kwargs.get('order')
		order_by = kwargs.get('order_by')
		page = kwargs.get('page')
		per_page = kwargs.get('per_page')
		limit = kwargs.get('limit')
		offset = kwargs.get('offset')

		query = self

		for criteria in pyd.flatten(criterion):
			if isinstance(criteria, dict):
				query = query.filter_by(**criteria)
			else:
				query = query.filter(criteria)

		if order_by is not None:
			if isinstance(order_by, (str, BaseColumn)):
				order = asc if order is None else utils.getobj(order, sqlalchemy)
				order_by = [order(order_by)]
			elif not isinstance(order_by, (list, tuple)):
				order_by = [order_by]
			query = query.order_by(*order_by)
		elif order is not None:
			query = query.order(utils.getobj(order, sqlalchemy))

		if per_page or page:
			query = query.paginate(per_page, page)
		elif limit or offset:
			if limit:
				query = query.limit(limit)
			if offset:
				query = query.offset(offset)

		return query


