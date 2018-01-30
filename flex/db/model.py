import inspect
from sqlalchemy import asc, desc, MetaData
from sqlservice import ModelBase
from sqlservice.model import ModelMeta as BaseModelMeta
from sqlalchemy.ext.declarative import (
		declared_attr, has_inherited_table,
		declarative_base as _declarative_base
	)
from .utils import order_dir, is_mapped_class
from .column import get_orderable_members, set_late_creation_order, Column
from sqlalchemy.ext.hybrid import hybrid_property
from . import types

from flex.helpers import uzi
from flex.conf import config
from flex.utils.carbon import carbon
from flex.core.exc import ImproperlyConfigured
from flex.utils.module_loading import import_string
from flex.utils.decorators import locked_cached_property

from .managers import Manager, ArchivesManager



MODEL_OPTIONS = set([
	('bind', 'bind_key', True),
	('applabel', 'applabel', True),
	('tablename', '_tablename', True),
	('query_class', '_query_class', True),
	('manager_class', '_manager_class', True),
	('archives_manager_class', '_archives_manager_class', True),
	# ('soft_deletes_on', 'soft_deletes_on', True),
	# ('validator', '_validator', True),
	# ('auto_validate', 'auto_validate', True),
	('timestamps', '_timestamps', True),
	('ordering', '_ordering', True),
	('ordering_inverse', '_ordering_inverse', True),
	('ordering_direction', 'ordering_direction', True),
	('mapper_args', 'mapper_args', False),
	('table_args', 'table_args', True),
])


CONSTRAINT_NAMING_CONVENTION = {
	"ix": 'ix_%(column_0_label)s',
	"uq": "uq_%(table_name)s_%(column_0_name)s",
	"ck": "ck_%(table_name)s_%(constraint_name)s",
	"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
	"pk": "pk_%(table_name)s"
}


