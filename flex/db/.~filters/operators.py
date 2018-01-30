from . import exc
from .const import NOTHING

class Operators(object):

	all = {
		'=='			: '__eq__',
		'!='			: '__ne__',
		'>'				: '__gt__',
		'>='			: '__ge__',
		'<'				: '__lt__',
		'<='			: '__le__',
		'has'			: '__contains__',
		'like'			: 'like',
		'ilike'			: 'ilike',
		'in'			: 'in_',
		'notin'			: 'notin_',
		'notlike'		: 'notlike',
		'notilike'		: 'notilike',
		'is'			: 'is_',
		'isnot'			: 'isnot',
		'startswith'	: 'startswith',
		'endswith'		: 'endswith',
		'contains'		: 'contains',
		'between'		: 'between',
		'match'			: 'match',

		#Case insensitive operators.
		'i_eq'			: 'i_eq',
		'i_ne'			: 'i_ne',
		'i_lt'			: 'i_lt',
		'i_le'			: 'i_le',
		'i_gt'			: 'i_gt',
		'i_ge'			: 'i_ge',
		'i_has'			: 'i_has',
		'i_in'			: 'i_in_',
		'i_notin'		: 'i_notin_',
		'i_is'			: 'i_is_',
		'i_isnot'		: 'i_isnot',
		'i_match'		: 'i_match',
		'i_like'		: 'i_like',
		'i_notlike'		: 'i_notlike',
		'i_contains'	: 'i_contains',
		'i_startswith'	: 'i_startswith',
		'i_endswith'	: 'i_endswith',
		'i_between'		: 'i_between',
	}


	aliases = {
		'='			: '==',
		'^'			: 'startswith',
		'$'			: 'endswith',
		'%'			: 'like',
		'!%'		: 'notlike',

		#Case insensitive aliases.
		'i(==)'		: 'i_eq',
		'i(=)'		: 'i_eq',
		'i(!=)'		: 'i_ne',
		'i(<)'		: 'i_lt',
		'i(<=)'		: 'i_le',
		'i(>)'		: 'i_gt',
		'i(>=)'		: 'i_ge',
		'i(%)'		: 'i_like',
		'i(!%)'		: 'i_notlike',
		'i(^)'		: 'i_startswith',
		'i($)'		: 'i_endswith',
	}

	def get(self, abstract, default=NOTHING):
		abstract = self.alias(abstract)
		concrete = self.all.get(abstract)
		if concrete is None:
			if default is NOTHING:
				raise KeyError("Invalid filter operator {}.".format(abstract))
			else:
				concrete = default
		return concrete

	def alias(self, abstract):
		return self.aliases.get(str(abstract), str(abstract))

	def has(self, abstract):
		abstract = self.alias(abstract)
		return abstract in self.all

	def make(self, abstract, other=NOTHING, subject=None, args=None, kwargs=None, **metadata):
		concrete = self.get(abstract)
		operator = Operator(str(abstract), concrete, other, args=args, kwargs=kwargs, **metadata)
		return operator.on(subject) if subject else operator

	def __contains__(self, other):
		return self.has(other)

	def __getitem__(self, abstract):
		return self.get(abstract)


class Operator(object):
	"""docstring for Operator"""
	def __init__(self, abstract, concrete, other=NOTHING, args=None, kwargs=None, **metadata):
		self.abstract = abstract
		self.concrete = concrete
		self._subject = None
		args = args or ()
		if other is not NOTHING:
			args = (other,) + args
		self.args = args
		self.kwargs = kwargs or {}
		self.metadata = metadata

	@property
	def subject(self):
		if self._subject:
			return self._subject
		if self.concrete and callable(self.concrete):
			return self.concrete
		raise exc.FilterOperatorError(
				"Operator {} as {} has no valid subject.".format(self.concrete, self.abstract)
			)

	@subject.setter
	def subject(self, value):
		self._subject = value

	def on(self, subject):
		if self.concrete and isinstance(self.concrete, str):
			name = self.concrete
			try:
				self._subject = getattr(subject, self.concrete)
			except (AttributeError, KeyError):
				raise exc.FilterOperatorError("Invalid operator {} on {}. "
					"Method {} does not exist in source.".format(self.abstract, subject, self.concrete))
			except Exception as e:
				raise e
		elif not self.concrete and callable(subject):
			self._subject = subject
		return self

	def __call__(self, *args, **kwargs):
		args = self.args + args
		kargs = self.kwargs.copy()
		kargs.update(kwargs)
		return self.subject(*args, **kargs)

	def __eq__(self, other):
		if isinstance(other, Operator):
			other = other.concrete
		return other == self.concrete

	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		return self.abstract

	def __repr__(self):
		return '<filter operator {} as {} with args: {}, kwargs: {}>'.format(
				self.concrete, self.abstract, self.args, self.kwargs)


operators = Operators()