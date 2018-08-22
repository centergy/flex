from werkzeug.local import LocalProxy, Local
from .decorators import export

__all__ = [
	'Local',
]

@export
class Proxy(LocalProxy):
	__slots__ = ()


@export
class CallableProxy(Proxy):
	__slots__ = ('__doc__',)

	def __init__(self, func, name=None):
		super(CallableProxy, self).__init__(func, name or func.__name__)
		object.__setattr__(self, '__doc__', func.__doc__)

	def __call__(self):
		return self._get_current_object()



@export
def proxy(func=None, name=None, callable=False):
	"""A decorator that converts a function into a `Proxy` or `CallableProxy`.
	"""
	def wrapper(fn):
		return CallableProxy(fn, name) if callable else Proxy(fn, name)
	return wrapper if func is None else  wrapper(func)

