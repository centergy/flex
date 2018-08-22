import sqlalchemy as sa
from sqlalchemy import asc, desc
from sqlservice.core import mapper_primary_key as get_primary_key


NOTHING = object()

# def pk_eq_criterion(model, ident):
# 	if not isinstance(ident, (tuple, list)):
# 		ident = (ident,)
# 	criterion = []
# 	for col, val in zip(get_primary_key(model), ident):
# 		criterion.append(col == val)
# 	return criterion


# def pk_not_eq_criterion(model, ident):
# 	if not isinstance(ident, (tuple, list)):
# 		ident = (ident,)
# 	criterion = []
# 	for col, val in zip(get_primary_key(model), ident):
# 		criterion.append(col != val)
# 	return criterion


def getobj(obj, source, default=NOTHING):
	if isinstance(obj, str):
		if default is NOTHING:
			return getattr(source, obj)
		else:
			return getattr(source, obj, default)
	return obj


_order_funcs = {
	'asc' : asc,
	'desc': desc
}


def order_dir(order, default=None, silent=False):
	if not order:
		order = default

	if isinstance(order, str) and order.lower() in _order_funcs:
		return _order_funcs[order.lower()]

	if order in (asc, desc):
		return order

	if not silent:
		raise ValueError("Invalid order direction. {}".format(order))

	return None

def is_mapped_class(entity):
	"""Return True if the given object is a mapped class,
	:class:`.Mapper`, or :class:`.AliasedClass`.
	"""
	insp = sa.inspect(entity, False)
	return insp is not None and \
			not insp.is_clause_element and \
			(insp.is_mapper or insp.is_aliased_class)


class _SQLAlchemyState(object):
	"""Remembers configuration for the (db, app) tuple."""
	__slots__ = 'db', 'connectors',

	def __init__(self, db):
		self.db = db
		self.connectors = {}


_appstatekey = 'sqlalchemy_client'

def _set_app_state(db, app):
	app.extensions[_appstatekey] = _SQLAlchemyState(db)

def _get_app_state(app):
	"""Gets the state for the application"""
	assert _appstatekey in app.extensions, \
		'The sqlalchemy client was not registered to the current ' \
		'application.  Please make sure to call init_app() first.'
	return app.extensions[_appstatekey]


def app_get_db_client(app):
	state = _get_app_state(app)
	return state.db


