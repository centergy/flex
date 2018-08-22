
from weakref import WeakValueDictionary
from collections import defaultdict, Iterable

from flex.utils.decorators import export, deprecated

from .signals import ANY, Signal, NamedSignal
from .namespaces import Namespace, WeakNamespace



__all__ = [
	'ANY', 'signals'
]


@deprecated(alt='%s.signals.signal()' % __name__)
def signal(name, doc=None):
	"""Return the :class:`NamedSignal` *name*, creating it if required.

	Repeated calls to this function will return the same signal object.
	"""
	from warnings import warn
	warn(
		'Function %s.%s() is deprecated. Use signals.signal()' % (__name__, signal.__name__),
		DeprecationWarning
	)
	return signals.signal(name, doc)



@deprecated(alt='%s.signals.pipeline()' % __name__)
def pipeline(name, doc=None):
	"""Return the :class:`NamedSignal` *name*, creating it if required.

	Repeated calls to this function will return the same signal object.
	"""
	from warnings import warn
	warn(
		'Function %s.%s() is deprecated. Use signals.pipeline()' % (__name__, pipeline.__name__),
		DeprecationWarning
	)
	return signals.pipeline(name, doc)




@deprecated(alt='%s.signals.receiver()' % __name__)
def receiver(signal, sender=ANY, weak=True, retval=False):
	"""A decorator for connecting receivers to signals. Used by passing in the
	signal (or list of signals) name(s) or instance(s) and a sender
	(or list of senders).
	"""
	from warnings import warn
	warn(
		'Function %s.%s() is deprecated. Use signals.receiver()' % (__name__, receiver.__name__),
		DeprecationWarning
	)

	if not isinstance(signal, (list, tuple)):
		signal = (signal,)

	if not isinstance(sender, (list, tuple)):
		sender = (sender,)

	def decorator(fn):
		for sig in signal:
			if isinstance(sig, str):
				sig = signals.signal(sig)
			for sen in sender:
				sig.connect(fn, sen, weak, retval=retval)
		return fn
	return decorator


# @export
# def pipe(pipeline, sender=ANY, weak=True):
# 	"""A decorator for connecting pipes to pipelines. Used by passing in the
# 	pipeline (or list of pipelines) name(s) or instance(s) and a sender
# 	(or list of senders).
# 	"""
# 	from warnings import warn
# 	warn(
# 		'Function %s.%s() is deprecated. Use signals.receiver()' % (__name__, pipe.__name__),
# 		DeprecationWarning
# 	)
# 	return receiver(pipeline, sender, weak, retval=True)





signals = Namespace()




