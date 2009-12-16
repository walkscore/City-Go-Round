# Random tools to help us work with App Engine's blobstore

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.core.handlers import wsgi


def work_around_app_engine_blobstore_internal_redirect_bug(request):
    """
    App Engine's internal redirect code hands us a wsgi request with improperly encoded
    multipart form data. As it so happens, it is possible to mecahnically fix said improper
    encoding, so we go ahead and do so here.
    """

    # TODO davepeck: determine if this is a bug in production App Engine, too...
    if not settings.RUNNING_APP_ENGINE_LOCAL_SERVER:
        return request

    request_bytes = request.META['wsgi.input'].read()
    request.META['wsgi.input'].close()
    request_bytes.replace('\n', '\r\n')    
    new_request_file = StringIO(request_bytes)
    new_request_environ = request.environ
    new_request_environ['wsgi.input'] = new_request_file    
    working_request = wsgi.WSGIRequest(environ = new_request_environ)
    
    return working_request
