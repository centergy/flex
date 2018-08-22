from ..conf import config as global_config
from ..utils.module_loading import import_string
from ..utils.lazy import SimpleLazyObject

DEFAULTS = dict(
	filter_backends=(),
)

IMPORT_STRINGS = [
	'filter_backends',
]

def _perform_import(value):
	if isinstance(value, str):
		return import_string(value)
	elif isinstance(value, (tuple, list)):
		return [_perform_import(v) for v in value]
	return value


def _load_config():
	rv = global_config.namespace('VIEWS_')
	rv.setdefaults(DEFAULTS)

	for key in IMPORT_STRINGS:
		rv[key] = _perform_import(rv[key])

	return rv


config = SimpleLazyObject(_load_config)






