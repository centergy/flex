import blinker as bl
from weakref import WeakValueDictionary
from blinker import receiver_connected, ANY
from flex.datastructures.collections import AttrDict, MutableAttrMap
from flex.utils.decorators import export, locked_cached_property
from collections import Iterable


__all__ = [
	'receiver_connected', 'ANY', 'signals'
]

NOTHING = object()

@export
class Signal(bl.Signal):

	@locked_cached_property
	def receiver_connected(self):
		"""Emitted after each :meth:`connect`.

		The signal sender is the signal instance, and the :meth:`connect`
		arguments are passed through: *receiver*, *sender*, and *weak*.

		.. versionadded:: 1.2

		"""
		return self.__class__(doc="Emitted after a receiver connects.")

	@locked_cached_property
	def receiver_disconnected(self):
		"""Emitted after :meth:`disconnect`.

		The sender is the signal instance, and the :meth:`disconnect` arguments
		are passed through: *receiver* and *sender*.

		Note, this signal is emitted **only** when :meth:`disconnect` is
		called explicitly.

		The disconnect signal can not be emitted by an automatic disconnect
		(due to a weakly referenced receiver or sender going out of scope),
		as the receiver and/or sender instances are no longer available for
		use at the time this signal would be emitted.

		An alternative approach is available by subscribing to
		:attr:`receiver_connected` and setting up a custom weakref cleanup
		callback on weak receivers and senders.

		.. versionadded:: 1.2

		"""
		return self.__class__(doc="Emitted after a receiver disconnects.")

	def send(self, sender=None, *, value=NOTHING, **kwargs):
		"""Emit this signal on behalf of *sender*, passing on \*\*kwargs.

		Returns a list of 2-tuples, pairing receivers with their return
		value. The ordering of receiver notification is undefined.

		:param \*sender: Any object or ``None``.  If omitted, synonymous
		  with ``None``.  Only accepts one positional argument.

		:param \*\*kwargs: Data to be sent to receivers.

		"""
		return [r for r in self.trigger(sender, value=value, **kwargs)]

	def trigger(self, sender=None, *, value=NOTHING, **kwargs):
		"""Emit this signal on behalf of *sender*, passing on \*\*kwargs.

		Returns a list of 2-tuples, pairing receivers with their return value.

		:param \*sender: Any object or ``None``.  If omitted, synonymous
		  with ``None``.  Only accepts one positional argument.

		:param \*\*kwargs: Data to be sent to receivers.

		"""
		kw = dict(value=value, **kwargs) if value is not NOTHING else kwargs

		for receiver in (self.receivers and self.receivers_for(sender) or ()):
			yield receiver, receiver(sender, **kw)

	def pipe(self, sender=None, value=None, **kwargs):
		"""Emit this signal on behalf of *sender* as a pipeline, passing on the
		value and \*\*kwargs. The return value of each receiver is passed to
		the next as value.

		Returns the return value of the last reciver.

		:param sender: Any object or ``None``.  If omitted, synonymous
		  with ``None``.

		:param value: Any object or ``None``. If omitted, synonymous
		  with ``None``.

		:param \*\*kwargs: Data to be sent to receivers.

		"""
		for receiver in (self.receivers and self.receivers_for(sender) or ()):
			value = receiver(sender, value=value, **kwargs)
		return value



@export
class NamedSignal(Signal):
	"""A named generic notification emitter."""

	def __init__(self, name, doc=None):
		super(NamedSignal, self).__init__(doc)
		#: The name of this signal.
		self.name = name

	def __repr__(self):
		base = super(NamedSignal, self).__repr__()
		return "%s; %r>" % (base[:-1], self.name)



@export
class Namespace(AttrDict):
	"""A mapping of signal names to signals."""
	__slots__ = ()

	def signal(self, name, doc=None):
		"""Return the :class:`NamedSignal` *name*, creating it if required.

		Repeated calls to this function will return the same signal object.

		"""
		try:
			return self[name]
		except KeyError:
			return self.setdefault(name, NamedSignal(name, doc))

	def pipeline(self, name, doc=None):
		"""Return the :class:`NamedSignal` *name*, creating it if required.

		Repeated calls to this function will return the same signal object.
		"""
		return self.signal(name, doc)



@export
class WeakNamespace(WeakValueDictionary, MutableAttrMap):
	"""A weak mapping of signal names to signals.

	Automatically cleans up unused Signals when the last reference goes out
	of scope.  This namespace implementation exists for a measure of legacy
	compatibility with Blinker <= 1.2, and may be dropped in the future.
	"""

	__slots__ = ()

	def signal(self, name, doc=None):
		"""Return the :class:`NamedSignal` *name*, creating it if required.

		Repeated calls to this function will return the same signal object.
		"""
		try:
			return self[name]
		except KeyError:
			return self.setdefault(name, NamedSignal(name, doc))

	def pipeline(self, name, doc=None):
		"""Return the :class:`NamedSignal` *name*, creating it if required.

		Repeated calls to this function will return the same signal object.
		"""
		return self.signal(name, doc)



@export
def signal(name, doc=None):
	"""Return the :class:`NamedSignal` *name*, creating it if required.

	Repeated calls to this function will return the same signal object.
	"""
	return signals.signal(name, doc)



def pipeline(name, doc=None):
	"""Return the :class:`NamedSignal` *name*, creating it if required.

	Repeated calls to this function will return the same signal object.
	"""
	return signals.pipeline(name, doc)



@export
def receiver(signal, sender=ANY, weak=True):
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
				sig = signals.signal(sig)
			for sen in sender:
				sig.connect(fn, sen, weak)
		return fn
	return decorator



signals = Namespace()




