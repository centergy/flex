import six
from marshmallow import (
	utils as marsh_utils, Schema as BaseSerializer, SchemaOpts as BaseSerializerOpts,
	pre_load, post_load, post_dump, MarshalResult, ValidationError,
	validates_schema, validates
)
import marshmallow_sqlalchemy as marsh_sa
from flex.http.exc import ValidationError as HttpValidationError
from ..db import db
from . import fields, validate, sanitizers


class SerializerOpts(BaseSerializerOpts):

	def __init__(self, meta, *args, **kwargs):
		super(SerializerOpts, self).__init__(meta, *args, **kwargs)
		self.strict = getattr(meta, 'strict', False)


class Serializer(BaseSerializer):
	OPTIONS_CLASS = SerializerOpts


class ModelSerializerOpts(marsh_sa.ModelSchemaOpts, SerializerOpts):

	def __init__(self, meta, *args, **kwargs):
		SerializerOpts.__init__(self, meta, *args, **kwargs)
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


class ModelSerializer(Serializer, marsh_sa.ModelSchema):
	OPTIONS_CLASS = ModelSerializerOpts

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



