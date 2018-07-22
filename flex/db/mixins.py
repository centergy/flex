from ..db import (
	orm, types, event, Model, Table, Column, ForeignKey as FK,
	Query, defer_column_creation
)
from sqlalchemy_mptt.mixins import BaseNestedSets
from sqlalchemy import Index, UniqueConstraint, desc, asc, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import generic_relationship


import datetime

class _BaseNestedSet(object):

	@hybrid_property
	def is_root_node(self):
		return self.parent_id == None

	def path_to_root(self, reverse=False, inclusive=True, session=None):
		"""Generate path from a leaf or intermediate node to the root."""
		table = self.__class__
		query = self._base_query_obj(session=session)
		query = query.filter(table.is_ancestor_of(self, inclusive=inclusive))
		return self._base_order(query, order=(asc if reverse else desc))

	@classmethod
	def rebuild_tree(cls, session, tree_id):
		""" This method rebuid tree.

		Args:
			session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session
			tree_id (int or str): id of tree
		"""
		session.query(cls).filter_by(tree_id=tree_id)\
			.update({cls.left: 0, cls.right: 0, cls.level: 0})
		top = session.query(cls).filter_by(parent_id=None)\
			.filter_by(tree_id=tree_id).one()
		top.left = left = 1
		top.right = right = 2
		top.level = level = 1

		def recursive(children, left, right, level):
			level = level + 1
			for i, node in enumerate(children):
				same_level_right = children[i - 1].right
				left = left + 1

				if i > 0:
					left = left + 1
				if same_level_right:
					left = same_level_right + 1

				right = left + 1
				node.left = left
				node.right = right
				parent = node.parent

				j = 0
				while parent:
					parent.right = right + 1 + j
					parent = parent.parent
					j += 1

				node.level = level
				recursive(node.children.all(), left, right, level)

		recursive(top.children.all(), left, right, level)




@defer_column_creation
class NestedSet(_BaseNestedSet, BaseNestedSets):
	sqlalchemy_mptt_default_level = 0

	@declared_attr
	def __table_args__(cls):
		return (
			Index(None, cls.left),
			Index(None, cls.right),
			Index(None, cls.level),
		)

	@declared_attr
	def tree_id(cls):
		return Column("tree_id", types.Integer)

	@declared_attr
	def parent_id(cls):
		pk = cls.get_pk_column()
		if not pk.name:
			pk.name = cls.get_pk_name()

		return Column("parent_id", FK('%s.%s' % (cls.__tablename__, pk.name), ondelete='CASCADE'))

	@declared_attr
	def parent(self):
		return orm.relation(
			self,
			order_by=lambda: self.left,
			foreign_keys=lambda: [self.parent_id],
			remote_side='{}.{}'.format(self.__name__, self.get_pk_name()),
			backref=orm.backref('children', cascade="all,delete",
							# lazy="dynamic",
							order_by=lambda: (self.tree_id, self.left)),
		)

	@declared_attr
	def left(cls):
		return Column("lft", types.Integer, nullable=False)

	@declared_attr
	def right(cls):
		return Column("rgt", types.Integer, nullable=False)

	@declared_attr
	def level(cls):
		return Column("level", types.Integer, nullable=False, default=0)




@defer_column_creation
class Trashable(object):
	pass



# @event.listens_for(Query, "before_compile", retval=True)
# def filter_archived(query):
# for desc in query.column_descriptions:
# 	if issubclass(desc['type'], Trashable):
# 		entity = desc['entity']
# 		query = query.filter(entity.deleted == False)
# 		return query