class Options(object):
	"""docstring for ModelOptions"""

	def __init__(self, meta):
		self.meta = meta
		self.bind_key = None
		self.applabel = None
		self._tablename = None
		self._query_class = 'flex.db.query.Query'
		self._timestamps = config.get('MODEL_TIMESTAMPS', True)
		self._manager_class = Manager
		self._archives_manager_class = ArchivesManager
		# self.soft_deletes_on = 'archived_at'
		# self._validator = None
		# self.auto_validate = True
		self._ordering = []
		self._ordering_inverse = []
		self.ordering_direction = 'asc'
		self.mapper_args = {}
		self.table_args = None

	# @locked_cached_property
	# def soft_deletes(self):
	# 	return self.soft_deletes_on and hasattr(self.model_class, self.soft_deletes_on)

	@locked_cached_property
	def tablename(self):
		if not has_inherited_table(self.model_class):
			if not self._tablename:
				if self.applabel:
					return '%s_%s' % (self.applabel, uzi.snake(self.model_class.__name__))
				else:
					return uzi.snake(self.model_class.__name__)
			else:
				return self._tablename

	@locked_cached_property
	def query_class(self):
		cls = self._query_class
		if isinstance(cls, str):
			cls = import_string(cls, self.model_class.__module__)
		if inspect.isfunction(cls):
			cls = cls()
		return cls

	@locked_cached_property
	def manager_class(self):
		cls = self._manager_class
		if isinstance(cls, str):
			cls = import_string(cls, self.model_class.__module__)
		if inspect.isfunction(cls):
			cls = cls()
		return cls

	@locked_cached_property
	def archives_manager_class(self):
		cls = self._archives_manager_class
		if isinstance(cls, str):
			cls = import_string(cls, self.model_class.__module__)
		if inspect.isfunction(cls):
			cls = cls()
		if not issubclass(cls, self.manager_class):
			cls = type(cls.__name__, (self.manager_class, cls,), {})
		return cls

	# @locked_cached_property
	# def validator(self):
	# 	cls = self._validator
	# 	if isinstance(cls, str):
	# 		cls = import_string(cls, self.model_class.__module__)
	# 	if inspect.isfunction(cls):
	# 		cls = cls()
	# 	return cls

	@locked_cached_property
	def ordering(self):
		rv = self._parse_ordering(self._ordering, self.ordering_direction)
		if not rv and self.pk_columns:
			self.ordering_direction = desc
			rv = self._parse_ordering(self.pk_columns, desc)
		return rv

	@locked_cached_property
	def ordering_inverse(self):
		ordering = self._ordering_inverse or [f for o, f in self.ordering]
		direction = desc if self.ordering_direction is asc else asc
		return self._parse_ordering(ordering, direction)

	@locked_cached_property
	def pk_columns(self):
		return self.model_class.pk_columns()

	@locked_cached_property
	def polymorphic_identity(self):
		if self.mapper_args:
			return self.mapper_args.get('polymorphic_identity')
		return None

	def contribute_to_class(self, cls, name):
		self.model_class = cls
		base_opts = getattr(cls, name, None)

		for opt in MODEL_OPTIONS:
			key, attr, inherit = opt if isinstance(opt, (tuple, list)) else (opt, opt, False)
			if self.meta and hasattr(self.meta, key):
				setattr(self, attr, getattr(self.meta, key))
			elif inherit and base_opts:
				setattr(self, attr, getattr(base_opts, attr))

		del self.meta
		setattr(cls, name, self)

		self._set_model_timestamp_columns()

		return

	def _prepare(self):
		self.ordering_direction = order_dir(self.ordering_direction)
		#Touch cached properties ordering and ordering_inverse
		self.ordering
		self.ordering_inverse

	def _set_model_timestamp_columns(self):
		if self._timestamps:
			cols = self._timestamps
			if cols is True:
				cols = ('created_at', 'modified_at')

			if not isinstance(cols, (list, tuple)) or len(cols) != 2:
				raise ImproperlyConfigured(
					'Model Meta.timestamps. Allowed values: True, False or a '\
					'list/tuple of \'created-at-column-name\'/True/False and '\
					'\'modified-at-column-name\'/True/False. %r given.' % (cols,)
				)

			created_at, modified_at = cols
			if created_at is True:
				created_at = 'created_at'

			if modified_at is True:
				modified_at = 'modified_at'

			if created_at and not hasattr(self.model_class, created_at):
				col = Column(
						created_at, types.Carbon(),
						default=carbon.now, nullable=False
					)
				set_late_creation_order(col)
				setattr(self.model_class, created_at, col)

			if modified_at and not hasattr(self.model_class, modified_at):
				col = Column(
						modified_at, types.Carbon(), nullable=False,
						default=carbon.now, onupdate=carbon.now
					)
				set_late_creation_order(col)
				setattr(self.model_class, modified_at, col)

	def _parse_ordering(self, ordering, direction='asc', idirection=None):
		rv = []
		direction = order_dir(direction)
		if idirection is None:
			idirection = desc if direction is asc else asc

		for order_field in ordering:
			if not isinstance(order_field, (tuple, list)):
				if isinstance(order_field, str):
					order_field = order_field.strip()
					order = idirection if order_field[0] == '-' else direction
					field = order_field[1:] if order_field[0] == '-' else order_field
				else:
					field = order_field
					order = direction
			else:
				order, field = (direction, order_field[0])\
							if len(order_field) == 1 else order_field

			if isinstance(field, str):
				field = getattr(self.model_class, field)

			rv.append((order_dir(order), field))

		return rv


class _AppendMixin(object):
	pass


def append_mixins(*mixins):
	"""Append the given mixin classes to the given model."""
	class mixin(_AppendMixin, *mixins):
		pass
	return mixin



