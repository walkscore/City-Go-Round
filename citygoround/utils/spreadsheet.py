import os

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

try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper  # Python 2.3, 2.4 fallback.

from google.appengine.api.urlfetch import fetch as fetch_url


def get_spreadsheet(key, worksheetId):
    """ gets helpfully formatted data from a google spreadsheet """
    
    jsondata = json.loads( fetch_url( "http://spreadsheets.google.com/feeds/list/%s/%s/public/values?alt=json"%(key,worksheetId) ).content )

    for entry in jsondata["feed"]["entry"]:
        updated_str = entry['updated']['$t'] 
        updated = datetime.strptime( updated_str[:updated_str.index(".")] , "%Y-%m-%dT%H:%M:%S")
        
        data = dict( [ (k[4:], v['$t']) for k, v in entry.items() if "gsx$" in k ] )
            
        yield {'updated':updated, 'data':data}