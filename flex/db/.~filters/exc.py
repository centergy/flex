

class FilterError(Exception):
	pass

class FilterFieldError(FilterError):
	pass

class FilterParamError(FilterError):
	pass

class FilterRequestError(FilterError):
	pass

class FilterOperatorError(FilterError):
	"""docstring for Filter peratorError"""
	pass