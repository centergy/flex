
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



class ListModelMixin(object):
	"""List a queryset."""

	def get_list(self):
		return self.apply_pagination(self.query(apply_filters=True))

	def list(self, *args, **kwargs):
		data = self.get_list()
		if data is not None:
			self.payload.data = self.get_serializer().dump(data, many=True).data


class RetrieveModelMixin(object):
	"""Retrieve a model instance."""

	def retrieve(self, *args, **kwargs):
		obj = self.get_object()
		if obj is not None:
			self.payload.data = self.get_serializer().dump(obj).data


class UpdateModelMixin(object):
	"""
	Update a model instance.
	"""
	def on_update_success(self, obj):
		if obj is not None:
			data = self.get_update_success_data(obj)
			if data is not None:
				self.payload.data = data

	def get_update_success_data(self, obj):
		return self.get_serializer().dump(obj) if obj is not None else None

	def update(self, *args, **kw):
		instance = self.get_object()
		if instance is None:
			return self.abort(404)

		data = self.get_serializer(strict=True)\
				.load(self.request.input, partial=kw.pop('partial', False))\
				.data
		instance = self.perform_update(instance, data)
		self.on_update_success(instance)

	def perform_update(self, instance, data):
		if hasattr(instance, 'update') and callable(instance.update):
			instance.update(**data)
		else:
			for k,v in data.items():
				setattr(instance, k, v)
		instance.save()
		self.manager.db.commit()
		return instance

	def partial_update(self, *args, **kwargs):
		kwargs['partial'] = True
		return self.update(*args, **kwargs)



class DestroyModelMixin(object):
	"""
	Destroy a model instance.
	"""
	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		self.perform_destroy(instance)
		return Response(status=status.HTTP_204_NO_CONTENT)

	def perform_destroy(self, instance):
		instance.delete()
