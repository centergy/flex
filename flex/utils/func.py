
try:
	import flask as fl
	from flask import current_app, url_for, request
	flask_is_installed = True
except ImportError as e:
	flask_is_installed = False

if flask_is_installed:
	import os
	from urllib.parse import quote, quote_plus, unquote, unquote_plus, urlparse, urljoin

	__all__ = ['asset_url', 'url_is', 'is_safe_url', 'redirect']


	def is_safe_url(target):
		real = urlparse(request.host_url)
		url = urlparse(urljoin(request.host_url, target))
		return url.scheme in ('http', 'https') and \
				real.netloc == url.netloc

	def redirect(location, code=302, safe=False, Response=None):
		if safe and not is_safe_url(location):
			raise exc.UnSafeUrlError("Error redirecting to `{0}`.")
		return fl.redirect(location, code=code, Response=Response)


	def asset_url(path, blueprint=None):
		folder = current_app.config.get('ASSETS_FOLDER', '/assets/')
		path = os.path.join(folder.lstrip('/'), path.lstrip('/'))
		endpoint = '{}.static'.format(blueprint) if blueprint else 'static'
		return url_for(endpoint, filename=path)


	def url_is(value, *is_endpoint, **kwargs):
		is_endpoint = True if len(is_endpoint)>0 and is_endpoint[0] is True else False
		if is_endpoint:
			path = url_for(value, **kwargs)
		else:
			path = value

		if not path:
			return False
		return request.path.strip('/').startswith(path.strip('/'))
else:
	__all__ = []
