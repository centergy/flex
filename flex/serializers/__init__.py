import six
from marshmallow import (
	utils as marsh_utils, Schema as BaseSchema, SchemaOpts,
	pre_load, post_load, post_dump, MarshalResult, ValidationError
)
import marshmallow_sqlalchemy as marsh_sa

from ..db import db
from . import fields



class Schema(BaseSchema):
	__envelope__ = {
		'dump' : None,
		'load' : None,
	}

	def get_envelope_key(self, many, action):
		if not self.__envelope__:
			return None
		envelope = self.__envelope__.get(action, None)
		if not envelope:
			return None
		if isinstance(envelope, str):
			return envelope
		elif isinstance(envelope, (tuple, list)):
			return envelope[1] if many else envelope[0]
		elif isinstance(envelope, dict):
			return envelope.get('many') if many else envelope.get('single')
		raise Exception("Invalid schema envelope configuration in {}".format(self.__class__))

	@pre_load(pass_many=True)
	def _pre_process_loaded(self, data, many):
		return self.sanitize_data(self.unwrap_envelope(data, many), many)

	def sanitize_data(self, data, many):
		return data

	# def sanitize_data(self, data, many):
	# 	if not data:
	# 		return data
	# 	if many:
	# 		return self.sanitize_many(data)
	# 	else:
	# 		return self.sanitize_one(data)

	# def sanitize_many(self, items):
	# 	for item in items:
	# 		self.sanitize_one(item)
	# 	return items

	# def sanitize_one(self, data):
	# 	for k,v in data.items():
	# 		data[k] = self.sanitize_field(v, k, data)
	# 	return data

	# def sanitize_field(self, value, field_name, data):
	# 	field = self.fields.get(field_name)
	# 	if field:
	# 		sanitizers = field.metadata.get('sanitize')
	# 		if sanitizers:
	# 			for sanitizer in yielder(sanitizers):
	# 				sanitizer = _get_sanitizer(sanitizer)
	# 				value = sanitizer(value)
	# 	return value

	def unwrap_envelope(self, data, many):
		key = self.get_envelope_key(many, 'load')
		return data[key] if key else data

	@post_dump(pass_many=True)
	def wrap_with_envelope(self, data, many=False):
		key = self.get_envelope_key(many, 'dump')
		return {key: data} if key else data



class ModelSchemaOpts(marsh_sa.ModelSchemaOpts):

	def __init__(self, meta, *args, **kwargs):
		self.model = getattr(meta, 'model', None)
		self.model_converter = getattr(meta, 'model_converter', marsh_sa.ModelConverter)
		self.include_fk = getattr(meta, 'include_fk', False)
		self._sqla_session = getattr(meta, 'sqla_session', lambda: db.session)
		SchemaOpts.__init__(self, meta, *args, **kwargs)

	@property
	def sqla_session(self):
		if self._sqla_session:
			if callable(self._sqla_session):
				return self._sqla_session()
			return self._sqla_session


class ModelSchema(Schema, marsh_sa.ModelSchema):
	OPTIONS_CLASS = ModelSchemaOpts

	# def on_bind_field(self, name, field):



