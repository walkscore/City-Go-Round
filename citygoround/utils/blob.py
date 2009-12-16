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

    from bootstrap import BREAKPOINT; BREAKPOINT()
    request_bytes = request.META['wsgi.input'].read()
    fixed_request_bytes = request_bytes.replace('\n', '\r\n')    
    request.environ['wsgi.input'].close()    
    request.environ['wsgi.input'] = StringIO(fixed_request_bytes)
    return request