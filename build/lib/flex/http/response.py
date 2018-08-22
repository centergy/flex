from flask import Response as BaseResponse
from .payload import Payload


class Response(BaseResponse):
	"""docstring for Response"""
	def __init__(self, payload=None, status=None, headers=None,
				mimetype=None, content_type=None, **kwargs):
		kwargs['headers'] = headers
		kwargs['mimetype'] = mimetype
		kwargs['content_type'] = content_type
		super(Response, self).__init__(payload, status, **kwargs)

	# @property
	# def is_sequence(self):
	# 	"""If the iterator is buffered, this property will be `True`.  A
	# 	response object will consider an iterator to be buffered if the
	# 	response attribute is a list or tuple.

	# 	.. versionadded:: 0.6
	# 	"""
	# 	return isinstance(self.response, (tuple, list, Payload))

	# def iter_encoded(self):
	# 	if isinstance(self.response, Payload):
	# 		cont
	# 		if isinstance(item, text_type):
	# 			yield item.encode(charset)
	# 		else:
	# 			yield item

