from flex.utils.decorators import export
from threading import local as thread_local, RLock


class SingletonType(type):

	def __new__(mcls, name, bases, dct):
		dct.setdefault('__singleton_value__', None)
		dct.setdefault('__singleton_lock__', RLock())
		return super(SingletonType, mcls).__new__(mcls, name, bases, dct)


@export
class Singleton(object, metaclass=SingletonType):

	__slots__ = ()

	def __new__(cls, *args, **kwargs):
		with cls.__singleton_lock__:
			if cls.__singleton_value__ is None:
				cls.__singleton_value__ = super(Singleton, cls)\
						.__new__(cls, *args, **kwargs)
			return cls.__singleton_value__



class ThreadLocalSingletonType(type):

	def __new__(mcls, name, bases, dct):
		dct.setdefault('__singleton_value__', thread_local())
		return super(ThreadLocalSingletonType, mcls).__new__(mcls, name, bases, dct)


@export
class ThreadLocalSingleton(object, metaclass=ThreadLocalSingletonType):

	__slots__ = ()

	def __new__(cls, *args, **kwargs):
		if not hasattr(cls.__singleton_value__, 'value'):
			cls.__singleton_value__.value = super(ThreadLocalSingleton, cls)\
						.__new__(cls, *args, **kwargs)
		return cls.__singleton_value__.value

