from .decorators import class_property
from functools import partial
import curses
import re


class StaticEcho:

	BLUE = '\033[94m'
	GREEN = '\033[92m'
	RED = '\033[31m'
	YELLOW = '\033[93m'
	ORANGE = '\033[91m'
	MAGENTA = '\033[95m'

	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

	HEADER = MAGENTA

	WARNING = YELLOW
	FAIL = ORANGE

	COLS = None

	@classmethod
	def _set_cols(self, stdscr):
		self.COLS = curses.COLS

	@class_property
	def cols(self):
		curses.wrapper(self._set_cols)
		return self.COLS

	@classmethod
	def hr(self, *args, hr='-', lhr=True, rhr=True, **kwargs):
		txt = self.format(*args, **kwargs)
		txt = ' %s ' % re.sub(r'(?:\\033\[\d\d?m)+', txt, '')
		lt = len(txt)
		cols = self.cols
		ll = cols - lt

		lhr = hr if lhr is True else lhr
		rhr = hr if rhr is True else rhr

		if ll >= cols/10:
			if not lhr:
				left, right = '', rhr*int(ll)
			elif not rhr:
				left, right = lhr*int(ll), ''
			else:
				left = right = hr*int(ll/2)
		else:
			sp = ' '*int(ll/2) if ll >= 4 else ''
			left = right = hr*cols
			left = '%s\n%s' % (left, sp)
			right = '%s\n%s' % (sp, right)

		rv = left+txt+right
		sp = cols - len(rv)
		if sp > 0:
			rv += hr*sp
		return rv

	@classmethod
	def format(self, *args, _=' ',  fargs=None, **fkwargs):
		text = _.join((str(a) for a in args))
		return text.format(*fargs, **fkwargs) if fargs or fkwargs else text

	@classmethod
	def header(self, *args, **kwargs):
		return self.HEADER + self.format(*args, **kwargs) + self.ENDC

	@class_property
	def magenta(self):
		return self.header

	@classmethod
	def red(self, *args, **kwargs):
		return self.RED + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def blue(self, *args, **kwargs):
		return self.BLUE + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def green(self, *args, **kwargs):
		return self.GREEN + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def warn(self, *args, **kwargs):
		return self.WARNING + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def fail(self, *args, **kwargs):
		return self.FAIL + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def bold(self, *args, **kwargs):
		return self.BOLD + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def uline(self, *args, **kwargs):
		return self.UNDERLINE + self.format(*args, **kwargs) + self.ENDC

	@classmethod
	def echo(self, *args, f='', end='\n', **kwargs):
		b4 = f
		if f and re.search(r'^(?:.*\,)?\s*(hr)\s*(?:\,.*)?$', f):
			txt = self.hr(*args, **kwargs)
			f = re.sub(r'^(.*\,)?\s*(hr)\s*(\,.*)?$', r'\1\3', f)
		else:
			txt = self.format(*args, **kwargs)

		for style in f.split(','):
			style = style.strip()
			if style.isdigit():
				txt = '\033[' + style + 'm' + txt + self.ENDC
			elif style:
				style = getattr(self, style)
				txt = style(txt)
		print(txt)

	def __call__(self, *args, **kwargs):
		return self.echo(*args, **kwargs)


class Echo(StaticEcho):

	def __init__(self, autobr=True, before=None, after=None):
		self.autobr = autobr
		self.before = before
		self.after = after
		self.printfunc = partial(print, end='')

	# def _set_cols(self, stdscr):
	# 	self.COLS = curses.COLS

	# def cols(self):
	# 	curses.wrapper(self._set_cols)
	# 	return self.COLS

	def hr(self, *args, hr='-', **kwargs):
		txt = self.format(*args, **kwargs)
		txt = txt and ' %s ' % txt
		lt = len(txt.encode())
		cols = self.cols
		ll = cols - lt
		if ll >= cols/10:
			left = right = (hr*int(ll/2))
		else:
			sp = ' '*int(ll/2) if ll >= 4 else ''
			left = right = hr*cols
			left = '%s\n%s' % (left, sp)
			right = '%s\n%s' % (sp, right)

		rv = '%s%s%s' % (left, txt, right)
		sp = cols - len(rv)
		if sp > 0:
			rv += hr*sp
		return rv

	def format(self, *args, _=' ',  fargs=None, **fkwargs):
		text = _.join((str(a) for a in args))
		return text.format(*fargs, **fkwargs) if fargs or fkwargs else text

	def header(self, *args, **kwargs):
		return self.HEADER + self.format(*args, **kwargs) #+ self.ENDC

	@property
	def magenta(self):
		return self.header

	def red(self, *args, **kwargs):
		return self.RED + self.format(*args, **kwargs) #+ self.ENDC

	def blue(self, *args, **kwargs):
		return self.BLUE + self.format(*args, **kwargs) #+ self.ENDC

	def green(self, *args, **kwargs):
		return self.GREEN + self.format(*args, **kwargs) #+ self.ENDC

	def warn(self, *args, **kwargs):
		return self.WARNING + self.format(*args, **kwargs) #+ self.ENDC

	def fail(self, *args, **kwargs):
		return self.FAIL + self.format(*args, **kwargs) #+ self.ENDC

	def orange(self, *args, **kwargs):
		return self.ORANGE + self.format(*args, **kwargs) #+ self.ENDC

	def yellow(self, *args, **kwargs):
		return self.YELLOW + self.format(*args, **kwargs) #+ self.ENDC

	def bold(self, *args, **kwargs):
		return self.BOLD + self.format(*args, **kwargs) #+ self.ENDC

	def uline(self, *args, **kwargs):
		return self.UNDERLINE + self.format(*args, **kwargs) #+ self.ENDC

	def echo(self, *args, f='', end=None, label=False, **kwargs):

		if not label and self.before:
			args = self.before(self) + args

		b4 = f
		if f and re.search(r'^(?:.*\,)?\s*(hr)\s*(?:\,.*)?$', f):
			txt = self.hr(*args, **kwargs)
			f = re.sub(r'^(.*\,)?\s*(hr)\s*(\,.*)?$', r'\1\3', f)
		else:
			txt = self.format(*args, **kwargs)

		for style in f.split(','):
			style = style.strip()
			if style.isdigit():
				txt = '\033[' + style + 'm' + txt + self.ENDC
			elif style:
				style = getattr(self, style)
				txt = style(txt)

		self.printfunc(txt, self.ENDC)
		self.autobr and self.br()
		end and	(self.br() if end is True and not self.autobr else self.printfunc(end))
		return self

	def br(self):
		self.printfunc('%s\n' % self.ENDC)
		return self

	def __call__(self, *args, **kwargs):
		return self.echo(*args, **kwargs)



def parse_args(self, args):
	style = None
	prev = None
	for arg in args:
		pass


echo = Echo()
