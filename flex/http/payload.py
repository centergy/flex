# -*- coding: utf-8 -*-
"""
	flex.http.payload
	~~~~~~~~~~~~~~~~

	Payloads are the recommended way to implement a more flexible
	way of building responses especially in class based views.

	:copyright: (c) 2018 by David Kyalo.
"""

import flask as fl
from .status import is_status_ok, status_code_name
from collections import OrderedDict
from flex.datastructures import AttrBag, AttrDict
from werkzeug.datastructures import OrderedMultiDict, Headers as BaseHeaders
from flex.utils.decorators import dict_lookup_property


NOTHING = object()

def _is_status_ok(code):
	return status.is_success(code)


class Headers(BaseHeaders):
	pass



class response_property(dict_lookup_property):

	def lookup(self, obj):
		return obj._response_options


class body_property(dict_lookup_property):

	def lookup(self, obj):
		return obj.body


class context_property(dict_lookup_property):

	def lookup(self, obj):
		return obj.context


class Payload(object):

	__slots__ = ('_body', '_context', '_response_options', 'is_prepared')

	status = response_property('status', doc='The HTTP Status code.')
	mimetype = response_property('mimetype', doc='''The mimetype''')
	headers = response_property('headers', read_only=True, doc='The HTTP Headers')

	data = body_property('data', doc='The payload data.')
	errors = body_property('errors', doc='The payload errors.')

	# deferred = context_property('deferred', default=False,
	# 	doc='Defer rendering when to_response is called.'
	# )
	renderer = context_property('renderer', doc='The renderer to use to render the response body.')
	renderers = context_property('renderers', doc='List of renderers to choose from.')
	template_name = context_property('template_name', doc='The HTML template file name.')

	def __init__(self, status=None, mimetype=None, headers=None, data=None,
			errors=None, context=None):
		self._response_options = dict(
			status=status,
			mimetype=mimetype,
			headers= Headers(headers)
		)

		self._body = AttrBag(OrderedDict())

		self._body.ok = None
		self._body.code = None
		self._body.status = None
		self._body.data = OrderedDict() if data is None else data
		self._body.errors = OrderedMultiDict() if errors is None else errors

		self._context = AttrBag(**(context or {}))
		self.is_prepared = False

	@property
	def body(self):
		return self._body

	@property
	def context(self):
		return self._context

	def prepare(self):
		if not self.is_prepared:
			self.body.code = self.status or 200
			self.body.ok = is_status_ok(self.body.code)
			self.body.status = status_code_name(self.body.code)

			if not self.renderer:
				self.renderer, self.mimetype = fl.current_app\
						.perform_content_negotiation(
							renderers=self.renderers,
							mimetype=self.mimetype
						)
			else:
				self.mimetype = self.mimetype or self.renderer.mimetype

			self.is_prepared = True

	def to_response(self, **options):
		self.renderers = options.pop('renderers', self.renderers)

		self.prepare()

		self._response_options.update(options)
		cls = fl.current_app.response_class
		return cls(self.render(), **self._response_options)

	def render(self):
		return self.renderer(self)

	def __getitem__(self, key):
		try:
			return self._body[key]
		except KeyError as e:
			raise KeyError(key) from e

	def __delitem__(self, key):
		try:
			del self._body[key]
		except KeyError as e:
			raise KeyError(key) from e

	def __setitem__(self, key, value):
		self._body[key] = value

	def __repr__(self):
		return '%s({ body: %r, response: %r, context: %r })' \
		% (self.__class__.__name__, self.body,
			self._response_options, self.context,
		)

	def __str__(self):
		return self.__repr__()

