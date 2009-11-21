"""nameddict - Modifiable namedtuple, with named indexing

Original idea and help from Dave Peck <davepeck@davepeck.org> <http://davepeck.org/>.

Supports obj.a to access field named "a".  Named indexing means ["name"] instead of [0].

Defaults are stored as _defaults, which is modifiable.  Fields are stored as _fields, which should be treated readonly.

TODO:
- document interface more thoroughly
- write tests, cleanup
- see if it's better to go the exec route (as namedtuple does)
- decide if the field ordering is expected or implementation detail
    - currently the given ordering is kept
"""

import re
import sys
from keyword import iskeyword


def validate_names(names):
    seen = set()
    for name in names:
        if iskeyword(name) or not re.match("^[a-zA-Z][a-zA-Z0-9_]*$", name):
            raise ValueError("invalid: %r" % name)
        elif name in seen:
            raise ValueError("duplicate: %r" % name)
        else:
            seen.add(name)


def nameddict(name=None, keys=(), defaults=None, module=None):
    if defaults is None:
        defaults = {}
    keys = list(keys) # handles all iterables
    keys.extend(k for k in defaults.keys() if k not in keys)
    keys = set(keys)
    validate_names(keys)

    class nameddict(object):
        __slots__ = keys
        _fields = keys
        _defaults = defaults
                
        @classmethod
        def from_dict(cls, d):
            clean_d = {}
            for k, v in d.iteritems():
                clean_d[str(k)] = v
            return cls(**clean_d)
            
        def __init__(self, **values):
            for k, v in defaults.iteritems():
                setattr(self, k, v)
            for k, v in values.iteritems():
                if k not in keys:
                    raise Exception("Invalid key.")
                setattr(self, k, v)

        def __getitem__(self, attr):
            return getattr(self, attr)

        def __setitem__(self, attr, value):
            if attr not in keys:
                raise Exception("Invalid key.")
            setattr(self, attr, value)

        def __delitem__(self, attr):
            delattr(self, attr)

        def __iter__(self):
            return iter(self._fields)

        def _items(self, default=None):
            for k in self:
                yield k, getattr(self, k, default)

        def to_dict(self, default=None):
            return dict((k, getattr(self, k, default)) for k in self)

        def __repr__(self):
            # nameddict.__module__ instead of self.__module__ or type(self).__module__
            # not sure, but I think this is the least fragile
            # of couse, __repr__ may be overridden in a derived class
            return "%s.%s(%s)" % (nameddict.__module__, nameddict.__name__,
                ", ".join("%s=%r" % (k, getattr(self, k)) for k in self if hasattr(self, k)))
                # using hasattr instead of getattr(self, k, None)
                # which is slightly different: missing attributes are missing, instead of =None
                # e.g. (a=1) instead of (a=1, b=None)

    nameddict.__name__ = name or "<nameddict>"
    if module is not None:
        nameddict.__module__ = module
    elif hasattr(sys, '_getframe'):
        # if no sys._getframe, pass module=__name__
        nameddict.__module__ = sys._getframe(1).f_globals.get("__name__", "__main__")
    else:
        nameddict.__module__ = "<unknown>"

    return nameddict


def main():
    D = nameddict("D", ["a"], {"b": 3})
    d = D()
    print type(d).__name__, repr(d), repr(type(d))
    d.a = 42
    print d["a"]
    print d.b
    print d.to_dict()
    print list(d._items())
    print d._fields, d._defaults, d.__slots__
    print
    print nameddict(keys="a b c".split(), module=__name__)
    print nameddict(keys="a b c".split(), module=__name__)()


if __name__ == "__main__":
    import pdb
    try:
        main()
    except Exception, e:
        print "%s: %s" % (type(e).__name__, e)
        pdb.post_mortem(sys.exc_info()[2])
