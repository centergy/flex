import builtins



class VoidType(object):
	__slots__ = ()

	def __new__(cls):
		if not hasattr(builtins, 'Void'):
			builtins.Void = super(VoidType, cls).__new__(cls)
		return builtins.Void

	def __len__(self):
		return 0

	def __bool__(self):
		return False
	__nonzero__ = __bool__

	# def __getnewargs__(self):
	# 	return ()

	def __str__(self):
		return 'Void'

	def __repr__(self):
		return 'Void'


__VOID = VoidType()
