from flask import Request as BaseRequest
from flex.utils.decorators import cached_property

class Request(BaseRequest):

	@property
	def input(self):
		"""The submitted data. If the mimetype is :mimetype:`application/json`
		this will contain the parsed JSON data or ``None``. Otherwise, returns
		the :attribute:`form` attribute
		"""
		return self.get_json(cache=True) if self.is_json else self.form

