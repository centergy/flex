from functools import wraps
from marshmallow.fields import *
from marshmallow.fields import Field, missing_, __all__ as __ma_all__
from collections import Iterable
from .. import sanitizers as san


__all__ = list(__ma_all__)


_default_error_messages = dict(
	required='This field is required.',
	null='This field is required.',
	blank='This field may not be blank.'
)


Field.default_error_messages.update(_default_error_messages)
Field.blank_values = [None, '', [], (), {}]
Field.blank_to_none = False


_orig_init = Field.__init__
_orig_deserialize = Field.deserialize
_orig_validate_missing = Field._validate_missing

def _monkey_patch_field_cls():

	@wraps(_orig_init)
	def __init__(self, *args, **kwargs):
		self.required = kwargs.get('required', False)
		self.allow_none = kwargs.get('allow_none', False)
		none_if_blank = kwargs.pop('none_if_blank', False)
		self.blank =  kwargs.pop('blank', none_if_blank)
		self.blank_to_none = none_if_blank or self.blank_to_none

		sanitizers = kwargs.pop('sanitize', ())

		if isinstance(sanitizers, Iterable):
			self.sanitizers = list(sanitizers)
		elif sanitizers:
			self.sanitizers = [sanitizers,]
		else:
			self.sanitizers = []

		_orig_init(self, *args, **kwargs)

	@wraps(_orig_validate_missing)
	def _validate_missing(self, value):
		if value is missing_ and self.required:
			self.fail('required')

		if self._is_blank(value):
			if not self.blank:
				self.fail('null') if value is None else self.fail('blank')
		elif value is None and not self.allow_none:
			self.fail('null')

	@wraps(_orig_deserialize)
	def deserialize(self, value, attr=None, data=None):
		if value is not missing_ and value is not None and not self._is_blank(value):
			value = self._sanitize(value)


		self._validate_missing(value)

		if self.blank and self._is_blank(value) and self.blank_to_none:
			return None

		if value is None and (self.allow_none or self.blank):
			return None

		rv = self._deserialize(value, attr, data)
		self._validate(rv)
		return rv

	def _is_blank(self, value):
		return value in self.blank_values

	def _sanitize(self, value):
		for sanitizer in self.sanitizers:
			value = sanitizer(value)
		return value


	Field.__init__  = __init__
	Field._is_blank  = _is_blank
	Field._sanitize  = _sanitize
	Field.deserialize  = deserialize
	Field._validate_missing = _validate_missing


_monkey_patch_field_cls()
del _monkey_patch_field_cls



_orig_string_init = String.__init__

def _monkey_patch_string_cls():

	@wraps(_orig_string_init)
	def __init__(self, *args, **kwargs):
		strip = kwargs.pop('strip', False)
		_orig_string_init(self, *args, **kwargs)
		if strip not in (False, None):
			if isinstance(strip, str):
				self.sanitizers.insert(0, san.strip(strip))
			else:
				self.sanitizers.insert(0, san.strip())


	String.__init__  = __init__


_monkey_patch_string_cls()
del _monkey_patch_string_cls


