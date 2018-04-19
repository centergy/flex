from . import monkeypatch as __monkeypatch_
from sqlalchemy import orm, Table, ForeignKey
from .model import declarative_base, BaseModel, append_mixins
from .column import Column, defer_column_creation
from sqlservice import event
from .query import Query
from .managers import Manager, ArchivesManager, manager_property, archives_manager_property
from sqlalchemy.orm.base import _generative as generative_method
from .client import Client
from . import types, utils
import uuid

def uuid_pk_column(as_uuid=True, default=uuid.uuid4, **kw):
	return Column(types.pg.UUID(as_uuid=as_uuid), primary_key=True, default=default, **kw)

def int_pk_column(as_uuid=True, **kw):
	return Column(types.Integer, primary_key=True, **kw)

db = Client()

Model = db.Model


from . import mixins
