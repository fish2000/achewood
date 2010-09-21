import os, sys, codecs, time
from decorator import decorator
from functools import partial
from pprint import pprint, pformat

def decoflex(decfac, *args, **kw):
	def wrapped(df, param=None, *args, **kw):
		return partial(df, param, *args, **kw)
	return partial(wrapped, decfac, *args, **kw)


@decoflex
def monkeypatch(cls, f, *args, **kwargs):
	if 'fname' in kwargs:
		setattr(cls, kwargs["fname"], f)
		del kwargs['fname']
	else:
		if not hasattr(f, "__name__"):
			raise AttributeError("Need 'fname' attribute OR __name__ for decorated function")
		else:
			setattr(cls, f.__name__, f)
	return f


## misc decorators
@decorator
def test(f, *args, **kwargs):
	sout = codecs.getwriter('iso-8859-1')(sys.stdout)
	print "\n"
	#print "=============================================================================="
	print "TESTING: %s()" % getattr(f, "__name__", "<unnamed>")
	print "------------------------------------------------------------------------------"
	print "\n"
	t1 = time.time()
	out = f(*args, **kwargs)
	t2 = time.time()
	dt = str((t2-t1)*1.00)
	dtout = dt[:(dt.find(".")+4)]
	print "------------------------------------------------------------------------------"
	print 'RESULTS:'
	#print '%s\n' % out
	pprint(out)
	print 'Test finished in %ss' % dtout
	print "=============================================================================="


@decorator
def timeit(f, *args, **kwargs):
	t1 = time.time()
	out = f(*args, **kwargs)
	t2 = time.time()
	dt = str((t2-t1)*1.00)
	dtout = dt[:(dt.find(".")+4)]
	return dtout, out


@decorator
def onlinetest(f, *args, **kwargs):
	yrself = args[0] # ?!
	if yrself.online:
		test(f, *args, **kwargs)
	else:
		test(lambda: "(OFFLINE)")


## next three from http://pypi.python.org/pypi/decorator
@decorator
def trace(f, *args, **kwargs):
	#print "%s :: %s, %s" % (f.__name__, args, kwargs)
	out = f(*args, **kwargs)
	
	sys.stderr.write("\n>>> TRACE: %s :: %s \n>>> %s \n>>> %s \n>>> %s \n" % (
		#hasattr(f, "__module__") and f.__module__ or "NIL",
		hasattr(f, "im_class") and f.im_class or "NIL",
		f.__name__,
		(len(args) > 0) and "ARGS: \n %s" % pformat(args, indent=5) or "ARGS: NONE",
		(len(kwargs) > 0) and "KW: \n %s" % pformat(kwargs, indent=5) or "KW: NONE",
		out and "OUT: \n %s" % pformat(out, indent=5) or "OUT: NONE",
	))
	
	return out


def memoize(f):
	f._cache = {}
	return decorator(_memoize, f)


def _memoize(f, *args, **kw):
	if kw:
		key = args, frozenset(kw.iteritems())
	else:
		key = args
	_cache = f._cache
	if key in _cache:
		return _cache[key]
	else:
		_cache[key] = out = f(*args, **kw)
		return out

