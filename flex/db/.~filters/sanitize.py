from tea.utils.encoding import force_text
import re


REAL_INT_REGEX = re.compile(r'^[0-9]+$')

def real_int(value, base=10):
	if isinstance(value, int):
		return value
	try:
		if force_text(int(value, base)) == force_text(value):
			return int(value, base)
		else:
			return None
	except Exception:
		return None


def real_abs_int(value, base=10):
	value = real_int(value, base)
	return None if value is None else abs(value)