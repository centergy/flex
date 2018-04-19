from intervals import (
	AbstractInterval, canonicalize, CharacterInterval,
	DateInterval, DateTimeInterval, DecimalInterval,
	FloatInterval, Interval, IntervalFactory,
	IntInterval, NumberInterval, IllegalArgument,
	IntervalException, RangeBoundsException
)

__all__ = [
	'AbstractInterval', 'CharacterInterval', 'canonicalize',
	'DateInterval', 'DateTimeInterval', 'DecimalInterval',
	'FloatInterval', 'Interval', 'IntervalException',
	'IntervalFactory', 'IntInterval', 'IllegalArgument',
	'NumberInterval', 'RangeBoundsException'
]

from flex.datastructures.enum import IntEnum
from flex.utils.decorators import export

class IntervalFlags(IntEnum):

	LEFT_OPEN = 1 << 0	 							# 0001 == 1
	RIGHT_OPEN = 1 << 1								# 0010 == 2
	OPEN = LEFT_OPEN | RIGHT_OPEN					# 0011 == 3

	LEFT_UNBOUND = LEFT_OPEN | 1 << 2				# 0101 == 5
	RIGHT_UNBOUND = RIGHT_OPEN | 1 << 3				# 1010 == 10
	UNBOUND = LEFT_UNBOUND | RIGHT_UNBOUND			# 1111 == 12

	# LEFT_CLOSED = ~LEFT_OPEN & ~LEFT_UNBOUND		#
	# RIGHT_CLOSED = ~RIGHT_OPEN & ~RIGHT_UNBOUND		#
	# CLOSED = ~OPEN & ~UNBOUND						#

	LEFT_CLOSED = 1 << 0						# 0001 = 1
	RIGHT_CLOSED = 1 << 1						# 0010 = 2
	CLOSED = LEFT_CLOSED | RIGHT_CLOSED			# 0011 = 3

	LEFT_BOUND = 1 << 2 					# 0100 == 4
	RIGHT_BOUND = 1 << 3					# 1000 == 8
	BOUND = LEFT_BOUND | RIGHT_BOUND		# 1100 == 12

	FIXED = 1 << 4




# def test_flags():
# 	testTrue(LEFT_UNBOUND, LEFT_OPEN, '&', LEFT_UNBOUND & LEFT_OPEN)
# 	testTrue(RIGHT_UNBOUND, RIGHT_OPEN, '&', RIGHT_UNBOUND & RIGHT_OPEN)
# 	testTrue(UNBOUND, OPEN, '&', UNBOUND & OPEN)

# 	echo(f='hr').br()

# 	testFalse(
# 		(LEFT_CLOSED | LEFT_UNBOUND),
# 		LEFT_UNBOUND, '&',
# 		(LEFT_CLOSED | LEFT_UNBOUND) & LEFT_UNBOUND,
# 		'(%s | %s)' % (LEFT_CLOSED, LEFT_UNBOUND)
# 	)
# 	testFalse(LEFT_CLOSED, LEFT_UNBOUND, '&', LEFT_CLOSED & LEFT_UNBOUND)
# 	testFalse(RIGHT_CLOSED, RIGHT_UNBOUND, '&', RIGHT_CLOSED & RIGHT_UNBOUND)
# 	testFalse(CLOSED, UNBOUND, '&', CLOSED & UNBOUND)

# 	echo(f='hr').br()

# 	testFalse(LEFT_CLOSED, LEFT_UNBOUND, '&', LEFT_CLOSED & LEFT_UNBOUND)



# def testTrue(v1, v2, op, res, exp1=None, exp2=None, reverse=False):

# 	exp1 = exp1 or v1
# 	exp2 = exp2 or v2

# 	# passed = not res if reverse else res
# 	color = '' if (not res if reverse else res) else 'red,bold'
# 	title = ('%s %s %s' % (exp1, op, exp2)).replace('IntervalFlags.', '')
# 	title = re.sub(r'([A-Z][\w]+\.)([A-Z][A-Z0-9_]+)', r'\2', '%s %s %s' % (exp1, op, exp2))

# 	pl, ll, lt = -24, 18, max(len(title)+4, 44)

# 	echo('', title, ' ', f=color).br()\
# 		('-'*lt, f=color).br()\
# 		(pad('%d' % v1, pl))('=')(bits(v1), f='bold').br()\
# 		(pad('%d' % v2, pl))('=')(bits(v2), f='bold').br()\
# 		(' '*(-pl-4), '-'*ll, f=color).br()\
# 		(pad('%d %s %d' % (v1, op, v2), pl))('=')\
# 		(bits(res), f='bold,yellow')('=')\
# 		('%d' % res).br().br()\
# 		# (' ', '='*ll, f=color).br().br()


# def testFalse(v1, v2, op, res, exp1=None, exp2=None):
# 	return testTrue(v1, v2, op, res, exp1, exp2, reverse=True)



# def _flags_2_global():
# 	g = globals()
# 	for f in IntervalFlags:
# 		g[f.name] = f

# _flags_2_global()
# del _flags_2_global


# import re
# from flex.helpers import uzi
# from flex.helpers.uzi import pad
# from flex.utils.echo import echo

# def bits(v, s=8, p=None, glen=4, gsep='-'):
# 	p, v = p or s, int(v)
# 	while abs(v) > 2**p:
# 		p *= 2
# 	regex = re.compile(r'([01%(gsep)s]{%(glen)d,})([01]{%(glen)d})' % dict(gsep=re.escape(gsep), glen=glen))
# 	return regex.sub(r'\1%s\2' % gsep, ('{0:0%sb}' % p).format(v))



# echo('Intervals', f='hr,bold,green').br().br()


# test_flags()


# echo.br()(f='hr,green,bold').br()



