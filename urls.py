# NOTE: Must import *, since Django looks for things here, e.g. handler500.
from django.conf.urls.defaults import *

# Load the opentransit application's URLs
urlpatterns = patterns('', url(r'', include('opentransit.urls')))

# Load the GAEUNIT URLs.
urlpatterns += patterns('gaeunit.gaeunit', 
    url(r'^admin/test.*$', 'django_test_runner'),
    url(r'^admin/run', 'django_json_test_runner'),
)
    