class ModelMeta(BaseModelMeta):
	def __new__(mcls, name, bases, dct):
		dct['_declared_class_attrs'] = list(dct.keys())
		meta = dct.get('Meta')
		if meta:
			if hasattr(meta, 'table_args'):
				dct['__table_args__'] = meta.table_args
			if hasattr(meta, 'mapper_args'):
				dct['__mapper_args__'] = meta.mapper_args

		cls = super(ModelMeta, mcls).__new__(mcls, name, bases, dct)
		if not meta:
			meta = getattr(cls, 'Meta', None)
		cls._add_to_class('_opts', Options(meta))
		cls._prepare()
		return cls

	def __init__(cls, name, bases, dct):
		del cls._declared_class_attrs
		dct.pop('_declared_class_attrs', None)

		super(ModelMeta, cls).__init__(name, bases, dct)

		if cls._opts.bind_key is not None and hasattr(cls, '__table__'):
			cls.__table__.info['bind_key'] = cls._opts.bind_key

		cls._fix_creation_order(bases)

	def _declared_in_class(cls, attr):
		return attr in cls._declared_class_attrs

	def _prepare(cls):
		if not is_mapped_class(cls):
			return
		cls._opts._prepare()

	def _add_to_class(cls, name, value):
		if not inspect.isclass(value) and hasattr(value, 'contribute_to_class'):
			value.contribute_to_class(cls, name)
		else:
			setattr(cls, name, value)

	def _fix_creation_order(cls, bases):
		for base in bases:
			if issubclass(base, _AppendMixin):
				for mixin in reversed(base.__bases__):
					if mixin is not _AppendMixin:
						cls._fix_inherited_attrs_creation_order(mixin)

	def _fix_inherited_attrs_creation_order(cls, mixin):
		for name, value in get_orderable_members(mixin):
			set_late_creation_order(getattr(cls, name))


class BaseModel(ModelBase):
	metaclass = ModelMeta

	@hybrid_property
	def pk(self):
		cols = self.pk_columns()
		return cols[0] if len(cols) == 1 else None

	@declared_attr
	def __tablename__(cls):
		if has_inherited_table(cls):
			return None
		return cls._opts.tablename

	@classmethod
	def column(cls, name):
		return cls.columns()[name]

	def _exists(self):
		ident = self.class_mapper().identity_key_from_instance(self)
		for pk in ident[1]:
			if pk is None:
				return False
		return True

	# def validate(self):
	# 	cls = self._opts.validator
	# 	if not cls:
	# 		return True

	# 	validator = cls(self)
	# 	if self._exists():
	# 		return validator.validate('update')
	# 	else:
	# 		return validator.validate('create')


def declarative_base(cls=None, metadata=None, mapper=None,
					name=None, class_registry=None, metaclass=None):
	"""Function and decorator that converts a normal class into a SQLAlchemy
	declarative base class.

	Args:
		:param cls:
			A type to use as the base for the generated declarative ase class.
			May be a class or tuple of classes. Defaults to :class:`.BaseModel`.

		:param metadata:
			An optional MetaData instance. All Table objects implicitly
			declared by subclasses of the base will share this MetaData. A
			MetaData instance will be created if none is provided. If not
			passed in, `cls.metadata` will be used if set. Default: ``None``.

		:param mapper:
			An optional callable, defaults to :func:`~sqlalchemy.orm.mapper`.
			Will be used to map subclasses to their Tables.

		:param name:
			Defaults to ``cls.__name__``.  The display name for the generated
			class. Customizing this is not required, but can improve clarity in
			tracebacks and debugging.

		:param class_registry: optional dictionary that will serve as the
			registry of class names-> mapped classes when string names
			are used to identify classes inside of :func:`.relationship`
			and others.  Allows two or more declarative base classes
			to share the same registry of class names for simplified
			inter-base relationships.

		:param metaclass:
			Defaults to :class:`.ModelMeta`.  A metaclass or __metaclass__
			compatible callable to use as the meta type of the generated
			declarative base class.


	Returns:
		class: Declarative base class
	"""

	cls = cls or BaseModel

	if metadata is None:
		metadata = getattr(cls, 'metadata', MetaData(naming_convention=CONSTRAINT_NAMING_CONVENTION))

	if metaclass is None:
		metaclass = getattr(cls, 'metaclass', None)

	options = {
			'cls': cls,
			'name': name or cls.__name__
		}

	if hasattr(cls, '__init__'):
		options['constructor'] = cls.__init__

	if metadata:
		options['metadata'] = metadata

	if metaclass:
		options['metaclass'] = metaclass

	if mapper:
		options['mapper'] = mapper

	if class_registry:
		options['class_registry'] = class_registry

	Base = _declarative_base(**options)

	if metaclass:
		Base.metaclass = metaclass

	return Base