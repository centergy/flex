import six
from marshmallow import (
	utils as marsh_utils, Schema as BaseSchema, SchemaOpts as BaseSchemaOpts,
	pre_load, post_load, post_dump, MarshalResult, ValidationError,
	validates_schema, validates
)
import marshmallow_sqlalchemy as marsh_sa
from flex.http.exc import ValidationError as HttpValidationError
from ..db import db
from . import fields, validate


class SchemaOpts(BaseSchemaOpts):

	def __init__(self, meta, *args, **kwargs):
		super(SchemaOpts, self).__init__(meta, *args, **kwargs)
		self.strict = getattr(meta, 'strict', False)


class Schema(BaseSchema):
	OPTIONS_CLASS = SchemaOpts


class ModelSchemaOpts(marsh_sa.ModelSchemaOpts, SchemaOpts):

	def __init__(self, meta, *args, **kwargs):
		SchemaOpts.__init__(self, meta, *args, **kwargs)
		self.model = getattr(meta, 'model', None)
		self.model_converter = getattr(meta, 'model_converter', marsh_sa.ModelConverter)
		self.include_fk = getattr(meta, 'include_fk', False)
		self._sqla_session = getattr(meta, 'sqla_session', lambda: db.session)

	@property
	def sqla_session(self):
		if self._sqla_session:
			if callable(self._sqla_session):
				return self._sqla_session()
			return self._sqla_session


class ModelSchema(Schema, marsh_sa.ModelSchema):
	OPTIONS_CLASS = ModelSchemaOpts

	# def on_bind_field(self, name, field):



def validation_error_handler(e):
	if isinstance(e, ValidationError):
		return HttpValidationError(e.normalized_messages('invalid_input')).get_response()
	raise e


class SerializersAddon(object):

	__slots__ = ()

	# default_config = dict()
	name = 'flex.serializers'

	def init_app(self, app):
		if self.name not in app.extensions:
			app.register_error_handler(ValidationError, validation_error_handler)
			app.extensions[self.name] = True


addon = SerializersAddon()



