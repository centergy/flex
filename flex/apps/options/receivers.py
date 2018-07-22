from flex.signal import signals, receiver
from .signals import install_options
from .core import options


@receiver('auth.register_user_perms')
def _create_user_perms(app, **kwargs):
	return {
		# 'options.write': 'Can Edit Options',
	}



@reciver('auth.register_user_groups')
def _create_user_groups(app, **kwargs):
	return {}



@reciver('install')
def _install_app_options(app):
	install_options.send(app, options=options)
