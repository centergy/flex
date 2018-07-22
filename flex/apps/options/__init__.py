from flex.core import Blueprint

from . import models
from .core import options


bp = Blueprint(
	'flex.apps.options', __name__,
	addons=(options,)
)

