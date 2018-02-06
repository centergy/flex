
class ListModelMixin(object):
	"""List a queryset."""

	def get_list(self):
		return self.apply_pagination(self.query(apply_filters=True))

	def list(self, *args, **kwargs):
		data = self.get_list()
		if data is not None:
			self.payload.data = self.get_serializer().dump(data, many=True).data


class CreateModelMixin(object):
	"""Create a model instance."""

	create_success_status = 201

	def get_create_success_data(self, obj):
		if self.lookup_field and hasattr(obj, self.lookup_field):
			key = self.lookup_kwarg or self.lookup_field
			return { key : str(getattr(obj, self.lookup_field)) }

	def on_create_success(self, obj):
		if obj is not None:
			data = self.get_create_success_data(obj)
			if data is not None:
				self.payload.data = data
		if self.create_success_status:
			self.payload.status = self.create_success_status

	def perform_create(self, data):
		obj = self.manager.create(**data)
		self.manager.db.commit()
		return obj

	def create(self, *args, **kwargs):
		data = self.get_serializer(strict=True).load(self.request.input).data
		obj = self.perform_create(data)
		self.on_create_success(obj)



class RetrieveModelMixin(object):
	"""Retrieve a model instance."""

	def retrieve(self, *args, **kwargs):
		obj = self.get_object()
		if obj is not None:
			self.payload.data = self.get_serializer().dump(obj).data
