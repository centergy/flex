import string
import random
from flex.db import (
	orm, types, event, Model, Table, Column, ForeignKey as FK, big_int_pk_column, mixins
)
import sqlalchemy as sa
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from flex.utils.decorators import export




@export
class Option(Model):

	class Meta:
		tablename = 'flex_options_option'
		autocommit = True
		manager_class = '..managers.OptionsDbManager'

	key = Column(types.String(255), primary_key=True, nullable=False)
	value = Column(types.PickleType)
	# cached = Column(types.Boolean, nullable=False, default=True, server_default=sa.text('TRUE'))

