from .session import Session


class MetaProxy(object):

	def __init__(self, model, meta_attr, meta_model, auto_save=False, session=None):
		self.model = model
		self.meta_attr = meta_attr
		self.meta_model = meta_model
		self.auto_save = auto_save
		self.session = session or Session.object_session(model)

	@property
	def entities(self):
		return getattr(self.model, self.meta_attr)

	def get(self, key, default=None):
		meta = self.fetch_entity(key)
		if meta is None:
			return default
		return meta.value

	def set(self, key, value):
		self.add_entity(self.create_entity(key, value))

	def setdefault(self, key, default=None):
		entity = self.entities.setdefault(key, self.create_entity(key, default))
		return entity.value

	def pop(self, key, default=None):
		meta = self.entities.pop(key, None)
		if meta is None:
			return default
		return meta.value

	def delete(self, key):
		self.pop(key)

	def clear(self):
		self.entities.clear()

	def update(self, *iterables):
		pass

	def changed(self, *entities):
		if self.auto_save:
			self.session.add_all(entities)
			self.session.commit()

	def add_entity(self, entity):
		self.entities[entity.key] = entity
		self.session.add(entity)

	def fetch_entity(self, key, default=None):
		return self.entities.get(key, default)

	def create_entity(self, key, value):
		return self.meta_model(key=key, value=value)

	def __getitem__(self, key):
		return self.get(key)

	def __setitem__(self, key, value):
		return self.set(key, value)

	def __delitem__(self, key):
		return self.delete(key)
