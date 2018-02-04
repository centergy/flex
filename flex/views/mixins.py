
class ListModelMixin(object):
	"""List a queryset."""

	def get_list(self):
		return self.apply_pagination(self.query(apply_filters=True))

	def list(self, *args, **kwargs):
		data = self.get_list()
		self.payload.data = self.get_serializer().dump(data, many=True).data


class CreateModelMixin(object):
	"""Create a model instance."""

	def get_success_status(self):
		return 201

	def get_payload_data(self, obj):
		if self.lookup_field and hasattr(obj, self.lookup_field):
			key = self.lookup_kwarg or self.lookup_field
			return { key : getattr(obj, self.lookup_field) }

	def perform_create(self, data):
		obj = self.manager.create(data)

	def create(self, *args, **kwargs):
		data, errors = self.get_serializer().loads(self.request.input)
		if errors:
			return self.abort(400, errors)

		obj = self.perform_create(data)
		if obj is not None:
			data = self.get_payload_data(obj)
			if data is not None:
				self.payload.data = data

		self.payload.status = self.get_success_status()



class RetrieveModelMixin(object):
	"""Retrieve a model instance."""

	def retrieve(self, *args, **kwargs):
		obj = self.get_object()
		if obj is None:
			self.abort(404)
		self.payload.data = self.get_serializer().dump(obj).data
