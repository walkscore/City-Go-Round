# Standard Python Imports
import os
import sys
import logging

# Log a message each time this module get loaded.
logging.info('Loading %s, app version = %s', __name__, os.getenv('CURRENT_VERSION_ID'))

def bootstrap_django():
    # Declare the Django version we need.
    from google.appengine.dist import use_library
    use_library('django', '1.1')

    # Fail early if we can't import Django 1.x.  Log identifying information.
    import django
    logging.info('django.__file__ = %r, django.VERSION = %r', django.__file__, django.VERSION)
    assert django.VERSION[0] >= 1, "This Django version is too old"

    # Custom Django configuration.
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    from django.conf import settings
    settings._target = None
    
bootstrap_django()

# AppEngine imports.
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template as template_registrar

# Helper to enter the debugger.  This passes in __stdin__ and
# __stdout__, because stdin and stdout are connected to the request
# and response streams.  You must import this from __main__ to use it.
# (I tried to make it universally available via __builtin__, but that
# doesn't seem to work for some reason.)
def BREAKPOINT():
  import pdb
  p = pdb.Pdb(None, sys.__stdin__, sys.__stdout__)
  p.set_trace()

# Import various parts of Django.
import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher
import django.forms

# Work-around to avoid warning about django.newforms in djangoforms.
django.newforms = django.forms

# Django signal handler to log an exception
def log_exception(*args, **kwds):
  if sys is None:
      pass
  else:
      cls, err = sys.exc_info()[:2]
      logging.exception('Exception in request: %s: %s', cls.__name__, err)

# Log all exceptions detected by Django.
django.core.signals.got_request_exception.connect(log_exception)

# Unregister Django's default rollback event handler.
django.core.signals.got_request_exception.disconnect(django.db._rollback_on_exception)

def main():
    application = django.core.handlers.wsgi.WSGIHandler()
    template_registrar.register_template_library('citygoround.tags')    
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
