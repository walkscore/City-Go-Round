import sys
import traceback

def BREAKPOINT():
    import pdb
    p = pdb.Pdb(None, sys.__stdin__, sys.__stdout__)
    p.set_trace()

def _typename(t):
    if t:
        return str(t).split("'")[1]
    else:
        return "{type: None}"

def _typeof(thing):
    return _typename(type(thing))

def exception_string():
    exc = sys.exc_info()
    exc_type = _typename(exc[0])
    exc_message = str(exc[1])
    exc_contents = "".join(traceback.format_exception(*sys.exc_info()))
    return "[%s]\n %s" % (exc_type, exc_contents)
