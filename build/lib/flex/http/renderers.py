from flex.utils import json
from collections import OrderedDict
from flask import request, render_template


class BaseRenderer(object):

	mimetype = None
	format = None
	template_name = None

	def get_payload_body(self, payload):
		return dict(payload.body.get_items())

	def render(self, payload):
		raise NotImplementedError('Renderer class requires .render() to be implemented')

	def __call__(self, *args, **kwargs):
		return self.render(*args, **kwargs)



class JSONRenderer(BaseRenderer):

	mimetype = 'application/json'
	format = 'json'

	def get_payload_body(self, payload):
		return OrderedDict(payload.body.get_items())

	def render(self, payload):
		return json.dumps(self.get_payload_body(payload))



class HTMLRenderer(BaseRenderer):

	mimetype = 'text/html'
	format = 'html'
	template_name = None

	def get_template_name(self, payload):
		return payload.template_name or self.template_name

	def render(self, payload):
		template_name = self.get_template_name(payload)
		if not template_name:
			raise RuntimeError(
				'Template name not set for request: %s' % (request.path,)
			)
		return render_template(template_name, **self.get_payload_body(payload))
