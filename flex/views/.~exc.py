from tea.utils import MessageBag
from exc import ValidationError

class ViewError(Exception):
	pass


class ViewSetupError(ViewError):
	pass

class InvalidValueError(ViewError):
	pass

class TemplateError(ViewError):
	pass

class TemplateNameError(TemplateError):
	pass


class SerializationError(MessageBag, Exception):
	pass