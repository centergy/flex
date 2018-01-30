

# class CreateModelMixin(object):
# 	"""
# 	Create a model instance.
# 	"""
# 	def create(self, request, *args, **kwargs):
# 		serializer = self.get_serializer(data=request.data)
# 		serializer.is_valid(raise_exception=True)
# 		self.perform_create(serializer)
# 		headers = self.get_success_headers(serializer.data)
# 		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# 	def perform_create(self, serializer):
# 		serializer.save()

# 	def get_success_headers(self, data):
# 		try:
# 			return {'Location': data[api_settings.URL_FIELD_NAME]}
# 		except (TypeError, KeyError):
# 			return {}


class ListModelMixin(object):
	"""List a queryset."""

	def list(self):
		query = self.get_query(True)
		page = self.paginate_query(query)
		serializer = self.get_serializer()

		if page is not None:
			return serializer.dump(page, many=True).data
		else:
			return serializer.dump(query, many=True).data

	def get(self):
		self.payload.data = self.list()


class CreateModelMixin(object):
	"""Create a model instance."""

	def create(self):
		data, errors = self.get_serializer()\
				.loads(self.request.get_data(as_text=True))
		if not errors:
			self.model_class.objects.save(data)
			self.payload.status = 201
			self.payload.data['pk'] = data.pk
			return self.dispatch()
		else:
			self.payload.errors = errors
			return self.abort(400)

	def perform_create(self):
		pass

	def post(self, **kwargs):
		self.create()


class RetrieveModelMixin(object):
	"""Retrieve a model instance."""

	def retrieve(self):
		obj = self.get_object()
		if obj is not None:
			return self.get_serializer().dump(obj).data

	def get(self, **kwargs):
		self.payload.data = self.retrieve()
		if self.payload.data is None:
			return self.abort(404)

