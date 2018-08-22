from threading import RLock
from weakref import WeakValueDictionary

from blinker.base import ANY

from flex.utils.decorators import export

from .signals import NamedSignal


class BaseSignalNamespace(object):
	__slots__ = ()

	singal_class = NamedSignal

	def __init__(self, name=None):
		super(BaseSignalNamespace, self).__init__()
		# self.ns_lock = RLock()
		self.name = name

	def signal(self, name, doc=None):
		"""Return the :class:`NamedSignal` *name*, creating it if required.

		Repeated calls to this function will return the same signal object.
		"""
		try:
			rv = self[name]
		except KeyError:
			rv = self[name] = self.singal_class(name, doc)
		return rv

	def pipeline(self, name, doc=None, **config):
		"""Return the :class:`NamedSignal` *name*, creating it if required.
		Repeated calls to this function will return the same signal object.
		"""
		return self.signal(name, doc, **config)

	def receiver(self, signal, sender=ANY, weak=True, retval=False):
		"""A decorator for connecting receivers to signals. Used by passing in the
		signal (or list of signals) name(s) or instance(s) and a sender
		(or list of senders).
		"""
		if not isinstance(signal, (list, tuple)):
			signal = (signal,)

		if not isinstance(sender, (list, tuple)):
			sender = (sender,)

		def decorator(fn):
			for sig in signal:
				if isinstance(sig, str):
					sig = self.signal(sig)
				for sen in sender:
					sig.connect(fn, sen, weak, retval=retval)
			return fn
		return decorator

	def pipe(self, pipeline, sender=ANY, weak=True):
		"""A decorator for connecting pipes to pipelines. Used by passing in the
		pipeline (or list of pipelines) name(s) or instance(s) and a sender
		(or list of senders).
		"""
		return self.receiver(pipeline, sender, weak, retval=True)





@export
class Namespace(BaseSignalNamespace, dict):
	"""A mapping of signal names to signals."""
	__slots__ = ('name',)



@export
class WeakNamespace(BaseSignalNamespace, WeakValueDictionary):
	"""A weak mapping of signal names to signals.

	Automatically cleans up unused Signals when the last reference goes out
	of scope.  This namespace implementation exists for a measure of legacy
	compatibility with Blinker <= 1.2, and may be dropped in the future.
	"""
	__slots__ = ('name',)

