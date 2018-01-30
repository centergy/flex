import flask
from urllib.parse import urlparse, urljoin
from flask import request, url_for, current_app

from flex.http import exc


def is_safe_url(target):
	real = urlparse(request.host_url)
	url = urlparse(urljoin(request.host_url, target))
	return url.scheme in ('http', 'https')\
		and (real.netloc == url.netloc\
			or url.netloc in current_app.config.ALLOWED_HOSTS)


def redirect(location, code=302, safe=True, Response=None):
	if safe and not is_safe_url(location):
		raise exc.PermissionDenied()
	return flask.redirect(location, code=code, Response=Response)
