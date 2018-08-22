"""
Content negotiation deals with selecting an appropriate renderer given the
incoming request.  Typically this will be based on the request's Accept header.
"""

import flask as fl
from . import exc



class BaseContentNegotiator(object):

	def get_accept_mimetypes(self, request=None):
		"""Given the incoming request, return a list of mimetypes this client
		supports as :class:`~werkzeug.datastructures.MIMEAccept` object.
		"""
		return (request or fl.request).accept_mimetypes

	def select_renderer(self, renderers, mimetype=None, prefer=None, request=None):
		raise NotImplementedError('.select_renderer() must be implemented')


class DefaultContentNegotiator(BaseContentNegotiator):

	def _get_precedence(self, accepts, mimetype):
		ix = accepts.find(mimetype)
		if ix < 0: return 0

		v = accepts[ix][0]
		if '/' not in v: return 0

		vtype, vsubtype = v == '*' and ('*', '*') or v.split('/', 1)
		vtype, vsubtype = vtype.strip(), vsubtype.strip()

		if not vtype or not vsubtype or (vtype == '*' and vsubtype != '*'):
			return 0
		elif vtype == '*':
			return 1
		elif vsubtype == '*':
			return 2
		else:
			return 3

	def _filter_renderers(self, accepts, renderers):
		best_quality = -1
		for r in renderers:
			q = accepts.quality(r.mimetype)
			if q > 0 and q >= best_quality:
				p = self._get_precedence(accepts, r.mimetype)
				best_quality = q
				yield r, q, p

	def best_matches(self, accepts, renderers, limit=None):
		rv = []
		best_quality = -1
		renderers = self._filter_renderers(accepts, renderers)
		for renderer, quality, precedence in sorted(renderers, key=lambda i: i[1:], reverse=True):
			if quality < best_quality or (limit and len(rv) >= limit):
				break
			best_quality = quality
			rv.append((renderer, renderer.mimetype))

		return rv

	def select_renderer(self, renderers, mimetype=None, prefer=None, request=None):
		"""Given the incoming request and a list of renderers, return a
		two-tuple of: (renderer, mimetype).
		"""
		accepts = self.get_accept_mimetypes(request)

		if mimetype:
			if accepts.quality(mimetype) > 0:
				for renderer in renderers:
					if renderer.mimetype == mimetype:
						return renderer, mimetype
			raise exc.NotAcceptable()

		renderers = self.best_matches(accepts, renderers)
		if renderers:
			if prefer:
				for renderer, mimetype in renderers:
					if mimetype == prefer:
						return renderer, mimetype
			return renderers[0]

		raise exc.NotAcceptable()
