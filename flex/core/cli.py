from flask_script import(
	Manager as BaseManager, Shell, Command as BaseCommand,
	Server as BaseServer, Option, Group, prompt, prompt_bool,
	prompt_pass, prompt_choices
)
from datetime import datetime
from flex.carbon import carbon
from . import signals
from flask import current_app


__all__ = (
	'Manager', 'Shell', 'Command', 'Server', 'Option', 'Group',
	'prompt', 'prompt_bool', 'prompt_pass', 'prompt_choices'
)


class Manager(BaseManager):

	def set_app(self, app):
		self.app = app

	def command(self, *fn, name=None, timeit=None, **kwargs):
		def wrap(func, name=name, timeit=timeit, kwargs=kwargs):
			name = name or func.__name__
			command = Command(func, timeit, name)
			self.add_command(name, command, **kwargs)
			return func

		fn = fn[0] if fn else None
		if fn:
			if callable(fn):
				return wrap(fn)
			elif isinstance(fn, str):
				name = fn
				# raise ValueError('Unexpected positional argument. '\
				# 	'Expected the command\'s function or callable.')
		return wrap



class Command(BaseCommand):

	def __init__(self, func=None, timeit=None, name=None):
		super(Command, self).__init__(func)
		self.name = name if name else func.__name__ if func else ''
		self.timeit = True if timeit is None else timeit

	def __call__(self, app=None, *args, **kwargs):
		with app.test_request_context():
			st = datetime.now()
			print('')
			# echo(self.name, 'at', st.strftime('%H:%M:%S'), f='hr,bold')
			print(self.name, 'at', st.strftime('%H:%M:%S'))
			print('-'*140)
			print('')
			rv = self.run(*args, **kwargs)
			print('')
			if self.timeit:
				et = datetime.now()
				print('-'*140)
				# echo('Done in:', et-st, f='hr,bold')
				print('Done in:', et-st)

			# echo(hr='=', f='hr')
			print('='*140)
			return rv



class Server(BaseServer):
	pass
	# def __init__(self, host=None, port=None, **options):
	# 	super(Server, self).__init__(host=host, port=port, **options)


def install_command(addons=''):
	for addon in (x.strip() for x in addons.split(',') if x.strip()):
		print('Installing:', addon)
		obj = current_app._load_addon(addon)
		signals.install.send(addon, addon=obj, app=current_app._get_current_object())
		signals.install.send(obj, app=current_app._get_current_object())
		print('')
