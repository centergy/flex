import warnings
from .module_loading import ModuleMovedDeprecationWarning

warnings.warn(
	'Module {o} has been moved to new location flex.datastructures. '\
	'Importing {o} is deprecated, use flex.datastructures instead.'\
	.format(o=__name__),
	ModuleMovedDeprecationWarning, stacklevel=2
)

from flex.datastructures import *