from collections import defaultdict

import blinker as bl
from blinker.base import ANY, ANY_ID, hashable_identity

from flex.utils.decorators import export, locked_cached_property


__all__ = [
	'ANY',
]

NOTHING = object()


@export
class Signal(bl.Signal):
	_config_keys = dict(
		get_sender_id='get_sender_id'
	)

	def __init__(self, doc=None):
		super(Signal, self).__init__(doc)
		self._pipes = defaultdict(set)

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

	@classmethod
	def hashable_id(cls, obj):
		return hashable_identity(obj)

	def get_sender_id(self, sender):
		return sender

	def configure(self, **kw):
		for k in kw:
			if k in self._config_keys:
				setattr(self, self._config_keys[k], kw[k])
		return self

	def connect(self, receiver, sender=ANY, weak=True, retval=False):
		"""Connect *receiver* to signal events sent by *sender*.

		:param receiver: A callable.  Will be invoked by :meth:`send` with
		  `sender=` as a single positional argument and any \*\*kwargs that
		  were provided to a call to :meth:`send`.

		:param sender: Any object or :obj:`ANY`, defaults to ``ANY``.
		  Restricts notifications delivered to *receiver* to only those
		  :meth:`send` emissions sent by *sender*.  If ``ANY``, the receiver
		  will always be notified.  A *receiver* may be connected to
		  multiple *sender* values on the same Signal through multiple calls
		  to :meth:`connect`.

		:param weak: If true, the Signal will hold a weakref to *receiver*
		  and automatically disconnect when *receiver* goes out of scope or
		  is garbage collected.  Defaults to True.
		"""
		rv = super(Signal, self).connect(receiver, sender, weak)
		if retval and rv:
			sid = ANY_ID if sender is ANY else self.hashable_id(self.get_sender_id(sender))
			self._pipes[self.hashable_id(receiver)].add(sid)
		return rv

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
		sender_id = sender if sender is None else self.get_sender_id(sender)
		for receiver in (self.receivers and self.receivers_for(sender_id) or ()):
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
		sender_id = sender if sender is None else self.get_sender_id(sender)
		for receiver in (self.receivers and self.receivers_for(sender_id) or ()):
			if self.is_pipe(receiver, sender_id=sender_id):
				value = receiver(sender, value=value, **kwargs)
			else:
				receiver(sender, value=value, **kwargs)
		return value

	def is_pipe(self, receiver, sender=None, sender_id=None):
		rid = self.hashable_id(receiver)
		if rid in self._pipes:
			if sender_id is None:
				sender_id = self.get_sender_id(sender) if sender is not None else None
			return bool(self._pipes[rid]) if sender_id is None else self.hashable_id(sender_id) in self._pipes[rid]

	def _disconnect(self, receiver_id, sender_id):
		super(Signal, self)._disconnect(receiver_id, sender_id)
		if receiver_id in self._pipes:
			if sender_id == ANY_ID:
				self._pipes.pop(receiver_id)
			else:
				self._pipes[receiver_id].remove(sender_id)



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

