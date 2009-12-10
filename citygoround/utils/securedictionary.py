import os

# NOTE davepeck:
# This code is a heavily modified version of Werkzeug's secure cookie code.
# The copyright to this code is owned by Werkzeug's specific authors, though I have
# made substantial changes. It is no longer concerned just with cookies, and it plays
# nicely in a django + App Engine world.

from hashlib import sha1
import cPickle as pickle
from hmac import new as hmac
import urllib

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.template import RequestContext
import django.shortcuts
from django.conf import settings
from datetime import datetime

from .quote import url_quote, url_quote_plus, url_unquote, url_unquote_plus

try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from google.appengine.api.urlfetch import fetch as fetch_url


class UnquoteError(Exception):
    pass

_timegm = None
def _date_to_unix(arg):
    global _timegm
    if isinstance(arg, datetime):
        arg = arg.utctimetuple()
    elif isinstance(arg, (int, long, float)):
        return int(arg)
    if _timegm is None:
        from calendar import timegm as _timegm
    return _timegm(arg)

def _quote(value):
    return ''.join(pickle.dumps(value).encode('base64').splitlines()).strip()

def _unquote(value):
    try:
        return pickle.loads(value.decode('base64'))
    except:
        raise UnquoteError("whoops.")

def serialize_dictionary(dictionary, secret_key=settings.SERIALIZATION_SECRET_KEY, expires=None):
    secret_key = str(secret_key)    
    if expires:
        dictionary['_expires'] = _date_to_unix(expires)        
    mac = hmac(secret_key, None, sha1)
    result = []
    for key, value in dictionary.iteritems():
        result.append('%s=%s' % (url_quote_plus(key), _quote(value)))
        mac.update('|' + result[-1])        
    return '%s?%s' % (mac.digest().encode('base64').strip(),'&'.join(result))

def deserialize_dictionary(string, secret_key=settings.SERIALIZATION_SECRET_KEY):
    items = None
    if isinstance(string, unicode):
        string = string.encode('utf-8', 'ignore')
    try:
        base64_hash, data = string.split('?', 1)        
    except (ValueError, IndexError):
        items = None
    else:
        items = {}
        mac = hmac(secret_key, None, sha1)
        for item in data.split('&'):
            mac.update('|' + item)
            if not '=' in item:
                items = None
                break
            key, value = item.split('=', 1)
            # try to make the key a string
            key = url_unquote_plus(key)
            try:
                key = str(key)
            except UnicodeError:
                pass
            items[key] = value

        # no parsing error and the mac looks okay, we can now
        # sercurely unpickle our cookie.
        try:
            client_hash = base64_hash.decode('base64')
        except Exception:
            items = client_hash = None
        if items is not None and client_hash == mac.digest():
            try:
                for key, value in items.iteritems():
                    items[key] = _unquote(value)
            except UnquoteError:
                items = None
            else:
                if '_expires' in items:
                    if time() > items['_expires']:
                        items = None
                    else:
                        del items['_expires']
        else:
            items = None
    return items
