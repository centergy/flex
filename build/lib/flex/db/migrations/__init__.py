import os
import argparse
from flask import current_app
from alembic import __version__ as __alembic_version__
from alembic.config import Config as AlembicConfig
from alembic import command

from flex.utils.local import proxy

@proxy
def migrations():
	return current_app.extensions['migrate']


alembic_version = tuple([int(v) for v in __alembic_version__.split('.')[0:3]])


class _MigrateConfig(object):
	def __init__(self, migrate, db, **kwargs):
		self.migrate = migrate
		self.db = db
		self.directory = migrate.directory
		self.configure_args = kwargs

	# @property
	# def metadata(self):
	# 	"""
	# 	Backwards compatibility, in old releases app.extensions['migrate']
	# 	was set to db, and env.py accessed app.extensions['migrate'].metadata
	# 	"""
	# 	return self.db.metadata


class Config(AlembicConfig):
	def get_template_directory(self):
		package_dir = os.path.abspath(os.path.dirname(__file__))
		return os.path.join(package_dir, 'templates')


class Migrate(object):
	def __init__(self, app=None, db=None, directory='.migrations', **kwargs):
		self.configure_callbacks = []
		self.db = db
		self.directory = directory
		self.alembic_ctx_kwargs = kwargs
		if app is not None and db is not None:
				self.init_app(app, db, directory)

	def init_app(self, app, db=None, directory=None, **kwargs):
		self.db = db or self.db
		self.directory = directory or self.directory
		self.alembic_ctx_kwargs.update(kwargs)
		app.extensions['migrate'] = _MigrateConfig(self, self.db,
			**self.alembic_ctx_kwargs)

	def configure(self, f):
		self.configure_callbacks.append(f)
		return f

	def call_configure_callbacks(self, config):
		for f in self.configure_callbacks:
			config = f(config)
		return config

	def get_config(self, directory, x_arg=None, opts=None):
		if directory is None:
			directory = self.directory
		config = Config(os.path.join(directory, 'alembic.ini'))
		config.set_main_option('script_location', directory)
		if config.cmd_opts is None:
			config.cmd_opts = argparse.Namespace()
		for opt in opts or []:
			setattr(config.cmd_opts, opt, True)
		if not hasattr(config.cmd_opts, 'x'):
			if x_arg is not None:
				setattr(config.cmd_opts, 'x', [])
				if isinstance(x_arg, list) or isinstance(x_arg, tuple):
					for x in x_arg:
						config.cmd_opts.x.append(x)
				else:
					config.cmd_opts.x.append(x_arg)
			else:
				setattr(config.cmd_opts, 'x', None)
		return self.call_configure_callbacks(config)


