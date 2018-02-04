import os
import sys
from flask.helpers import get_root_path
from flex.utils.decorators import locked_cached_property
from flex.datastructures import ChainMap
from collections import Iterable

class AppType(type):

	def __new__(mcls, name, bases, dct):
		dct['_declared_class_attrs'] = list(dct.keys())

		cls = super(AppType, mcls).__new__(mcls, name, bases, dct)
		if not meta:
			meta = getattr(cls, 'Meta', None)
		cls._add_to_class('_opts', Options(meta))
		cls._prepare()
		return cls

class application(object):

	namespaces = ('.models',)

	def __init__(self, import_name, label=None, root_path=None):
		#: The name of the package or module.  Do not change this once
		#: it was set by the constructor.
		self.import_name = import_name

		if label is not None:
			self.label = label

		models = models or self.model_modules
		if isinstance(models, str):


		#: Where is the app root located?
		self.root_path = root_path or get_root_path(self.import_name)

	@locked_cached_property
	def name(self):
		"""The name of the application. This is usually the import name with the
		difference that it's guessed from the run file if the import name is main.
		"""
		if self.import_name == '__main__':
			fn = getattr(sys.modules['__main__'], '__file__', None)
			if fn is None:
				return '__main__'
			return os.path.splitext(os.path.basename(fn))[0]
		return self.import_name

	@locked_cached_property
	def label(self):
		"""The label used to namespace the application's members such as models.
		"""
		return self.name.rpartition('.')[2]

	@locked_cached_property
	def models(self):
		"""The name of the application.  This is usually the import name
		with the difference that it's guessed from the run file if the
		import name is main.  This name is used as a display name when
		Flask needs the name of the application.  It can be set and overridden
		to change the value.

		.. versionadded:: 0.8
		"""
		if self.import_name == '__main__':
			fn = getattr(sys.modules['__main__'], '__file__', None)
			if fn is None:
				return '__main__'
			return os.path.splitext(os.path.basename(fn))[0]
		return

	def open_resource(self, resource, mode='rb'):
		"""Opens a resource from the application's resource folder.  To see
		how this works, consider the following folder structure::

			/myapplication.py
			/schema.sql
			/static
				/style.css
			/templates
				/layout.html
				/index.html

		If you want to open the :file:`schema.sql` file you would do the
		following::

			with app.open_resource('schema.sql') as f:
				contents = f.read()
				do_something_with(contents)

		:param resource: the name of the resource.  To access resources within
						 subfolders use forward slashes as separator.
		:param mode: resource file opening mode, default is 'rb'.
		"""
		if mode not in ('r', 'rb'):
			raise ValueError('Resources can only be opened for reading')
		return open(os.path.join(self.root_path, resource), mode)


