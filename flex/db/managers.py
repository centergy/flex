from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError
from collections import defaultdict
from threading import Lock

#########################################################
## Is this really thread safe??? Checkout the copy()s. ##
#########################################################



class manager_property(object):

	__slots__ = '_db', '_cache', '_lock', '_instances'

	def __init__(self, db, cache=True):
		self._db = db
		self._cache = cache
		if self._cache:
			self._lock = Lock()
			self._instances = {}

	def __get__(self, obj, cls):
		if self._cache:
			with self._lock:
				if cls not in self._instances:
					self._instances[cls] = self.create_instance(cls)
				return self._instances[cls]
		else:
			return self.create_instance(cls)

	def create_instance(self, cls):
		try:
			orm.class_mapper(cls)
			return cls._opts.manager_class(self._db, cls)
		except UnmappedClassError:
			return None


class archives_manager_property(object):

	def __init__(self, context=None, using=None):
		self.using = using
		self.context = context

	def __get__(self, obj, cls):
		try:
			orm.class_mapper(cls)
			return cls._opts.archives_manager_class(
					self.using or cls._db_client, cls, self.context
				)
		except UnmappedClassError:
			return None



class Manager(object):
	"""Exposes an API for managing persistence operations for ORM-mapped objects.
	to the application layer.
	"""
	model_class = None
	proxy_query_methods = True
	context = dict()


	def __init__(self, db, model_class=None, context=None):
		self.db = db

		if model_class is not None:
			self.model_class = model_class

		if isinstance(self.model_class, str):
			self.model_class = self.db.get_model(self.model_class)

		if self.__class__.context:
			self.context = self.__class__.context.copy()
		else:
			self.context = {}

		if context is not None:
			self.context.update(context)

	def new_query(self, *args, **kwargs):
		cls = self.model_class._opts.query_class
		return cls(args or self.model_class, self.db.session, **kwargs)

	def query(self, *args, **kwargs):
		q = self.apply_context_filters(self.new_query(*args, **kwargs))
		return q

	def apply_context_filters(self, query):
		if not self.context:
			return query
		for k,v in self.context.items():
			query = query.filter(getattr(self.model_class, k) == v)
		return query

	# def apply_archives_filters(self, query, with_archived=False):
	# 	if not with_archived and query.model_class self.model_class._opts.soft_deletes:
	# 		if
	# 		col = getattr(self.model_class, self._opts.soft_deletes_on)
	# 		query = query.filter(col is None)

	def get(self, ident):
		return self.query().filter(*self._pk_criterion(ident)).first()

	def _pk_criterion(self, ident):
		if not isinstance(ident, (tuple, list)):
			ident = (ident,)
		# criterion = []
		for col, val in zip(self.model_class.pk_columns(), ident):
			# criterion.append(col == val)
			yield col == val
		# return criterion

	def apply_context_data(self, model):
		if not self.context:
			return model
		for k,v in self.context.items():
			setattr(model, k, v)
		return model

	def new_entity(self, **data):
		return self.model_class(**data)

	def new(self, **data):
		return self.apply_context_data(self.new_entity(**data))

	def create(self, *args, **kwargs):
		if len(args) > 1:
			raise TypeError('expected at most 1 positional arg, got %d' % len(args))

		data = dict(args[0]) if args else kwargs
		if args and kwargs:
			data.update(kwargs)
		return self.create_model(data)

	def create_model(self, data):
		model = self.new(**data)
		model.save()
		return model

	# def default_update_data(self):
	# 	return {}

	# def get_update_data(self, data):
	# 	default = self.default_update_data().copy()
	# 	if data is not None:
	# 		default.update(data)
	# 	return default

	# def update(self, model, data=None):
	# 	model = self.update_model(model, self.get_update_data(data))
	# 	return model

	# def update_model(self, model, data):
	# 	model.update(data)
	# 	# model.validate()
	# 	self.db.add(model)
	# 	return model

	# def save(self, *models, commit=True, before=None, after=None, identity=None):
	# 	# raise Exception("Re implement this.")
	# 	models = self.db.save(models, before=before, after=after, identity=identity)
	# 	if commit:
	# 		self.db.commit()
	# 	return models

	# def delete(self, *models):
	# 	for model in models:
	# 		self.db.delete(model)
	# 	self.db.commit()
	# 	return True

	def with_context(self, **context):
		repo = self.copy()
		repo.context.update(context)
		return repo

	def copy(self, model_class=None):
		return self.__class__(
			db=self.db, model_class=model_class or self.model_class,
			context=self.context
		)

	def __call__(self, **kwargs):
		return self.with_context(**kwargs)

	def __getattr__(self, key):
		# if self.proxy_query_methods:
		query = self.query()
		attr = getattr(query, key, None)

		if attr is None:
			raise AttributeError('The attribute "{0}" is not an attribute of '
						'{1} nor is it available in of the query object for {2}.'
						.format(key, self.__class__, self.model_class))

		return attr


class ArchivesManager(Manager):

	context = dict(is_archived=False)